import chainlet


class NamedChainlet(chainlet.ChainLink):
    """Chainlet with nice representation"""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '%s' % self.name
