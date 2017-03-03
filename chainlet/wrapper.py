class WrapperMixin(object):
    r"""
    Mixin for :py:class:`ChainLink`\ s that wrap other objects

    Apply as a mixin via multiple inheritance:

    .. code:: python

        class MyWrap(WrapperMixin, ChainLink):
            def __init__(self, slave):
                super().__init__(slave=slave)

            def send(self, value):
                value = self.__wrapped__.send(value)
                super().send(value)

    Wrappers bind their slave to ``__wrapped__``, as is the Python standard,
    and also expose them via the ``slave`` property for convenience.
    """
    def __init__(self, slave):
        super(WrapperMixin, self).__init__()
        self.__wrapped__ = slave

    @property
    def slave(self):
        return self.__wrapped__
