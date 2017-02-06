from __future__ import division, absolute_import


class ChainLink(object):
    """
    An element in a chain

    Each element may fork to an arbitrary number of elements, and have an
    arbitrary number of parents.
    """
    def __init__(self):
        self._parents = []
        self._children = []

    def bind_parents(self, *parents, _rebound=False):
        self._parents.extend(parents)
        if not _rebound:
            for parent in parents:
                parent.bind_parent(self, _rebound=True)

    def bind_children(self, *children, _rebound=False):
        self._parents.extend(children)
        if not _rebound:
            for child in children:
                child.bind_parent(self, _rebound=True)

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

    def __next__(self):
        raise StopIteration('Not Iterable')

    def send(self, value=None):
        """Send a value to this element"""
        for child in self._children:
            child.send(value)

    def throw(self, type, value=None, traceback=None):
        for child in self._children:
            child.throw(type, value, traceback)

    def close(self):
        for child in self._children:
            child.close()
        self._children = type(self._children)()
