from __future__ import absolute_import, division
import chainlet


class NamedChainlet(chainlet.ChainLink):
    """Chainlet with nice representation"""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '%s' % self.name


class Adder(NamedChainlet):
    def __init__(self, value=2):
        NamedChainlet.__init__(self, name='%+d' % value)
        self.value = value

    def send(self, value=None):
        return value + self.value
