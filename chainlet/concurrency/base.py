import threading
import multiprocessing
import collections
import itertools

from .. import chainlink
from .. import signals
from ..chainsend import eager_send


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
                except BaseException as err:
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
    __slots__ = ('_futures', '_results', '_exception', '_done', '_result_lock')

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
                    except BaseException as err:
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


class SafeTee(object):
    """
    Thread-safe version of :py:func:`itertools.tee`

    :param iterable: source iterable to split
    :param n: number of safe iterators to produce for `iterable`
    :type n: int
    """
    __slots__ = ('_count', '_tees', '_mutex')

    def __init__(self, iterable, n=2):
        self._count = n
        self._tees = iter(itertools.tee(iterable, n))
        self._mutex = threading.Lock()

    def __iter__(self):
        try:
            tee = next(self._tees)
        except StopIteration:
            raise ValueError('too many iterations (expected %d)' % self._count)
        try:
            while True:
                with self._mutex:
                    value = next(tee)
                yield value
        except StopIteration:
            return


def multi_iter(iterable, count=2):
    """Return `count` independent, thread-safe iterators for `iterable`"""
    # no need to special-case re-usable, container-like iterables
    if not isinstance(
            iterable,
            (
                    list, tuple, set,
                    FutureChainResults,
                    collections.Sequence, collections.Set, collections.Mapping, collections.MappingView
            )):
        iterable = SafeTee(iterable, n=count)
    return (iter(iterable) for _ in range(count))


class LocalExecutor(object):
    """
    Executor for futures using local execution stacks without concurrency

    :param max_workers: maximum number of threads in pool
    :type max_workers: int or float
    :param identifier: base identifier for all workers
    :type identifier: str
    """
    _min_workers = max(CPU_CONCURRENCY, 2)

    def __init__(self, max_workers, identifier=''):
        self.identifier = identifier or ('%s_%d' % (self.__class__.__name__, id(self)))
        self._max_workers = max_workers if max_workers > 0 else float('inf')

    @staticmethod
    def submit(call, *args, **kwargs):
        """
        Submit a call for future execution

        :return: future for the call execution
        :rtype: StoredFuture
        """
        return StoredFuture(call, *args, **kwargs)


DEFAULT_EXECUTOR = LocalExecutor(-1, 'chainlet_local')


class ConcurrentBundle(chainlink.Bundle):
    """
    A group of chainlets that concurrently process each :term:`data chunk`

    Processing of chainlets is performed using only the requesting threads.
    This allows thread-safe usage, but requires explicit concurrent usage
    for blocking actions, such as file I/O or :py:func:`time.sleep`,
    to be run in parallel.

    Concurrent bundles implement element concurrency:
    the same data is processed concurrently by multiple elements.
    """
    executor = DEFAULT_EXECUTOR

    def chainlet_send(self, value=None):
        if self.chain_join:
            return FutureChainResults([
                self.executor.submit(eager_send, element, values)
                for element, values in zip(self.elements, multi_iter(value, len(self.elements)))
            ])
        else:
            values = (value,)
            return FutureChainResults([
                self.executor.submit(eager_send, element, values)
                for element in self.elements
            ])


class ConcurrentChain(chainlink.Chain):
    """
    A group of chainlets that concurrently process each :term:`data chunk`

    Processing of chainlets is performed using only the requesting threads.
    This allows thread-safe usage, but requires explicit concurrent usage
    for blocking actions, such as file I/O or :py:func:`time.sleep`,
    to be run in parallel.

    Concurrent chains implement data concurrency:
    multiple data is processed concurrently by the same elements.

    :note: A :py:class:`ConcurrentChain` will *always* :term:`join`
           and :term:`fork` to handle all data.
    """
    executor = DEFAULT_EXECUTOR

    def __init__(self, elements):
        super(ConcurrentChain, self).__init__(elements)
        self._stripes = None
        # need to receive all data for parallelism
        self.chain_join = True
        self.chain_fork = True

    def _compile_stripes(self):
        stripes, buffer = [], []
        for element in self.elements:
            if element.chain_join:
                if buffer:
                    stripes.append(chainlink.Chain(buffer))
                    buffer = []
                stripes.append(element)
            elif element.chain_fork:
                if buffer:
                    buffer.append(element)
                    stripes.append(chainlink.Chain(buffer))
                    buffer = []
                else:
                    stripes.append(element)
            else:
                buffer.append(element)
        if buffer:
            stripes.append(chainlink.Chain(buffer))
        self._stripes = stripes

    def chainlet_send(self, value=None):
        if self._stripes is None:
            self._compile_stripes()
        if self.chain_join:
            values = value
        else:
            values = [value]
        try:
            for stripe in self._stripes:
                if not stripe.chain_join:
                    values = FutureChainResults([
                        self.executor.submit(eager_send, stripe, [value])
                        for value in values
                    ])
                else:
                    values = eager_send(stripe, values)
                if not values:
                    break
            if self.chain_fork:
                return values
            else:
                try:
                    return next(iter(values))
                except IndexError:
                    raise signals.StopTraversal
        # An element in the chain is exhausted permanently
        except signals.ChainExit:
            raise StopIteration
