import unittest

from chainlet import ChainLink, genlet, funclet
from chainlet.dataflow import joinlet, forklet

from chainlet_unittests.utility import produce


class Decorators(unittest.TestCase):
    def test_chainlink(self):
        """Decorate: class Join(ChainLink) ..."""
        @joinlet
        class Join(ChainLink):
            def chainlet_send(self, value=None):
                return sum(value)

        @forklet
        class Fork(ChainLink):
            def chainlet_send(self, value=None):
                return [value]

        self._test_flow(join_type=Join, fork_type=Fork)

    def test_genlet(self):
        """Decorate: @genlet ..."""
        @joinlet
        @genlet
        def join():
            value = yield
            while True:
                value = yield sum(value)

        @forklet
        @genlet
        def fork():
            value = yield
            while True:
                value = yield [value]

        self._test_flow(join_type=join, fork_type=fork)

    def test_funclet(self):
        """Decorate: @funclet ..."""
        @joinlet
        @funclet
        def join(value):
            return sum(value)

        @forklet
        @funclet
        def fork(value):
            return [value]

        self._test_flow(join_type=join, fork_type=fork)

    def _test_flow(self, join_type, fork_type):
        join_chain = (produce([1, 1, 1]), produce([2, 2, 2])) >> join_type()
        self.assertEqual(list(join_chain), [3, 3, 3])
        fork_chain = produce([1, 1, 1]) >> fork_type()
        self.assertEqual(list(fork_chain), [[1], [1], [1]])
        fork_join_chain = produce([1, 1, 1]) >> fork_type() >> join_type()
        self.assertEqual(list(fork_join_chain), [1, 1, 1])
