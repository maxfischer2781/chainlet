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

        class SimpleWrapper(WrapperMixin, ChainLink):
            /"/"/"Chainlink that calls ``slave`` for each chunk/"/"/"
            def __init__(self, slave):
                super().__init__(slave=slave)

            def chainlet_send(self, value):
                value = self.__wrapped__.send(value)

    Wrappers bind their slave to ``__wrapped__``, as is the Python standard,
    and also expose them via the ``slave`` property for convenience.

    Additionally, subclasses provide the :py:meth:`~.wraplet` to create factories of wrappers.
    This requires :py:meth:`~.__init_slave__` to be defined.
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

    # wraplet specific special methods
    # repr for wraplet instances
    def __wraplet_repr__(self):  # pragma: no cover
        return '<%s.%s wraplet at %x>' % (
            self.__module__,
            self.__class__.__qualname__,
            id(self)
        )

    def __init_slave__(self, slave_factory, *slave_args, **slave_kwargs):
        """Create a slave from ``slave_factory``"""
        raise NotImplementedError

    @classmethod
    def wraplet(cls, *cls_args, **cls_kwargs):
        """
        Create a factory to produce a Wrapper from a slave factory

        :param cls_args: positional arguments to provide to the Wrapper class
        :param cls_kwargs: keyword arguments to provide to the Wrapper class
        :return:

        .. code:: python

            cls_wrapper_factory = cls.wraplet(*cls_args, **cls_kwargs)
            link_factory = cls_wrapper_factory(slave_factory)
            slave_link = link_factory(*slave_args, **slave_kwargs)
        """
        if cls.__init_slave__ in (None, WrapperMixin.__init_slave__):
            raise TypeError('type %r does not implement the wraplet protocol' % getname(cls))

        def wrapper_factory(slave_factory):
            """Factory to create a new class by wrapping ``slave_factory``"""
            class Wraplet(cls):  # pylint:disable=abstract-method
                _slave_factory = staticmethod(slave_factory)
                # Assign the wrapped attributes directly instead of
                # using functools.wraps, as we may deal with arbitrarry
                # class/callable combinations.
                __doc__ = slave_factory.__doc__
                # While the wrapped instance wraps the slave, the
                # wrapper class wraps the slave factory. Any instance
                # then just hides the class level attribute.
                # Exposing __wrapped__ here allows introspection,such
                # as inspect.signature, to pick up metadata.
                __wrapped__ = slave_factory
                # In Py3.X, objects without any annotations just provide an
                # empty dict.
                __annotations__ = getattr(slave_factory, '__annotations__', {})

                def __init__(self, *slave_args, **slave_kwargs):
                    slave = self.__init_slave__(self._slave_factory, *slave_args, **slave_kwargs)
                    super(Wraplet, self).__init__(slave, *cls_args, **cls_kwargs)

                __repr__ = cls.__wraplet_repr__

            # swap places with our target so that both can be pickled/unpickled
            Wraplet.__name__ = getname(slave_factory).split('.')[-1]
            Wraplet.__qualname__ = getname(slave_factory)
            Wraplet.__module__ = slave_factory.__module__
            # this is enough for Py3.4+ to find the slave
            slave_factory.__qualname__ = Wraplet.__qualname__ + '._slave_factory'
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
                if getattr(sys.modules[slave_factory.__module__], slave_factory.__name__, slave_factory) is slave_factory:
                    slave_factory.__name__ += name_separator + '_slave_factory'
                    setattr(sys.modules[slave_factory.__module__], slave_factory.__name__, slave_factory)
            return Wraplet
        return wrapper_factory
