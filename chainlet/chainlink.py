from __future__ import division, absolute_import
import sys

from .compat import throw_method as _throw_method
from . import utility


END_OF_CHAIN = utility.Sentinel('END OF CHAIN')


class StopTraversal(Exception):
    """
    Stop the traversal of a chain

    :param return_value: the value returned by the chain

    Any chain element raising :py:exc:`~.StopTraversal` signals that
    subsequent elements of the chain should not be visited. If
    ``return_value`` is set, it becomes the final return value of the chain.
    Otherwise, no return value is provided.

    :note: This signal explicitly affects the current chain only. It does not
           affect other, parallel chains of a graph.
    """
    def __init__(self, return_value=END_OF_CHAIN):
        Exception.__init__(self)
        self.return_value = return_value


class _ElementExhausted(Exception):
    """An element has no more values to produce"""


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
    ``parent >> child`` and ``child << parent``. Forking and joining of chains
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

    Aside from binding, every :py:class:`ChainLink` implements the
    `Generator-Iterator Methods`_ interface:

    .. method:: link.__next__()
                link.send(None)

       Create a new chunk of data. Raise :py:exc:`StopIteration` if there are
       no more chunks. Implicitly used in ``next(link)`` and ``for chunk in link``.

    .. method:: link.send(chunk)

       Process a data ``chunk``, and return the result.

    .. method:: link.chainlet_send(chunk)

       Process a data ``chunk`` locally, and return the result.

       This method implements data processing in an element; subclasses must
       overwrite it to define how they handle data.

       This method should only be called to explicitly traverse elements in a chain.
       Client code should use ``next(link)`` and ``link.send(chunk)`` instead.

    .. method:: link.throw(type[, value[, traceback]])

       Raises an exception of ``type`` inside the link. The link may either
       return a final result (including :py:const:`None`), raise :py:exc:`StopIteration` if there are no
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
    return an empty container. Any `1 -> 1` and `n -> 1` element must raise
    :py:exc:`StopTraversal`.

    .. _Generator-Iterator Methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
    """
    chain_linker = None
    #: whether this element processes several data chunks at once
    chain_join = False
    #: whether this element produces several data chunks at once
    chain_fork = False

    def __rshift__(self, children):
        """
        self >> children

        :param children: child or children to bind
        :type children: ChainLink or iterable[ChainLink]
        :returns: link between self and children
        :rtype: LinearChain, ParallelChain or MetaChain
        """
        linker = self.chain_linker if self.chain_linker is not None else DEFAULT_LINKER
        return linker(self, children)

    def __rrshift__(self, parents):
        # parent >> self
        return self << parents

    def __lshift__(self, parents):
        """
        self << parents

        :param parents: parent or parents to bind
        :type parents: ChainLink or iterable[ChainLink]
        :returns: link between self and children
        :rtype: LinearChain, ParallelChain or MetaChain
        """
        linker = self.chain_linker if self.chain_linker is not None else DEFAULT_LINKER
        return linker(parents, self)

    def __rlshift__(self, children):
        # children << self
        return self >> children

    def __iter__(self):
        while True:
            try:
                yield self.chainlet_send(None)
            except StopTraversal as err:
                if err.return_value is not END_OF_CHAIN:
                    yield err.return_value
            except StopIteration:
                break

    def __next__(self):
        return self.send(None)

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):
        """Send a value to this element for processing"""
        # we do one explicit loop to keep overhead low...
        try:
            return self.chainlet_send(value)
        except StopTraversal as err:
            if err.return_value is not END_OF_CHAIN:
                return err.return_value
            # ...then do the correct loop if needed
            while True:
                try:
                    return self.chainlet_send(value)
                except StopTraversal as err:
                    if err.return_value is not END_OF_CHAIN:
                        return err.return_value

    def chainlet_send(self, value=None):
        """Send a value to this element for processing"""
        raise NotImplementedError  # overwrite in subclasses

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

    def chainlet_send(self, value=None):
        raise NotImplementedError


class LinearChain(Chain):
    """
    A linear sequence of chainlets, with each element preceding the next
    """
    chain_join = False
    chain_fork = False

    def chainlet_send(self, value=None):
        for element in self.elements:
            # a StopTraversal may be raised here
            # we do NOT catch it, but let it bubble up instead
            # whoever catches it can extract a potential early return value
            value = element.chainlet_send(value)
        return value

    def __repr__(self):
        return ' >> '.join(repr(elem) for elem in self.elements)


class ConcurrentChain(Chain):  # pylint: disable=abstract-method
    """
    A collection of concurrent chainlets, with multiple elements running at the same time
    """
    chain_join = False
    chain_fork = True

    def __iter__(self):
        while True:
            try:
                result = self.chainlet_send(None)
                if result:
                    yield result
            except StopIteration:
                break

    def send(self, value=None):
        """Send a value to this element for processing"""
        # we do one explicit loop to keep overhead low...
        result = self.chainlet_send(value)
        if result:
            return result
        # ...then do the correct loop if needed
        while True:
            result = self.chainlet_send(value)
            if result:
                return result

    def __repr__(self):
        return repr(self.elements)


class ParallelChain(ConcurrentChain):
    """
    A parallel sequence of chainlets, with each element ranked the same
    """
    chain_join = False
    chain_fork = True

    def chainlet_send(self, value=None):
        try:
            return type(self.elements)(self._send_iter(value))
        except _ElementExhausted:
            raise StopIteration

    def _send_iter(self, value):
        exhausted_elements = 0
        for element in self.elements:
            if element.chain_fork:
                # we explicitly fetch the first item to see if the iterable is empty
                # without forcing the consumption of all items
                element_iter = iter(element.chainlet_send(value))
                try:
                    yield next(element_iter)
                except StopIteration:
                    exhausted_elements += 1
                for val in element_iter:
                    yield val
            else:
                # this is a bit of a judgement call - MF@20170329
                # either we
                # - catch StopTraversal and return, but that means further elements will still get it
                # - we suppress StopTraversal, denying any return_value
                # - we return the Exception, which means later elements must check/filter it
                try:
                    yield element.chainlet_send(value)
                except StopTraversal as err:
                    if err.return_value is not END_OF_CHAIN:
                        yield err.return_value
                except StopIteration:
                    exhausted_elements += 1
        if exhausted_elements and exhausted_elements == len(self.elements):
            raise _ElementExhausted


class MetaChain(ConcurrentChain):
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

    def chainlet_send(self, value=None):
        # traverse breadth first to allow for synchronized forking and joining
        values = [value]
        for element in self.elements:
            # aggregate input for joining paths, flatten output of parallel paths
            if element.chain_join and element.chain_fork:
                values = self._send_n_to_m(element, values)
            # flatten output of parallel paths for each input
            elif not element.chain_join and element.chain_fork:
                values = self._send_1_to_m(element, values)
            # neither fork nor join, unwrap input and output
            elif not element.chain_join and not element.chain_fork:
                values = self._send_1_to_1(element, values)
            elif element.chain_join and not element.chain_fork:
                values = self._send_n_to_1(element, values)
            else:
                raise NotImplementedError
            if not values:
                break
        return values

    @staticmethod
    def _send_n_to_m(element, values):
        # aggregate input for joining paths, flatten output of parallel paths
        return element.chainlet_send(values)

    @staticmethod
    def _send_1_to_m(element, values):
        # flatten output of parallel paths for each input
        return_values = []
        for value in values:
            try:
                return_values.extend(element.chainlet_send(value))
            except StopTraversal as err:
                if err.return_value is not END_OF_CHAIN:
                    return_values.extend(err.return_value)
        return return_values

    @staticmethod
    def _send_n_to_1(element, values):
        # aggregate input for joining paths
        try:
            return [element.chainlet_send(values)]
        except StopTraversal as err:
            if err.return_value is not END_OF_CHAIN:
                return [err.return_value]
            return []

    @staticmethod
    def _send_1_to_1(element, values):
        # unpack input, pack output
        return_values = []
        for value in values:
            try:
                return_values.append(element.chainlet_send(value))
            except StopTraversal as err:
                if err.return_value is not END_OF_CHAIN:
                    return_values.append(err.return_value)
        return return_values

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
