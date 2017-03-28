from __future__ import absolute_import, division
import unittest

from chainlet import compat


class TestPython2(unittest.TestCase):
    def test_throw(self):
        """compat: throw method"""
        class Throwable(object):
            throw = compat.throw_method

        for err_type in (ValueError, TypeError, SystemExit, KeyError, IndexError, StopIteration):
            with self.assertRaises(err_type):
                Throwable().throw(err_type)
