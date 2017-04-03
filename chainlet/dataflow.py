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


def joinlet(chainlet):
    """
    Decorator to mark a chainlet as joining

    :param chainlet: a chainlet to mark as joining
    :type chainlet: chainlink.ChainLink
    :return: the chainlet modified inplace
    :rtype: chainlink.ChainLink
    """
    chainlet.chain_join = True
    return chainlet


def forklet(chainlet):
    """
    Decorator to mark a chainlet as forking

    :param chainlet: a chainlet to mark as forking
    :type chainlet: chainlink.ChainLink
    :return: the chainlet modified inplace
    :rtype: chainlink.ChainLink
    """
    chainlet.chain_fork = True
    return chainlet
