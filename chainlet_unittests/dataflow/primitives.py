import itertools
import unittest

from chainlet_unittests.utility import Adder


class ChainPrimitives(unittest.TestCase):
    def test_pair(self):
        """Push single link chain as `parent >> child`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for parent, child in itertools.product(elements, repeat=2):
            for initial in (0, 15, -15, -1E6, +1E6):
                with self.subTest(parent=parent, child=child, initial=initial):
                    expected = initial + parent.value + child.value
                    chain_a = parent >> child
                    self.assertEqual(chain_a.send(initial), expected)

    def test_multi(self):
        """Push multi link chain as `a >> b >> c >> ...`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for chain in itertools.product(elements, repeat=5):
            for initial in (0, 15, -15, -1E6, +1E6):
                with self.subTest(chain=chain, initial=initial):
                    expected = initial + sum(element.value for element in chain)
                    a, b, c, d, e = chain
                    chain_a = a >> b >> c >> d >> e
                    self.assertEqual(chain_a.send(initial), expected)

    def test_fork(self):
        """Push fork link chain as `a >> (b, c)`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for a, b, c in itertools.product(elements, repeat=3):
            for initial in (0, 15, -15, -1E6, +1E6):
                with self.subTest(a=a, b=b, c=c, initial=initial):
                    expected = [initial + a.value + b.value, initial + a.value + c.value]
                    chain_a = a >> (b, c)
                    self.assertEqual(chain_a.send(initial), expected)
