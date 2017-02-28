import itertools
import unittest

import chainlet

from chainlet_unittests.utility import Adder


class PushChain(unittest.TestCase):
    def test_prime(self):
        """Prime generator for use"""
        def generator():
            primer = yield
            yield primer
        # prime for use
        prime_true = chainlet.GeneratorLink(generator(), prime=True)
        self.assertEqual(prime_true.send('pingpong'), 'pingpong')
        prime_false = chainlet.GeneratorLink(generator(), prime=False)
        self.assertIsNone(next(prime_false))
        self.assertEqual(prime_false.send('pingpong'), 'pingpong')
        # make sure generator has ended
        for name, link in (('prime_true', prime_true), ('prime_false', prime_false)):
            with self.subTest(name=name):
                with self.assertRaises(StopIteration):
                    next(link)
