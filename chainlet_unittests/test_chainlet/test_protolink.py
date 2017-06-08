from __future__ import absolute_import, print_function
import unittest
import random

from chainlet.protolink import iterlet, reverselet, enumeratelet, filterlet, printlet

from chainlet_unittests.utility import Buffer


def odd(value):
    """Test if value is odd"""
    return value % 2 != 0


def even(value):
    """Test if value is even"""
    return value % 2 == 0


class WriteBuffer(list):
    def __init__(self):
        list.__init__(self)
        self._line_buffer = []

    def write(self, value):
        if value == '\n':
            self.append(''.join(self._line_buffer))
            self._line_buffer = []
        else:
            self._line_buffer.append(value)


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
        """Push to enumeration as  `... >> enumeratelet() >> ...`"""
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

    def test_filterlet_pull(self):
        """Pull from iterable as `filterlet(condition, iterable) >> ...`"""
        fixed_iterable = self._get_test_seq()
        for condition in (odd, even):
            self.assertEqual(list(filterlet(condition, fixed_iterable)), list(filter(condition, fixed_iterable)))
            buffer = Buffer()
            chain = filterlet(condition, fixed_iterable) >> buffer
            self.assertEqual(list(chain), list(filter(condition, fixed_iterable)))
            self.assertEqual(buffer.buffer, list(filter(condition, fixed_iterable)))

    def test_filterlet_push(self):
        """Push to filter as `... >> filterlet(condition) >> ...`"""
        fixed_iterable = self._get_test_seq()
        for condition in (odd, even):
            self.assertEqual(
                list(iterlet(fixed_iterable) >> filterlet(condition)), list(filter(condition, fixed_iterable))
            )
            buffer = Buffer()
            chain = iterlet(fixed_iterable) >> filterlet(condition) >> buffer
            self.assertEqual(list(chain), list(filter(condition, fixed_iterable)))
            self.assertEqual(buffer.buffer, list(filter(condition, fixed_iterable)))

    def test_printlet_flat(self):
        """Push to print as  `... >> printlet(flatten=False) >> ..."""
        write_buffer = WriteBuffer()
        chain_buffer = Buffer()
        flat_iterable = ['Hello World', 'This is a drill']
        chain = iterlet(flat_iterable) >> printlet(file=write_buffer) >> chain_buffer
        self.assertEqual(list(chain), flat_iterable)  # no modification by print
        self.assertEqual(chain_buffer.buffer, flat_iterable)
        self.assertEqual(write_buffer, flat_iterable)

    def test_printlet_flatten(self):
        """Push to print as  `... >> printlet(flatten=False) >> ..."""
        write_buffer = WriteBuffer()
        chain_buffer = Buffer()
        flat_iterable = ['Hello World', 'This is a drill']
        nested_iterable = [elem.split() for elem in flat_iterable]
        chain = iterlet(nested_iterable) >> printlet(file=write_buffer, flatten=True) >> chain_buffer
        self.assertEqual(list(chain), nested_iterable)  # no modification by print
        self.assertEqual(chain_buffer.buffer, nested_iterable)
        self.assertEqual(write_buffer, flat_iterable)
