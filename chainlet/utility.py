class Sentinel(object):
    """Unique placeholders for signals"""
    def __init__(self, name=None):
        self.name = name

    def __eq__(self, other):
        return other is self

    def __hash__(self):
        return id(self)

    def __str__(self):
        if self.name is not None:
            return str(self.name)
        return repr(self)

    def __repr__(self):
        if self.name is not None:
            return '<%s %r at 0x%x>' % (self.__class__.__name__, self.name, id(self))
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))
