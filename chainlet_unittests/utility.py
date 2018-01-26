from __future__ import absolute_import, division, print_function
import os
import multiprocessing
import threading

import chainlet
import chainlet.dataflow
import chainlet.chainlink
import chainlet.signals


class NamedChainlet(chainlet.dataflow.NoOp):
    """Chainlet with nice representation"""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '%s' % self.name


class Adder(NamedChainlet):
    def __init__(self, value=2):
        NamedChainlet.__init__(self, name='<%+d>' % value)
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


class MultiprocessBuffer(Buffer):
    def __init__(self):
        super(MultiprocessBuffer, self).__init__()
        self._queue = multiprocessing.Queue()
        self._close_signal = os.urandom(16)
        self._pid = os.getpid()
        receiver = threading.Thread(target=self._recv)
        receiver.daemon = True
        receiver.start()

    def _recv(self):
        _close_signal = self._close_signal
        _queue = self._queue
        buffer = self.buffer
        del self
        while True:
            value = _queue.get()
            if value == _close_signal:
                break
            buffer.append(value)
        _queue.close()

    def chainlet_send(self, value=None):
        self._queue.put(value)
        return value

    def __del__(self):
        self._queue.put(self._close_signal)
        self._queue.close()


@chainlet.genlet(prime=False)
def produce(iterable):
    """Produce values from an iterable for a chain"""
    for element in iterable:
        yield element


@chainlet.funclet
def abort_swallow(value):
    """Always abort the chain without returning"""
    raise chainlet.signals.StopTraversal


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
        raise chainlet.signals.StopTraversal


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
            raise chainlet.signals.StopTraversal
        self._count += 1
        return value
