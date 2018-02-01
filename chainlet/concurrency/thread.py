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
    """
    A group of chainlets that concurrently process each :term:`data chunk`

    Processing of chainlets is performed using threads. This allows
    blocking actions, such as file I/O or :py:func:`time.sleep`,
    to be run in parallel.
    """
    chain_types = ThreadLinkPrimitives()
    executor = DEFAULT_EXECUTOR


class ThreadChain(ConcurrentChain):
    chain_types = ThreadLinkPrimitives()
    executor = DEFAULT_EXECUTOR


ThreadLinkPrimitives.base_bundle_type = ThreadBundle
ThreadLinkPrimitives.base_chain_type = ThreadChain
ThreadLinkPrimitives.flat_chain_type = ThreadChain
