Blocks & Actions
================

Blocks
------

Blocks are PyDesignFlow's first-class building blocks. To define a Block, create an own subclass of *pdf.Block*::

    import pydesignflow as pdf

    class TestBlock(pdf.Block):
        # ...

In order to use blocks, they need to be integrated using a Flow object::

    flow = pdf.Flow()
    flow['test'] = TestBlock()

In this case, a new instance of TestBlock is assigned to the block ID *'test'*.

Actions
-------

Define actions by implementing methods and decorating them with *@pdf.action()*::

     class TestBlock(pdf.Block):
        @pdf.action()
        def syn(self, cwd):
            syn = pdf.Result()
            # ...
            syn.result1 = "asdf"
            return syn

The *action()* decorator creates a Action class for the function that it decorates.

This is the only supported way for defining actions. Please do not create custom action classes, such as by creating a subclass of Action.

Action dependencies
-------------------

Declare dependencies between actions using the *requires* argument to *@action*.

Example for delaring a action "pnr"::

    @pdf.action(requires={'syn':'.syn'})
    def pnr(self, cwd, syn):
        pnr = pdf.Result()

        print("result1 of syn was: ", syn.result1)
        # Do something with syn.result1 here.

        pnr.result1 = "asdf"
        return pnr

The method name "pnr" is in also called the *action ID*.

The keys of the *requires* dictionary are mapped to keyword arguments of the corresponding action function. Its values are **requirement spec** strings, which can be one of the following:

1. To require the result of an action with the action ID "action_id", the requirement spec should be ".action_id".
2. To require the result of an action "action_id" in a referenced block "block_ref", the requirement spec should be "block_ref.action_id".
3. A direct reference to a block by its ID is also possible: "=block_id.action_id"

Variant 2 is generally preferred over variant 3. Variant 2 requires that *"block_ref"* is included the *dependency_map* dictionary that is passed to the Block on creation. Example::
    
    class TestBlock(pdf.Block):
        @pdf.action()
        def syn(self, cwd):
            syn = pdf.Result()
            syn.result1 = "asdf"
            return syn

    class AnotherBlock(pdf.Block):
        @pdf.action({'syn_of_xyz':'xyz.syn'})
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

Invoking flow actions
---------------------



Configurable Blocks & Actions
-----------------------------

Actions are not configurable. If you want your block to provide multiple similar action (e. g. behavioral simulation, netlist simulation), declare them as as separate actions. Functionality shared between actions should best be encapsulated in functions or non-@action methods.

If configurable blocks are desired, this should be done at Block subclass instatiation time, i. e. during flow declaration. Once created, a Block subclass object should be considered fixed in configuration.