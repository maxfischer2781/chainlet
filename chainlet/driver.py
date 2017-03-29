from __future__ import division, absolute_import
import threading


class ChainDriver(object):
    """
    Actively drives chains by pulling them

    This driver pulls all mounted chains via a single thread. This drives chains
    synchronously, but blocks all chains if any individual chain blocks.
    """
    def __init__(self):
        self.mounts = []
        self._run_lock = threading.Lock()
        self._run_thread = None

    def mount(self, *chains):
        """Add chains to this driver"""
        self.mounts.extend(chains)

    @property
    def running(self):
        """Whether the driver is running, either via :py:meth:`run` or :py:meth:`start`"""
        return self._run_lock.locked()

    def start(self, daemon=True):
        """
        Start driving the chain asynchronously, return immediately

        :param daemon: ungracefully kill the driver when the program terminates
        :type daemon: bool
        """
        if self._run_lock.acquire(False):
            try:
                # there is a short race window in which `start` release the lock,
                # but `run` has not picked it up yet, but the thread exists anyway
                if self._run_thread is None:
                    self._run_thread = threading.Thread(target=self._run_in_thread)
                    self._run_thread.daemon = daemon
                    self._run_thread.start()
            finally:
                self._run_lock.release()

    def _run_in_thread(self):
        try:
            self.run()
        finally:
            self._run_thread = None

    def run(self):
        """
        Start driving the chain, block until done
        """
        with self._run_lock:
            while self.mounts:
                for mount in self.mounts:
                    try:
                        next(mount)
                    except StopIteration:
                        self.mounts.remove(mount)


class ThreadedChainDriver(ChainDriver):
    """
    Actively drives chains by pulling them

    This driver pulls all mounted chains via independent threads. This drives chains
    concurrently, without blocking for any specific chain. Chains sharing elements
    may need to be synchronized explicitly.

    :param daemon: run threads as ``daemon``, i.e. do not wait for them to finish
    :type daemon: bool
    """
    def __init__(self, daemon=True):
        super(ThreadedChainDriver, self).__init__()
        self.daemon = daemon

    def run(self):
        with self._run_lock:
            runner_threads = [
                threading.Thread(target=self._mount_driver, args=(mount,)) for mount in self.mounts
            ]
            for runner_thread in runner_threads:
                runner_thread.daemon = self.daemon
                runner_thread.start()
            for runner_thread in runner_threads:
                runner_thread.join()

    def _mount_driver(self, mount):
        try:
            while True:
                next(mount)
        except StopIteration:
            self.mounts.remove(mount)
