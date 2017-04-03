"""
Compatibility layer for different python implementations
"""
from __future__ import absolute_import
try:
    from .python2 import throw_method
except SyntaxError:
    from .python3 import throw_method

__all__ = ['throw_method']
