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
import itertools

import chainlet.wrapper
from . import chainlink


class PartialSlave(object):
    __slots__ = ('func', 'args', 'keywords')

    def __new__(cls, slave, *args, **keywords):
        if hasattr(slave, 'func'):
            args = slave.args + args
            new_keywords = slave.keywords.copy()
            new_keywords.update(keywords)
            keywords = new_keywords
            slave = slave.func
        self = super(PartialSlave, cls).__new__(cls)
        self.func = slave
        self.args = args
        self.keywords = keywords
        return self

    def __call__(self, value=None, *args, **kwargs):
        new_args = self.args + args
        new_kwargs = self.keywords.copy()
        new_kwargs.update(kwargs)
        return self.func(value, *new_args, **new_kwargs)

    def __getnewargs__(self):
        return self.func, self.args, self.keywords

    def __getstate__(self):
        return self.func, self.args, self.keywords

    def __setstate__(self, state):
        self.func, self.args, self.keywords = state


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

    When receiving a :tern:`data chunk` ``value`` as part of a chain, :py:meth:`send` acts like
    ``slave(value, *args, **kwargs)``. Any calls to :py:meth:`throw` and :py:meth:`close`
    are ignored.
    """
    def __init__(self, slave, *args, **kwargs):
        if args or kwargs:
            slave = PartialSlave(slave, *args, **kwargs)
        super(FunctionLink, self).__init__(slave=slave)

    @staticmethod
    def __init_slave__(slave_factory, *slave_args, **slave_kwargs):
        if slave_args or slave_kwargs:
            return PartialSlave(slave_factory, *slave_args, **slave_kwargs)
        return slave_factory

    def chainlet_send(self, value=None):
        """Send a value to this element"""
        return self.__wrapped__(value)

    def __wraplet_repr__(self):  # pragma: no cover
        if hasattr(self.__wrapped__, 'args'):
            return '<%s.%s(%s)>' % (
                self.__module__,
                self.__class__.__qualname__,
                ', '.join(
                    itertools.chain(
                        (repr(arg) for arg in self.__wrapped__.args),
                        ('%s=%r' % (key, value) for key, value in self.__wrapped__.keywords.items())
                    )
                )
            )
        return '<%s.%s>' % (self.__module__, self.__class__.__qualname__)


def funclet(function):
    """
    Convert a function to a :py:class:`~chainlink.ChainLink`

    .. code:: python

        @funclet
        def square(value):
            "Convert every data chunk to its numerical square"
            return value ** 2

    The :term:`data chunk` ``value`` is passed anonymously as the first positional parameter.
    In other words, the wrapped function should have the signature:

    .. py:function:: .slave(value, *args, **kwargs)
    """
    return FunctionLink.wraplet()(function)
