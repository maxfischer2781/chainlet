from __future__ import absolute_import, division
import unittest
import random
try:
    import cPickle as pickle
except ImportError:
    import pickle

import chainlet
import chainlet.funclink

from chainlet_unittests.utility import NamedChainlet


def pingpong(value):
    return value


def new_pingpong():
    return chainlet.funclink.FunctionLink(pingpong)

@chainlet.funclet
def pingponglet(value):
    """Return a value unchanged"""
    return value


class TestFunctionLink(unittest.TestCase):
    @staticmethod
    def _get_test_iterable():
        return [0, 22, -22, 1E6, 'foobar'] + [random.random() for _ in range(20)]

    def test_funclet_generator(self):
        """FunctionLink: generator interface"""
        test_values = self._get_test_iterable()
        for funclet in (pingponglet, new_pingpong):
            funclet_instance = funclet()
            for value in test_values:
                self.assertIsNone(next(funclet_instance))
                self.assertEqual(funclet_instance.send(value), value)
                self.assertIsNone(next(funclet_instance))
                self.assertEqual(funclet_instance.send(value), value)
                self.assertEqual(funclet_instance.send(value), funclet_instance.slave(value))  # function preserved

    def test_funclet_chain(self):
        """FunctionLink: individual funclet in chain"""
        test_values = self._get_test_iterable()
        for funclet in (pingponglet, new_pingpong):
            chain = NamedChainlet('start') >> funclet() >> NamedChainlet('stop')
            for value in test_values:
                self.assertEqual(chain.send(value), value)
                self.assertIsNone(next(chain))
                self.assertEqual(chain.send(value), value)

    def test_long_chain(self):
        """FunctionLink: chain of funclets"""
        test_values = self._get_test_iterable()
        for funclet in (pingponglet, new_pingpong):
            chain = NamedChainlet('start') >> funclet() >> funclet() >> funclet() >> funclet() >> NamedChainlet('stop')
            for value in test_values:
                self.assertEqual(chain.send(value), value)
                self.assertIsNone(next(chain))
                self.assertEqual(chain.send(value), value)
