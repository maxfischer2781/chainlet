from .. import signals
from ..chainsend import lazy_send
from .link import ChainLink
from .compound import CompoundLink


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

ChainLink.chain_types.base_chain_type = Chain
ChainLink.chain_types.flat_chain_type = FlatChain
