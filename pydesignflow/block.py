from pathlib import Path
import re

from .errors import FlowError

from collections import namedtuple
ResultId = namedtuple('ResultId', ('block_id', 'action_id'))


def parse_requirement_spec(spec):
    m = re.match(r"((=)?([a-zA-Z0-9_]+))?\.([a-zA-Z0-9_]+)", spec)
    if not m:
        raise ValueError(f"Malformed requirement spec \"{spec}\".")
    action_id = m.group(4)
    is_direct_ref = bool(m.group(2))
    block_ref = m.group(3)

    return is_direct_ref, block_ref, action_id

class ActionPrototype:
    """
    ActionPrototypes exist once per class. They are created from the @action
    decorator at class setup time.

    The corresponding Action objects are then created at runtime using the
    create method.

    This could possibly also be solved with a metaclass.
    """
    def __init__(self, func, requires):
        self.func = func
        self.requires = requires        

    def create(self):
        return Action(self.func, self.requires)

class Action:
    def __init__(self, func, requires):
        self.func = func
        self.requires = requires
        self.block = None
        self.id = None
        self._registered = False

    def register(self, block, action_id):
        """
        Called by Block
        """
        if self._registered:
            raise FlowError(f"Attempt to register {self} multiple times.")
        self.block = block
        self.id = action_id
        self._registered = True

    def parse_requires(self):
        for k, v in self.requires.items():
            is_direct_ref, block_ref, action_id = parse_requirement_spec(v)
            yield k, is_direct_ref, block_ref, action_id
        
    def resolve_requires(self, block_id_self):
        for key, is_direct_ref, block_ref, action_id in self.parse_requires():
            if is_direct_ref:
                block_id = block_ref
            elif block_ref:
                block_id = self.block.dependency_map[block_ref]
            else:
                block_id = block_id_self

            yield key, ResultId(block_id, action_id)    

    def dependency_results(self, sess):
        kwargs = {}

        for key, result_id in self.resolve_requires(self.block.id):
            kwargs[key] = sess.get_result(result_id)

        return kwargs

    def run(self, sess):
        cwd = sess.action_dir(self.block.id, self.id)

        cwd.mkdir(parents=True, exist_ok=True)

        kwargs = self.dependency_results(sess)

        res = self.func(self.block, cwd, **kwargs)
        if res != None:
            block_id = self.block.id
            action_id = self.id
            json_str = res.json(sess, block_id, action_id)
            sess.write_result(block_id, action_id, json_str)

def action(requires={}):
    return lambda func: ActionPrototype(func, requires)

class Block():
    def __init__(self, dependency_map={}):
        """
        Args:
            dependecy_map: Dict mapping  block reference strings to block IDs.
                Keys of this dictionary must exactly match the blocks referenced.
        """
        self.actions={}
        self.block_references = set()
        self.auto_register_actions()
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


    def auto_register_actions(self):
        """
        Registers all Action objects in the .actions dictionary.

        Alternately, a similar automatic detection can be implemented using a
        metaclass and __prepare__.
        """
        for key in dir(self):
            val = getattr(self, key)
            if isinstance(val, ActionPrototype):
                # Bidirectional reference:
                act = val.create()
                act.register(self, key)
                self.actions[key] = act

    def get_all_block_refs(self):
        block_refs = set()
        for action in self.actions.values():
            for _, is_direct_ref, block_ref, _ in action.parse_requires():
                if not is_direct_ref and block_ref:
                    block_refs.add(block_ref)
        return block_refs