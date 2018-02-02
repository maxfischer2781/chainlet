import itertools
import unittest
import time

import chainlet
from chainlet.dataflow import NoOp, MergeLink

from chainlet_unittests.utility import Adder


@chainlet.funclet
def sleep(value, seconds):
    time.sleep(seconds)
    return value


class PrimitiveTestCases(object):
    class ConcurrentChain(unittest.TestCase):
        chain_type = chainlet.chainlink.Chain
        converter = None

        def test_concurrent(self):
            """concurrent sleep"""
            sleep_chain = self.chain_type((Adder(1), sleep(seconds=0.05), sleep(seconds=0.05)))
            start_time = time.time()
            result = list(sleep_chain.dispatch(range(5)))
            end_time = time.time()
            self.assertEqual(result, list(range(1, 6)))
            self.assertLess(end_time - start_time, 0.5)

        def test_convert_concurrent(self):
            """concurrent sleep from converter"""
            if self.converter is None:
                raise unittest.SkipTest('no converter for %s' % self.__class__.__name__)
            sleep_chain = self.converter(Adder(1) >> sleep(seconds=0.05) >> sleep(seconds=0.05))
            start_time = time.time()
            result = list(sleep_chain.dispatch(range(5)))
            end_time = time.time()
            self.assertEqual(result, list(range(1, 6)))
            self.assertLess(end_time - start_time, 0.5)

    class ConcurrentBundle(unittest.TestCase):
        bundle_type = chainlet.chainlink.Bundle
        converter = None

        def test_concurrent(self):
            """concurrent sleep"""
            sleep_chain = NoOp() >> self.bundle_type((sleep(seconds=0.1) for _ in range(5)))
            start_time = time.time()
            result = sleep_chain.send(1)
            end_time = time.time()
            self.assertEqual(result, [1, 1, 1, 1, 1])
            self.assertLess(end_time - start_time, 0.5)

        def test_convert_concurrent(self):
            """concurrent sleep from converter"""
            if self.converter is None:
                raise unittest.SkipTest('no converter for %s' % self.__class__.__name__)
            sleep_chain = NoOp() >> self.converter([sleep(seconds=0.1) for _ in range(5)])
            start_time = time.time()
            result = sleep_chain.send(1)
            end_time = time.time()
            self.assertEqual(result, [1, 1, 1, 1, 1])
            self.assertLess(end_time - start_time, 0.5)

        def test_simple(self):
            """simple bundle as `a >> (b, c)`"""
            primitives = [Adder(val) for val in (0, -2, 16, -1E6)]
            for elements in itertools.product(primitives, repeat=3):
                a, b, c = elements
                reference_chain = a >> (b, c)
                concurrent_chain = a >> self.bundle_type((b, c))
                for initial in (0, -12, 124, -12234, +1E6):
                    self.assertEqual(reference_chain.send(initial), concurrent_chain.send(initial))

        def test_multi(self):
            """nested bundle as `a >> (b,  c >> (d, e >> ...`"""
            primitives = [Adder(val) for val in (0, -2, -1E6)]
            for elements in itertools.product(primitives, repeat=6):
                a, b, c, d, e, f = elements
                reference_chain = a >> (b, c >> (d, e >> f))
                concurrent_chain = a >> self.bundle_type((b, c >> self.bundle_type((d, e >> f))))
                for initial in (0, -12, 124, -12234, +1E6):
                    self.assertEqual(reference_chain.send(initial), concurrent_chain.send(initial))

        def test_repacking(self):
            """chained bundles as `a >> (b, c, d) >> (e, f, g) >> ..."""
            primitives = [Adder(val) for val in (0, -2, -1E6)]
            delay = 0.00001  # sleep to interleave threads
            for elements in itertools.product(primitives, repeat=6):
                a, b, c, d, e, f = elements
                reference_chain = a >> (b, c, d) >> (MergeLink() >> c, MergeLink() >> d, e) >> f
                concurrent_chain = a >> self.bundle_type(
                    (sleep(seconds=delay) >> b, sleep(seconds=delay) >> c, sleep(seconds=delay) >> d)) >> self.bundle_type(
                    (
                        MergeLink() >> sleep(seconds=delay) >> c,
                        MergeLink() >> sleep(seconds=delay) >> d,
                        sleep(seconds=delay) >> e)
                ) >> f
                for initial in (0, -12, 124, -12234, +1E6):
                    sequential = reference_chain.send(initial)
                    concurrent = concurrent_chain.send(initial)
                    self.assertEqual(sequential, concurrent)
