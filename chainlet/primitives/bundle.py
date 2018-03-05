from .. import signals
from ..chainsend import lazy_send
from .link import ChainLink
from .compound import CompoundLink


class Bundle(CompoundLink):
    """
    A group of chainlets that concurrently process each :term:`data chunk`
    """
    chain_fork = True
    __slots__ = ('chain_join',)

    def __init__(self, elements):
        super(Bundle, self).__init__(elements)
        if self.elements:
            self.chain_join = any(element.chain_join for element in self.elements)
        else:
            self.chain_join = False

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


def bundle_sequences(element):
    """
    Convert sequence types to bundles

    This converter automatically constructs a :py:class:`~.Bundle`
    from any :py:class:`tuple`, :py:class:`list` or :py:class:`set`
    encountered during linking.
    The following two lines produce the same chain:

    .. code:: python

        a >> [b, c, d] >> e
        a >> Bundle((b, c, d)) >> e
    """
    if isinstance(element, (tuple, list, set)):
        return Bundle(element)
    return NotImplemented

ChainLink.chain_types.add_converter(bundle_sequences)
ChainLink.chain_types.base_bundle_type = Bundle
