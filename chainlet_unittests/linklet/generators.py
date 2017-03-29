import unittest
import random

import chainlet

from chainlet_unittests.utility import NamedChainlet


class GeneratorLink(unittest.TestCase):
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

    def test_close(self):
        """Release underlying generator"""
        @chainlet.genlet
        def pingpong():
            last = yield
            while True:
                last = yield last

        with self.subTest(case='close'):
            genlet = pingpong()
            genlet.close()
            with self.assertRaises(StopIteration):
                next(genlet)
            with self.assertRaises(StopIteration):
                next(genlet.slave)  # underlying resource is closed

        with self.subTest(case='throw'):
            genlet = pingpong()
            with self.assertRaises(GeneratorExit):
                genlet.throw(GeneratorExit)
            with self.assertRaises(StopIteration):
                next(genlet)
            with self.assertRaises(StopIteration):
                next(genlet.slave)  # underlying resource is closed

    def test_linklet(self):
        """Chainlink via decorator"""
        @chainlet.genlet
        def pingpong():
            last = yield
            while True:
                last = yield last

        test_values = [0, 22, -22, 1E6, 'foobar'] + [random.random() for _ in range(20)]
        with self.subTest(case='generator interface'):
            genlet = pingpong()
            for value in test_values:
                self.assertEqual(genlet.send(value), value)
                self.assertIsNone(next(genlet))
                self.assertEqual(genlet.send(value), value)
                self.assertEqual(genlet.send(value), genlet.slave.send(value))  # genlet works like generator
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

    def test_prime_linklet(self):
        """Prime genlet for use"""
        for prime in (True, False):
            with self.subTest(prime=prime):
                @chainlet.genlet(prime)
                def prime_arg():
                    primer = yield
                    yield primer

                @chainlet.genlet(prime=prime)
                def prime_kwarg():
                    primer = yield
                    yield primer

                for genlet in (prime_arg, prime_kwarg):
                    link = genlet()
                    # explicitly prime for use
                    if not prime:
                        self.assertIsNone(next(link))
                    self.assertEqual(link.send('pingpong'), 'pingpong')
                    # make sure generator has ended
                    with self.assertRaises(StopIteration):
                        next(link)
