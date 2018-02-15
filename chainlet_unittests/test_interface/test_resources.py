from __future__ import absolute_import, division
import unittest

import chainlet
from chainlet.primitives import link, neutral, bundle

from chainlet_unittests.utility import Adder


class ClosableLink(link.ChainLink):
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


@chainlet.genlet
def pingpong():
    value = yield
    while True:
        value = yield value


class TestClose(unittest.TestCase):
    """Closing chainlets to release resources"""
    def test_link(self):
        """close basic links without side effects"""
        for link_class in link.ChainLink, neutral.NeutralLink:
            with self.subTest(link=link_class):
                link_instance = link_class()
                link_instance.close()
                link_instance.close()

    def test_chain(self):
        """close chain with children"""
        pure_chain = ClosableLink() >> ClosableLink() >> ClosableLink() >> ClosableLink()
        for linklet in pure_chain.elements:
            self.assertFalse(linklet.closed)
        pure_chain.close()
        for linklet in pure_chain.elements:
            self.assertTrue(linklet.close)
        pure_chain.close()
        for linklet in pure_chain.elements:
            self.assertTrue(linklet.close)

    def test_bundle(self):
        """close bundle with children"""
        pure_bundle = bundle.Bundle((ClosableLink(), ClosableLink(), ClosableLink(), ClosableLink()))
        for linklet in pure_bundle.elements:
            self.assertFalse(linklet.closed)
        pure_bundle.close()
        for linklet in pure_bundle.elements:
            self.assertTrue(linklet.close)
        pure_bundle.close()
        for linklet in pure_bundle.elements:
            self.assertTrue(linklet.close)

    def test_bundle_chain(self):
        """close bested chain and bundle with children"""
        chain_bundle = ClosableLink() >> (ClosableLink(), ClosableLink() >> ClosableLink()) >> ClosableLink()

        def get_elements(test_chain):
            yield test_chain[0]
            yield test_chain[1][0]
            yield test_chain[1][1][0]
            yield test_chain[1][1][1]
            yield test_chain[2]
        for linklet in get_elements(chain_bundle):
            self.assertFalse(linklet.closed)
        chain_bundle.close()
        for linklet in get_elements(chain_bundle):
            self.assertTrue(linklet.close)
        chain_bundle.close()
        for linklet in get_elements(chain_bundle):
            self.assertTrue(linklet.close)

    def test_generator(self):
        generator_chain = Adder(1) >> pingpong() >> Adder(1)
        for val in (-10, 0, 1, 3):
            self.assertEqual(generator_chain.send(val), val + 2)
        generator_chain.close()
        with self.assertRaises(StopIteration):
            generator_chain.send(1)


class TestContext(unittest.TestCase):
    """Context chainlets to manage resources"""
    def test_link(self):
        """with basic links without side effects"""
        for link_class in link.ChainLink, neutral.NeutralLink:
            with self.subTest(link=link_class):
                with link_class() as link_instance:
                    link_instance.close()
                link_instance.close()

    def test_chain(self):
        """with chain with children"""
        with ClosableLink() >> ClosableLink() >> ClosableLink() >> ClosableLink() as pure_chain:
            for linklet in pure_chain.elements:
                self.assertFalse(linklet.closed)
        for linklet in pure_chain.elements:
            self.assertTrue(linklet.close)
        pure_chain.close()
        for linklet in pure_chain.elements:
            self.assertTrue(linklet.close)

    def test_bundle(self):
        """with bundle with children"""
        with bundle.Bundle((ClosableLink(), ClosableLink(), ClosableLink(), ClosableLink())) as pure_bundle:
            for linklet in pure_bundle.elements:
                self.assertFalse(linklet.closed)
        for linklet in pure_bundle.elements:
            self.assertTrue(linklet.close)
        pure_bundle.close()
        for linklet in pure_bundle.elements:
            self.assertTrue(linklet.close)

    def test_bundle_chain(self):
        """with bested chain and bundle with children"""
        def get_elements(test_chain):
            yield test_chain[0]
            yield test_chain[1][0]
            yield test_chain[1][1][0]
            yield test_chain[1][1][1]
            yield test_chain[2]
        with ClosableLink() >> (ClosableLink(), ClosableLink() >> ClosableLink()) >> ClosableLink() as chain_bundle:
            for linklet in get_elements(chain_bundle):
                self.assertFalse(linklet.closed)
        for linklet in get_elements(chain_bundle):
            self.assertTrue(linklet.close)
        chain_bundle.close()
        for linklet in get_elements(chain_bundle):
            self.assertTrue(linklet.close)

    def test_generator(self):
        with Adder(1) >> pingpong() >> Adder(1) as generator_chain:
            for val in (-10, 0, 1, 3):
                self.assertEqual(generator_chain.send(val), val + 2)
        with self.assertRaises(StopIteration):
            generator_chain.send(1)
