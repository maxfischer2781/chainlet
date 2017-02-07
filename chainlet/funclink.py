"""
Helpers for creating ChainLinks from functions

Tools of this module allow writing simpler code by expressing functionality
via functions. The interface to other `chainlet` objects is automatically
built around the functions. Using functions in chains allows for simple,
stateless blocks.

A regular function can be directly used by wrapping :py:class:`FunctionLink`
around it:

.. code:: python

    from mylib import producer, consumer

    def stepper(value, resolution=10):
        return (value // resolution) * resolution

    producer >> FunctionLink(windowed_average, 20) >> consumer

If a function is used only as a chainlet, one may permanently convert it by
applying a decorator:

.. code:: python

    from collections import deque
    from mylib import producer, consumer

    @GeneratorLink.linklet
    def stepper(value, resolution=10):
        # ...

    producer >> stepper(20) >> consumer
"""
from __future__ import division, absolute_import
import functools

from . import chainlink


class FunctionLink(chainlink.WrapperMixin, chainlink.ChainLink):
    """
    Wrapper making a generator act like a ChainLink

    :param slave: the function to wrap
    :param args: positional arguments for the slave
    :param kwargs: keyword arguments for the slave

    :note: Use the :py:meth:`linklet` method if you wish to decorate a
           function to produce FunctionLinks.

    This class wraps a function partially, using it to perform
    work when receiving a value and passing on the result. The `slave` can be
    any object that is callable.

    Calling is performed naively - ``next(wrapper)`` translates to
    ``wrapper.slave(*args, **kwargs)``, and ``wrapper.send(value)`` translates
    to ``wrapper.slave(value, *args, **kwargs)``.
    """
    def __init__(self, slave, *args, **kwargs):
        super(FunctionLink, self).__init__(slave=slave)
        # prime slave for receiving send
        self._wrapped_args = args
        self._wrapped_kwargs = kwargs

    def __next__(self):
        return self.__wrapped__(*self._wrapped_args, **self._wrapped_kwargs)

    def send(self, value=None):
        """Send a value to this element"""
        result = self.__wrapped__(value=value, *self._wrapped_args, **self._wrapped_kwargs)
        return super(FunctionLink, self).send(result)

    @classmethod
    def linklet(cls, target):
        """
        Convert any callable constructor to a chain link constructor
        """
        def linker(*args, **kwargs):
            """Creates a new instance of a chain link"""
            return cls(target, *args, **kwargs)
        functools.update_wrapper(linker, target)
        return linker
