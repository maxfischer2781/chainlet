import itertools
import unittest

from chainlet_unittests.utility import Adder, produce, abort_return, abort_swallow, AbortEvery, ReturnEvery


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

    def test_abort(self):
        """Abort in nested fork"""
        elements = [Adder(val) for val in (0, -2, -1E6)]
        for elements in itertools.product(elements, repeat=3):
            with self.subTest(elements=elements):
                a, b, c = elements
                initials = (0, 15, -15, -1E6, +1E6, 0)
                chain_abort_one_swallow = produce(initials) >> a >> (b >> abort_swallow(), c)
                self.assertEqual(
                    list(chain_abort_one_swallow),
                    [[initial + a.value + c.value] for initial in initials]
                )
                chain_abort_all_swallow = produce(initials) >> a >> (b >> abort_swallow(), c >> abort_swallow())
                self.assertEqual(
                    list(chain_abort_all_swallow),
                    []
                )
                chain_abort_one_return = produce(initials) >> a >> (b >> abort_return(), c)
                self.assertEqual(
                    list(chain_abort_one_return),
                    [[initial + a.value + b.value, initial + a.value + c.value] for initial in initials]
                )
                for every in (2, 3):
                    chain_abort_nth_return = produce(initials) >> a >> (b >> AbortEvery(every), c)
                    self.assertEqual(
                        list(chain_abort_nth_return),
                        [
                            [initial + a.value + b.value, initial + a.value + c.value]
                            if (idx+1) % every else
                            [initial + a.value + c.value]
                            for idx, initial in enumerate(initials)
                        ]
                    )
                    chain_abort_nth_swallow = produce(initials) >> a >> (b >> ReturnEvery(every), c)
                    self.assertEqual(
                        list(chain_abort_nth_swallow),
                        [
                            [initial + a.value + c.value]
                            if (idx) % every else
                            [initial + a.value + b.value, initial + a.value + c.value]
                            for idx, initial in enumerate(initials)
                        ]
                    )
