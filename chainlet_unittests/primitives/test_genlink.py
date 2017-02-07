import unittest

from chainlet.genlink import GeneratorLink

from .._utility import Consumer


class TestGeneratorLink(unittest.TestCase):
    def test_init(self):
        """Wrapping and priming"""
        def generator():
            primed = (yield) is None or 1
            yield primed
        primed = GeneratorLink(generator(), prime=True)
        self.assertEqual(next(primed), 1)  # explicitly primed
        unprimed = GeneratorLink(generator(), prime=False)
        self.assertIsNone(next(unprimed))  # must be primed manually
        self.assertEqual(next(unprimed), 1)  # manually primed
        default_primed = GeneratorLink(generator())
        self.assertEqual(next(default_primed), 1)  # implicitly primed
        for name, link in (('primed', primed), ('unprimed', unprimed), ('default_primed', default_primed)):
            with self.subTest(subject=name):
                with self.assertRaises(StopIteration):
                    next(link)

    def test_linklet(self):
        """Wrapping by decorator"""
        @GeneratorLink.linklet
        def producer(param=1):
            while True:
                yield param

        @GeneratorLink.linklet
        def pingpong(param=1):
            last = yield
            while True:
                last = yield (last * param)

        tests = [((), {})]
        tests.extend(((param,), {}) for param in (0, 1000, -20, -1E16))
        tests.extend(((), {'param': param}) for param in (0, 1000, -20, -1E16))
        for args, kwargs in tests:
            param = kwargs.get('param', 1 if not args else args[0])
            with self.subTest(param=param, args=args, kwargs=kwargs):
                linklet1, consumer1 = producer(*args, **kwargs), Consumer()
                linklet1 >> consumer1
                self.assertIsInstance(linklet1, GeneratorLink)
                for _ in range(10):
                    self.assertEqual(next(consumer1), param)  # linear link works as producer generator
                self.assertEqual(consumer1.next_buffer, [param for _ in range(10)])
                linklet2, consumer2 = pingpong(*args, **kwargs), Consumer()
                linklet2 >> consumer2
                for count in range(10):
                    self.assertEqual(linklet2.send(count), count * param)  # send in value, ignore yield of param
                self.assertEqual(consumer2.send_buffer, [count * param for count in range(10)])
