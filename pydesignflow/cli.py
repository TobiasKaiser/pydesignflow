import sys
import argparse
from pathlib import Path
from .result import Result

class CLI:
    def __init__(self, flow):
        self.flow = flow

    def create_parser(self, prog):
        parser = argparse.ArgumentParser(
            description='PyDesignFlow command line interface',
            prog=prog,
        )

        default_build_dir = Path.cwd() / "build"
        parser.add_argument("--build-dir", "-B", default=default_build_dir,
            help="Build directory")
        parser.add_argument("--build-missing-requirements", "-r", action="store_true",
            help="In addition to specified task, build missing requirements.")
        parser.add_argument("--rebuild-requirements", "-R", action="store_true",
            help="Re-build all requirements, even if flow results were found.")
        parser.add_argument("--clean", "-c", action="store_true",
            help="Remove flow results.")
        parser.add_argument("block", nargs='?')
        parser.add_argument("task", nargs='?')

        return parser

    def main(self, args: list[str], prog: str):
        if len(self.flow.blocks) < 1:
            print("No blocks defined. Please define at least one block.")
            sys.exit(1)

        self.args = self.create_parser(prog).parse_args(args)
        self.sess = self.flow.session_at(self.args.build_dir)

        if self.args.clean:
            self.sess.clean(self.args.block, self.args.task)
        elif self.args.block and self.args.task:
            self.build()
        else:
            self.print_status()

    def build(self):
        build_requirements = None
        if self.args.rebuild_requirements:
            build_requirements = "all"
        elif self.args.build_missing_requirements:
            build_requirements = "missing"
        self.sess.run(
            block_id=self.args.block,
            task_id=self.args.task,
            build_requirements=build_requirements,
            verbose=True
        )

    def print_status(self):
        if self.args.build_missing_requirements:
            print("--build-missing-requirements requires block and task")
            sys.exit(1)
        if self.args.rebuild_requirements:
            print("--rebuild-requirements requires block and task")
            sys.exit(1)
        print(self.sess.status(block_id=self.args.block))