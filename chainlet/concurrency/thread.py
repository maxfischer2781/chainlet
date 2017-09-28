import threading

from .. import chainlink


_THREAD_NOT_DONE = object()


class ReturnThread(threading.Thread):
    def __init__(self, *iargs, **ikwargs):
        super(ReturnThread, self).__init__(*iargs, **ikwargs)
        self._return_value = _THREAD_NOT_DONE
        self._exception_value = None

    def run(self):
        try:
            if self._target:
                self._return_value = self._target(*self._args, **self._kwargs)
        except (StopIteration, chainlink.StopTraversal) as err:
            self._exception_value = err
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    @property
    def return_value(self):
        if self._return_value is _THREAD_NOT_DONE:
            if not self.is_alive():
                self.start()
            self.join()
        if self._exception_value is not None:
            raise self._exception_value
        return self._return_value


class ThreadLinker(chainlink.ChainLinker):
    """
    Helper for linking individual :term:`chainlinks` to form compound :term:`chainlinks`

    This Linker creates a direct implementation of the data flow.
    It creates the longest :py:class:`~chainlink.Bundle` possible, maximising the number of concurrent branches.
    """
    def link(self, *elements):
        elements = self.normalize(*elements)
        elements = self.expand(*elements)
        chain = self.bind_chain(*elements)
        chain.chain_linker = self
        return chain

    def expand(self, *elements):
        # We iterate in reverse through the elements, so
        # later elements can be constructed once and then
        # just cloned.
        # This means our BUFFERS ARE REVERSED as well!
        static = []  # elements which cannot be bound to a preceding bundle
        buffer = []  # buffer of elements that have not been bound yet
        for element in reversed(elements):
            if element.chain_join:
                print('join', element)
                buffer.append(element)
                static += buffer
                buffer = []
            elif isinstance(element, ThreadBundle):
                print('bundle', element)
                buffer.append(self.rebundle(element, list(reversed(buffer))))
            elif element:
                print('push', element)
                buffer.append(element)
        static += buffer
        return list(reversed(static))

    def rebundle(self, bundle, tail):
        print('rebundle', bundle, tail)
        return type(bundle)(
            self.link(chain, *tail) for chain in bundle.elements
        )


class ThreadBundle(chainlink.Bundle):
    """
    A group of chainlets that concurrently process each :term:`data chunk`

    Processing of chainlets is performed using threads. This allows
    blocking actions, such as file I/O or :py:func:`time.sleep`,
    to be run in parallel.
    """
    chain_linker = ThreadLinker()

    def chainlet_send(self, value=None):
        result_threads = self._dispath_send(value)
        return self._collect_send(result_threads)

    def _dispath_send(self, value):
        result_threads = []
        for element in self.elements:
            send_thread = ReturnThread(target=element.chainlet_send, args=(value,))
            send_thread.start()
            result_threads.append((
                element.chain_join,
                element.chain_fork,
                send_thread
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
        count = 10
    try:
        duration = float(sys.argv[2])
    except IndexError:
        duration = 1.0 / count
    noop = chainlet.dataflow.NoOp()
    chn = noop >> ThreadBundle([sleep(seconds=duration) for _ in range(count)]) >> noop
    print(chn)
    start_time = time.time()
    chn.send(start_time)
    end_time = time.time()
    delta = end_time - start_time
    per_thread = (delta - duration) / count
    print(delta, 'ideal=%.1f' % duration, 'reldev=%02d%%' % ((delta - duration) / duration * 100), 'pthread', per_thread)
