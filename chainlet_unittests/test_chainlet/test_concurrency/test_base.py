from __future__ import absolute_import, division
import unittest

from chainlet.concurrency import base

from . import testbase_primitives


def return_stored(payload):
    return payload


def raise_stored(payload):
    raise payload


class TestMultiIter(unittest.TestCase):
    def test_builtin(self):
        """multi iter on list, tuple, ..."""
        values = tuple(range(20))
        for base_type in (list, tuple, set):
            iterable = base_type(values)
            self._test_multi_tee(iterable, values)

    def test_generator(self):
        """multi iter on `(val for val in values)`"""
        values = tuple(range(20))
        iterable = (val for val in values)
        self._test_multi_tee(iterable, values)

    def test_future_chain(self):
        """multi iter on future chain results"""
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
        self.assertEqual((next(b), next(b)), (next(c), next(c)))
        for _ in range(8):
            self.assertEqual(next(b), next(c))
            self.assertEqual(next(c), next(b))
        self.assertEqual((next(b), next(b)), (next(c), next(c)))
        with self.assertRaises(StopIteration):
            next(b)
        with self.assertRaises(StopIteration):
            next(c)
        # test final iteration
        self.assertEqual(set(d), set(values))


class TestFutureChainResults(unittest.TestCase):
    def test_exception(self):
        for ex_type in (Exception, ArithmeticError, KeyError, IndexError, OSError, AssertionError, SystemExit):
            with self.subTest(ex_type=ex_type):
                raise_middle_iterable = base.FutureChainResults([
                    base.StoredFuture(return_stored, [1, 2]),
                    base.StoredFuture(raise_stored, ex_type),
                    base.StoredFuture(return_stored, [3])
                ])
                a, b, c, d = (iter(raise_middle_iterable) for _ in range(4))
                self.assertEqual((next(a), next(b)), (1, 1))
                self.assertEqual((next(a), next(b), next(c)), (2, 2, 1))
                self.assertEqual(next(c), 2)
                with self.assertRaises(ex_type):
                    next(a)
                with self.assertRaises(ex_type):
                    next(b)
                with self.assertRaises(ex_type):
                    next(c)
                with self.assertRaises(ex_type):
                    list(d)


# non-concurrent primitives
class NonConcurrentBundle(testbase_primitives.PrimitiveTestCases.ConcurrentBundle):
    test_concurrent = None


# dummy-concurrent primitives
class LocalBundle(testbase_primitives.PrimitiveTestCases.ConcurrentBundle):
    test_concurrent = None
    bundle_type = base.ConcurrentBundle
