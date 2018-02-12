from .. import signals
from ..chainsend import lazy_send
from .compound import CompoundLink


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
