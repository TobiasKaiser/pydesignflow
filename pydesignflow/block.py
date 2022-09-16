from pathlib import Path
import re
import shutil
from datetime import datetime

from .errors import FlowError

from collections import namedtuple
from .result import Result

TargetId = namedtuple('TargetId', ('block_id', 'task_id'))

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
    def __init__(self, func, requires, always_rebuild):
        self.func = func
        self.requires = requires
        self.always_rebuild = always_rebuild

    def create(self):
        return Target(self.func, self.requires, self.always_rebuild)

class Target:
    def __init__(self, func, requires, always_rebuild):
        self.func = func
        self.requires = requires
        self.block = None
        self.id = None
        self.always_rebuild = always_rebuild
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

def task(requires={}, always_rebuild=False):
    return lambda func: TargetPrototype(
        func=func,
        requires=requires,
        always_rebuild=always_rebuild,
    )

class Block():
    def __init__(self, dependency_map={}):
        """
        Args:
            dependecy_map: Dict mapping  block reference strings to block IDs.
                Keys of this dictionary must exactly match the blocks referenced.
        """
        self.tasks={}
        self.block_references = set()
        self.auto_register_tasks()
        self.id = None
        self._registered = False

        expected_block_refs = self.get_all_block_refs()
        if set(dependency_map.keys()) != expected_block_refs:
            raise ValueError(f"dependency_map must declare exactly "
                f"the following block references: {expected_block_refs}")

        self.dependency_map=dependency_map

    def register(self, flow, block_id):
        """
        Called by Flow
        """
        if self._registered:
            raise FlowError(f"Attempt to register {self} multiple times.")
        self.id = block_id
        self.flow = flow
        self._registered = True
        self.setup()

    def setup(self):
        """
        Override this method in subclasses to provide setup functionality.
        """
        pass


    def auto_register_tasks(self):
        """
        Registers all Target objects in the .tasks dictionary.

        Alternately, a similar automatic detection can be implemented using a
        metaclass and __prepare__.
        """
        for key in dir(self):
            val = getattr(self, key)
            if isinstance(val, TargetPrototype):
                # Bidirectional reference:
                act = val.create()
                act.register(self, key)
                self.tasks[key] = act

    def get_all_block_refs(self):
        block_refs = set()
        for task in self.tasks.values():
            for _, is_direct_ref, block_ref, _ in task.parse_requires():
                if not is_direct_ref and block_ref:
                    block_refs.add(block_ref)
        return block_refs