.. _filemgmt:

File Management Helpers
=======================

The submodule *pydesignflow.filemgmt* is **independent of the core PyDesignFlow** functionality. It is useful for dealing with typical VLSI library and design files. It offers the helper functions *checkfile* and *checkdir* and the helper class *FileCollection*.

The following code shows usage of *FileCollection*. The referenced files must exist::

    from pydesignflow import filemgmt

    c.add(Path("fast_hot.lib"),  speed='fast', temp=100)
    c.add(Path("fast_cold.lib"), speed='fast', temp=-10)
    c.add(Path("slow_hot.lib"),  speed='slow', temp=100)
    c.add(Path("slow_cold.lib"), speed='slow', temp=-10)

    x = c.one(speed='slow', temp=100) # returns Path("slow_hot.lib")

    # Equivalent to the statement above:
    x = c(speed='slow', temp=100) # returns Path("slow_hot.lib")

Reference
---------

.. automodule:: pydesignflow.filemgmt
    :members: