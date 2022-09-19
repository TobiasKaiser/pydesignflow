Design Decisions
================

TBD

Requested flow steps are executed regardless of whether source files have been modified since the last invocation of the flow step. This simplifies the design flow considerably. See the article `Build System Observations`_ for some thoughts about this. Even small source modifications typically require discarding all design results on block level. This takes a long time anyway, so determining the appropriate next flow step is probably not be a significant burden for the user.

.. _Build System Observations: http://www.oilshell.org/blog/2017/05/31.html