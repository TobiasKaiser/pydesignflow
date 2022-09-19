PyDesignFlow: Micro-Framework for FPGA / VLSI Design Flow in Python
===================================================================

**This is work-in-progress and not currently usable yet.**


PyDesignFlow is a **technology- and tool-agnostic micro-framework** for building **FPGA / VLSI design flows** in Python.

Principles:

- PyDesignFlow follows an imperative approach, not a declarative approach.
- Blocks are the first-class design objects in PyDesignFlow. Simple designs can be realized with a single block. In hierarchical designs, blocks can be integrated in other blocks. Block boundaries are set by hand, bottom-up design flow is the default.
- Different Tasks can be performed on blocks.
- In contast to the popular Makefile approach, no file-level prerequisite tracking is attempted. Requested flow steps are executed regardless of whether source files have been modified since the last invocation of the flow step. This simplifies the design flow considerably. See the article `Build System Observations`_ for some thoughts about this. Even small source modifications typically require discarding all design results on block level. This takes a long time anyway, so determining the appropriate next flow step is probably not be a significant burden for the user.
- Blocks have Tasks and Tasks have no further configuration options.

Todo:

- test cli
- Automatically generate flow documentation

.. _Build System Observations: http://www.oilshell.org/blog/2017/05/31.html

License
-------

Copyright 2022 Tobias Kaiser

SPDX-License-Identifier: Apache-2.0