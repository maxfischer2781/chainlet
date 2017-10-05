from __future__ import division, absolute_import
import sys

from .compat import throw_method as _throw_method
from . import utility


__all__ = ['END_OF_CHAIN', 'StopTraversal', 'ChainLink']

END_OF_CHAIN = utility.Sentinel('END OF CHAIN')


class StopTraversal(Exception):
    """
    Stop the traversal of a chain

    :param return_value: the value returned by the chain

    Any chain element raising :py:exc:`~.StopTraversal` signals that
    subsequent elements of the chain should not be visited. If
    ``return_value`` is set, it becomes the final return value of the chain.
    Otherwise, no return value is provided.

    Raising :py:exc:`~.StopTraversal` does *not* mean the element is exhausted.
    It may still produce values regularly on future traversal.
    If an element will *never* produce values again, it should raise :py:exc:`StopIteration`.

    :note: This signal explicitly affects the current chain only. It does not
           affect other, parallel chains of a graph.
    """
    def __init__(self, return_value=END_OF_CHAIN):
        Exception.__init__(self)
        self.return_value = return_value


class _ElementExhausted(Exception):
    """An element has no more values to produce"""


class ChainTypes(object):
    """
    Helper for primitives/types forming chains

    :warning: This is an internal, WIP helper.
              Names, APIs and signatures are subject to change.
    """
    #: callables to convert elements; must return a ChainLink or raise TypeError
    _converters = []
    _instance = None
    chain_type = None  # type: Type[Chain]
    flat_chain_type = None  # type: Type[FlatChain]
    bundle_type = None  # type: Type[Bundle]

    def __new__(cls):
        if not cls.__dict__.get('_instance'):
            cls._instance = object.__new__(cls)
            cls._converters = []
        return cls._instance

    def convert(self, element):
        if isinstance(element, ChainLink):
            return element
        for converter in self.converters:
            link = converter(element)
            if link is not NotImplemented:
                return link
        raise TypeError('%r cannot be converted to a chainlink' % element)

    def supersedes(self, other):
        return isinstance(self, type(other)) and type(other) != type(self)

    @property
    def converters(self):
        for cls in self.__class__.mro():
            try:
                for converter in cls._converters:
                    yield converter
            except AttributeError:
                pass

    @classmethod
    def add_converter(cls, converter):
        """
        Add a converter to this Converter type and all its children

        Each converter is a callable with the signature

        .. py:function:: converter(element: object) -> :py:class:`ChainLink`

        and must create a :py:class:`ChainLink` for any valid ``element`` input.
        For any ``element`` that is not valid input, :py:const:`NotImplemented` must be returned.
        """
        cls._converters.append(converter)


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
    chain_types = ChainTypes()
    #: whether this element processes several data chunks at once
    chain_join = False
    #: whether this element produces several data chunks at once
    chain_fork = False

    def _link(self, parent, child):
        """Link the chainlinks parent to child"""
        chain = self.chain_types.chain_type((parent, child))
        # avoid having arbitrary type for empty links
        if not chain:
            return NeutralLink()
        # avoid useless nesting
        elif len(chain) == 1:
            return chain[0]
        else:
            return chain

    def __rshift__(self, child):
        """
        self >> child

        :param child: following link to bind
        :type child: ChainLink or iterable[ChainLink]
        :returns: link between self and child
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        # NOTE: The semantics and details for superseding operators
        #       are NOT part of a stable API.
        child = self.chain_types.convert(child)
        if child.chain_types.supersedes(self.chain_types):
            return child << self
        return self._link(self, child)

    def __rrshift__(self, parent):
        # parent >> self
        return self << parent

    def __lshift__(self, parent):
        """
        self << parents

        :param parent: preceding link to bind
        :type parent: ChainLink or iterable[ChainLink]
        :returns: link between self and children
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        # -- type hierarchy based reflection
        # see note on __rshift__
        parent = self.chain_types.convert(parent)
        if parent.chain_types.supersedes(self.chain_types):
            return parent >> self
        return self._link(parent, self)

    def __rlshift__(self, child):
        # child << self
        return self >> child

    def __iter__(self):
        if self.chain_fork:
            return self._iter_fork()
        return self._iter_flat()

    def _iter_flat(self):
        while True:
            try:
                yield self.chainlet_send(None)
            except StopTraversal as err:
                if err.return_value is not END_OF_CHAIN:
                    yield err.return_value
            except StopIteration:
                break

    def _iter_fork(self):
        while True:
            try:
                result = list(self.chainlet_send(None))
                if result:
                    yield result
            except (StopIteration, _ElementExhausted):
                break

    def __next__(self):
        return self.send(None)

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):
        """Send a value to this element for processing"""
        if self.chain_fork:
            return self._send_fork(value)
        return self._send_flat(value)

    def _send_flat(self, value=None):
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

    def _send_fork(self, value=None):
        # we do one explicit loop to keep overhead low...
        result = list(self.chainlet_send(value))
        if result:
            return result
        # ...then do the correct loop if needed
        while True:
            result = list(self.chainlet_send(value))
            if result:
                return result

    def chainlet_send(self, value=None):
        """Send a value to this element for processing"""
        raise NotImplementedError  # overwrite in subclasses

    throw = _throw_method

    def close(self):
        """Close this element, freeing resources and blocking further interactions"""
        pass


