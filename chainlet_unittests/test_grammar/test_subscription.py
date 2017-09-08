import itertools
import unittest

from chainlet.dataflow import MergeLink

from chainlet_unittests.utility import Adder


class ChainSubscription(unittest.TestCase):
    def test_pair(self):
        """Subscribe chain[i:j:k] for `a >> b`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for elements in itertools.product(elements, repeat=2):
            with self.subTest(elements=elements):
                a, b = elements

                def factory():
                    return a >> b
                self._assert_subscriptable(factory)

    def test_flatchain(self):
        """Subscribe chain[i:j:k] for `a >> b >> c ...`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for elements in itertools.product(elements, repeat=5):
            with self.subTest(elements=elements):
                a, b, c, d, e = elements

                def factory():
                    return a >> b >> c >> d >> e
                self._assert_subscriptable(factory)

    def test_fork(self):
        """Subscribe chain[i:j:k] for `a >> (b, c) >> d ...`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for elements in itertools.product(elements, repeat=5):
            with self.subTest(elements=elements):
                a, b, c, d, e = elements

                def factory():
                    return a >> (b, c) >> MergeLink() >> d >> e
                self._assert_subscriptable(factory)

    def _assert_subscriptable(self, chain_factory):
        with self.subTest(verify='interface available'):
            chain_instance = chain_factory()
            self.assertIsNotNone(getattr(chain_instance, '__len__', None))
            self.assertIsNotNone(getattr(chain_instance, '__getitem__', None))
        with self.subTest(verify='indexing'):
            chain_instance = chain_factory()
            self.assertEqual(len(chain_instance), len(chain_instance.elements))
            self.assertEqual([chain_instance[idx] for idx in range(len(chain_instance))], list(chain_instance.elements))
        with self.subTest(verify='slicing'):
            chain_instance = chain_factory()
            for start in range(len(chain_instance)):
                for stop in range(start, len(chain_instance)):
                    sub_chain = chain_instance[start:stop]
                    self.assertEqual(sub_chain.elements, chain_instance.elements[start:stop])
        with self.subTest(verify='consistency'):
            chain_instance = chain_factory()
            for index in range(len(chain_instance)):
                self.assertEqual(chain_instance[:index] >> chain_instance[index:], chain_instance)
        with self.subTest(verify='data flow'):
            chain_instance = chain_factory()
            for index in range(len(chain_instance)):
                first_chain, second_chain = chain_instance[:index], chain_instance[index:]
                temp_result = first_chain.send(1)
                self.assertEqual(second_chain.send(temp_result), chain_instance.send(1))
