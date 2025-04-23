# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import sys
import os
from pathlib import Path

try:
    import argcomplete
except:
    argcomplete = None

import argparse

from .errors import ResultRequired
from .ansiterm import ANSITerm, NoColor
from .target import TargetId
from .monitor import monitor

class CLI:
    def __init__(self, flow):
        self.flow = flow

    def create_parser(self, prog):

        def block_completer(prefix, parsed_args, **kwargs):
            if '.' in prefix:
                # Dot-Notation
                block = prefix.split('.')[0]
                parsed_args.block = block
                return {f"{block}.{k}":v for k,v in task_completer(parsed_args=parsed_args, prefix=prefix, **kwargs).items()}
            return {x:"Blocks" for x in self.flow.blocks.keys()}

        def task_completer(parsed_args, **kwargs):
            block = parsed_args.block
            if (block == None) or (block not in self.flow.blocks):
                # no task suggestions when no/undefined block is defined
                return []
            return {x:"Tasks" for x in self.flow.blocks[block].tasks.keys()}

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
        parser.add_argument("--monitor", "-M", action="store_true",
            help="Continuously monitor build directory for changes. A message is printed whenever a new target build is started or finished.")
        parser.add_argument("--hidden", "-a", action="store_true",
            help="Show hidden target.")
        parser.add_argument("--no-color", "-n", action="store_true",
            help="Do not color output.")
        parser.add_argument("--brief", "-b", action="store_true",
            help="Show brief list of blocks and target names instead of detailed table.")
        parser.add_argument("block", nargs='?').completer = block_completer
        parser.add_argument("task", nargs='?').completer = task_completer

        if argcomplete:
            argcomplete.autocomplete(parser, always_complete_options=False)
        return parser

    def main(self, args: list[str], prog: str):
        # https://stackoverflow.com/questions/12492810/python-how-can-i-make-the-ansi-escape-codes-to-work-also-in-windows
        # Needed for ANSI escape codes (terminal colors) in Windows:
        if os.name == 'nt':
            os.system("")

        if len(self.flow.blocks) < 1:
            raise SystemExit("No blocks defined. Please define at least one block.")

        self.args = self.create_parser(prog).parse_args(args)

        if self.args.no_color or not sys.stdout.isatty():
            self.color = NoColor
        else:
            self.color = ANSITerm

        if self.args.block != None and ('.' in self.args.block):
            if self.args.task != None:
                raise SystemExit("Too many arguments.")
            self.args.block, self.args.task = self.args.block.split('.', 1)

        self.build_dependencies = "missing"
        if self.args.rebuild_dependencies:
            self.build_dependencies = "all"
        elif self.args.no_dependencies:
            self.build_dependencies = None

        self.sess = self.flow.session_at(Path(self.args.build_dir))

        if self.args.monitor:
            if self.args.block != None:
                raise SystemExit("Cannot specify --monitor together with block/task.")
            monitor(self.sess)
            return

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
            print(f"{self.color.FgBrightBlue}PyDesignFlow Build Plan:{self.color.Reset}\n{p}\n")
            if not self.args.dry_run:
                p.run(color=self.color)

    def print_status(self):
        if self.args.no_dependencies:
            print("--no-dependencies requires block and task")
            sys.exit(1)
        if self.args.rebuild_dependencies:
            print("--rebuild-dependencies requires block and task")
            sys.exit(1)
        if self.args.block:
            self.args.hidden = True
        print(self.sess.status(block_id=self.args.block, show_hidden=self.args.hidden, color=self.color, brief=self.args.brief))
