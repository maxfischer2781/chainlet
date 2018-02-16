import sys

from .. import signals
from ..chainsend import lazy_send
from ..compat import throw_method as _throw_method
from ..primitives.linker import LinkPrimitives


class ChainLink(object):
    r"""
    BaseClass for elements in a chain

    A chain is created by binding :py:class:`ChainLink`\ s together. This is
    a directional process: a binding is always made between parent and child.
    Each child can be the parent to another child, and vice versa.

    The direction dictates how data is passed along the chain:

    * A parent may :py:meth:`send` a data chunk to a child.
    * A child may pull the :py:func:`next` data chunk from the parent.

    Chaining is done with ``>>`` and ``<<`` operators as
    ``parent >> child`` and ``child << parent``. Forking and joining of chains
    requires a sequence of multiple elements as parent or child.

    .. describe:: parent >> child
                  child << parent

       Bind ``child`` and ``parent``. Both directions of the statement are
       equivalent: if ``a`` is made a child of ``b``, then `b`` is made a
       parent of ``a``, and vice versa.

    .. describe:: parent >> (child_a, child_b, ...)
                  parent >> [child_a, child_b, ...]
                  parent >> {child_a, child_b, ...}

       Bind ``child_a``, ``child_b``, etc. as children of ``parent``.

    .. describe:: (parent_a, parent_b, ...) >> child
                  [parent_a, parent_b, ...] >> child
                  {parent_a, parent_b, ...} >> child

       Bind ``parent_a``, ``parent_b``, etc. as parents of ``child``.

    Aside from binding, every :py:class:`ChainLink` implements the
    `Generator-Iterator Methods`_ interface:

    .. method:: iter(link)

       Create an iterator over all data chunks that can be created.
       Empty results are ignored.

    .. method:: link.__next__()
                link.send(None)
                next(link)

       Create a new chunk of data. Raise :py:exc:`StopIteration` if there are
       no more chunks. Implicitly used by ``next(link)``.

    .. method:: link.send(chunk)

       Process a data ``chunk``, and return the result.

    .. note:: The ``next`` variants contrast with ``iter`` by also returning empty chunks.
              Use variations of ``next(iter(link))`` for an explicit iteration.

    .. method:: link.chainlet_send(chunk)

       Process a data ``chunk`` locally, and return the result.

       This method implements data processing in an element; subclasses must
       overwrite it to define how they handle data.

       This method should only be called to explicitly traverse elements in a chain.
       Client code should use ``next(link)`` and ``link.send(chunk)`` instead.

    .. method:: link.throw(type[, value[, traceback]])

       Raises an exception of ``type`` inside the link. The link may either
       return a final result (including :py:const:`None`), raise :py:exc:`StopIteration` if there are no
       more results, or propagate any other, unhandled exception.

    .. method:: link.close()

       Close the link, cleaning up any resources.. A closed link may raise
       :py:exc:`RuntimeError` if data is requested via ``next`` or processed via ``send``.

    When used in a chain, each :py:class:`ChainLink` is distinguished by its handling
    of input and output. There are two attributes to signal the behaviour when chained.
    These specify whether the element performs a `1 -> 1`, `n -> 1`, `1 -> m` or `n -> m`
    processing of data.

    .. py:attribute:: chain_join

       A :py:class:`bool` indicating that the element expects the values of all
       preceding elements at once. That is, the `chunk` passed in via :py:meth:`send`
       is an *iterable* providing the return values of the previous elements.

    .. py:attribute:: chain_fork

       A :py:class:`bool` indicating that the element produces several values
       at once. That is, the return value is an *iterable* of data chunks,
       each of which should be passed on independently.

    To prematurely stop the traversal of a chain, `1 -> n` and `n -> m` elements should
    return an empty container. Any `1 -> 1` and `n -> 1` element must raise
    :py:exc:`StopTraversal`.

    .. _Generator-Iterator Methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
    """
    chain_types = LinkPrimitives()
    #: whether this element processes several data chunks at once
    chain_join = False
    #: whether this element produces several data chunks at once
    chain_fork = False
    __slots__ = ()

    def _link(self, parent, child):
        """Link the chainlinks parent to child"""
        return self.chain_types.link(parent, child)

    def __rshift__(self, child):
        """
        self >> child

        :param child: following link to bind
        :type child: ChainLink or iterable[ChainLink]
        :returns: link between self and child
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        child = self.chain_types.convert(child)
        return self._link(self, child)

    def __rrshift__(self, parent):
        # parent >> self
        return self << parent

    def __lshift__(self, parent):
        """
        self << parent

        :param parent: preceding link to bind
        :type parent: ChainLink or iterable[ChainLink]
        :returns: link between self and children
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        parent = self.chain_types.convert(parent)
        return self._link(parent, self)

    def __rlshift__(self, child):
        # child << self
        return self >> child

    def __iter__(self):
        if self.chain_fork:
            return self._iter_fork()
        return self._iter_flat()

    def _iter_flat(self):
        while True:
            try:
                yield self.chainlet_send(None)
            except signals.StopTraversal:
                continue
            except StopIteration:
                break

    def _iter_fork(self):
        while True:
            try:
                result = list(self.chainlet_send(None))
                if result:
                    yield result
            except (StopIteration, signals.ChainExit):
                break

    def __next__(self):
        return self.send(None)

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):
        """Send a single value to this element for processing"""
        if self.chain_fork:
            return self._send_fork(value)
        return self._send_flat(value)

    def _send_flat(self, value=None):
        try:
            return self.chainlet_send(value)
        except signals.StopTraversal:
            return None

    def _send_fork(self, value=None):
        return list(self.chainlet_send(value))

    def dispatch(self, values):
        """Dispatch multiple values to this element for processing"""
        for result in lazy_send(self, values):
            yield result

    def chainlet_send(self, value=None):
        """Send a value to this element for processing"""
        raise NotImplementedError  # overwrite in subclasses

    throw = _throw_method

    def close(self):
        """Close this element, freeing resources and possibly blocking further interactions"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


ChainLink.chain_types.base_link_type = ChainLink
