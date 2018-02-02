from __future__ import division, absolute_import, print_function
import sys

from . import signals
from .chainsend import lazy_send
from .compat import throw_method as _throw_method

__all__ = ['ChainLink']


class LinkPrimitives(object):
    """
    Primitives used in a linker domain

    :warning: This is an internal, WIP helper.
              Names, APIs and signatures are subject to change.
    """
    #: callables to convert elements; must return a ChainLink or raise TypeError
    _converters = []
    _instance = None
    #: the basic :term:`chainlink` type from which all primitives of this domain derive
    base_link_type = None  # type: Type[ChainLink]
    #: the basic :term:`chain` type holding sequences of :term:`chainlinks <chainlink>`
    base_chain_type = None  # type: Type[Chain]
    #: the flat :term:`chain` type holding sequences of simple :term:`chainlinks <chainlink>`
    flat_chain_type = None  # type: Type[FlatChain]
    #: the basic :term:`bundle` type holding groups of concurrent :term:`chainlinks <chainlink>`
    base_bundle_type = None  # type: Type[Bundle]

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

    .. method:: iter(link)

       Create an iterator over all data chunks that can be created.
       Empty results are ignored.

    .. method:: link.__next__()
                link.send(None)
                next(link)

       Create a new chunk of data. Raise :py:exc:`StopIteration` if there are
       no more chunks. Implicitly used by ``next(link)``.

    .. method:: link.send(chunk)

       Process a data ``chunk``, and return the result.

    .. note:: The ``next`` variants contrast with ``iter`` by also returning empty chunks.
              Use variations of ``next(iter(link))`` for an explicit iteration.

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
    chain_types = LinkPrimitives()
    #: whether this element processes several data chunks at once
    chain_join = False
    #: whether this element produces several data chunks at once
    chain_fork = False

    def _link(self, parent, child):
        """Link the chainlinks parent to child"""
        chain = self.chain_types.base_chain_type((parent, child))
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
        child = self.chain_types.convert(child)
        return self._link(self, child)

    def __rrshift__(self, parent):
        # parent >> self
        return self << parent

    def __lshift__(self, parent):
        """
        self << parent

        :param parent: preceding link to bind
        :type parent: ChainLink or iterable[ChainLink]
        :returns: link between self and children
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        parent = self.chain_types.convert(parent)
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
            except signals.StopTraversal:
                continue
            except StopIteration:
                break

    def _iter_fork(self):
        while True:
            try:
                result = list(self.chainlet_send(None))
                if result:
                    yield result
            except (StopIteration, signals.ChainExit):
                break

    def __next__(self):
        return self.send(None)

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):
        """Send a single value to this element for processing"""
        if self.chain_fork:
            return self._send_fork(value)
        return self._send_flat(value)

    def _send_flat(self, value=None):
        try:
            return self.chainlet_send(value)
        except signals.StopTraversal:
            return None

    def _send_fork(self, value=None):
        return list(self.chainlet_send(value))

    def dispatch(self, values):
        """Dispatch multiple values to this element for processing"""
        for result in lazy_send(self, values):
            yield result

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

    def __init__(self, elements):
        super(Bundle, self).__init__(elements)
        if self.elements:
            self.chain_join = any(element.chain_join for element in self.elements)

    def chainlet_send(self, value=None):
        if self.chain_join:
            values = list(value)
        else:
            values = (value,)
        results = []
        elements_exhausted = 0
        for element in self.elements:
            try:
                results.extend(lazy_send(element, values))
            except signals.ChainExit:
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

    :note: Some optimised chainlets may assimilate subsequent chainlets during linking.
           The rules for splitting chains still apply, though the actual chain elements
           may differ from the provided ones.
    """
    chain_join = False
    chain_fork = False

    def __new__(cls, elements):
        if not any(element.chain_fork or element.chain_join for element in cls._flatten(elements)):
            return super(Chain, cls).__new__(cls.chain_types.flat_chain_type)
        return super(Chain, cls).__new__(cls.chain_types.base_chain_type)

    def __init__(self, elements):
        super(Chain, self).__init__(self._flatten(elements))
        if elements:
            self.chain_fork = self._chain_forks(elements)
            self.chain_join = elements[0].chain_join

    @classmethod
    def _flatten(cls, elements):
        for element in elements:
            if not element:
                continue
            elif isinstance(element, Chain) and not element.chain_types.supersedes(cls.chain_types):
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

    # extract-link for first element
    # When linking to a chain, the chain as a single element shadows
    # the link behaviour of the head/tail.
    def __rshift__(self, child):
        """
        self >> child

        :param child: following link to bind
        :type child: ChainLink or iterable[ChainLink]
        :returns: link between self and child
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        child = self.chain_types.convert(child)
        if self and type(self.elements[-1]).__rshift__ not in (
                self.chain_types.base_link_type.__rshift__, self.chain_types.base_chain_type.__rshift__
        ):
            return self._link(self[:-1], self.elements[-1] >> child)
        return self._link(self, child)

    def __lshift__(self, parent):
        """
        self << parents

        :param parent: preceding link to bind
        :type parent: ChainLink or iterable[ChainLink]
        :returns: link between self and children
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        parent = self.chain_types.convert(parent)
        if self and type(self.elements[0]).__lshift__ not in (
                self.chain_types.base_link_type.__lshift__, self.chain_types.base_chain_type.__lshift__
        ):
            return self._link(self.elements[0] << parent, self[1:])
        return self._link(parent, self)

    def chainlet_send(self, value=None):
        # traverse breadth first to allow for synchronized forking and joining
        if self.chain_join:
            values = value
        else:
            values = [value]
        try:
            for element in self.elements:
                values = lazy_send(element, values)
                if not values:
                    break
            if self.chain_fork:
                return list(values)
            else:
                try:
                    return next(iter(values))
                except IndexError:
                    raise signals.StopTraversal
        # An element in the chain is exhausted permanently
        except signals.ChainExit:
            raise StopIteration

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

LinkPrimitives.add_converter(bundle_sequences)
LinkPrimitives.base_link_type = ChainLink
LinkPrimitives.base_chain_type = Chain
LinkPrimitives.flat_chain_type = FlatChain
LinkPrimitives.base_bundle_type = Bundle
