from __future__ import absolute_import, division
import unittest
import random
import copy
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


@chainlet.funclet
def no_defaults(*args, **kwargs):
    return args, kwargs


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

    def test_pickle_copy(self):
        """FunctionLink: copy, deepcopy and pickle"""
        for case, instance in (
            ('no arguments', no_defaults()),
            ('positional only', no_defaults(1, 2, 'foo', {'c': 3})),
            ('keyword only', no_defaults(one=1, two=2, foo='foo', map={'c': 3})),
            ('mixed arguments', no_defaults(1, 2, foo='foo', map={'c': 3})),
        ):
            with self.subTest(case):
                native = instance
                # slave is preserved
                self.assertEqual(native.slave(), copy.copy(native).slave())
                self.assertEqual(native.slave(), copy.deepcopy(native).slave())
                self.assertEqual(native.slave(), pickle.loads(pickle.dumps(native)).slave())
                # chainlet is preserved
                self._subtest_cloned_result(native, copy.copy(native))
                self._subtest_cloned_result(native, copy.deepcopy(native))
                self._subtest_cloned_result(native, pickle.loads(pickle.dumps(native)))

    def _subtest_cloned_result(self, original, clone):
        # direct access
        self.assertEqual(original.send(), clone.send())
        # chain access
        original_chain = NamedChainlet('start') >> original >> NamedChainlet('stop')
        clone_chain = NamedChainlet('start') >> clone >> NamedChainlet('stop')
        self.assertEqual(original_chain.send(), clone_chain.send())
