# pylint: disable=syntax-error
import collections as collections_abc


@staticmethod
def throw_method(type, value=None, traceback=None):  # pylint: disable=redefined-builtin
    """Throw an exception in this element"""
    raise type, value, traceback

__all__ = ['collections_abc', 'throw_method']
