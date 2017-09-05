"""
Compatibility layer for different python implementations
"""
from __future__ import absolute_import
import sys
try:
    from .python2 import throw_method
except SyntaxError:
    from .python3 import throw_method

# load optional minor-version compatibility fixes
# this currently works via side-effects only
try:
    _compat_sub_module = 'python%d_%d' % sys.version_info[:2]
    __import__(_compat_sub_module)
except ImportError:
    pass

#: Python version compatibility was established for
COMPAT_VERSION = sys.version_info

__all__ = [
    'COMPAT_VERSION',
    'throw_method'
]
