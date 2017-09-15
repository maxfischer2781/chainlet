import unittest
import random
import copy
try:
    import cPickle as pickle
except ImportError:
    import pickle

import chainlet
import chainlet.genlink

from chainlet_unittests.utility import NamedChainlet


def counter_generator(*args, **kwargs):
    for arg in args:
        yield arg
    for item in sorted(kwargs.items()):
        yield item


def pickle_copy(obj):
    pickle_data = pickle.dumps(obj)
    return pickle.loads(pickle_data)


class TestStashedGenerator(unittest.TestCase):
    @staticmethod
    def _get_test_args():
        return (
            ((), {}),
            ((1,), {}),
            ((), {'a': 1}),
            (list(range(16)), dict(('a%d' % item, item**2) for item in range(16))),
            (
                    [random.random() for _ in range(128)],
                    dict(('a%d' % random.randint(0, 96), random.random()) for _ in range(128))
            ),
        )

    def test_content(self):
        """StashedGenerator: produces same content as generator"""
        for args, kwargs in self._get_test_args():
            with self.subTest(args=args, kwargs=kwargs):
                native_gen = counter_generator(*args, **kwargs)
                stashed_gen = chainlet.genlink.StashedGenerator(counter_generator, *args, **kwargs)
                # iterate via __iter__
                self.assertEqual(list(native_gen), list(stashed_gen))
                # cannot iterate past content
                for this_gen in (native_gen, stashed_gen):
                    with self.assertRaises(StopIteration):
                        next(this_gen)
                # iterate via next
                native_gen = counter_generator(*args, **kwargs)
                stashed_gen = chainlet.genlink.StashedGenerator(counter_generator, *args, **kwargs)
                for _ in range(len(args) + len(kwargs)):
                    self.assertEqual(next(native_gen), next(stashed_gen))
                # iterate via send
                native_gen = counter_generator(*args, **kwargs)
                stashed_gen = chainlet.genlink.StashedGenerator(counter_generator, *args, **kwargs)
                for _ in range(len(args) + len(kwargs)):
                    self.assertEqual(native_gen.send(None), stashed_gen.send(None))

    def test_pickle_copy(self):
        """StashedGenerator: copy, deepcopy and pickle"""
        for args, kwargs in self._get_test_args():
            for copier in (copy.copy, copy.deepcopy, pickle_copy):
                with self.subTest(copier=copier, args=args, kwargs=kwargs):
                    # can copy before iteration
                    stashed_gen = chainlet.genlink.StashedGenerator(counter_generator, *args, **kwargs)
                    copied_gen = copier(stashed_gen)
                    self.assertEqual(list(stashed_gen), list(copied_gen))
                    # fails after iteration
                    with self.assertRaises(TypeError):
                        copier(stashed_gen)


class TestGeneratorLink(unittest.TestCase):
    def test_prime(self):
        """Prime generator for use"""
        def generator():
            primer = yield
            yield primer
        # prime for use
        prime_true = chainlet.genlink.GeneratorLink(generator(), prime=True)
        self.assertEqual(prime_true.send('pingpong'), 'pingpong')
        prime_false = chainlet.genlink.GeneratorLink(generator(), prime=False)
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
