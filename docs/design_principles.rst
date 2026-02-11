.. _design_principles:

Design Principles
=================

PyDesignFlow makes several deliberate design choices to keep the framework simple while giving designers maximum control over complex, long-running design flows.

No Source File Tracking
-----------------------

Unlike traditional build systems like Make, **PyDesignFlow does not track source file changes**. Targets are executed when explicitly requested, regardless of whether source files have been modified since the last execution.

This design provides several benefits:

- **Simplicity**: No need to specify and maintain complex source file dependency lists.
- **Designer control**: The designer decides when to rebuild results, avoiding unnecessary long tool runtimes.
- **Practicality**: In FPGA/VLSI design flows, even small source modifications typically require discarding all design results at the block level and re-running design tools, which takes a long time. Since tool runtimes are long anyway, manually determining which targets to rebuild is not a significant burden for the user.

See the article `Build System Observations`_ for additional thoughts on this topic.

.. _Build System Observations: http://www.oilshell.org/blog/2017/05/31.html

Dependency Behavior
-------------------

- A dependency **not marked as** ``always_rebuild`` with a Result present is never rebuilt.
- Dependencies **marked as** ``always_rebuild`` are always rebuilt when needed.
- Missing dependencies are built automatically.
- The designer must remember to rebuild or clean targets manually when source files change.

Encapsulation of Task Outputs
------------------------------

Each task gets its own directory in the build folder and should write output files only to that directory. This encapsulation follows a functional programming style where tasks have well-defined inputs and outputs:

- Tasks receive a ``cwd`` parameter pointing to their output directory.
- Tasks can read output files and Result data from their input dependencies.
- Tasks should not modify files from dependencies (read-only access).
- Each task returns a **Result** object containing structured output data.
- Result objects are serialized to JSON (``result.json``) in the task's directory.
- When tasks are re-run, any previous Result is discarded and the old output directory is emptied.

This approach ensures tasks are isolated and reproducible, with clear data flow through the dependency graph.

Parameters
----------

PyDesignFlow supports **Block-level parameters** through class instantiation. A Block class can be instantiated multiple times with different parameter values, and each instance is added to the Flow under a different name. This provides a clean and explicit way to handle design variables, tool settings, and configuration options.

For example, a parameterized Block can be instantiated as::

    flow['BlockA_config1'] = MyBlock(voltage=1.8, mode='fast')
    flow['BlockA_config2'] = MyBlock(voltage=1.2, mode='slow')

PyDesignFlow deliberately avoids **task-level parameters** to keep complexity low. Task-level parameters would add significant complexity: build folder names would need to reflect parameter choices, parameter value propagation to dependencies would need to be defined, and adding or removing parameter values does not fit neatly in the ``@task`` decorator. Instead, parameter variations are handled by creating multiple Block instances.

**Project-wide (global) parameters** are generally discouraged but can be implemented using environment variables when necessary. When using environment variables, the user is responsible for tracking which results were produced with which parameter sets. Results with different parameters can be separated using different build folders. The ``--build-dir`` / ``-B`` command line option facilitates working with multiple build folders.
