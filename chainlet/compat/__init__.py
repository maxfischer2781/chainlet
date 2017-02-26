from __future__ import absolute_import
try:
    from .python2X import throw_method
except SyntaxError:
    from .python3X import throw_method
