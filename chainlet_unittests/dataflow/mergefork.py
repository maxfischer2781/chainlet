import itertools
import unittest

import chainlet

from ..utility import produce


@chainlet.forklet
@chainlet.genlet(prime=False)
def produce_iterables(iterable):
    """Produce iterables from an iterable for a chain"""
    for element in iterable:
        yield element


class ChainMerging(unittest.TestCase):
    def test_merge_numerical(self):
        inputs = [[1, 2, 3], [4, 5, 6], [7.5, 8.5, 9.5]]
        chain = [produce(chunk) for chunk in inputs] >> chainlet.MergeLink()
        self.assertEqual(list(chain), [[sum(row)] for row in zip(*inputs)])
