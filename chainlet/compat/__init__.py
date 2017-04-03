"""
Compatibility layer for different python implementations
"""
from __future__ import absolute_import
try:
    from .python2 import throw_method, collections_abc
except SyntaxError:
    from .python3 import throw_method, collections_abc

__all__ = ['collections_abc', 'throw_method']
