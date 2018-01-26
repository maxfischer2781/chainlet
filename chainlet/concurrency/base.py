import threading
import multiprocessing

import chainlet.signals
from .. import chainlink


CPU_CONCURRENCY = multiprocessing.cpu_count()


class StoredFuture(object):
    """
    Call stored for future execution

    :param call: callable to execute
    :param args: positional arguments to ``call``
    :param kwargs: keyword arguments to ``call``
    """
    __slots__ = ('_instruction', '_result', '_mutex')

    def __init__(self, call, *args, **kwargs):
        self._instruction = call, args, kwargs
        self._result = None
        self._mutex = threading.Lock()

    def realise(self):
        """
        Realise the future if possible

        If the future has not been realised yet, do so in the current thread.
        This will block execution until the future is realised.
        Otherwise, do not block but return whether the result is already available.

        This will not return the result nor propagate any exceptions of the future itself.

        :return: whether the future has been realised
        :rtype: bool
        """
        if self._mutex.acquire(False):
            # realise the future in this thread
            try:
                if self._result is not None:
                    return True
                call, args, kwargs = self._instruction
                try:
                    result = call(*args, **kwargs)
                except Exception as err:
                    self._result = None, err
                else:
                    self._result = result, None
                return True
            finally:
                self._mutex.release()
        else:
            # indicate whether the executing thread is done
            return self._result is not None

    def await_result(self):
        """Wait for the future to be realised"""
        # if we cannot realise the future, another thread is doing so already
        # wait for the mutex to be released by it once it has finished
        if not self.realise():
            with self._mutex:
                pass

    @property
    def result(self):
        """
        The result from realising the future

        If the result is not available, block until done.

        :return: result of the future
        :raises: any exception encountered during realising the future
        """
        if self._result is None:
            self.await_result()
        chunks, exception = self._result
        if exception is None:
            return chunks
        raise exception  # re-raise exception from execution


class FutureChainResults(object):
    """
    Chain result computation stored for future and concurrent execution

    Acts as an iterable for the actual results. Each future can be executed
    prematurely by a concurrent executor, with a synchronous fallback as
    required. Iteration can lazily advance through all available results
    before blocking.

    If any future raises an exception, iteration re-raises the exception
    at the appropriate position.

    :param futures: the stored futures for each result chunk
    :type futures: list[StoredFuture]
    """
    def __init__(self, futures):
        self._futures = iter(futures)
        self._results = []
        self._exception = None
        self._done = False
        self._result_lock = threading.Lock()

    def _set_done(self):
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
        while not self._done:
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
        for item in self._results[result_idx:]:
            yield item
        self._set_done()
