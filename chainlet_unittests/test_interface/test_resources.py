from __future__ import absolute_import, division
import unittest

from chainlet.primitives import link, neutral, bundle


class ClosableLink(link.ChainLink):
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class TestClose(unittest.TestCase):
    """Closing chainlets to release resources"""
    def test_link(self):
        """close basic links without side effects"""
        for link_class in link.ChainLink, neutral.NeutralLink:
            with self.subTest(link=link_class):
                link_instance = link_class()
                link_instance.close()

    def test_chain(self):
        """close chain with children"""
        pure_chain = ClosableLink() >> ClosableLink() >> ClosableLink() >> ClosableLink()
        for linklet in pure_chain.elements:
            self.assertFalse(linklet.closed)
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
