from . import signals


__all__ = ['lazy_send', 'eager_send']


def lazy_send(chainlet, chunks):
    """
    Canonical version of `chainlet_send` that always takes and returns an iterable

    :param chainlet: the chainlet to receive and return data
    :type chainlet: chainlink.ChainLink
    :param chunks: the stream slice of data to pass to ``chainlet``
    :type chunks: iterable
    :return: the resulting stream slice of data returned by ``chainlet``
    :rtype: iterable
    """
    fork, join = chainlet.chain_fork, chainlet.chain_join
    if fork and join:
        return _send_n_get_m(chainlet, chunks)
    elif fork:
        return _lazy_send_1_get_m(chainlet, chunks)
    elif join:
        return _lazy_send_n_get_1(chainlet, chunks)
    else:
        return _lazy_send_1_get_1(chainlet, chunks)


def eager_send(chainlet, chunks):
    """
    Eager version of `lazy_send` evaluating the return value immediately

    :note: The return value by an ``n`` to ``m`` link is considered fully evaluated.

    :param chainlet: the chainlet to receive and return data
    :type chainlet: chainlink.ChainLink
    :param chunks: the stream slice of data to pass to ``chainlet``
    :type chunks: iterable
    :return: the resulting stream slice of data returned by ``chainlet``
    :rtype: iterable
    """
    fork, join = chainlet.chain_fork, chainlet.chain_join
    if fork and join:
        return _send_n_get_m(chainlet, chunks)
    elif fork:
        return tuple(_lazy_send_1_get_m(chainlet, chunks))
    elif join:
        return tuple(_lazy_send_n_get_1(chainlet, chunks))
    else:
        return tuple(_lazy_send_1_get_1(chainlet, chunks))


def _send_n_get_m(chainlet, chunks):
    # aggregate input for joining paths, flatten output of parallel paths
    # iterator goes in, iterator comes out
    return chainlet.chainlet_send(chunks)


def _lazy_send_1_get_m(element, values):
    # flatten output of each send for each input
    # chunk goes in, iterator comes out
    for value in values:
        try:
            for return_value in element.chainlet_send(value):
                yield return_value
        except signals.StopTraversal:
            continue
        except StopIteration:
            raise signals.ChainExit


def _lazy_send_n_get_1(element, values):
    # pass on everything, box input after joining chunks
    try:
        yield element.chainlet_send(values)
    except signals.StopTraversal:
        return


def _lazy_send_1_get_1(element, values):
    # unpack input, pack output
    # chunks from iterator go in, one chunk comes out for each chunk
    for value in values:
        try:
            yield element.chainlet_send(value)
        except signals.StopTraversal:
            continue
        except StopIteration:
            raise signals.ChainExit
