.. _filemgmt:

File Management Helpers
=======================

The submodule *pydesignflow.filemgmt* is **independent of the core PyDesignFlow** functionality. It is useful for managing VLSI library and design files that vary by attributes such as process corner, temperature, or voltage.

Key Features
------------

* **checkfile** and **checkdir**: Verify file/directory existence with error handling
* **FileCollection**: Manage file sets with associated attributes
* Pattern-based file discovery with **FileCollection.frompattern**

Basic Usage
-----------

The following example shows manual collection building::

    from pydesignflow import filemgmt
    from pathlib import Path

    c = filemgmt.FileCollection()
    c.add(Path("fast_hot.lib"),  speed='fast', temp=100)
    c.add(Path("fast_cold.lib"), speed='fast', temp=-10)
    c.add(Path("slow_hot.lib"),  speed='slow', temp=100)
    c.add(Path("slow_cold.lib"), speed='slow', temp=-10)

    # Get single file matching criteria
    x = c.one(speed='slow', temp=100)  # returns Path("slow_hot.lib")

    # Shorthand syntax
    x = c(speed='slow', temp=100)  # same as above

Pattern-Based Discovery
-----------------------

Create collections from file naming patterns::

    from pathlib import Path

    def decode_lib(name):
        # Parse "fast_100" -> {'speed': 'fast', 'temp': 100}
        parts = name.split('_')
        return {'speed': parts[0], 'temp': int(parts[1])}

    c = filemgmt.FileCollection.frompattern(
        Path("libs/"),
        pattern=r"(.*)\.lib",
        decoder=decode_lib
    )

    # Now use filtering as above
    lib = c(speed='slow', temp=-10)

Reference
---------

.. automodule:: pydesignflow.filemgmt
    :members:
