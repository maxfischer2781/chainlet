"""
Compatibility layer for different python implementations
"""
from __future__ import absolute_import
import sys
try:
    from .python2 import throw_method
except SyntaxError:
    from .python3 import throw_method

try:
    _compat_sub_module = 'python%d_%d' % sys.version_info[:2]
    __import__(_compat_sub_module)
except ImportError:
    pass

compat_version = sys.version_info

__all__ = [
    'compat_version',
    'throw_method'
]
