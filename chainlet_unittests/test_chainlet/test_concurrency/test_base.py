from __future__ import absolute_import, division
import unittest

from chainlet.concurrency import base


class TestMultiIter(unittest.TestCase):
    def test_builtin(self):
        values = tuple(range(20))
        for base_type in (list, tuple, set):
            iterable = base_type(values)
            self._test_multi_tee(iterable, values)

    def test_generator(self):
        values = tuple(range(20))
        iterable = (val for val in values)
        self._test_multi_tee(iterable, values)

    def test_future_chain(self):
        values = tuple(range(20))
        value_iter = iter(values)
        iterable = base.FutureChainResults([base.StoredFuture(lambda itr: [next(itr)], value_iter) for _ in range(len(values))])
        self._test_multi_tee(iterable, values)

    def _test_multi_tee(self, iterable, values):
        iters = list(base.multi_iter(iterable, count=4))
        self.assertEqual(len(iters), 4)
        a, b, c, d = iters
        # test single iteration
        self.assertEqual(set(a), set(values))
        # test interleaved iteration
        for _ in range(10):
            self.assertEqual(next(b), next(c))
            self.assertEqual(next(c), next(b))
        # test final iteration
        self.assertEqual(set(d), set(values))
