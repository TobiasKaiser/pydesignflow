PyDesignFlow: Micro-Framework for FPGA / VLSI Design Flow in Python
===================================================================

PyDesignFlow is a **technology- and tool-agnostic micro-framework** for building **FPGA / VLSI design flows** in Python.

Principles:

- All design objects are managed by a central **Flow** object, which is accessible via the command line tools *flow*. 
- A **Block** encapsulates a part of the design, e.g. a hardware component, a testbench or a software program.

  - Blocks are defined by subclassing *pydesignflow.Block*. One or more instances of the block are then added to the central *Flow* object.
  - In hierarchical designs, blocks can depend on other blocks. For example, this allows bottom-up hardware design, where small hardware components are first built and then integrated into larger hardware systems. Block boundaries are set by hand.
  - Blocks can have parameters / configuration options. A Block class can be instantiated with different options under different names.
  - Simple designs may be realized with a single block only.

- Every Block can define one or more **Tasks**.

  - Tasks are Python class methods using the special *@pydesignflow.task* decorator.
  - A task of a specific Block instance is called **Target**. Targets / Tasks can be built using the *flow* command line tool.
  - Running a Target produces a **Result**. There can be at most one result per target.
  
- **Task Dependencies:** Targets / Tasks can depend on Results of other Targets.

  - Missing dependencies are built automatically.
  - Dependencies marked as *always_rebuild* are always rebuilt.
  - In contrast to Makefiles, PyDesignFlow does not track source file changes.
  - A dependency not marked as *always_rebuild* with Result present it is never rebuilt. This means that the designer must remember to rebuild / clean Targets by hand if source files have changed.
  - By not having to specify correct source file dependencies, the design flow is kept simple. Furthermore, by giving the designer the choice of when to rebuild Results, long tool runtimes can be avoided. Maximum control over the design flow is retained.  

Full documentation is found at https://pydesignflow.readthedocs.io or in the docs/ folder.

License
-------

Copyright 2022 - 2024 Tobias Kaiser

SPDX-License-Identifier: Apache-2.0