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
    #: submodule implementing minor version compatibility
    COMPAT_SUBMODULE = __name__ + '.python%d_%d' % tuple(sys.version_info[:2])
    __import__(COMPAT_SUBMODULE)
except ImportError:
    COMPAT_SUBMODULE = None

#: Python version for which compatibility has been established
COMPAT_VERSION = sys.version_info

__all__ = [
    'COMPAT_VERSION',
    'throw_method'
]
