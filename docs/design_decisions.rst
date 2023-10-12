.. _design_decisions:

Design Decisions
================

Requested flow steps are executed regardless of whether source files have been modified since the last invocation of the flow step. This simplifies the design flow considerably. See the article `Build System Observations`_ for some thoughts about this. Even small source modifications typically require discarding all design results on block level. This takes a long time anyway, so determining the appropriate next flow step is likely not a significant burden for the user.

.. _Build System Observations: http://www.oilshell.org/blog/2017/05/31.html

Parameters
----------

PyDesignFlow has no support mechanisms for **task parameters** or **global parameters**. This could be seen as shortcoming, but was done on purpose to keep complexity low. Parameters could be design variables, design tool settings or flags such as GUI / batch mode, debug / release mode etc. 

**Parameters on task level** would open up a lot of possibilities, but also complicate things a lot. Build folder names would have to reflect the choice of parameters. How are parameter values propagated to dependencies? The ability to add or remove parameter values would be desirable but does not fit neatly in the @task decorator. Parameter sweeps could be done by depending on multiple versions of the same task with varying parameter values.

Even though PyDesignFlow has no mechanism for **global parameters**, they can be achieved using environment variables. If environment variables are used as parameters, it is the responsibility of the user to keep track of which results were produced using which parameter sets. One way to separate results with different parameters is to put them into different build folders. The command line option --build-dir / -B of the flow command can help with this.