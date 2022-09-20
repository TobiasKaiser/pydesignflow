from .errors import FlowError
from .target import TargetPrototype
from warnings import warn

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

        self.verify_block_refs(dependency_map)
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
        Subclasses should override this method to perform setup steps.
    
        Setup is performed during Flow creation, before any targets are
        executed but after the Flow objects registers the Block object.
        This means that, in contrast to __init__, the setup method can access
        the the .flow object, e.g. to read self.flow.base_dir.
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

    def required_block_refs(self) -> list[str]:
        """
        Returns:
            List of block names, which need to be provided to the constructor
            via dependency_map.
        """
        block_refs = set()
        for task in self.tasks.values():
            for _, is_direct_ref, block_ref, _ in task.parse_requires():
                if not is_direct_ref and block_ref:
                    block_refs.add(block_ref)
        return block_refs

    def verify_block_refs(self, dependency_map):
        """
        Raises ValueError if there is a mismatch between the dependencies
        provided to the constructor via dependency_map and the dependencies
        required by the tasks.
        """
        expected_block_refs = self.required_block_refs()
        if set(dependency_map.keys()) != expected_block_refs:
            raise ValueError(f"dependency_map must declare exactly "
                f"the following block references: {expected_block_refs}")