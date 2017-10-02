from __future__ import print_function
import sys
import threading

from .. import chainlink


_THREAD_NOT_DONE = object()


class ReturnThread(threading.Thread):
    def __init__(self, *iargs, **ikwargs):
        super(ReturnThread, self).__init__(*iargs, **ikwargs)
        self._return_value = _THREAD_NOT_DONE
        self._exception_value = None

    if sys.version_info[0] < 3:
        @property
        def _target(self):
            return self._Thread__target

        @_target.deleter
        def _target(self):
            del self._Thread__target

        @property
        def _args(self):
            return self._Thread__args

        @_args.deleter
        def _args(self):
            del self._Thread__args

        @property
        def _kwargs(self):
            return self._Thread__kwargs

        @_kwargs.deleter
        def _kwargs(self):
            del self._Thread__kwargs

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


class ThreadChainTypes(chainlink.ChainTypes):
    pass


class ThreadCompoundChainMixin(object):
    chain_types = ThreadChainTypes()

    def __rshift__(self, child):
        print('chain rshift')
        child = self.chain_types.convert(child)
        print(child, self)
        if isinstance(self.elements[-1], self.chain_types.bundle_type):
            return self._link(self[:-1], self.elements[-1] >> child)
        return self._link(self, child)

    def __rrshift__(self, parent):
        # parent >> self
        print('chain rrshift')
        return self << parent


class ThreadChain(ThreadCompoundChainMixin, chainlink.Chain):
    pass


class ThreadFlatChain(chainlink.FlatChain, ThreadChain):
    pass


class ThreadBundle(ThreadCompoundChainMixin, chainlink.Bundle):
    """
    A group of chainlets that concurrently process each :term:`data chunk`

    Processing of chainlets is performed using threads. This allows
    blocking actions, such as file I/O or :py:func:`time.sleep`,
    to be run in parallel.
    """
    def _link_child(self, child):
        if child.chain_join:
            return self._link(self, child)
        return self.chain_types.bundle_type(
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
        print('rshift')
        return self._link_child(self.chain_types.convert(child))

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


ThreadChainTypes.chain_type = ThreadChain
ThreadChainTypes.flat_chain_type = ThreadChain
ThreadChainTypes.bundle_type = ThreadBundle


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
