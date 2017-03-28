from __future__ import division, absolute_import
import sys

from .compat import throw_method as _throw_method
from . import utility


class ChainLink(object):
    r"""
    BaseClass for elements in a chain

    A chain is created by binding :py:class:`ChainLink`\ s together. This is
    a directional process: a binding is always made between parent and child.
    Each child can be the parent to another child, and vice versa.

    The direction dictates how data is passed along the chain:

    * A parent may :py:meth:`send` a data chunk to a child.
    * A child may pull the :py:func:`next` data chunk from the parent.

    Chaining is done with ``>>`` and ``<<`` operators as
    ``parent >> child`` and `child << parent`. Forking and joining of chains
    requires a sequence of multiple elements as parent or child.

    .. describe:: parent >> child
                  child << parent

       Bind ``child`` and ``parent``. Both directions of the statement are
       equivalent: if ``a`` is made a child of ``b``, then `b`` is made a
       parent of ``a``, and vice versa.

    .. describe:: parent >> (child_a, child_b, ...)
                  parent >> [child_a, child_b, ...]
                  parent >> {child_a, child_b, ...}

       Bind ``child_a``, ``child_b``, etc. as children of ``parent``.

    .. describe:: (parent_a, parent_b, ...) >> child
                  [parent_a, parent_b, ...] >> child
                  {parent_a, parent_b, ...} >> child

       Bind ``parent_a``, ``parent_b``, etc. as parents of ``child``.

    Aside from binding, every :py:class:`ChainLink` should implement the
    `Generator-Iterator Methods`_ interface as applicable:

    .. method:: link.__next__()
                link.send(None)

       Create a new chunk of data. Raise :py:exc:`StopIteration` if there are
       no more chunks. Implicitly used in ``next(link)`` and ``for chunk in link``.

    .. method:: link.send(chunk)

       Process a data ``chunk``, and return the result.

    .. method:: link.throw(type[, value[, traceback]])

       Raises an exception of ``type`` inside the link. The link may either
       return a final result, raise :py:exc:`StopIteration` if there are no
       more results, or propagate any other, unhandled exception.

    .. method:: link.close()

       Close the link, cleaning up any resources.. A closed link may raise
       :py:exc:`RuntimeError` if data is requested via ``next`` or processed via ``send``.

    When used in a chain, each :py:class:`ChainLink` is distinguished by its handling
    of input and output. There are two attributes to signal the behaviour when chained.
    These specify whether the element performs a `1 -> 1`, `n -> 1`, `1 -> m` or `n -> m`
    processing of data.

    .. py:attribute:: chain_join

       A :py:class:`bool` indicating that the element expects the values of all
       preceding elements at once. That is, the `chunk` passed in via :py:meth:`send`
       is an *iterable* providing the return values of the previous elements.

    .. py:attribute:: chain_fork

       A :py:class:`bool` indicating that the element produces several values
       at once. That is, the return value is an *iterable* of data chunks,
       each of which should be passed on independently.

    To prematurely stop the traversal of a chain, `1 -> n` and `n -> m` elements should
    return an empty container. Any `1 -> 1` and `n -> 1` element can define a
    special return value that stops traversal.

    .. py:attribute:: stop_traversal

       Special return value that stops further traversal of the chain when returned by
       `1 -> 1` and `n -> 1` elements. This attribute is ignored on`1 -> n` and `n -> m` elements.
       This value may be returned by calls to ``element.send`` and ``next(element)``,
       but is suppressed when using ``iter(element)``.

    .. _Generator-Iterator Methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
    """
    chain_linker = None
    #: special return value for :py:meth:`send` to abort further traversal of a chain
    stop_traversal = utility.Sentinel('END OF CHAIN')
    #: whether this element processes several data chunks at once
    chain_join = False
    #: whether this element produces several data chunks at once
    chain_fork = False

    def __rshift__(self, children):
        # self >> children
        linker = self.chain_linker if self.chain_linker is not None else DEFAULT_LINKER
        return linker(self, children)

    def __rrshift__(self, parents):
        # parent >> self
        return self << parents

    def __lshift__(self, parents):
        # self << parent
        linker = self.chain_linker if self.chain_linker is not None else DEFAULT_LINKER
        return linker(parents, self)

    def __rlshift__(self, children):
        # children << self
        return self >> children

    def __iter__(self):
        stop_traversal = self.stop_traversal
        while True:
            next_value = next(self)
            if next_value is not stop_traversal:
                yield next_value

    def __next__(self):
        return self.send(None)

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):  # pylint: disable=no-self-use
        """Send a value to this element for processing"""
        return value

    throw = _throw_method

    def close(self):
        """Close this element, freeing resources and blocking further interactions"""
        pass


