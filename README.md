# PyDesignFlow

A **technology- and tool-agnostic micro-framework** for building **FPGA / VLSI design flows** in Python.

## Quick Example

```python
from pydesignflow import Block, Flow, task, Result

class SynthesisBlock(Block):
    @task()
    def synthesize(self, cwd):
        # [Call synthesis tool here]
        result = Result()
        result.timing_met = True
        result.netlist = cwd / "netlist.v"
        return result

    @task(requires={'syn': '.synthesize'})
    def place_and_route(self, cwd, syn):
        if not syn.timing_met:
            raise RuntimeError("Synthesis timing not met, cannot proceed with P&R")
        print(f"Using netlist: {syn.netlist}")
        # [Call place & route tool here]
        result = Result()
        result.bitstream = cwd / "design.bit"
        result.utilization = 0.75
        return result

flow = Flow()
flow['fpga'] = SynthesisBlock()

if __name__ == '__main__':
    flow.cli_main()
```

Save this as `flow.py` (or `flow/__init__.py` as basis for a multi-file design flow), then run targets from the command line:

```bash
flow fpga.place_and_route
```

## Key Concepts

- **Flow**: Central object managing all design blocks, accessible via command line
- **Block**: Encapsulates a design component (hardware block, testbench, etc.). Define by subclassing `Block`.
- **Task**: Methods decorated with `@task()` that perform design steps. A task of a specific block instance is called a **Target**.
- **Result**: Data returned by tasks, serialized to JSON. At most one result per target.
- **Dependencies**: Tasks can depend on results from other tasks. Missing dependencies are built automatically.

## Design Principles

- **No source file tracking**: Unlike Make, PyDesignFlow doesn't track source changes. The designer decides when to rebuild, avoiding unnecessary long tool runtimes while maintaining simplicity.
- **Encapsulation**: Each task gets its own output directory and should only write there.
- **Flexibility**: Blocks support parameters through instantiation. Single or multi-block hierarchical designs are supported.

## Example Projects

- **[RISC-V Lab](https://github.com/tub-msc/rvlab)**: An FPGA-based RISC-V design platform and flow for teaching SoC development, using PyDesignFlow to manage hardware synthesis, simulation, and software builds.

## Related Tools

- **[NoTcl](https://github.com/TobiasKaiser/notcl)**: Python library for automating Tcl-based FPGA/VLSI tools without Tcl scripting, complementing PyDesignFlow by providing Python interfaces to design tools.

## Documentation

Full documentation: https://pydesignflow.readthedocs.io

## License

Copyright 2022 - 2026 Tobias Kaiser

SPDX-License-Identifier: Apache-2.0
