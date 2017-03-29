from __future__ import absolute_import, division

from . import chainlink


class NoOp(chainlink.ChainLink):
    """
    A noop element that returns any input unchanged

    This element is useful when an element is syntactically required, but no
    action is desired. For example, it can be used to split a pipeline into
    a modified and unmodifed version:

    .. code:: python

        translator = find_language >> (NoOp(), to_french, to_german) >>
    """
    def chainlet_send(self, value=None):
        return value
