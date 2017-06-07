from __future__ import absolute_import, division
import unittest
import random

import chainlet

from chainlet_unittests.utility import NamedChainlet


class FunctionLink(unittest.TestCase):
    def test_linklet(self):
        """Chainlink via decorator"""
        @chainlet.funclet
        def pingpong(value):
            return value

        test_values = [0, 22, -22, 1E6, 'foobar'] + [random.random() for _ in range(20)]
        with self.subTest(case='generator interface'):
            funclet = pingpong()
            for value in test_values:
                self.assertIsNone(next(funclet))
                self.assertEqual(funclet.send(value), value)
                self.assertIsNone(next(funclet))
                self.assertEqual(funclet.send(value), value)
                self.assertEqual(funclet.send(value), funclet.slave(value))  # funclet works like function
        with self.subTest(case='chain element'):
            chain = NamedChainlet('start') >> pingpong() >> NamedChainlet('stop')
            for value in test_values:
                self.assertEqual(chain.send(value), value)
                self.assertIsNone(next(chain))
                self.assertEqual(chain.send(value), value)
        with self.subTest(case='fill chain'):
            chain = NamedChainlet('start') >> pingpong() >> pingpong() >> pingpong() >> pingpong() >> NamedChainlet('stop')
            for value in test_values:
                self.assertEqual(chain.send(value), value)
                self.assertIsNone(next(chain))
                self.assertEqual(chain.send(value), value)
