"""
Helpers for creating ChainLinks from standard protocols of objects

Tools of this module allow writing simpler code by reusing functionality
of existing protocol interfaces and builtins. The interface to other `chainlet` objects is automatically
built around the objects. Using protocol interfaces in chains allows to easily
create chainlets from existing code.

Every protolink represents a specific Python protocol or builtin. For example, the :py:func:`~.iterlet`
protolink maps to ``iter(iterable)``. This allows pulling chunks from iterables to a chain:

.. code::

    from examples import windowed_average

    fixed_iterable = [1, 2, 4, 3]
    chain = iterlet(fixed_iterable) >> windowed_average(size=2)
    for value in chain:
        print(value)  # prints 1.0, 1.5, 3.0, 3.5

The protolinks exist mostly for convenience - they are thin wrappers using
:py:mod:`chainlet` primitives. As such, they are most useful to adjust existing
code and objects for pipelines.

Any protolink that works on iterables supports two modes of operation:

**pull**: iterable provided at instantiation
    Pull data chunks directly from an iterable, work on them, and send them along a chain.
    These are usually equivalent to a corresponding builtin, but support chaining.

**push**: no iterable provided at instantiation
    Wait for data chunks to be pushed in, work on them, and send them along a chain.
    These are usually equivalent to wrapping a chain in the corresponding builtin, but preserve
    chain features.
"""
from __future__ import absolute_import, print_function
import operator

from . import chainlink
from . import genlink
from . import funclink


@genlink.genlet(prime=False)
def iterlet(iterable):
    """
    Pull chunks from an object using iteration

    :param iterable: object supporting iteration
    :type iterable: iterable

    .. code::

        chain = iterlet([1, 2, 3, 4, 5, 5, 6, 6]) >> filterlet(lambda chunk: chunk % 2 == 0)
        for element in chain:
            print(element)  # prints 2, 4, 6, 6
    """
    for chunk in iterable:
        yield chunk


def reverselet(iterable):
    """
    Pull chunks from an object using reverse iteration

    :param iterable: object supporting reverse iteration
    :type iterable: iterable

    See :py:func:`~.iterlet` for an example.
    """
    return iterlet(reversed(iterable))


def enumeratelet(iterable=None, start=0):
    r"""
    Enumerate chunks of data from an iterable or a chain

    :param iterable: object supporting iteration, or an index
    :type iterable: iterable, None or int
    :param start: an index to start counting from
    :type start: int
    :raises TypeError: if both parameters are set and ``iterable`` does not support iteration

    In pull mode, :py:func:`~.enumeratelet` works similar to the
    builtin :py:func:`~.enumerate` but is chainable:

    .. code::

        chain = enumeratelet(['Paul', 'Thomas', 'Brian']) >> printlet(sep=':\t')
        for value in chain:
            pass  # prints `0:	Paul`, `1:	Thomas`, `2:	Brian`

    By default, :py:func:`~.enumeratelet` enumerates chunks passed in from a pipeline.
    To use a different starting index, *either* set the ``start`` keyword parameter *or*
    set the first positional parameter.

    .. code::

        chain = iteratelet(['Paul', 'Thomas', 'Brian']) >> enumeratelet() >> printlet(sep=':\t')
        for value in chain:
            pass  # prints `0:	Paul`, `1:	Thomas`, `2:	Brian`
    """
    # shortcut directly to chain enumeration
    if iterable is None:
        return _enumeratelet(start=start)
    try:
        iterator = iter(iterable)
    except TypeError:
        if start != 0:
            raise  # first arg is not iterable but start is explicitly set
        return _enumeratelet(start=iterable)  # first arg is not iterable, try short notation
    else:
        return iterlet(enumerate(iterator, start=start))


@genlink.genlet
def _enumeratelet(start=0):
    n = operator.index(start)
    chunk = yield
    while True:
        chunk = yield (n, chunk)
        n += 1


def filterlet(function=bool, iterable=None):
    """
    Filter chunks of data from an iterable or a chain

    :param function: callable selecting valid elements
    :type function: callable
    :param iterable: object providing chunks via iteration
    :type iterable: iterable or None

    For any chunk in ``iterable`` or the chain, it is passed on only if
    ``function(chunk)`` returns true.

    .. code::

        chain = iterlet(range(10)) >> filterlet(lambda chunk: chunk % 2 == 0)
        for value in chain:
            print(value)  # prints 0, 2, 4, 6, 8
    """
    if iterable is None:
        return _filterlet(function=function)
    else:
        return iterlet(elem for elem in iterable if function(elem))


@funclink.funclet
def _filterlet(value=None, function=bool):
    if function(value):
        return value
    raise chainlink.StopTraversal


@genlink.genlet
def printlet(flatten=False, **kwargs):
    chunk = yield
    if flatten:
        while True:
            print(*chunk, **kwargs)
            chunk = yield chunk
    else:
        while True:
            print(chunk, **kwargs)
            chunk = yield chunk


@genlink.genlet(prime=False)
def callet(callee):
    """
    Pull chunks from an object using individual calls

    :param callee: object supporting ``callee()``
    :type callee: callable

    .. code::

        import random

        chain = callet(random.random) >> windowed_average(size=200)
        for _ in range(50):
            print(next(chain))  # prints series converging to 0.5
    """
    while True:
        yield callee()
