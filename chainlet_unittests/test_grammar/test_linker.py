import itertools
import unittest

from chainlet.chainlink import LinearChain, ParallelChain

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
        """Empty link as () >> child_a"""
        chainlets = [NamedChainlet(idx) for idx in range(3)]
        for singlet in chainlets:
            for empty in (LinearChain(()), ParallelChain(()), (), set(), [], set()):
                with self.subTest(singlet=singlet, empty=empty):
                    single_out = singlet >> empty
                    self.assertIs(single_out, singlet)
                    single_in = empty >> singlet
                    self.assertIs(single_in, singlet)

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

    def test_parallel_type(self):
        """Parallel links preserving sequence type"""
        chainlet1 = NamedChainlet('1')
        chainlet2 = NamedChainlet('2')
        chainlet3 = NamedChainlet('3')
        for a, b, c in itertools.product((chainlet1, chainlet2, chainlet3), repeat=3):
            for pack_type in (list, tuple, set):
                with self.subTest(a=a, b=b, c=c, pack_type=pack_type):
                    chain_a = a >> pack_type((b, c))
                    self.assertSequenceEqual(chain_a.elements[1].elements, pack_type((b, c)))
                    self.assertIsInstance(chain_a.elements[1].elements, pack_type)
                    chain_b = pack_type((a, b)) >> c
                    self.assertSequenceEqual(chain_b.elements[0].elements, pack_type((a, b)))
                    self.assertIsInstance(chain_b.elements[0].elements, pack_type)
