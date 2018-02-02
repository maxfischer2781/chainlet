from __future__ import absolute_import, division
import unittest
import random
import copy
import functools
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


def pickle_copy(obj, proto):
    dump = pickle.dumps(obj, proto)
    return pickle.loads(dump)


@chainlet.funclet
def abcdefg(value, a=0, b=1, c=2, d=3, e=4, f=5, g=6):
    return value, a, b, c, d, e, f, g


try:  # py2 unbound method
    ABCDEFG = functools.partial(chainlet.funclink.FunctionLink, abcdefg.__wrapped__.__func__)
except AttributeError:
    ABCDEFG = functools.partial(chainlet.funclink.FunctionLink, abcdefg.__wrapped__)


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

    def test_arguments(self):
        """FunctionLink: arguments as .. >> funclink(*args, **kwargs) >> ..."""
        for description, linklet in (('FunctionLink', ABCDEFG), ('wrapper', abcdefg)):
            with self.subTest(target=description):
                argument_count = 7
                # default arguments
                default_chain = NamedChainlet('start') >> linklet() >> NamedChainlet('stop')
                for value in self._get_test_iterable():
                    result = list(default_chain.send(value))
                    self.assertEqual(result[0], value)
                    self.assertEqual(result[1:], list(range(argument_count)))
                # positional arguments
                for length in range(0, argument_count, 2):
                    positional_chain = NamedChainlet('start') >> linklet(*range(length, 0, -1)) >> NamedChainlet('stop')
                    for value in self._get_test_iterable():
                        result = list(positional_chain.send(value))
                        expect = list(range(length, 0, -1)) + list(range(length, argument_count))
                        self.assertEqual(result[0], value)
                        self.assertEqual(result[1:], expect)
                # keyword arguments
                for length in range(0, argument_count, 2):
                    kwargs = dict((chr(97 + idx), -idx) for idx in range(length))
                    positional_chain = NamedChainlet('start') >> linklet(**kwargs) >> NamedChainlet('stop')
                    for value in self._get_test_iterable():
                        result = list(positional_chain.send(value))
                        expect = list(range(0, -length, -1)) + list(range(length, argument_count))
                        self.assertEqual(result[0], value)
                        self.assertEqual(result[1:], expect)

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
                # chainlet is preserved
                self._subtest_cloned_result(native, copy.copy(native))
                self._subtest_cloned_result(native, copy.deepcopy(native))
            for proto in range(pickle.HIGHEST_PROTOCOL):
                with self.subTest(case, pickle_protocol=proto):
                    self.assertEqual(native.slave(), pickle_copy(native, proto).slave())
                    self._subtest_cloned_result(native, pickle_copy(native, proto))

    def _subtest_cloned_result(self, original, clone):
        self.assertIsNot(original, clone)
        # direct access
        self.assertEqual(original.send(), clone.send())
        # chain access
        original_chain = NamedChainlet('start') >> original >> NamedChainlet('stop')
        clone_chain = NamedChainlet('start') >> clone >> NamedChainlet('stop')
        self.assertEqual(original_chain.send(), clone_chain.send())
