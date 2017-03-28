from __future__ import absolute_import, division
import unittest
import itertools

from chainlet import utility


class TestSentinel(unittest.TestCase):
    """Sentinel Placeholders"""
    def test_comparison(self):
        """Sentinel compare by identity"""
        sentinels = [utility.Sentinel(str(num)) for num in range(3)]
        for a, b in itertools.product(sentinels, repeat=2):
            if a is b:
                self.assertEqual(a, b)
            else:
                self.assertNotEqual(a, b)

    def test_hashable(self):
        """Sentinels are hashable"""
        sentinels = [utility.Sentinel(str(num)) for num in range(3)]
        container = set(sentinels)
        self.assertEqual(len(container), len(sentinels))
        for sentinel in sentinels:
            self.assertIn(sentinel, container)
        for sentinel in container:
            self.assertEqual(sentinels.count(sentinel), 1)

    def test_pretty(self):
        """Sentinels are pretty printed"""
        sentinels = [utility.Sentinel(str(num)) for num in range(3)]
        for idx, sentinel in enumerate(sentinels):
            self.assertEqual(str(idx), str(sentinel))
        self.assertRegex(str(utility.Sentinel()), r'<.* at 0x.*>')
