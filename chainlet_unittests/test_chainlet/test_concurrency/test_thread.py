import chainlet.concurrency.thread

from . import testbase_primitives


class ThreadedBundle(testbase_primitives.PrimitiveTestCases.ConcurrentBundle):
    bundle_type = chainlet.concurrency.thread.ThreadBundle
    converter = staticmethod(chainlet.concurrency.thread.convert)


class ThreadedChain(testbase_primitives.PrimitiveTestCases.ConcurrentChain):
    chain_type = chainlet.concurrency.thread.ThreadChain
    converter = staticmethod(chainlet.concurrency.thread.convert)
