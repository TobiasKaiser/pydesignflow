.. _sphinx_ext:

Sphinx Extension
================

PyDesignFlow comes with a Sphinx extension that generates design flow
documentation from a Flow object, based on the blocks and tasks defined and
their docstrings. The extension provides both auto-documentation and
cross-referencing capabilities.

Setup
-----

Add :code:`'pydesignflow.sphinx_ext'` to the list of extensions in your
Sphinx ``conf.py`` file::

    extensions = [
        'pydesignflow.sphinx_ext',
        # ... other extensions
    ]

Auto-Documentation Directive
-----------------------------

The ``.. designflow::`` directive automatically generates documentation for
all blocks and tasks in a flow. Specify the name of the module containing
a *Flow* object named *flow*::

    .. designflow:: tests.flow_example1

This will output:

- All blocks with their types and docstrings
- All tasks within each block with their signatures
- Task dependencies (as clickable cross-references)
- Task metadata (``always_rebuild`` flag, etc.)

See :ref:`flow_example1_autodoc` for example output.

Cross-Referencing
-----------------

The extension provides a ``flow`` domain for linking to blocks and tasks:

.. code-block:: rst

    See :flow:task:`top.step1` for details.
    The :flow:target:`synthesis.elaborate` task processes RTL code.
    All tasks are in the :flow:block:`top` block.

Tasks use the ``block_id.task_id`` format. The ``:flow:target:`` role is an
alias for ``:flow:task:``. When using ``.. designflow::``, task dependencies
are automatically rendered as clickable links.

Domain Directives
-----------------

You can also manually document blocks and tasks using domain directives:

**Documenting a block:**

.. code-block:: rst

    .. flow:block:: synthesis

       The synthesis block handles RTL synthesis and elaboration.

**Documenting a task:**

.. code-block:: rst

    .. flow:task:: synthesis.elaborate

       Elaborates the RTL design and generates a netlist.

These directives create cross-reference targets that can be linked from
anywhere in your documentation using the roles described above.

Complete Example
----------------

Here's a complete example showing auto-documentation with manual cross-references:

.. code-block:: rst

    Design Flow Overview
    ====================

    Our FPGA design flow starts with the :flow:task:`synthesis.elaborate` task,
    which processes the RTL code. After synthesis completes, the
    :flow:task:`fpga.place_and_route` task maps the design to the target device.

    Complete Flow Reference
    -----------------------

    .. designflow:: myproject.flow

This will generate full documentation with clickable links between tasks and
their dependencies.