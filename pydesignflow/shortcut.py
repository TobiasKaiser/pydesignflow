import importlib.util
from pathlib import Path
import sys
import os
import warnings

def import_flow_addpath():
    if not Path(Path.cwd() / "flow" / "__init__.py").exists():
        raise FileNotFoundError()
    sys.path.insert(0, str(Path.cwd()))
    import flow
    return flow

def import_flow_importlib():
    spec=importlib.util.spec_from_file_location("flow", Path.cwd() / "flow" / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["flow"] = module
    spec.loader.exec_module(module)
    return module

import_flow = import_flow_importlib
"""
import_flow can be set to import_flow_importlib or import_flow_addpath.
They should both do roughly the same.
"""


def main():
    warnings.simplefilter('always', DeprecationWarning)

    try:
        flow = import_flow()
    except FileNotFoundError:
        print("Error: Could not import flow module.")
        print("Ensure that your working directory has a subdirectory flow/ with __init__.py.")
        sys.exit(1)

    prog = os.path.basename(sys.argv[0])
    args = sys.argv[1:]
    flow.flow.cli_main(args)

    #print("Hello, World!")
    #print(sys.argv)

if __name__=="__main__":
    main()