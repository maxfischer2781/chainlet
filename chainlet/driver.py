from __future__ import division, absolute_import
import threading

from . import chainlink


class ChainDriver(chainlink.ChainLink):
    """
    Actively drives a chain by pulling from parents and sending to children
    """
    def __init__(self):
        super(ChainDriver, self).__init__()
        self._run_lock = threading.Lock()
        self._run_thread = None

    @property
    def running(self):
        """Whether the driver is running, either via :py:meth:`run` or :py:meth:`start`"""
        return self._run_lock.locked()

    def start(self, daemon=True):
        """
        Start driving the chain, return immediately

        :param daemon: ungracefully kill the driver when the program terminates
        :type daemon: bool
        :raises RuntimeError: if the driver is already running
        """
        if self._run_lock.acquire(False):
            try:
                if self._run_thread is not None:
                    raise RuntimeError("ChainDriver already started")
                self._run_thread = threading.Thread(target=self._run_thread)
                self._run_thread.daemon = daemon
                self._run_thread.start()
            finally:
                self._run_lock.release()

    def _run_thread(self):
        try:
            self.run()
        finally:
            self._run_thread = None

    def run(self):
        """
        Start driving the chain, block until done
        """
        raise NotImplementedError


class SequentialChainDriver(ChainDriver):
    """
    Actively drives a chain by pulling from parents and sending to children

    This driver pulls and sends values sequentially. If any parent blocks on
    a call to `next(parent)`, the entire chain blocks until a value is available.
    """
    def run(self):
        with self._run_lock:
            while True:
                for parent in self._parents:
                    try:
                        value = next(parent)
                        self.send(value)
                    except StopIteration:
                        pass


class ThreadedChainDriver(ChainDriver):
    """
    Actively drives a chain by pulling from parents and sending to children

    This driver pulls and sends values via independent threads. This drives the
    chain concurrently, without blocking for any specific parent.

    :param daemon: run threads as ``daemon``, i.e. do not wait for them to finish
    :type daemon: bool
    :param synchronize: synchronize children so they handle one value at a time
    :type synchronize: bool
    """
    def __init__(self, daemon=True, synchronize=True):
        super(ThreadedChainDriver, self).__init__()
        self.daemon = daemon
        self._child_mutex = threading.Lock() if synchronize else None

    @property
    def synchronize(self):
        return self._child_mutex is not None

    def run(self):
        with self._run_lock:
            runner_threads = [
                threading.Thread(target=self._parent_chain_driver, args=parent) for parent in self._parents
            ]
            for runner_thread in runner_threads:
                runner_thread.daemon = self.daemon
                runner_thread.start()
            for runner_thread in runner_threads:
                runner_thread.join()

    def _parent_chain_driver(self, parent):
        if self._child_mutex:
            for value in parent:
                with self._child_mutex:
                    self.send(value)
        else:
            for value in parent:
                self.send(value)
