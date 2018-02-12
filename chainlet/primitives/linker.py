class LinkPrimitives(object):
    """
    Primitives used in a linker domain

    :warning: This is an internal, WIP helper.
              Names, APIs and signatures are subject to change.
    """
    #: callables to convert elements; must return a ChainLink or raise TypeError
    _converters = []
    _instance = None
    #: the basic :term:`chainlink` type from which all primitives of this domain derive
    base_link_type = None  # type: Type[ChainLink]
    #: a neutral link that does not change a chain
    neutral_link_type = None  # type: Type[NeutralLink]
    #: the basic :term:`chain` type holding sequences of :term:`chainlinks <chainlink>`
    base_chain_type = None  # type: Type[Chain]
    #: the flat :term:`chain` type holding sequences of simple :term:`chainlinks <chainlink>`
    flat_chain_type = None  # type: Type[FlatChain]
    #: the basic :term:`bundle` type holding groups of concurrent :term:`chainlinks <chainlink>`
    base_bundle_type = None  # type: Type[Bundle]

    def __new__(cls):
        if not cls.__dict__.get('_instance'):
            cls._instance = object.__new__(cls)
            cls._converters = []
        return cls._instance

    def link(self, parent, child):
        chain = self.base_chain_type((parent, child))
        # avoid arbitrary type for empty links
        if not chain:
            return self.neutral_link_type()
        # avoid useless nesting
        elif len(chain) == 1:
            return chain[0]
        else:
            return chain

    def convert(self, element):
        """Convert an element to a chainlink"""
        if isinstance(element, self.base_link_type):
            return element
        for converter in self.converters:
            link = converter(element)
            if link is not NotImplemented:
                return link
        raise TypeError('%r cannot be converted to a chainlink' % element)

    def supersedes(self, other):
        return isinstance(self, type(other)) and type(other) != type(self)

    @property
    def converters(self):
        for cls in self.__class__.mro():
            try:
                for converter in cls._converters:
                    yield converter
            except AttributeError:
                pass

    @classmethod
    def add_converter(cls, converter):
        """
        Add a converter to this Converter type and all its children

        Each converter is a callable with the signature

        .. py:function:: converter(element: object) -> :py:class:`ChainLink`

        and must create a :py:class:`ChainLink` for any valid ``element`` input.
        For any ``element`` that is not valid input, :py:const:`NotImplemented` must be returned.
        """
        cls._converters.append(converter)
