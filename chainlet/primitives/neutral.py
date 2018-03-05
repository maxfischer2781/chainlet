from .link import ChainLink


class NeutralLink(ChainLink):
    """
    An :term:`chainlink` that acts as a neutral element for linking

    This link does not have any effect on any :term:`data chunk` passed to it.
    It acts as a neutral element for linking, meaning its
    presence or absence in a :term:`chain` does not have any effect.

    This element is useful when an element is syntactically required, but no
    action on data is desired.
    It can be used to force automatic conversion,
    e.g. when linking to a :py:class:`tuple` of elements.

    :note: A :py:class:`~.NeutralLink` *does* have an effect in a :term:`bundle`.
           It creates an additional :term:`branch` which passes on data unchanged.
    """
    __slots__ = ()

    def chainlet_send(self, value=None):
        return value

    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return bool(self) == bool(other)
        return NotImplemented

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return super(NeutralLink, self).__repr__()

ChainLink.chain_types.neutral_link_type = NeutralLink
