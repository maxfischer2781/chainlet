"""
Thread based concurrency domain
"""
from __future__ import print_function
import threading
import time
import atexit
try:
    import Queue as queue
except ImportError:
    import queue

from .. import chainlink
from .base import StoredFuture, canonical_send, CPU_CONCURRENCY, FutureChainResults


class ThreadPoolExecutor(object):
    """
    Executor for futures using a pool of threads

    :param max_workers: maximum number of threads in pool
    :type max_workers: int or float
    :param identifier: base identifier for all workers
    :type identifier: str
    """
    _min_workers = max(CPU_CONCURRENCY, 2)

    def __init__(self, max_workers, identifier=''):
        self._max_workers = max_workers if max_workers > 0 else float('inf')
        self._workers = set()
        self._identifier = identifier or ('%s_%d' % (self.__class__.__name__, id(self)))
        self._queue = queue.Queue()
        self._ensure_worker()
        # need to pass in queue.Empty as queue module may be collected on shutdown
        atexit.register(self._teardown, queue.Empty)

    def _teardown(self, queue_empty):
        # prevent starting new workers
        self._min_workers, self._max_workers = 0, 0
        while True:
            try:
                self._queue.get(block=False)
            except queue_empty:
                break
        for worker in range(len(self._workers)):
            self._queue.put(None)
        for worker in tuple(self._workers):
            worker.join()

    def submit(self, call, *args, **kwargs):
        """
        Submit a call for future execution

        :return: future for the call execution
        :rtype: StoredFuture
        """
        future = StoredFuture(call, *args, **kwargs)
        self._queue.put(future)
        self._ensure_worker()
        return future

    def _execute_futures(self):
        while True:
            # try and get work
            try:
                future = self._queue.get(timeout=10)  # type: StoredFuture
            except queue.Empty:
                if self._dismiss_worker(threading.current_thread()):
                    break
            else:
                if future is None:
                    break
                future.realise()
                self._queue.task_done()
        # clean up dangling threads
        self._workers.discard(threading.current_thread())

    def _dismiss_worker(self, worker):
        """Dismiss ``worker`` unless it is still required"""
        self._workers.remove(worker)
        if len(self._workers) < self._min_workers:
            self._workers.add(worker)
            return False
        return True

    def _ensure_worker(self):
        """Ensure there are enougn workers available"""
        while len(self._workers) < self._min_workers or len(self._workers) < self._queue.qsize() < self._max_workers:
            worker = threading.Thread(
                target=self._execute_futures,
                name=self._identifier + '_%d' % time.time(),
            )
            worker.daemon = True
            self._workers.add(worker)
            worker.start()


DEFAULT_EXECUTOR = ThreadPoolExecutor(CPU_CONCURRENCY * 5, 'chainlet_thread')


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
    executor = DEFAULT_EXECUTOR

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
        return FutureChainResults([
            self.executor.submit(canonical_send, element, [value])
            for element in self.elements
        ])


ThreadLinkPrimitives.base_bundle_type = ThreadBundle


if __name__ == "__main__":
    # test/demonstration code
    import chainlet.dataflow
    import chainlet._debug
    import sys

    @chainlet.funclet
    def sleep(value, seconds, identifier='<anon>'):
        print(threading.get_ident(), 'sleep', seconds, '@', identifier, value)
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
    print('Chain [%d/%d] >> 1/%d' % (count, count, count))
    print('Main', threading.get_ident())
    noop = chainlet.dataflow.NoOp()
    chn = noop >> ThreadBundle([sleep(seconds=duration, identifier=_) for _ in range(count)]) >> sleep(seconds=duration) >> noop
    print(chn)
    start_time = time.time()
    chn.send(start_time)
    end_time = time.time()
    delta = end_time - start_time
    ideal = duration * 2
    per_thread = (delta - ideal) / count
    print('total=%.2f' % delta, 'ideal=%.2f' % ideal, 'reldev=%02d%%' % ((delta - ideal) / ideal * 100), 'perthread', per_thread)
