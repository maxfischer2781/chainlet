from __future__ import absolute_import
try:
    from .python2 import throw_method
except SyntaxError:
    from .python3 import throw_method
