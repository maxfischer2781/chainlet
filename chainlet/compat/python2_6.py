import copy_reg
import functools


def partial_reconstruct(target, args, keywords):
    return functools.partial(target, *args, **keywords)


def partial_reduce(partial):
    """Support pickle.dumps(partial)"""
    return partial_reconstruct, (partial.func, partial.args, partial.keywords)

copy_reg.pickle(functools.partial, partial_reduce)

__all__ = []
