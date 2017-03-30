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
    """Produce values from an iterable for a chain"""
    for element in iterable:
        yield element


@chainlet.funclet
def abort_return(value):
    """Always return input by aborting the chain"""
    raise chainlet.chainlink.StopTraversal(value)


@chainlet.funclet
def abort_swallow(value):
    """Always abort the chain without returning"""
    raise chainlet.chainlink.StopTraversal


class AbortEvery(chainlet.ChainLink):
    """
    Abort every n'th traversal of the chain

    This returns its input for calls 1, ..., n-1, then raise StopTraversal on n.
    """
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
    """
    Abort-return every n'th traversal of the chain

    This abort-returns its input for call 1, then raise StopTraversal on 2, ..., n.
    """
    def __init__(self, every=2):
        super(ReturnEvery, self).__init__()
        self.every = every
        self._count = 0

    def chainlet_send(self, value=None):
        if self._count % self.every:
            self._count += 1
            raise chainlet.chainlink.StopTraversal
        self._count += 1
        raise chainlet.chainlink.StopTraversal(value)
