Introduction
============

PyDesignFlow is built around three core concepts: **Blocks** encapsulate design components, **Tasks** define processing steps, and **Results** pass data between tasks. A **Flow** object manages all blocks and provides the command-line interface.

Blocks
------

Blocks encapsulate design components such as hardware modules, testbenches, or software builds. Define a block by subclassing *Block*::

    from pydesignflow import Block, Flow, task, Result

    class MyBlock(Block):
        # Define tasks here (see next section)

To use a block, instantiate it and assign it to a Flow with a unique block ID::

    flow = Flow()
    flow['top'] = MyBlock()

Blocks can have parameters by passing arguments to ``__init__()``. Configure blocks during instantiation; once created, blocks should be considered immutable::

    class MyBlock(Block):
        def __init__(self, voltage=1.8):
            super().__init__()
            self.voltage = voltage

    flow['block_1v8'] = MyBlock(voltage=1.8)
    flow['block_1v2'] = MyBlock(voltage=1.2)

Tasks
-----

Tasks are methods decorated with ``@task()`` that perform design flow steps. Each task receives a working directory (``cwd``) where it should write outputs::

    class MyBlock(Block):
        @task()
        def synthesize(self, cwd):
            result = Result()
            result.netlist = cwd / "netlist.v"
            result.timing_met = True
            return result

**Tasks are not parameterized.** For similar variants (e.g., behavioral vs. netlist simulation), define separate tasks. Share common functionality through regular methods or functions. Use block-level parameters for configuration.

Targets
~~~~~~~

A **target** is the combination of a block ID and task ID, uniquely identifying a buildable item. For example, ``top.synthesize`` refers to the ``synthesize`` task of the ``top`` block.

Each target has its own working directory: ``build/[block ID]/[task ID]/``. This directory is passed as the ``cwd`` parameter and should contain all task outputs.

.. note::
   The terms "target" and "task" are often used interchangeably. Technically, a task is a method in a Block class, while a target refers to that task in a specific Block instance.

.. _result_json:

Result Objects
--------------

Tasks can return a **Result** object to pass structured data to dependent tasks. If no data needs to be passed, return ``None``::

    @task()
    def synthesize(self, cwd):
        result = Result()
        result.area = 1234
        result.timing_met = True
        result.netlist = cwd / "netlist.v"
        return result

Supported data types for Result attributes:

- Scalars: ``str``, ``bool``, ``int``, ``float``, ``pathlib.Path``, ``datetime.datetime``
- Containers: ``dict``, ``list``, ``tuple`` (can be nested)

Path objects are serialized relative to the build directory. Upon task completion, the Result is serialized to ``result.json``::

    {
      "block_id": "top",
      "task_id": "synthesize",
      "data": {
        "area": 1234,
        "timing_met": true,
        "netlist": {
          "_type": "Path",
          "value": "top/synthesize/netlist.v"
        },
        "time_started": {
          "_type": "Time",
          "value": 1003.2
        },
        "time_finished": {
          "_type": "Time",
          "value": 1010.5
        }
      }
    }

.. _taskdeps:

Task Dependencies
-----------------

Declare dependencies using the ``requires`` argument to ``@task``. Keys are parameter names; values are requirement specifications::

    @task(requires={'syn': '.synthesize'})
    def place_route(self, cwd, syn):
        print(f"Area: {syn.area}")
        if not syn.timing_met:
            raise RuntimeError("Timing not met")
        # Continue with place & route...
        return Result()

Missing dependencies are built automatically before the task runs.

Requirement Specification Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Within-block reference** (recommended for same block):

   ``.task_id`` - References a task in the same block::

       @task(requires={'syn': '.synthesize'})
       def place_route(self, cwd, syn):
           # ...

**2. Symbolic block reference** (recommended for cross-block):

   ``block_ref.task_id`` - References a task in another block using a symbolic name::

       class MyBlock(Block):
           @task(requires={'other_syn': 'dependency.synthesize'})
           def my_task(self, cwd, other_syn):
               # ...

       flow['top'] = MyBlock(dependency_map={'dependency': 'other_block'})
       flow['other_block'] = OtherBlock()

   The ``dependency_map`` maps symbolic names (``dependency``) to actual block IDs (``other_block``), enabling block reuse without code changes.

**3. Direct block ID reference**:

   ``=block_id.task_id`` - Direct reference to a specific block::

       @task(requires={'syn': '=fpga_top.synthesize'})
       def my_task(self, cwd, syn):
           # ...

   This creates tight coupling and is generally discouraged.

Multi-Block Example
~~~~~~~~~~~~~~~~~~~~

::

    class SynthesisBlock(Block):
        @task()
        def synthesize(self, cwd):
            result = Result()
            result.netlist = cwd / "output.v"
            return result

    class PlaceRouteBlock(Block):
        @task(requires={'syn': 'synth.synthesize'})
        def place_route(self, cwd, syn):
            print(f"Using netlist: {syn.netlist}")
            return Result()

    flow = Flow()
    flow['syn_block'] = SynthesisBlock()
    flow['pnr_block'] = PlaceRouteBlock(dependency_map={'synth': 'syn_block'})

Using symbolic references (variant 2) keeps block IDs out of Block class code, making blocks more reusable.

