import re
import shutil
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from .errors import FlowError
from .result import Result

@dataclass(frozen=True, eq=True)
class TargetId:
    block_id: str
    task_id: str

    def __str__(self):
        return f"{self.block_id}.{self.task_id}"

def parse_requirement_spec(spec):
    m = re.match(r"((=)?([a-zA-Z0-9_]+))?\.([a-zA-Z0-9_]+)", spec)
    if not m:
        raise ValueError(f"Malformed requirement spec \"{spec}\".")
    task_id = m.group(4)
    is_direct_ref = bool(m.group(2))
    block_ref = m.group(3)

    return is_direct_ref, block_ref, task_id

class TargetPrototype:
    """
    TargetPrototypes exist once per class. They are created from the @task
    decorator at class setup time.

    The corresponding Target objects are then created at runtime using the
    create method.

    This could possibly also be solved with a metaclass.

    This is only a problem if there are multiple instances of the same Target
    e.g. due to multiple instances of a block.
    """
    def __init__(self, func, requires, always_rebuild, hidden):
        self.func = func
        self.requires = requires
        self.always_rebuild = always_rebuild
        self.hidden = hidden

    def create(self):
        return Target(self.func, self.requires, self.always_rebuild, self.hidden)

class Target:
    @property
    def __doc__(self):
        return self.func.__doc__

    def __init__(self, func, requires, always_rebuild, hidden):
        self.func = func
        self.requires = requires
        self.block = None
        self.id = None
        self.always_rebuild = always_rebuild
        self.hidden = hidden
        self._registered = False

    def register(self, block, task_id):
        """
        Called by Block
        """
        if self._registered:
            raise FlowError(f"Attempt to register {self} multiple times.")
        self.block = block
        self.id = task_id
        self._registered = True

    def parse_requires(self):
        for k, v in self.requires.items():
            is_direct_ref, block_ref, task_id = parse_requirement_spec(v)
            yield k, is_direct_ref, block_ref, task_id
        
    def resolve_requires(self):
        for key, is_direct_ref, block_ref, task_id in self.parse_requires():
            if is_direct_ref:
                block_id = block_ref
            elif block_ref:
                block_id = self.block.dependency_map[block_ref]
            else:
                block_id = self.block.id

            yield key, TargetId(block_id, task_id)

    def missing_requires(self, sess, rebuild:bool):
        for _, tid in self.resolve_requires():
            result_exists = (tid in sess.results)
            target = sess.flow.target(tid)
            if (not result_exists) or rebuild or target.always_rebuild:
                yield tid

    def dependency_results(self, sess):
        kwargs = {}

        for key, result_id in self.resolve_requires():
            kwargs[key] = sess.get_result(result_id)

        return kwargs

    def target_id(self):
        return TargetId(self.block.id, self.id)

    def run(self, sess):
        cwd = sess.task_dir(self.block.id, self.id)

        shutil.rmtree(cwd, ignore_errors=True)

        cwd.mkdir(parents=True, exist_ok=True)

        kwargs = self.dependency_results(sess)

        time_started = datetime.now()
        res = self.func(self.block, cwd, **kwargs)
        time_finished = datetime.now()
        if res:
            res.returned_data = True
        else:
            res = Result()
            res.returned_data = False
        res.time_started = time_started
        res.time_finished = time_finished
        block_id = self.block.id
        task_id = self.id
        json_str = res.json(sess, block_id, task_id)
        sess.write_result(block_id, task_id, json_str)