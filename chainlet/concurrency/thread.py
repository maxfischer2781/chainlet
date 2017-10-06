"""
Thread based concurrency domain
"""
from __future__ import print_function
import threading

from .. import chainlink


_THREAD_NOT_DONE = object()


class ThreadedCall(object):
    def __init__(self, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result = None
        self._thread = threading.Thread(target=self)
        self._thread.start()

    def __call__(self):
        try:
            self._result = self._func(*self._args, **self._kwargs), None
        except Exception as err:
            self._result = None, err
        del self._func, self._args, self._kwargs

    @property
    def return_value(self):
        if self._result is None:
            self._thread.join()
        result, error = self._result
        if error:
            raise error
        return result


class ThreadLinkPrimitives(chainlink.LinkPrimitives):
    pass


class ThreadBundle(chainlink.Bundle):
    """
    A group of chainlets that concurrently process each :term:`data chunk`

    Processing of chainlets is performed using threads. This allows
    blocking actions, such as file I/O or :py:func:`time.sleep`,
    to be run in parallel.
    """
    chain_types = ThreadLinkPrimitives()

    def _link_child(self, child):
        if child.chain_join:
            return self._link(self, child)
        return self.chain_types.base_bundle_type(
            sub_chain >> child for sub_chain in self.elements
        )

    def __rshift__(self, child):
        """
        self >> child

        :param child: following link to bind
        :type child: ChainLink or iterable[ChainLink]
        :returns: link between self and child
        :rtype: ChainLink, FlatChain, Bundle or Chain
        """
        return self._link_child(self.chain_types.convert(child))

    def chainlet_send(self, value=None):
        result_threads = self._dispath_send(value)
        return self._collect_send(result_threads)

    def _dispath_send(self, value):
        result_threads = []
        for element in self.elements:
            result_threads.append((
                element.chain_join,
                element.chain_fork,
                ThreadedCall(element.chainlet_send, value)
            ))
        return result_threads

    def _collect_send(self, result_threads):
        results = []
        elements_exhausted = 0
        for chain_join, chain_fork, send_thread in result_threads:
            if chain_fork:
                try:
                    results.extend(send_thread.return_value)
                except StopIteration:
                    elements_exhausted += 1
            else:
                # this is a bit of a judgement call - MF@20170329
                # either we
                # - catch StopTraversal and return, but that means further elements will still get it
                # - we suppress StopTraversal, denying any return_value
                # - we return the Exception, which means later elements must check/filter it
                try:
                    results.append(send_thread.return_value)
                except chainlink.StopTraversal as err:
                    if err.return_value is not chainlink.END_OF_CHAIN:
                        results.append(err.return_value)
                except StopIteration:
                    elements_exhausted += 1
        if elements_exhausted == len(self.elements):
            raise StopIteration
        return results


ThreadLinkPrimitives.base_bundle_type = ThreadBundle


if __name__ == "__main__":
    # test/demonstration code
    import chainlet.dataflow
    import time
    import sys

    @chainlet.funclet
    def sleep(value, seconds):
        time.sleep(seconds)
        return value

    try:
        count = int(sys.argv[1])
    except IndexError:
        count = 4
    try:
        duration = float(sys.argv[2])
    except IndexError:
        duration = 1.0 / count
    noop = chainlet.dataflow.NoOp()
    chn = noop >> ThreadBundle([sleep(seconds=duration) for _ in range(count)]) >> sleep(seconds=duration) >> noop
    print(chn)
    start_time = time.time()
    chn.send(start_time)
    end_time = time.time()
    delta = end_time - start_time
    ideal = duration * 2
    per_thread = (delta - ideal) / count
    print(delta, 'ideal=%.1f' % ideal, 'reldev=%02d%%' % ((delta - ideal) / ideal * 100), 'pthread', per_thread)