class Chain(ChainLink):
    """
    Baseclass for compound chainlets consisting of other chainlets

    :param elements: the chainlets making up this chain
    :type elements: iterable[:py:class:`ChainLink`]
    """
    def __init__(self, elements):
        self.elements = elements
        super(Chain, self).__init__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
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
    chain_join = False
    chain_fork = False

    def send(self, value=None):
        for element in self.elements:
            value = element.send(value)
            if value is element.stop_traversal:
                return self.stop_traversal
        return value

    def __repr__(self):
        return ' >> '.join(repr(elem) for elem in self.elements)


class ParallelChain(Chain):
    """
    A parallel sequence of chainlets, with each element ranked the same
    """
    chain_join = False
    chain_fork = True

    def send(self, value=None):
        return type(self.elements)(self._send_iter(value))

    def _send_iter(self, value):
        for element in self.elements:
            if element.chain_fork:
                for val in element.send(value):
                    yield val
            else:
                val = element.send(value)
                if val is not element.stop_traversal:
                    yield val

    def __repr__(self):
        return repr(self.elements)


class MetaChain(ParallelChain):
    """
    A mixed sequence of linear and parallel chainlets
    """
    def __init__(self, elements):
        _elements = []
        _elements_buffer = []
        for element in elements:
            if isinstance(element, ParallelChain):
                if _elements_buffer:
                    _elements.append(LinearChain(tuple(_elements_buffer)))
                    _elements_buffer = []
                _elements.append(element)
            else:
                _elements_buffer.append(element)
        super(MetaChain, self).__init__(tuple(elements))

    def send(self, value=None):
        # traverse breadth first to allow for synchronized forking and joining
        values = [value]
        for element in self.elements:
            # aggregate input for joining paths, flatten output of parallel paths
            if element.chain_join and element.chain_fork:
                values = element.send(values)
            # flatten output of parallel paths for each input
            elif not element.chain_join and element.chain_fork:
                values = [retval for value in values for retval in element.send(value)]
            # neither fork nor join, unwrap input and output
            elif not element.chain_join:
                stop_traversal = element.stop_traversal
                values = [
                    retval for retval in (element.send(value) for value in values) if retval is not stop_traversal
                ]
            else:
                values = [element.send(values)]
                if values[0] is element.stop_traversal:
                    values = []
        return values

    def __repr__(self):
        return ' >> '.join(repr(elem) for elem in self.elements)


def parallel_chain_converter(element):
    if isinstance(element, (tuple, list, set)):
        return ParallelChain(element)
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
            elif hasattr(element, 'elements') and not element.elements:
                pass
            else:
                _elements.append(element)
        if len(_elements) == 1:
            return _elements[0]
        if any(isinstance(element, ParallelChain) for element in _elements):
            return MetaChain(_elements)
        return LinearChain(_elements)

    def convert(self, element):
        for converter in self.converters:
            try:
                return converter(element)
            except TypeError:
                continue
        return element

    def __call__(self, *elements):
        return self.link(*elements)


DEFAULT_LINKER = ChainLinker()
