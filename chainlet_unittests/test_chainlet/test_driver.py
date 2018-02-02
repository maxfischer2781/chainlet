from __future__ import absolute_import, division
import unittest
import itertools
import random
import time

import chainlet.driver

from chainlet_unittests.utility import Adder, Buffer, MultiprocessBuffer, produce


class DriverMixin(object):
    driver_class = chainlet.driver.ChainDriver
    buffer_class = Buffer

    def test_drive_single(self):
        """Drive a single chain"""
        driver = self.driver_class()
        elements = [Adder(val) for val in (2, -2, 1E6, random.randint(-256, 256))]
        for run_async in (False, True):
            results = []
            self.assertFalse(driver.mounts)
            with self.subTest(run_async=run_async):
                for elements in itertools.product(elements, repeat=3):
                    initials = [0, 2, 1E6, -1232527]
                    expected = [initial + sum(element.value for element in elements) for initial in initials]
                    a, b, c = elements
                    buffer = self.buffer_class()
                    chain = produce(initials) >> a >> b >> c >> buffer
                    driver.mount(chain)
                    results.append([expected, buffer])
                if run_async:
                    driver.start()
                    driver.start()  # starting multiple times is allowed
                    time.sleep(0.05)  # let the driver startup
                    while driver.running:
                        time.sleep(0.05)
                else:
                    driver.run()
                for expected, buffer in results:
                    self.assertEqual(expected, buffer.buffer)


class TestChainDriver(DriverMixin, unittest.TestCase):
    driver_class = chainlet.driver.ChainDriver


class TestThreadedChainDriver(DriverMixin, unittest.TestCase):
    driver_class = chainlet.driver.ThreadedChainDriver


class TestMultiprocessChainDriver(DriverMixin, unittest.TestCase):
    driver_class = chainlet.driver.MultiprocessChainDriver
    buffer_class = MultiprocessBuffer
