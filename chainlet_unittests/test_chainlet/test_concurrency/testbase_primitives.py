import itertools
import unittest

import chainlet

from chainlet_unittests.utility import Adder, produce


class PrimitiveTestCases(object):
    class ConcurrentBundle(unittest.TestCase):
        bundle_type = chainlet.chainlink.Bundle

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
