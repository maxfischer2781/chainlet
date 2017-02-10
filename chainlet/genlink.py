"""
Helpers for creating ChainLinks from generators

Tools of this module allow writing simpler code by expressing functionality
via generators. The interface to other `chainlet` objects is automatically
built around the generators. Using generators in chains allows to carry state
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

    @GeneratorLink.linklet
    def windowed_average(size=8):
        # ...

    producer >> windowed_average(16) >> consumer
"""
from __future__ import division, absolute_import

from . import chainlink


class GeneratorLink(chainlink.WrapperMixin, chainlink.ChainLink):
    """
    Wrapper making a generator act like a ChainLink

    :param slave: the generator instance to wrap
    :param prime: advance the generator to the next/first yield
    :type prime: bool

    :note: Use the :py:meth:`linklet` method if you wish to decorate a
           generator *function* to produce GeneratorLinks.

    This class wraps an already instantiated generator, using it to perform
    work when receiving a value and passing on the result. The `slave` can be
    any object that implements the generator protocol.

    Calling `next(wrapper)` translates directly to `next(wrapper.slave)`. Note
    that the `slave` has no reference to its wrapper, including its parents and
    children - it can only act as a producer, disregarding previous elements of
    the chain.
    """
    def __init__(self, slave, prime=True):
        super(GeneratorLink, self).__init__(slave=slave)
        # prime slave for receiving send
        if prime:
            next(self.__wrapped__)

    def __next__(self):
        return next(self.__wrapped__)

    def send(self, value=None):
        """Send a value to this element"""
        result = self.__wrapped__.send(value)
        return super(GeneratorLink, self).send(result)

    def throw(self, type, value=None, traceback=None):
        super(GeneratorLink, self).throw(type, value, traceback)
        self.__wrapped__.throw(type, value, traceback)

    def close(self):
        super(GeneratorLink, self).close()
        self.__wrapped__.close()
