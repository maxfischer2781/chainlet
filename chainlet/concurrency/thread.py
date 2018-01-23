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
from .base import StoredFuture, canonical_send, CPU_CONCURRENCY


class ThreadPoolExecutor(object):
    _min_workers = max(CPU_CONCURRENCY, 2)

    def __init__(self, max_workers, identifier=''):
        self._max_workers = max_workers
        self._workers = set()
        self._identifier = identifier or ('%s_%d' % (self.__class__.__name__, id(self)))
        self._queue = queue.Queue()
        self._ensure_worker()
        atexit.register(self._teardown)

    def _teardown(self):
        while True:
            try:
                self._queue.get(block=False)
            except queue.Empty:
                break
        for worker in range(len(self._workers)):
            self._queue.put(None)
        for worker in tuple(self._workers):
            worker.join()

    def submit(self, call, *args, **kwargs):
        future = StoredFuture(call, *args, **kwargs)
        self._queue.put(future)
        self._ensure_worker()
        return future

    def execute_futures(self):
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
        while len(self._workers) < self._min_workers or len(self._workers) < self._queue.qsize() < self._max_workers:
            worker = threading.Thread(
                target=self.execute_futures,
                name=self._identifier + '_%d' % time.time(),
            )
            worker.daemon = True
            self._workers.add(worker)
            worker.start()


DEFAULT_EXECUTOR = ThreadPoolExecutor(CPU_CONCURRENCY * 5, 'chainlet_thread')


class AsyncChainResults(object):
    def __init__(self, futures):
        self._futures = iter(futures)
        self._results = []
        self._exception = None
        self._done = False
        self._result_lock = threading.Lock()

    def _set_done(self):
        if not self._done:
            self._done = True
            self._futures = None
            self._result_lock = None

    def __iter__(self):
        if self._done:
            for item in self._results:
                yield item
        else:
            for item in self._active_iter():
                yield item
        if self._exception is not None:
            raise self._exception

    def _active_iter(self):
        result_idx = 0
        # fast-forward existing results
        for item in self._results:
            yield item
            result_idx += 1
        # fetch remaining results safely
        while self._futures and not self._exception:
            # someone may have beaten us before we acquire this lock
            # constraints must be rechecked as needed
            with self._result_lock:
                try:
                    result = self._results[result_idx]
                except IndexError:
                    try:
                        future = next(self._futures)
                    except StopIteration:
                        break
                    try:
                        results = future.result
                    except Exception as err:
                        self._exception = err
                        break
                    else:
                        self._results.extend(results)
                        for item in results:
                            yield item
                            result_idx += 1
                else:
                    yield result
                    result_idx += 1
        self._done = True


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
        return AsyncChainResults([
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
