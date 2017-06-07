from __future__ import absolute_import
import itertools
import unittest
import random

from chainlet.protolink import iterlet, reverselet, enumeratelet

from chainlet_unittests.utility import Buffer


class Protolinks(unittest.TestCase):
    @staticmethod
    def _get_test_seq():
        return [0, 1, 2, 3, 4] + [random.random() for _ in range(20)] + [5, 6, 7, 8, 9]

    def test_iterlet_pull(self):
        """Pull from iterable as `iterlet(iterable) >> ...`"""
        fixed_iterable = self._get_test_seq()
        self.assertEqual(list(iterlet(fixed_iterable)), list(iter(fixed_iterable)))
        buffer = Buffer()
        chain = iterlet(fixed_iterable) >> buffer
        self.assertEqual(list(chain), fixed_iterable)
        self.assertEqual(buffer.buffer, fixed_iterable)

    def test_reverselet_pull(self):
        """Pull from iterable in reverse as `reverselet(iterable) >> ...`"""
        fixed_iterable = self._get_test_seq()
        self.assertEqual(list(reverselet(fixed_iterable)), list(reversed(fixed_iterable)))
        buffer = Buffer()
        chain = reverselet(fixed_iterable) >> buffer
        self.assertEqual(list(chain), list(reversed(fixed_iterable)))
        self.assertEqual(buffer.buffer, list(reversed(fixed_iterable)))

    def test_enumeratelet_pull(self):
        """Pull from iterable as `enumeratelet(iterable) >> ...`"""
        fixed_iterable = self._get_test_seq()
        self.assertEqual(list(enumeratelet(fixed_iterable)), list(enumerate(fixed_iterable)))
        buffer = Buffer()
        chain = enumeratelet(fixed_iterable) >> buffer
        self.assertEqual(list(chain), list(enumerate(fixed_iterable)))
        self.assertEqual(buffer.buffer, list(enumerate(fixed_iterable)))

    def test_enumeratelet_push(self):
        """Push to enumeration as  `>> enumeratelet() >> ...`"""
        fixed_iterable = self._get_test_seq()
        for start_val in [0, 2, 500] + [random.randint(-10, 10) for _ in range(5)]:
            for args, kwargs in (((), {}), ((), {'start': start_val}), ((start_val,), {})):
                with self.subTest(args=args, kwargs=kwargs):
                    try:
                        first_index = args[0]
                    except IndexError:
                        first_index = kwargs.get('start', 0)
                    self.assertEqual(
                        list(iterlet(fixed_iterable) >> enumeratelet(*args, **kwargs)),
                        list(enumerate(fixed_iterable, *args, **kwargs))
                    )
                    buffer = Buffer()
                    chain = iterlet(fixed_iterable) >> enumeratelet(*args, **kwargs) >> buffer
                    self.assertEqual(list(chain), list(enumerate(fixed_iterable, *args, **kwargs)))
                    self.assertEqual(buffer.buffer, list(enumerate(fixed_iterable, *args, **kwargs)))
                    self.assertEqual(buffer.buffer[0][0], first_index)
        with self.assertRaises(TypeError):
            enumeratelet(1, 1)
        with self.assertRaises(TypeError):
            enumeratelet(None, 1.0)
        with self.assertRaises(TypeError):
            enumeratelet(1.0)
