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
import sys
import types

from . import chainlink, wrapper


class StashedGenerator(object):
    """
    A :term:`generator iterator` which can be copied/pickled before any other operations

    :param generator_function: the source :term:`generator` function
    :type generator_function: function
    :param args: positional arguments to pass to ``generator_function``
    :param kwargs: keyword arguments to pass to ``generator_function``

    This class can be used instead of instantiating a :term:`generator` function.
    The following two calls will behave the same for all generator operations:

    .. code::

        my_generator(1, 2, 3, foo='bar')
        StashedGenerator(my_generator, 1, 2, 3, foo='bar')

    However, a :py:class:`StashedGenerator` can be pickled and unpickled before any generator
    operations are used on it.
    It explicitly disallows pickling after :py:func:`next`, :py:meth:`send`, :py:meth:`throw` or :py:meth:`close`.

    .. code::

        def parrot(what='Polly says %s'):
            value = yield
            while True:
                value = yield (what % value)

        simon = StashedGenerator(parrot, 'Simon says %s')
        simon2 = pickle.loads(pickle.dumps(simon))
        next(simon2)
        print(simon2.send('Hello'))  # Simon says Hello
        simon3 = pickle.loads(pickle.dumps(simon2))  # raise TypeError
    """
    def __init__(self, generator_function, *args, **kwargs):
        self._generator_function = generator_function
        self._args = args
        self._kwargs = kwargs
        self._generator = None

    @property
    def __class__(self):
        # fake our type to appear as a builtin generator
        return types.GeneratorType

    def _materialize(self):
        # create generator first so that we are sure it is working
        self._generator = _generator = self._generator_function(*self._args, **self._kwargs)
        # replace all our methods to avoid indirection
        self.send = _generator.send
        self.throw = _generator.throw
        self.close = _generator.close
        self.__iter__ = _generator.__iter__
        try:
            self.__next__ = _generator.__next__
        except AttributeError:
            self.next = _generator.next
        # free references so that things can be garbage collected
        self._generator_function, self._args, self._kwargs = None, None, None

    def __iter__(self):
        self._materialize()
        return iter(self._generator)

    def send(self, arg=None):
        """
        send(arg) -> send 'arg' into generator,
        return next yielded value or raise StopIteration.
        """
        self._materialize()
        return self._generator.send(arg)

    if sys.version_info < (3,):
        def next(self):
            """x.next() -> the next value, or raise StopIteration"""
            return self.send(None)
    else:
        def __next__(self):
            """Implement next(self)"""
            return self.send(None)

    def throw(self, typ, val=None, tb=None):
        """
        throw(typ[,val[,tb]]) -> raise exception in generator,
        return next yielded value or raise StopIteration.
        """
        self._materialize()
        self._generator.throw(typ, val, tb)

    def close(self):
        """close() -> raise GeneratorExit inside generator."""
        self._materialize()
        self._generator.close()

    def __getstate__(self):
        if self._generator is not None:
            raise TypeError('%s objects cannot be pickled after iteration' % type(self).__name__)
        return vars(self)


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

    @staticmethod
    def __init_slave__(raw_slave, *slave_args, **slave_kwargs):
        return StashedGenerator(raw_slave, *slave_args, **slave_kwargs)

    def chainlet_send(self, value=None):
        """Send a value to this element for processing"""
        return self.__wrapped__.send(value)

    def throw(self, type, value=None, traceback=None):  # pylint: disable=redefined-builtin
        """Raise an exception in this element"""
        return self.__wrapped__.throw(type, value, traceback)

    def close(self):
        """Close this element, freeing resources and blocking further interactions"""
        return self.__wrapped__.close()


def genlet(generator_function=None, prime=True):
    """
    Decorator to convert a generator function to a :py:class:`~chainlink.ChainLink`

    :param generator_function: the generator function to convert
    :type generator_function: generator
    :param prime: advance the generator to the next/first yield
    :type prime: bool

    When used as a decorator, this function can also be called with and without keywords.

    .. code:: python

        @genlet
        def pingpong():
            "Chainlet that passes on its value"
            last = yield
            while True:
                last = yield last

        @genlet(prime=True)
        def produce():
            "Chainlet that produces a value"
            while True:
                yield time.time()

        @genlet(True)
        def read(iterable):
            "Chainlet that reads from an iterable"
            for item in iterable:
                yield item
    """
    if generator_function is None:
        return GeneratorLink.wraplet(prime=prime)
    elif not callable(generator_function):
        return GeneratorLink.wraplet(prime=generator_function)
    return GeneratorLink.wraplet(prime=prime)(generator_function)
