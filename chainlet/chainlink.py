from __future__ import division, absolute_import
import sys
import functools


class ChainLink(object):
    """
    BaseClass for elements in a chain

    A chain is created by binding :py:class:`ChainLink`s together. This is
    a directional process: a binding is always made between parent and child.
    Each child can be the parent to another child, and vice versa.

    The direction dictates how data is passed along the chain:

    * A parent may :py:meth:`send` a data chunk to a child.
    * A child may pull the :py:func:`next` data chunk from the parent.

    Chaining is either done by explicitly calling :py:meth:`bind_parents` and
    :py:meth:`bind_children`, or the shorter operator syntax as
    ``parent >> child`` and `child << parent`.

    The number of children and parents per link is arbitrary: the chain may
    fork, join and even loop. Whether any of this is a sensible relation
    depends on the implementation of each link.

    Multiple bindings are created by passing multiple links when binding,
    and/or binding a link multiple times.

    .. describe:: parent >> child
                  child << parent

       Bind ``child`` and ``parent``. Both directions of the statement are
       equivalent: if ``a`` is made a child of ``b``, then `b`` is made a
       parent of ``a``, and vice versa.

    .. describe:: parent >> (child_a, child_b, ...)

       Bind ``child_a``, ``child_a``, etc. as individual children of ``parent``.

    .. describe:: (parent_a, parent_b, ...) >> child

       Bind ``parent_a``, ``parent_b``, etc. as individual parents of ``child``.

    :note: When binding multiple elements via ``>>`` and ``<<``, elements *must*
           be in a :py:class:`tuple`. Contrast ``parent >> child_a, child_b``
           which only binds ``child_a``, and ``parent >> [child_a, child_b]``
           which attempts and fails to bind a list *containing* children.

    Aside from binding, every :py:class:`ChainLink` should implement the
    `Generator-Iterator Methods`_ interface as applicable:

    .. method:: link.__next__()

       Pull the next data ``chunk`` from the link. Raise :py:exc:`StopIteration`
       if there are no more chunks. Implicitly used in ``next(link)`` and in
       ``for chunk in link``.

    .. method:: link.send(chunk)

       Send a data ``chunk`` into the link. Return the result based on this data,
       if any.

    .. method:: link.throw(type[, value[, traceback]])

       Raises an exception of ``type`` inside the link. The link may either
       return a final result, raise :py:exc:`StopIteration` if there are no
       more results, or propagate any other, unhandled exception.

    .. method:: link.close()

       Close the link.

    Note that the default implementation of these methods in :py:class:`ChainLink`
    attempts to satisfy the interface with a minimum of assumptions. Most
    importantly, the type, format and nesting of return values is up to
    implementations.

    In specific, :py:meth:`__next__` raises :py:exc:`StopIteration`
    unconditionally. In contrast, :py:meth:`send`, :py:meth:`throw` and
    :py:meth:`close` always return :py:const:`None`; additionally, these
    methods pass on any input to any bound children.

    Subclasses are encouraged to use the :py:func:`super` methods for
    :py:meth:`send`, :py:meth:`throw` and :py:meth:`close`.

    .. _Generator-Iterator Methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
    """
    def __init__(self):
        self._parents = []
        self._children = []

    def bind_parents(self, *parents, **kwargs):
        _rebound = kwargs.pop('_rebound', False)
        self._parents.extend(parents)
        if not _rebound:
            for parent in parents:
                parent.bind_parent(self, _rebound=True)

    def bind_children(self, *children, **kwargs):
        _rebound = kwargs.pop('_rebound', False)
        self._children.extend(children)
        if not _rebound:
            for child in children:
                child.bind_parents(self, _rebound=True)

    def __rshift__(self, children):
        if isinstance(children, tuple):
            self.bind_children(*children)
        else:
            self.bind_children(children)
        return children

    def __lshift__(self, parents):
        if isinstance(parents, tuple):
            self.bind_children(*parents)
        else:
            self.bind_children(parents)
        return parents

    def __iter__(self):
        return self

    def __next__(self):
        return self._next_of_parents()

    def _next_of_parents(self):
        if len(self._parents) == 1:
            return next(self._parents[0])
        raise StopIteration('Not Iterable')

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):
        """Send a value to this element"""
        all_retvals = self._send_to_children(value)
        if len(self._children) == 1:
            return all_retvals[0]

    def _send_to_children(self, value=None):
        return [child.send(value) for child in self._children]

    def throw(self, type, value=None, traceback=None):
        for child in self._children:
            child.throw(type, value, traceback)

    def close(self):
        for child in self._children:
            child.close()
        self._children = type(self._children)()


class WrapperMixin(object):
    """
    Mixin for :py:class:`ChainLink`s that wrap other objects

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

    @classmethod
    def linklet(cls, target):
        """
        Convert any callable constructor to a chain link constructor
        """
        def linker(*args, **kwargs):
            """
            Creates a new instance of a chain link

            :rtype: ChainLink
            """
            return cls(target(*args, **kwargs))
        functools.update_wrapper(linker, target)
        return linker
