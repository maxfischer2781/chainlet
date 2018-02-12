from __future__ import division, absolute_import, print_function

from chainlet.primitives.link import ChainLink
from chainlet.primitives.bundle import Bundle
from chainlet.primitives.chain import FlatChain, Chain
from chainlet.primitives.linker import LinkPrimitives

__all__ = ['ChainLink']


def bundle_sequences(element):
    if isinstance(element, (tuple, list, set)):
        return Bundle(element)
    return NotImplemented

LinkPrimitives.add_converter(bundle_sequences)
LinkPrimitives.base_link_type = ChainLink
LinkPrimitives.base_chain_type = Chain
LinkPrimitives.flat_chain_type = FlatChain
LinkPrimitives.base_bundle_type = Bundle
