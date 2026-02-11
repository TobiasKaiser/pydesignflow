# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from warnings import warn

from .target import TargetPrototype

def task(requires:dict[str,str]={}, always_rebuild=False, hidden=False):
    """
    Decorator for defining tasks within a Block.

    Tasks are methods that perform design flow steps and optionally return a Result object.
    Each task gets its own output directory and can depend on results from other tasks.

    Args:
        requires: Dictionary declaring task dependencies. Keys are parameter names for the
            decorated function; values are requirement specification strings (see :ref:`taskdeps`).
            Dependencies are automatically built if missing.
        always_rebuild: If True, this task is always rebuilt when it is a dependency of another
            task, even if a result already exists. Defaults to False.
        hidden: If True, the task is not shown in CLI help or status output. Defaults to False.

    Returns:
        Decorator function that converts the method into a task.

    Example::

        @task()
        def synthesize(self, cwd):
            result = Result()
            result.netlist = cwd / "netlist.v"
            return result

        @task(requires={'syn': '.synthesize'})
        def place_route(self, cwd, syn):
            print(f"Using {syn.netlist}")
            return Result()
    """
    return lambda func: TargetPrototype(
        func=func,
        requires=requires,
        always_rebuild=always_rebuild,
        hidden=hidden,
    )

def action(*args, **kwargs):
    warn('Use @task instead of @action.', DeprecationWarning, stacklevel=2)
    return task(*args, **kwargs)