class NeutralLink(ChainLink):
    """
    An :term:`chainlink` that acts as a neutral element for linking

    This link does not have any effect on any :term:`data chunk` passed to it.
    It acts as a neutral element for linking, meaning its
    presence or absence in a :term:`chain` does not have any effect.

    This element is useful when an element is syntactically required, but no
    action on data is desired.
    It can be used to force automatic conversion,
    e.g. when linking to a :py:class:`tuple` of elements.

    :note: A :py:class:`~.NeutralLink` *does* have an effect in a :term:`bundle`.
           It creates an additional :term:`branch` which passes on data unchanged.
    """
    def chainlet_send(self, value=None):
        return value

    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return bool(self) == bool(other)
        return NotImplemented

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return super(NeutralLink, self).__repr__()


# Chain/Graph compound objects
# These should probably not be public at all...
class CompoundLink(ChainLink):
    """
    Baseclass for compound chainlets consisting of other chainlets

    :param elements: the chainlets making up this chain
    :type elements: iterable[:py:class:`ChainLink`]

    These compound elements expose the regular interface of chainlets.
    They can again be chained or stacked to form more complex chainlets.

    Any :py:class:`CompoundLink` based on :term:`sequential <sequence>` or :term:`mapped <mapping>`
    elements allows for subscription:

    .. describe:: len(link)

       Return the number of elements in the link.

    .. describe:: link[i]

       Return the ``i``'th :term:`chainlink` of the link.

    .. describe:: link[i:j:k]

       Return a *new* link consisting of the elements defined by the :term:`slice` ``[i:j:k]``.
       This follows the same semantics as subscription of regular :term:`sequences <sequence>`.

    .. describe:: bool(link)

        Whether the link contains any elements.
    """
    def __init__(self, elements):
        self.elements = tuple(elements)
        super(CompoundLink, self).__init__()

    def __len__(self):
        return len(self.elements)

    def __bool__(self):
        return bool(self.elements)

    __nonzero__ = __bool__

    def __getitem__(self, item):
        if item.__class__ == slice:
            return self.__class__(self.elements[item])
        return self.elements[item]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.elements == other.elements
        return NotImplemented

    def __hash__(self):
        return hash(self.elements)

    def chainlet_send(self, value=None):
        raise NotImplementedError


class Bundle(CompoundLink):
    """
    A group of chainlets that concurrently process each :term:`data chunk`
    """
    chain_join = False
    chain_fork = True

    def chainlet_send(self, value=None):
        results = []
        elements_exhausted = 0
        for element in self.elements:
            if element.chain_fork:
                try:
                    results.extend(element.chainlet_send(value))
                except StopIteration:
                    elements_exhausted += 1
            else:
                # this is a bit of a judgement call - MF@20170329
                # either we
                # - catch StopTraversal and return, but that means further elements will still get it
                # - we suppress StopTraversal, denying any return_value
                # - we return the Exception, which means later elements must check/filter it
                try:
                    results.append(element.chainlet_send(value))
                except StopTraversal as err:
                    if err.return_value is not END_OF_CHAIN:
                        results.append(err.return_value)
                except StopIteration:
                    elements_exhausted += 1
        if elements_exhausted == len(self.elements):
            raise StopIteration
        return results

    def __repr__(self):
        return repr(self.elements)


