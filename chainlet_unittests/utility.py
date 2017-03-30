from __future__ import absolute_import, division, print_function
import chainlet
import chainlet.chainlink


class NamedChainlet(chainlet.NoOp):
    """Chainlet with nice representation"""
    def __init__(self, name):
        self.name = name

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


@chainlet.funclet
def abort_return(value):
    raise chainlet.chainlink.StopTraversal(value)


@chainlet.funclet
def abort_swallow(value):
    raise chainlet.chainlink.StopTraversal


class AbortEvery(chainlet.ChainLink):
    def __init__(self, every=2):
        super(AbortEvery, self).__init__()
        self.every = every
        self._count = 0

    def chainlet_send(self, value=None):
        self._count += 1
        if self._count % self.every:
            return value
        raise chainlet.chainlink.StopTraversal


class ReturnEvery(chainlet.ChainLink):
    def __init__(self, every=2):
        super(ReturnEvery, self).__init__()
        self.every = every
        self._count = 0

    def chainlet_send(self, value=None):
        self._count += 1
        if self._count % self.every:
            raise chainlet.chainlink.StopTraversal
        raise chainlet.chainlink.StopTraversal(value)
