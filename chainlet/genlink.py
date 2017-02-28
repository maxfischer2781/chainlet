"""
Helpers for creating ChainLinks from generators

Tools of this module allow writing simpler code by expressing functionality
via generators. The interface to other `chainlet` objects is automatically
built around the generator. Using generators in chains allows to carry state
between steps.

A regular generator can be directly used by wrapping :py:class:`GeneratorLink`
around it:

.. code:: python

    from collections import deque
    from mylib import producer, consumer

    def windowed_average(size=8):
        buffer = collections.deque([(yield)], maxlen=size)
        while True:
            new_value = yield(sum(buffer)/len(buffer))
            buffer.append(new_value)

    producer >> GeneratorLink(windowed_average(16)) >> consumer

If a generator is used only as a chainlet, one may permanently convert it by
applying a decorator:

.. code:: python

    from collections import deque
    from mylib import producer, consumer

    @genlet
    def windowed_average(size=8):
        # ...

    producer >> windowed_average(16) >> consumer
"""
from __future__ import division, absolute_import
import functools

from . import chainlink, wrapper


class GeneratorLink(wrapper.WrapperMixin, chainlink.ChainLink):
    """
    Wrapper making a generator act like a ChainLink

    :param slave: the generator instance to wrap
    :param prime: advance the generator to the next/first yield
    :type prime: bool

    :note: Use the :py:func:`linklet` function if you wish to decorate a
           generator *function* to produce GeneratorLinks.

    This class wraps a generator, using it to perform work when receiving
    a value and passing on the result. The `slave` can be any object that
    implements the generator protocol - the methods `send`, `throw` and `close`
    are directly called on the `slave`.
    """
    def __init__(self, slave, prime=True):
        super(GeneratorLink, self).__init__(slave=slave)
        # prime slave for receiving send
        if prime:
            next(self.__wrapped__)

    def __next__(self):
        return next(self.__wrapped__)

    def send(self, value=None):
        """Send a value to this element for processing"""
        return self.__wrapped__.send(value)

    def throw(self, type, value=None, traceback=None):
        """Raise an exception in this element"""
        return self.__wrapped__.throw(type, value, traceback)

    def close(self):
        """Close this element, freeing resources and blocking further interactions"""
        return self.__wrapped__.close()


def genlet(generator_function):
    """
    Convert a generator function to a :py:class:`~chainlink.ChainLink`
    """
    def linker(*args, **kwargs):
        """
        Creates a new generator instance acting as a chainlet.ChainLink

        :rtype: :py:class:`~chainlink.ChainLink`
        """
        return GeneratorLink(generator_function(*args, **kwargs))
    functools.update_wrapper(linker, generator_function)
    return linker
