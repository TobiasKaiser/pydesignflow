PyDesignFlow: Micro-Framework for FPGA / VLSI Design Flow in Python
===================================================================

**This is work-in-progress and not currently usable yet.**


PyDesignFlow is a **technology- and tool-agnostic micro-framework** for building **FPGA / VLSI design flows** in Python.

Principles:

- A **Block** represents a design part for which certain **Tasks** can be run. Simple designs can be realized with a single block. In hierarchical designs, blocks can be integrated in other blocks. Block boundaries are set by hand, bottom-up design flow is the default.
- Blocks can be instantiated multiple times (e.g. with different configurations).
- A **Target** is one task of a specific Block instance. Targets are identified by (block_id, task_id) tuples.
- Running a target produces a **Result**. There can be at most one result per target.
- The designer must decide whether targets must be rebuilt. PyDesignFlow does not check whether a target requires rebuilding due to source file changes. This simplifies the design flow.

Full documentation is found at https://pydesignflow.readthedocs.io or in the docs/ folder.

License
-------

Copyright 2022 Tobias Kaiser

SPDX-License-Identifier: Apache-2.0