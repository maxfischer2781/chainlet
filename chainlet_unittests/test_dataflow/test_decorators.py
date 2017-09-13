import itertools
import unittest

from chainlet import ChainLink, genlet, funclet
from chainlet.dataflow import joinlet, forklet, NoOp
from chainlet.protolink import printlet
import chainlet._debug

from chainlet_unittests.utility import Adder, produce, abort_return, abort_swallow, AbortEvery, ReturnEvery


class Decorators(unittest.TestCase):
    def test_chainlink(self):
        @joinlet
        class Join(ChainLink):
            def chainlet_send(self, value=None):
                return sum(value)

        @forklet
        class Fork(ChainLink):
            def chainlet_send(self, value=None):
                return [value]

        self._test_flow(join_type=Join, fork_type=Fork)

    def _test_flow(self, join_type, fork_type):
        join_chain = (produce([1, 1, 1]), produce([2, 2, 2])) >> join_type()
        self.assertEqual(list(join_chain), [3, 3, 3])
        fork_chain = produce([1, 1, 1]) >> fork_type()
        self.assertEqual(list(fork_chain), [[1], [1], [1]])
        fork_join_chain = produce([1, 1, 1]) >> fork_type() >> join_type()
        self.assertEqual(list(fork_join_chain), [1, 1, 1])
