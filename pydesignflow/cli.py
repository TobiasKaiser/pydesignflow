import sys
import argparse
from pathlib import Path
from .result import Result
from .errors import FlowError, ResultRequired
from .ansiterm import ANSITerm
from .target import TargetId

class CLI:
    def __init__(self, flow):
        self.flow = flow

    def create_parser(self, prog):
        parser = argparse.ArgumentParser(
            description='PyDesignFlow command line interface',
            prog=prog,
        )

        default_build_dir = str(Path.cwd() / "build")
        parser.add_argument("--build-dir", "-B", default=default_build_dir,
            help="Build directory")
        parser.add_argument("--no-dependencies", "-N", action="store_true",
            help="Do not build missing dependencies.")
        parser.add_argument("--rebuild-dependencies", "-R", action="store_true",
            help="Re-build all dependencies, even if flow results were found.")
        parser.add_argument("--dry-run", "-d", action="store_true",
            help="Print but do not run build plan.")
        parser.add_argument("--clean", "-c", action="store_true",
            help="Remove flow results.")
        parser.add_argument("--hidden", "-a", action="store_true",
            help="Show hidden target.")
        parser.add_argument("block", nargs='?')
        parser.add_argument("task", nargs='?')

        return parser

    def main(self, args: list[str], prog: str):
        if len(self.flow.blocks) < 1:
            raise SystemExit("No blocks defined. Please define at least one block.")

        self.args = self.create_parser(prog).parse_args(args)

        if self.args.block and ('.' in self.args.block):
            if self.args.task != None:
                raise SystemExit("Too many arguments.")
            self.args.block, self.args.task = self.args.block.split('.', 1)

        self.build_dependencies = "missing"
        if self.args.rebuild_dependencies:
            self.build_dependencies = "all"
        elif self.args.no_dependencies:
            self.build_dependencies = None

        self.sess = self.flow.session_at(Path(self.args.build_dir))

        if self.args.block and not self.flow.has_block(self.args.block):
            raise SystemExit(f"Block '{self.args.block}' not found.")

        tid = TargetId(self.args.block, self.args.task)
        if self.args.task and not self.flow.has_target(tid):
            raise SystemExit(f"Target '{tid}' not found.")


        if self.args.clean:
            self.sess.clean(self.args.block, self.args.task)
        elif self.args.block and self.args.task:
            self.build()
        else:
            self.print_status()

    def build(self):
        try:
            p = self.sess.plan(
                block_id=self.args.block,
                task_id=self.args.task,
                build_dependencies=self.build_dependencies
            )
        except ResultRequired as r:
            print(r)
        else:
            print(f"{ANSITerm.FgBrightBlue}PyDesignFlow Build Plan:{ANSITerm.Reset}\n{p}\n")
            if not self.args.dry_run:
                p.run()

    def print_status(self):
        if self.args.no_dependencies:
            print("--no-dependencies requires block and task")
            sys.exit(1)
        if self.args.rebuild_dependencies:
            print("--rebuild-dependencies requires block and task")
            sys.exit(1)
        if self.args.block:
            self.args.hidden = True
        print(self.sess.status(block_id=self.args.block, show_hidden=self.args.hidden))