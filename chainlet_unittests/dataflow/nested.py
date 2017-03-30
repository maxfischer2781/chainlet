import itertools
import unittest

from chainlet_unittests.utility import Adder


class ChainNested(unittest.TestCase):
    def test_multi(self):
        """Push nested fork as `a >> (b,  c >> (d, e >> ...`"""
        elements = [Adder(val) for val in (0, -2, -1E6)]
        for elements in itertools.product(elements, repeat=6):
            for initial in (0, -15, +1E6):
                with self.subTest(chain=elements, initial=initial):
                    a, b, c, d, e, f = elements
                    chain_a = a >> (b, c >> (d, e >> f))
                    expected = [
                        initial + a.value + b.value,
                        initial + a.value + c.value + d.value,
                        initial + a.value + c.value + e.value + f.value,
                    ]
                    self.assertEqual(len(chain_a.send(initial)), 3)  # flat result, number of leaf nodes
                    self.assertEqual(chain_a.send(initial), expected)
