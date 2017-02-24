from __future__ import division, absolute_import
import sys
import functools


class ChainLink(object):
    """
    BaseClass for elements in a chain

    A chain is created by binding :py:class:`ChainLink`\ s together. This is
    a directional process: a binding is always made between parent and child.
    Each child can be the parent to another child, and vice versa.

    The direction dictates how data is passed along the chain:

    * A parent may :py:meth:`send` a data chunk to a child.
    * A child may pull the :py:func:`next` data chunk from the parent.

    Chaining is either done by explicitly calling :py:meth:`bind_parents` and
    :py:meth:`bind_children`, or the shorter operator syntax as
    ``parent >> child`` and `child << parent`.

    The number of children and parents per link is arbitrary: the chain may
    fork, join and even loop. Whether any of this is a sensible relation
    depends on the implementation of each link.

    Multiple bindings are created by passing multiple links when binding,
    and/or binding a link multiple times.

    .. describe:: parent >> child
                  child << parent

       Bind ``child`` and ``parent``. Both directions of the statement are
       equivalent: if ``a`` is made a child of ``b``, then `b`` is made a
       parent of ``a``, and vice versa.

    .. describe:: parent >> (child_a, child_b, ...)

       Bind ``child_a``, ``child_a``, etc. as individual children of ``parent``.

    .. describe:: (parent_a, parent_b, ...) >> child

       Bind ``parent_a``, ``parent_b``, etc. as individual parents of ``child``.

    Aside from binding, every :py:class:`ChainLink` should implement the
    `Generator-Iterator Methods`_ interface as applicable:

    .. method:: link.__next__()

       Pull the next data ``chunk`` from the link. Raise :py:exc:`StopIteration`
       if there are no more chunks. Implicitly used in ``next(link)`` and in
       ``for chunk in link``.

    .. method:: link.send(chunk)

       Send a data ``chunk`` into the link. Return the result based on this data,
       if any.

    .. method:: link.throw(type[, value[, traceback]])

       Raises an exception of ``type`` inside the link. The link may either
       return a final result, raise :py:exc:`StopIteration` if there are no
       more results, or propagate any other, unhandled exception.

    .. method:: link.close()

       Close the link.

    Note that the default implementation of these methods in :py:class:`ChainLink`
    attempts to satisfy the interface with a minimum of assumptions. Most
    importantly, the type, format and nesting of return values is up to
    implementations.

    In specific, :py:meth:`__next__` simply calls ``next`` on the parent, or raise
    :py:exc:`StopIteration` if there is not exactly one parent.
    In contrast, :py:meth:`send`, :py:meth:`throw` and
    :py:meth:`close` always return :py:const:`None`; additionally, these
    methods pass on any input to any bound children.

    Subclasses are encouraged to use the :py:func:`super` methods for
    :py:meth:`send`, :py:meth:`throw` and :py:meth:`close`.

    .. _Generator-Iterator Methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
    """
    chain_linker = None

    def __rshift__(self, children):
        # self >> children
        linker = self.chain_linker if self.chain_linker is not None else default_linker
        return linker(self, children)

    def __rrshift__(self, children):
        # parent >> self
        return self << children

    def __lshift__(self, parents):
        # self << parent
        linker = self.chain_linker if self.chain_linker is not None else default_linker
        return linker(parents, self)

    def __rlshift__(self, parent):
        # children << self
        return self >> parent

    def __iter__(self):
        return self

    def __next__(self):
        return self.send(None)

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):
        """Send a value to this element for processing"""
        return value

    def throw(self, type, value=None, traceback=None):
        """Throw an exception is this element"""
        raise type(value, traceback)

    def close(self):
        """Close this element, freeing resources and blocking further interactions"""
        pass


class Chain(ChainLink):
    def __init__(self, *elements):
        self.elements = tuple(elements)

    def __eq__(self, other):
        if isinstance(other, Chain):
            return self.elements == other.elements
        return NotImplemented

    def __hash__(self):
        return hash(self.elements)

    def send(self, value=None):
        raise NotImplementedError


class LinearChain(Chain):
    """
    A linear sequence of chainlets, with each element preceding the next
    """
    def send(self, value=None):
        for element in self.elements:
            value = element.send(value)
        return value

    def __repr__(self):
        return ' >> '.join(repr(elem) for elem in self.elements)


class ParallelChain(Chain):
    """
    A parallel sequence of chainlets, with each element ranked the same
    """
    def send(self, value=None):
        return [element.send(value) for element in self.elements]


class MetaChain(ParallelChain):
    """
    A mixed sequence of linear and parallel chainlets
    """
    def send(self, value=None):
        values = []
        for element in self.elements:
            if isinstance(element, ParallelChain):
                # flatten output of parallel paths
                values = [elem.send(value) for value in values for elem in element]
            else:
                values = [element.send(value) for value in values]
        return value


def parallel_chain_converter(element):
    if isinstance(element, (tuple, list, set)):
        return ParallelChain(*element)
    raise TypeError


class ChainLinker(object):
    """
    Helper for linking objects to chains
    """
    #: functions to convert elements; must return a ChainLink or raise TypeError
    converters = [parallel_chain_converter]

    def link(self, *elements):
        _elements = []
        for element in elements:
            element = self.convert(element)
            if isinstance(element, (LinearChain, MetaChain)):
                _elements.extend(element.elements)
            else:
                _elements.append(element)
        if any(isinstance(element, ParallelChain) for element in _elements):
            return MetaChain(*_elements)
        return LinearChain(*_elements)

    def convert(self, element):
        for converter in self.converters:
            try:
                return converter(element)
            except TypeError:
                continue
        return element

    def __call__(self, *elements):
        return self.link(*elements)


default_linker = ChainLinker()


class WrapperMixin(object):
    """
    Mixin for :py:class:`ChainLink`\ s that wrap other objects

    Apply as a mixin via multiple inheritance:

    .. code:: python

        class MyWrap(WrapperMixin, ChainLink):
            def __init__(self, slave):
                super().__init__(slave=slave)

            def send(self, value):
                value = self.__wrapped__.send(value)
                super().send(value)

    Wrappers bind their slave to ``__wrapped__``, as is the Python standard,
    and also expose them via the ``slave`` property for convenience.
    """
    def __init__(self, slave):
        super(WrapperMixin, self).__init__()
        self.__wrapped__ = slave

    @property
    def slave(self):
        return self.__wrapped__

    @classmethod
    def linklet(cls, target):
        """
        Convert any callable constructor to a chain link constructor
        """
        def linker(*args, **kwargs):
            """
            Creates a new instance of a chain link

            :rtype: ChainLink
            """
            return cls(target(*args, **kwargs))
        functools.update_wrapper(linker, target)
        return linker
