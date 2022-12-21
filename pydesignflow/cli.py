import sys
import argparse
from pathlib import Path
from .result import Result
from .errors import FlowError, ResultRequired

class ANSITerm:
    FgBrightBlue = "\x1b[94m"
    BgBlue = "\x1b[44m"
    Reset = "\x1b[0m"

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
        parser.add_argument("--no-dependencies", "-N", action="store_true",
            help="Do not build missing requirements.")
        parser.add_argument("--rebuild-requirements", "-R", action="store_true",
            help="Re-build all requirements, even if flow results were found.")
        parser.add_argument("--dry-run", "-d", action="store_true",
            help="Print but do not run build plan.")
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

        self.build_requirements = "missing"
        if self.args.rebuild_requirements:
            self.build_requirements = "all"
        elif self.args.no_dependencies:
            self.build_requirements = None

        self.sess = self.flow.session_at(self.args.build_dir)

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
                build_requirements=self.build_requirements
            )
        except ResultRequired as r:
            print(r)
        else:
            print(f"{ANSITerm.FgBrightBlue}PyDesignFlow Build Plan:{ANSITerm.Reset}\n{p}\n")
            if not self.args.dry_run:
                p.run(style=ANSITerm.FgBrightBlue, style_reset=ANSITerm.Reset)

    def print_status(self):
        if self.args.no_dependencies:
            print("--no-dependencies requires block and task")
            sys.exit(1)
        if self.args.rebuild_requirements:
            print("--rebuild-requirements requires block and task")
            sys.exit(1)
        print(self.sess.status(block_id=self.args.block))