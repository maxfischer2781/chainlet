import itertools
import unittest

import chainlet.dataflow

from ..utility import produce


try:
    zip_longest = itertools.zip_longest
except AttributeError:
    zip_longest = itertools.izip_longest


@chainlet.forklet
@chainlet.genlet(prime=False)
def produce_iterables(iterable):
    """Produce iterables from an iterable for a chain"""
    for element in iterable:
        yield element


class ChainMerging(unittest.TestCase):
    def test_merge_unknown(self):
        """Merge unknown types from multiple elements"""
        class Numerical(object):
            def __init__(self, value):
                self.value = value

            def __add__(self, other):
                return self.value + other

            def __radd__(self, other):
                return self.value + other
        inputs = [[1, 2, 3], [4, 5, 6], [7.5, 8.5, 9.5]]
        inputs = [[Numerical(val) for val in chunk] for chunk in inputs]
        chain = [produce(chunk) for chunk in inputs] >> chainlet.MergeLink()
        with self.assertRaises(ValueError):
            list(chain)
        chain = [produce(chunk) for chunk in inputs] >> chainlet.MergeLink((Numerical, chainlet.dataflow.merge_numerical))
        self.assertEqual(list(chain), [[sum(row)] for row in zip(*inputs)])

    def test_merge_numerical(self):
        """Merge numbers from multiple elements"""
        inputs = [[1, 2, 3], [4, 5, 6], [7.5, 8.5, 9.5]]
        chain = [produce(chunk) for chunk in inputs] >> chainlet.MergeLink()
        self.assertEqual(list(chain), [[sum(row)] for row in zip(*inputs)])

    def test_merge_list(self):
        """Merge lists from multiple elements"""
        inputs = [[[1], [2], [3]], [[4], [5], [6]], [[7.5], [8.5], [9.5]]]
        chain = [produce(chunk) for chunk in inputs] >> chainlet.MergeLink()
        self.assertEqual(list(chain), [[sum(row, [])] for row in zip(*inputs)])

    def test_merge_dict(self):
        """Merge dicts from multiple elements"""
        inputs = [
            [{idx: str(idx)} for idx in range(3)],
            [{idx: str(idx)} for idx in range(3, 6)],
            [{idx: str(idx)} for idx in range(3)]
        ]
        chain = [produce(chunk) for chunk in inputs] >> chainlet.MergeLink()
        self.assertEqual(list(chain), [[{idx: str(idx), idx+3: str(idx+3)}] for idx in range(3)])

    def test_merge_unbalanced(self):
        """Merge from multiple elements with empty ones"""
        for inputs in ([[1, 2, 3], [4, 5, 6], [7.5, 8.5, 9.5], []], [[1, 2, 3], [], []], [[], [], []]):
            with self.subTest(inputs=inputs):
                chain = [produce(chunk) for chunk in inputs] >> chainlet.MergeLink()
                self.assertEqual(
                    list(chain),
                    [[sum(elem for elem in row if elem is not None)] for row in zip_longest(*inputs)]
                )
