import sys
if sys.version_info[:2] != (2, 6):
    raise ImportError
import copy_reg
import functools


def partial_reconstruct(target, args, kwargs):
    return functools.partial(target, *args, **kwargs)


def partial_reduce(partial):
    """Support pickle.dumps(partial)"""
    return partial_reconstruct, (partial.func, partial.args, partial.kwargs)

copy_reg.pickle(functools.partial, partial_reduce)

__all__ = []
