"""
Provides the Flow class and a corresponding 'flow' command-line interface.
"""

from pathlib import Path
from .session import BuildSession
from .cli import CLI
from .target import TargetId, Target

class Flow:
    def __init__(self):
        self.blocks = {}

    def __iter__(self):
        return iter(self.blocks)

    def __getitem__(self, key):
        return self.blocks[key]

    def __setitem__(self, key, value):
        if key in self.blocks:
            raise TypeError(f"Block {key} assigned multiple times.")
        self.blocks[key]=value
        value.register(self, key)

    @property
    def base_dir(self):
        """
        Returns the flow base directory, which typically includes flow.py or
        flow/__init__.py. Currently, it is assumed that this is always the
        current working directory (cwd). 
        """
        return Path.cwd()

    def session_at(self, build_dir):
        return BuildSession(self, build_dir)

    def cli_main(self, args: list[str], prog="flow") -> None:
        """
        Invoke the Flow's command line interface.
        
        Args:
            args: List of command line arguments, e.g. argv[1:]
            prog: Name of executable, e.g. argv[0]
        """
        CLI(self).main(args, prog)

    def target(self, result_id: TargetId) -> Target:
        return self[result_id.block_id].tasks[result_id.task_id]