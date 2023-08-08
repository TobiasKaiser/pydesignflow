.. _sphinx_ext:

Sphinx Extension
================

PyDesignFlow comes with a small Sphinx extension that can generate design flow
documentation from a Flow object, based on the blocks and tasks defined and
their docstrings.

To use the Sphinx extension, add :code`'pydesignflow.sphinx_ext'` to the 
list of extensions in your Sphinx conf.py file. The *designflow* directive is
then available and outputs the full design flow documentation. Specify the name
of the module containing a *Flow* object named *flow*. Example::

    .. designflow:: tests.flow_example1

See :ref:`flow_example1_autodoc` for example output.