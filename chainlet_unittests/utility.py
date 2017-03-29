from __future__ import absolute_import, division, print_function
import chainlet


class NamedChainlet(chainlet.ChainLink):
    """Chainlet with nice representation"""
    def __init__(self, name):
        self.name = name

    @staticmethod
    def chainlet_send(value=None):  # pylint: disable=no-self-use
        """Send a value to this element for processing"""
        return value

    def __repr__(self):
        return '%s' % self.name


class Adder(NamedChainlet):
    def __init__(self, value=2):
        NamedChainlet.__init__(self, name='%+d' % value)
        self.value = value

    def chainlet_send(self, value=None):
        return value + self.value


class Buffer(chainlet.ChainLink):
    def __init__(self):
        self.buffer = []

    def chainlet_send(self, value=None):
        self.buffer.append(value)
        return value

    def __repr__(self):
        return '<%s>' % self.buffer


@chainlet.genlet(prime=False)
def produce(iterable):
    for element in iterable:
        yield element
