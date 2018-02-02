class StopTraversal(Exception):
    """
    Stop the traversal of a chain

    Any chain element raising :py:exc:`~.StopTraversal` signals that
    subsequent elements of the chain should not be visited with the current value.

    Raising :py:exc:`~.StopTraversal` does *not* mean the element is exhausted.
    It may still produce values regularly on future traversal.
    If an element will *never* produce values again, it should raise :py:exc:`ChainExit`.

    :note: This signal explicitly affects the current chain only. It does not
           affect other, parallel chains of a graph.

    .. versionchanged:: 1.3
       The ``return_value`` parameter was removed.
    """
    def __init__(self):
        Exception.__init__(self)


class ChainExit(Exception):
    """
    Terminate the traversal of a chain
    """
    pass
