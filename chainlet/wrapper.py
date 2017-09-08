from __future__ import absolute_import
import sys


def getname(obj):
    """
    Return the most qualified name of an object

    :param obj: object to fetch name
    :return: name of ``obj``
    """
    for name_attribute in ('__qualname__', '__name__'):
        try:
            # an object always has a class, as per Python data model
            return getattr(obj, name_attribute, getattr(obj.__class__, name_attribute))
        except AttributeError:
            pass
    raise TypeError('object of type %r does not define a canonical name' % type(obj))


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
        # inherit settings from slave
        for attr in ('chain_join', 'chain_fork'):
            try:
                setattr(self, attr, getattr(slave, attr))
            except AttributeError:
                pass

    @property
    def slave(self):
        return self.__wrapped__

    def __repr__(self):
        return '<%s wrapper %s.%s at %x>' % (
            self.__class__.__name__, self.__wrapped__.__module__,
            getname(self.__wrapped__),
            id(self)
        )

    def __init_slave__(self, raw_slave, *slave_args, **slave_kwargs):
        raise NotImplementedError

    @classmethod
    def wraplet(cls, *cls_args, **cls_kwargs):
        def wrapper_factory(raw_slave):
            """Factory to create a new class by wrapping ``raw_slave``"""
            class Wraplet(cls):  # pylint:disable=abstract-method
                _raw_slave = staticmethod(raw_slave)
                # Assign the wrapped attributes directly instead of
                # using functools.wraps, as we may deal with arbitrarry
                # class/callable combinations.
                __doc__ = raw_slave.__doc__
                # While the wrapped instance wraps the slave, the
                # wrapper class wraps the slave factory. Any instance
                # then just hides the class level attribute.
                # Exposing __wrapped__ here allows introspection,such
                # as inspect.signature, to pick up metadata.
                __wrapped__ = raw_slave
                # In Py3.X, objects without any annotations just provide an
                # empty dict.
                __annotations__ = getattr(raw_slave, '__annotations__', {})

                def __init__(self, *slave_args, **slave_kwargs):
                    slave = self.__init_slave__(self._raw_slave, *slave_args, **slave_kwargs)
                    super(Wraplet, self).__init__(slave, *cls_args, **cls_kwargs)

                def __repr__(self):
                    return '<%s wrapper %s.%s at %x>' % (
                        self.__class__.__name__, self.__module__,
                        self.__class__.__qualname__,
                        id(self)
                    )

            # swap places with our target so that both can be pickled/unpickled
            Wraplet.__name__ = getname(raw_slave).split('.')[-1]
            Wraplet.__qualname__ = getname(raw_slave)
            Wraplet.__module__ = raw_slave.__module__
            # this is enough for Py3.4+ to find the slave
            raw_slave.__qualname__ = Wraplet.__qualname__ + '._raw_slave'
            # ## This is an EVIL hack! Do not use use this at home unless you understand it! ##
            # enable python2 lookup of the slave via its wrapper
            # This allows to implicitly pickle slave objects which already support pickle,
            # e.g. function and partial.
            # python2 pickle performs the equivalent of getattr(sys.modules[obj.__module__, obj.__name__]
            # which does not allow dotted name lookups. To work around this, we place the slave into the
            # module, globally, using the qualified name *explicitly*. As qualified names are not valid identifiers,
            # this will not create a collision unless someone tries to do the same trick.
            if sys.version_info[:2] <= (3, 4):
                # While 3.4 adds support for using __qualname__, that is *only* for protocol 4. Older
                # protocols still require __name__. However, 3.4 *explicitly* disallows using dotted names,
                # which defeats the obvious way of injecting the proper dotted name. Instead, an illegal name
                # using : in place of . is used, which should also not conflict.
                name_separator = '.' if sys.version_info[:2] != (3, 4) else ':'
                # Make sure we actually register the correct entity
                # Since we are only working with __name__, the slave could be defined
                # in an inner scope. In this case, registering it in the global namespace
                # may increase its lifetime, or replace an actual global slave of the
                # same name.
                # There are two cases we have to check here:
                # slave = wraplet(slave)
                #   The slave already exists in the module namespace, with its __name__.
                #   The object with that name must be *identical* to the slave.
                # @wraplet\ndef slave
                #   Neither slave nor Wrapper exist in the namespace yet (they are only bound *after*
                #   the wraplet returns). No object may exist with the same name.
                if getattr(sys.modules[raw_slave.__module__], raw_slave.__name__, raw_slave) is raw_slave:
                    raw_slave.__name__ += name_separator + '_raw_slave'
                    setattr(sys.modules[raw_slave.__module__], raw_slave.__name__, raw_slave)
            return Wraplet
        return wrapper_factory
