import itertools
import unittest
import operator
try:
    _reduce = reduce
except NameError:
    from functools import reduce as _reduce

from chainlet.chainlink import FlatChain, Bundle, NeutralLink

from chainlet_unittests.utility import NamedChainlet


class LinkerGrammar(unittest.TestCase):
    def test_pair(self):
        """Single link as `parent >> child`"""
        chainlet1 = NamedChainlet('1')
        chainlet2 = NamedChainlet('2')
        for parent, child in itertools.product((chainlet1, chainlet2), repeat=2):
            with self.subTest(parent=parent, child=child):
                chain_a = parent >> child
                self.assertSequenceEqual(chain_a.elements, (parent, child))
                chain_a_inv = child << parent
                self.assertSequenceEqual(chain_a.elements, chain_a_inv.elements)

    def test_tripple(self):
        """Chained link as `source >> link >> consumer`"""
        chainlet1 = NamedChainlet('1')
        chainlet2 = NamedChainlet('2')
        chainlet3 = NamedChainlet('3')
        for a, b, c in itertools.product((chainlet1, chainlet2, chainlet3), repeat=3):
            with self.subTest(a=a, b=b, c=c):
                chain_a = a >> b >> c
                self.assertSequenceEqual(chain_a.elements, (a, b, c))
                chain_a_inv = c << b << a
                self.assertSequenceEqual(chain_a.elements, chain_a_inv.elements)
                chain_a_child_sub = a >> b
                chain_a_child_full = chain_a_child_sub >> c
                chain_a_parent_sub = b >> c
                chain_a_parent_full = a >> chain_a_parent_sub
                self.assertSequenceEqual(chain_a.elements, chain_a_child_full.elements)
                self.assertSequenceEqual(chain_a.elements, chain_a_parent_full.elements)
                # do not allow mutating existing chain
                self.assertNotEqual(chain_a_child_sub, chain_a_child_full)
                self.assertNotEqual(chain_a_parent_sub, chain_a_parent_full)

    def test_single(self):
        """Isolated link as `() >> child_a`"""
        chainlets = [NamedChainlet(idx) for idx in range(3)]
        for singlet in chainlets:
            for empty in (FlatChain(()), Bundle(()), NeutralLink(), (), set(), [], set()):
                with self.subTest(singlet=singlet, empty=empty):
                    single_out = singlet >> empty
                    self.assertIs(single_out, singlet)
                    single_in = empty >> singlet
                    self.assertIs(single_in, singlet)

    def test_operator(self):
        """Programmatic link with operator.rshift/operator.lshift"""
        chainlets = [NamedChainlet(idx) for idx in range(10)]
        chain_full = _reduce(operator.rshift, chainlets)
        self.assertSequenceEqual(chain_full.elements, chainlets)
        chain_full_inv = _reduce(operator.lshift, chainlets)
        self.assertSequenceEqual(chain_full_inv.elements, list(reversed(chainlets)))
        link_chain = NeutralLink()
        call_chain = NeutralLink()
        for idx, link in enumerate(chainlets):
            prev_link_chain, prev_call_chain = link_chain, call_chain
            link_chain = link_chain >> link
            call_chain = operator.rshift(call_chain, link)
            self.assertEqual(link_chain, call_chain)
            # do not allow mutating existing chain
            self.assertNotEqual(link_chain, prev_link_chain)
            self.assertNotEqual(call_chain, prev_call_chain)

    def test_empty(self):
        """Empty link as `() >> ()`"""
        for empty_a in (FlatChain(()), Bundle(()), NeutralLink()):
            for empty_b in (FlatChain(()), Bundle(()), NeutralLink(), (), set(), [], set()):
                with self.subTest(empty_a=empty_a, empty_b=empty_b):
                    chain = empty_a >> empty_b
                    self.assertIsInstance(chain, NeutralLink)
                    chain = empty_b >> empty_a
                    self.assertIsInstance(chain, NeutralLink)
                    chain = empty_a >> empty_b >> empty_a >> empty_b
                    self.assertIsInstance(chain, NeutralLink)

    def test_parallel(self):
        """Parallel link as `parent >> (child_a, child_b, ...)` and `(parent_a, parent_b, ...) >> child`"""
        chainlet1 = NamedChainlet('1')
        chainlet2 = NamedChainlet('2')
        chainlet3 = NamedChainlet('3')
        for a, b, c in itertools.product((chainlet1, chainlet2, chainlet3), repeat=3):
            with self.subTest(a=a, b=b, c=c):
                chain_a = a >> (b, c)
                self.assertIs(chain_a.elements[0], a)
                self.assertSequenceEqual(chain_a.elements[1].elements, (b, c))
                chain_a_inv = (b, c) << a
                self.assertSequenceEqual(chain_a.elements, chain_a_inv.elements)
                chain_b = (a, b) >> c
                self.assertIs(chain_b.elements[1], c)
                self.assertSequenceEqual(chain_b.elements[0].elements, (a, b))
                chain_b_inv = c << (a, b)
                self.assertSequenceEqual(chain_b.elements, chain_b_inv.elements)
