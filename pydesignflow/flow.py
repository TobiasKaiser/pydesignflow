"""
Provides the Flow class and a corresponding 'flow' command-line interface.
"""

import sys
import os
import importlib
from pathlib import Path
import argparse

class Flow():
    def __init__(self):
        self.blocks = {}

    def ___getitem__(self, key):
        return self.blocks[key]

    def __setitem__(self, key, value):
        if key in self.blocks:
            raise TypeError(f"Block {key} assigned multiple times.")
        self.blocks[key]=value

    def cli_main(self):
        if len(self.blocks) < 1:
            print("Flow.blocks_dict is empty. Please define at least one block.")
            sys.exit(1)
        
        parser = argparse.ArgumentParser(description='PyDesignFlow command line interface')

        default_build_dir = Path.cwd() / "build"
        parser.add_argument("--build-dir", "-B", default=default_build_dir, help="Build directory")
        

        #parser.add_argument("block", choices=self.blocks.keys(), help="Block name")
        # Python bug: add_subparsers with required=True requires dest to be set to something else
        # than None; otherwise error reporting is messed up: https://bugs.python.org/issue29298
        subparsers = parser.add_subparsers(help='Select block', dest="block", required=True)
        for key, val in self.blocks.items():
            subparser = subparsers.add_parser(key)
            val.populate_subparser(subparser)

        args = parser.parse_args()

        args.func(args, args.build_dir)

def import_flow_importlib():
    spec=importlib.util.spec_from_file_location("flow", Path.cwd() / "flow" / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["flow"] = module
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError:
        raise ImportError()
    return module

def import_flow_addpath():
    sys.path.insert(0, str(Path.cwd()))
    import flow
    return flow


import_flow = import_flow_importlib
"""
import_flow can be set to import_flow_importlib or import_flow_addpath.
They should both do roughly the same.
"""


def main():
    try:
        flow = import_flow()
    except ImportError:
        print("Could not import flow module. Ensure that your working directory has a subdirectory flow/ with __init__.py.")
        sys.exit(1)

    flow.flow.cli_main()

    #print("Hello, World!")
    #print(sys.argv)

if __name__=="__main__":
    main()