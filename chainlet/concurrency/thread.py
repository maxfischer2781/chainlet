"""
Thread based concurrency domain

Primitives of this module implement concurrency based on threads.
This allows blocking actions, such as I/O and certain extension modules, to be run in parallel.
Note that regular Python code is not parallelised by threads due to the :term:`Global Interpreter Lock`.
See the :py:mod:`threading` module for details.

:warning: The primitives in this module should not be used manually, and may change without deprecation warning.
          Use :py:func:`convert` instead.
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
from .base import StoredFuture, CPU_CONCURRENCY, LocalExecutor, ConcurrentBundle, ConcurrentChain


class ThreadPoolExecutor(LocalExecutor):
    """
    Executor for futures using a pool of threads

    :param max_workers: maximum number of threads in pool
    :type max_workers: int or float
    :param identifier: base identifier for all workers
    :type identifier: str
    """
    _min_workers = max(CPU_CONCURRENCY, 2)

    def __init__(self, max_workers, identifier=''):
        super(ThreadPoolExecutor, self).__init__(max_workers=max_workers, identifier=identifier)
        self._workers = set()
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
        """Ensure there are enough workers available"""
        while len(self._workers) < self._min_workers or len(self._workers) < self._queue.qsize() < self._max_workers:
            worker = threading.Thread(
                target=self._execute_futures,
                name=self.identifier + '_%d' % time.time(),
            )
            worker.daemon = True
            self._workers.add(worker)
            worker.start()


DEFAULT_EXECUTOR = ThreadPoolExecutor(CPU_CONCURRENCY * 5, 'chainlet_thread')


class ThreadLinkPrimitives(chainlink.LinkPrimitives):
    pass


class ThreadBundle(ConcurrentBundle):
    chain_types = ThreadLinkPrimitives()
    executor = DEFAULT_EXECUTOR

    def __repr__(self):
        return 'threads(%s)' % super(ThreadBundle, self).__repr__()


class ThreadChain(ConcurrentChain):
    chain_types = ThreadLinkPrimitives()
    executor = DEFAULT_EXECUTOR

    def __repr__(self):
        return 'threads(%s)' % super(ThreadChain, self).__repr__()


ThreadLinkPrimitives.base_bundle_type = ThreadBundle
ThreadLinkPrimitives.base_chain_type = ThreadChain
ThreadLinkPrimitives.flat_chain_type = ThreadChain


def convert(element):
    """
    Convert a regular :term:`chainlink` to a thread based version

    :param element: the chainlink to convert
    :return: a threaded version of ``element`` if possible, or the element itself
    """
    element = chainlink.LinkPrimitives().convert(element)
    if isinstance(element, chainlink.LinkPrimitives.base_bundle_type):
        return ThreadLinkPrimitives.base_bundle_type(element.elements)
    elif isinstance(element, chainlink.LinkPrimitives.base_chain_type):
        return ThreadLinkPrimitives.base_chain_type(element.elements)
    return element
