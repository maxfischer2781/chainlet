from .link import ChainLink


class CompoundLink(ChainLink):
    """
    Baseclass for compound chainlets consisting of other chainlets

    :param elements: the chainlets making up this chain
    :type elements: iterable[:py:class:`ChainLink`]

    These compound elements expose the regular interface of chainlets.
    They can again be chained or stacked to form more complex chainlets.

    Any :py:class:`CompoundLink` based on :term:`sequential <sequence>` or :term:`mapped <mapping>`
    elements allows for subscription:

    .. describe:: len(link)

       Return the number of elements in the link.

    .. describe:: link[i]

       Return the ``i``'th :term:`chainlink` of the link.

    .. describe:: link[i:j:k]

       Return a *new* link consisting of the elements defined by the :term:`slice` ``[i:j:k]``.
       This follows the same semantics as subscription of regular :term:`sequences <sequence>`.

    .. describe:: bool(link)

        Whether the link contains any elements.
    """
    __slots__ = ('elements',)

    def __init__(self, elements):
        self.elements = tuple(elements)
        super(CompoundLink, self).__init__()

    def __len__(self):
        return len(self.elements)

    def __bool__(self):
        return bool(self.elements)

    __nonzero__ = __bool__

    def __getitem__(self, item):
        if item.__class__ == slice:
            return self.__class__(self.elements[item])
        return self.elements[item]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.elements == other.elements
        return NotImplemented

    def __hash__(self):
        return hash(self.elements)

    def chainlet_send(self, value=None):
        raise NotImplementedError

    def close(self):
        for element in self.elements:
            element.close()