class Chain(CompoundLink):
    """
    A group of chainlets that sequentially process each :term:`data chunk`

    :param elements: the chainlets making up this chain
    :type elements: iterable[:py:class:`ChainLink`]

    :note: If ``elements`` contains a :py:class:`~.Chain`, this is flattened
           and any sub-elements are directly included in the new :py:class:`~.Chain`.

    Slicing a chain guarantees consistency of the sum of parts and the chain.
    Linking an ordered, complete sequence of subslices recreates an equivalent chain.

    .. code:: python

        chain == chain[:i] >> chain[i:]

    Also, splitting a chain allows to pass values along the parts for equal results.
    This is useful if you want to inspect a chain at a specific position.

    .. code:: python

        chain_result = chain.send(value)
        temp_value = chain[:i].send(value)
        split_result = chain[i:].send(temp_value)
        chain_result == temp_value
    """
    chain_join = False
    chain_fork = False

    def __new__(cls, elements):
        if not any(element.chain_fork or element.chain_join for element in cls._flatten(elements)):
            return super(Chain, cls).__new__(cls.chain_types.flat_chain_type)
        return super(Chain, cls).__new__(cls.chain_types.chain_type)

    def __init__(self, elements):
        super(Chain, self).__init__(self._flatten(elements))
        if elements:
            self.chain_fork = self._chain_forks(elements)
            self.chain_join = elements[0].chain_join

    @staticmethod
    def _flatten(elements):
        for element in elements:
            if not element:
                continue
            elif isinstance(element, Chain):
                for sub_element in element.elements:
                    yield sub_element
            else:
                yield element

    @staticmethod
    def _chain_forks(elements):
        """Detect whether a sequence of elements leads to a fork of streams"""
        # we are only interested in the result, so unwind from the end
        for element in reversed(elements):
            if element.chain_fork:
                return True
            elif element.chain_join:
                return False
        return False

    def chainlet_send(self, value=None):
        # traverse breadth first to allow for synchronized forking and joining
        if self.chain_join:
            values = value
        else:
            values = [value]
        try:
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
            if self.chain_fork:
                return list(values)
            else:
                try:
                    return next(iter(values))
                except IndexError:
                    raise StopTraversal
        # An element in the chain is exhausted permanently
        except _ElementExhausted:
            raise StopIteration

    @staticmethod
    def _send_n_to_m(element, values):
        # aggregate input for joining paths, flatten output of parallel paths
        # iterator goes in, iterator comes out
        return element.chainlet_send(values)

    @staticmethod
    def _send_1_to_m(element, values):
        # flatten output of parallel paths for each input
        # chunks from iterator go in, iterator comes out for each chunk
        for value in values:
            try:
                for return_value in element.chainlet_send(value):
                    yield return_value
            except StopTraversal as err:
                if err.return_value is not END_OF_CHAIN:
                    for return_value in err.return_value:
                        yield return_value
            except StopIteration:
                raise _ElementExhausted

    @staticmethod
    def _send_n_to_1(element, values):
        # aggregate input for joining paths
        # iterator goes in, values comes out
        try:
            return [element.chainlet_send(values)]
        except StopTraversal as err:
            if err.return_value is not END_OF_CHAIN:
                return [err.return_value]
            return []

    @staticmethod
    def _send_1_to_1(element, values):
        # unpack input, pack output
        # chunks from iterator go in, one chunk comes out for each chunk
        for value in values:
            try:
                yield element.chainlet_send(value)
            except StopTraversal as err:
                if err.return_value is not END_OF_CHAIN:
                    yield err.return_value
            except StopIteration:
                raise _ElementExhausted

    def __repr__(self):
        return ' >> '.join(repr(elem) for elem in self.elements)


class FlatChain(Chain):
    """
    A specialised :py:class:`Chain` which never forks or joins internally
    """
    chain_join = False
    chain_fork = False

    # short circuit to the flat iter/send, since this is all we ever need
    __iter__ = ChainLink._iter_flat  # pylint:disable=protected-access
    send = ChainLink._send_flat  # pylint:disable=protected-access

    def chainlet_send(self, value=None):
        for element in self.elements:
            # a StopTraversal may be raised here
            # we do NOT catch it, but let it bubble up instead
            # whoever catches it can extract a potential early return value
            value = element.chainlet_send(value)
        return value


def bundle_sequences(element):
    if isinstance(element, (tuple, list, set)):
        return Bundle(element)
    return NotImplemented

ChainTypes.add_converter(bundle_sequences)
ChainTypes.chain_type = Chain
ChainTypes.flat_chain_type = FlatChain
ChainTypes.bundle_type = Bundle
