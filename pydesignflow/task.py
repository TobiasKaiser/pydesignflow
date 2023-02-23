from warnings import warn

from .target import TargetPrototype

def task(requires:dict[str,str]={}, always_rebuild=False, hidden=False):
    """
    In a previous versin, task was known as action.

    Args:
        requires: Dict declaring dependencies of task. Dict keys declare which
            argument names will be used to pass results to the decorated task
            function. Values are requirement spec strings, described in
            :ref:`taskdeps`.
        always_rebuild: If this is set to True, the target will be rebuild every
            time it is a direct dependency of another target
            
    Returns:
       Anonymous function for decorating Block methods, which returns
       TargetPrototype instances.
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