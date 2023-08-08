Introduction
============

Blocks
------

Blocks are PyDesignFlow's first-class building blocks. To define a Block, create an own subclass of *pdf.Block*::

    import pydesignflow as pdf

    class MyBlock(pdf.Block):
        # ...

In order to use a Block, instantiate it and assign it a particular block ID in connection with a Flow object::

    flow = pdf.Flow()
    flow['top'] = MyBlock()

In this case, a new instance of MyBlock is assigned to the block ID *'top'*.

If configurable blocks are desired, this should be done at Block subclass instatiation time, i. e. during flow declaration. Once created, a Block subclass object should be considered fixed in configuration.

Tasks
-----

Define tasks by implementing methods and decorating them with *@pdf.task()*::

     class MyBlock(pdf.Block):
        @pdf.task()
        def syn(self, cwd):
            syn = pdf.Result()
            # ...
            syn.result1 = "asdf"
            return syn

The *task()* decorator creates a TargetPrototype class for the function that it decorates. This is the only supported way for defining tasks. Please do not create custom TargetPrototype classes, such as by creating a subclass of TargetPrototype.

**Tasks are not configurable.** If you want your block to provide multiple similar task (e. g. behavioral simulation, netlist simulation), declare them as as separate tasks. Functionality shared between tasks should best be encapsulated in functions or non-@task methods. You can also achieve configurability by have paramters on block-level.

A task ID in connection with a block ID uniquely identifies a **target**. The task ID is the name of the task method; the block ID is the name under which a block is registered in the Flow object (*top* in the example above).

Every target has its **own working directory**, which is passed as first argument (*cwd*) to the associated task method on invocation. The working directory is named *build/[block ID]/[task ID]*. The working directory can be used to store build results and furthermore contains a *result.json* file (see :ref:`result_json`) if the target was built successfully.

Notice: The terms **target and task are used somewhat interchangably** in PyDesignFlow. The idea between the distinction is mostly relevant for the internal architecture of PyDesignFlow: A task is just the method defined for a particular Block class; a target connects the task to a particular Block *instance* and thus uniquely identifies a potential Result.

.. _result_json:

Result objects & result.json
----------------------------

As shown in the example above, a task can return a **Result** object. If a task does not need this functionality, it can also return None.

Upon completion of a task, a *result.json* file is created in the target's working directory. It look like this::

    {
      "block_id": "top",
      "task_id": "syn",
      "data": {
        "result1": "asdf",
        "returned_data": true,
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

The string attribute *result1* that was assigned by the task *syn* has been written to this JSON file and can be used by subsequent tasks (see :ref:`taskdeps`).

The following data types are suitable as Result attributes: dict, list, tuple, str, bool, int, float, datetime.datetime and pathlib.Path. dicts, list and tuples can also be nested. Path and datetime are supported using a simple JSON serialization / deserialization scheme. For *pathlib.Path* objects, paths relative to the *build/* directory are used for serialization.
 
.. _taskdeps:

Task Dependencies
-----------------

Declare dependencies between tasks using the *requires* argument to *@task*.

Example for delaring a task "pnr"::

    @pdf.task(requires={'syn':'.syn'})
    def pnr(self, cwd, syn):
        pnr = pdf.Result()

        print("result1 of syn was: ", syn.result1)
        # Do something with syn.result1 here.

        pnr.result1 = "asdf"
        return pnr

The method name "pnr" is in also called the *task ID*.

The keys of the *requires* dictionary are mapped to keyword arguments of the corresponding task function. Its values are **requirement spec** strings, which can be one of the following:

1. To require the result of an task with the task ID "task_id", the requirement spec should be ".task_id".
2. To require the result of an task "task_id" in a referenced block "block_ref", the requirement spec should be "block_ref.task_id".
3. A direct reference to a block by its ID is also possible: "=block_id.task_id"

Variant 2 is generally preferred over variant 3. Variant 2 requires that *"block_ref"* is included the *dependency_map* dictionary that is passed to the Block on creation. Example::
    
    class TestBlock(pdf.Block):
        @pdf.task()
        def syn(self, cwd):
            syn = pdf.Result()
            syn.result1 = "asdf"
            return syn

    class AnotherBlock(pdf.Block):
        @pdf.task({'syn_of_xyz':'xyz.syn'})
        def syn(self, cwd, syn_of_xyz):
            syn = pdf.Result()

            print("result1 of syn (xyz) was: ", syn_of_xyz.result1)
            # Do something with syn.result1 here.      

            syn.another_result = "hjkl"
            return syn


    flow = pdf.Flow()
    flow['test'] = TestBlock()
    flow['another'] = TestBlock(dependency_map={'xyz':'test'})

This layer of indirection makes it possible to swap out the subblock *xyz* of *AnotherBlock* without any modifications to the *AnotherBlock* class.

By using only requirement spec variants 1 and 2, block IDs can be entirely kept out of Block subclass code; only the flow declaration will need to deal with block IDs.

