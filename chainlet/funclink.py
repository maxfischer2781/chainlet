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

    producer >> FunctionLink(stepper, 20) >> consumer

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

import chainlet.wrapper
from . import chainlink


class FunctionLink(chainlet.wrapper.WrapperMixin, chainlink.ChainLink):
    """
    Wrapper making a function act like a ChainLink

    :param slave: the function to wrap
    :param args: positional arguments for the slave
    :param kwargs: keyword arguments for the slave

    :note: Use the :py:func:`~.funclet` function if you wish to decorate a
           function to produce FunctionLinks.

    This class wraps a function (or other callable), calling it to perform
    work when receiving a value and passing on the result. The ``slave`` can be
    any object that is callable, and should take at least a named parameter ``value``.

    When receiving a value as part of a chain, :py:meth:`send` acts like
    ``slave(value=value, *args, **kwargs)``. Any calls to :py:meth:`throw` and :py:meth:`close`
    are ignored.
    """
    def __init__(self, slave, *args, **kwargs):
        if args or kwargs:
            slave = functools.partial(slave, *args, **kwargs)
        super(FunctionLink, self).__init__(slave=slave)

    @staticmethod
    def __init_slave__(raw_slave, *slave_args, **slave_kwargs):
        if slave_args or slave_kwargs:
            return functools.partial(raw_slave, *slave_args, **slave_kwargs)
        return raw_slave

    def chainlet_send(self, value=None):
        """Send a value to this element"""
        return self.__wrapped__(value=value)


def funclet(function):
    """
    Convert a function to a :py:class:`~chainlink.ChainLink`

    .. code:: python

        @funclet
        def square(value):
            "Convert every data chunk to its numerical square"
            return value ** 2
    """
    return FunctionLink.wraplet()(function)
