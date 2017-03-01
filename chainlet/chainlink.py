from __future__ import division, absolute_import
import sys

from .compat import throw_method as _throw_method


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
    ``parent >> child`` and `child << parent`. Forking and joining of chains
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

    Aside from binding, every :py:class:`ChainLink` should implement the
    `Generator-Iterator Methods`_ interface as applicable:

    .. method:: link.__next__()
                link.send(None)

       Create a new chunk of data. Raise :py:exc:`StopIteration` if there are
       no more chunks. Implicitly used in ``next(link)`` and ``for chunk in link``.

    .. method:: link.send(chunk)

       Process a data ``chunk``, and return the result.

    .. method:: link.throw(type[, value[, traceback]])

       Raises an exception of ``type`` inside the link. The link may either
       return a final result, raise :py:exc:`StopIteration` if there are no
       more results, or propagate any other, unhandled exception.

    .. method:: link.close()

       Close the link, cleaning up any resources.. A closed link may raise
       :py:exc:`RuntimeError` if data is requested via ``next``or processed via ``send``.

    .. _Generator-Iterator Methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
    """
    chain_linker = None

    def __init__(self):
        self._path = None

    def _compile_paths(self):
        """Compile the paths visited by this element"""
        return LinearChain((self,)),

    @property
    def paths(self):
        """
        All chains visited by this element

        :returns: :py:class:`~.LinearChain`
        """
        if self._path is None:
            self._path = self._compile_paths()
        return self._path

    def __rshift__(self, children):
        # self >> children
        linker = self.chain_linker if self.chain_linker is not None else DEFAULT_LINKER
        return linker(self, children)

    def __rrshift__(self, parents):
        # parent >> self
        return self << parents

    def __lshift__(self, parents):
        # self << parent
        linker = self.chain_linker if self.chain_linker is not None else DEFAULT_LINKER
        return linker(parents, self)

    def __rlshift__(self, children):
        # children << self
        return self >> children

    def __iter__(self):
        return self

    def __next__(self):
        return self.send(None)

    if sys.version_info < (3,):
        def next(self):
            return self.__next__()

    def send(self, value=None):  # pylint: disable=no-self-use
        """Send a value to this element for processing"""
        return value

    throw = _throw_method

    def close(self):
        """Close this element, freeing resources and blocking further interactions"""
        pass


class Chain(ChainLink):
    def __init__(self, elements):
        self.elements = elements
        super(Chain, self).__init__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.elements == other.elements
        return NotImplemented

    def __hash__(self):
        return hash(self.elements)

    def send(self, value=None):
        raise NotImplementedError


class LinearChain(Chain):
    """
    A linear sequence of chainlets, with each element preceding the next
    """
    def _compile_paths(self):
        return self,

    def send(self, value=None):
        for element in self.elements:
            value = element.send(value)
        return value

    def __repr__(self):
        return ' >> '.join(repr(elem) for elem in self.elements)


class ParallelChain(Chain):
    """
    A parallel sequence of chainlets, with each element ranked the same
    """
    def _compile_paths(self):
        return tuple(path for element in self.elements for path in element.paths)

    def send(self, value=None):
        return [element.send(value) for element in self.elements]

    def __repr__(self):
        return repr(self.elements)


class MetaChain(ParallelChain):
    """
    A mixed sequence of linear and parallel chainlets
    """
    def __init__(self, elements):
        _elements = []
        _elements_buffer = []
        for element in elements:
            if isinstance(element, ParallelChain):
                if _elements_buffer:
                    _elements.append(LinearChain(tuple(_elements_buffer)))
                    _elements_buffer = []
                _elements.append(element)
            else:
                _elements_buffer.append(element)
        super(MetaChain, self).__init__(tuple(elements))

    def _compile_paths(self):
        if not self.elements:
            return ()
        element_iter = iter(self.elements)
        paths = next(element_iter).paths
        for element in element_iter:
            paths = [old_path >> new_path for old_path in paths for new_path in element.paths]
        return tuple(paths)

    def send(self, value=None):
        values = [value]
        for element in self.elements:
            if isinstance(element, ParallelChain):
                # flatten output of parallel paths
                values = [retval for value in values for retval in element.send(value)]
            else:
                values = [element.send(value) for value in values]
        return values

    def __repr__(self):
        return ' >> '.join(repr(elem) for elem in self.elements)


def parallel_chain_converter(element):
    if isinstance(element, (tuple, list, set)):
        return ParallelChain(element)
    raise TypeError


class ChainLinker(object):
    """
    Helper for linking objects to chains
    """
    #: functions to convert elements; must return a ChainLink or raise TypeError
    converters = [parallel_chain_converter]

    def link(self, *elements):
        _elements = []
        for element in elements:
            element = self.convert(element)
            if isinstance(element, (LinearChain, MetaChain)):
                _elements.extend(element.elements)
            else:
                _elements.append(element)
        if any(isinstance(element, ParallelChain) for element in _elements):
            if len(_elements) == 1:
                return _elements[0]
            return MetaChain(_elements)
        return LinearChain(_elements)

    def convert(self, element):
        for converter in self.converters:
            try:
                return converter(element)
            except TypeError:
                continue
        return element

    def __call__(self, *elements):
        return self.link(*elements)


DEFAULT_LINKER = ChainLinker()
