import itertools
import unittest

from chainlet_unittests.utility import Adder, produce, abort_return, abort_swallow, AbortEvery, ReturnEvery


class ChainIteration(unittest.TestCase):
    def test_pair(self):
        """Iter single link chain as `parent >> child`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for elements in itertools.product(elements, repeat=2):
            with self.subTest(elements=elements):
                initials = (0, 15, -15, 200, -200, -1E6, +1E6)
                expected = [initial + sum(element.value for element in elements) for initial in initials]
                a, b = elements

                def factory():
                    return produce(initials) >> a >> b
                self._test_iter(factory, expected)

    def _test_iter(self, chain_factory, expected):
        with self.subTest(case='plain'):
            self._test_iter_one(chain_factory, expected)

        with self.subTest(case='abort_return'):
            def factory_return():
                return chain_factory() >> abort_return()
            self._test_iter_one(factory_return, expected)

        with self.subTest(case='abort_swallow'):
            def factory_swallow():
                return chain_factory() >> abort_swallow()
            self._test_iter_one(factory_swallow, [])

        with self.subTest(case='AbortEvery 2'):
            def factory_second():
                return chain_factory() >> AbortEvery(2)
            self._test_iter_one(factory_second, expected[::2])

        with self.subTest(case='AbortEvery 3'):
            def factory_second():
                return chain_factory() >> AbortEvery(3)
            self._test_iter_one(factory_second, [val for idx, val in enumerate(expected) if (idx + 1) % 3])

        with self.subTest(case='ReturnEvery 2'):
            def factory_second():
                return chain_factory() >> ReturnEvery(2)
            self._test_iter_one(factory_second, expected[1::2])

        with self.subTest(case='ReturnEvery 3'):
            def factory_second():
                return chain_factory() >> ReturnEvery(3)
            self._test_iter_one(factory_second, expected[2::3])

    def _test_iter_one(self, chain_factory, expected):
        chain_list = chain_factory()
        self.assertEqual(list(chain_list), expected)
        chain_iter = chain_factory()
        expect_iter = iter(expected)
        for elem in chain_iter:
            self.assertEqual(elem, next(expect_iter))
        chain_enumerate = chain_factory()
        for idx, elem in enumerate(chain_enumerate):
            self.assertEqual(elem, expected[idx])
        chain_next = chain_factory()
        expect_next = iter(expected)
        for _ in range(len(expected)):
            self.assertEqual(next(chain_next), next(expect_next))

    def test_multi(self):
        """Iter multi link chain as `a >> b >> c >> ...`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for elements in itertools.product(elements, repeat=5):
            with self.subTest(elements=elements):
                initials = (0, 15, -15, -1E6, +1E6)
                expected = [initial + sum(element.value for element in elements) for initial in initials]
                a, b, c, d, e = elements

                def factory():
                    return produce(initials) >> a >> b >> c >> d >> e
                self._test_iter(factory, expected)

    def test_fork(self):
        """Push fork link chain as `a >> (b, c)`"""
        elements = [Adder(val) for val in (0, -2, 2, 1E6, -1E6)]
        for a, b, c in itertools.product(elements, repeat=3):
            for initial in (0, 15, -15, -1E6, +1E6):
                with self.subTest(a=a, b=b, c=c, initial=initial):
                    expected = [initial + a.value + b.value, initial + a.value + c.value]
                    chain_a = a >> (b, c)
                    self.assertEqual(chain_a.send(initial), expected)
