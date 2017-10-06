import chainlet.concurrency.thread

from . import testbase_primitives


class ThreadedBundle(testbase_primitives.PrimitiveTestCases.ConcurrentBundle):
    bundle_type = chainlet.concurrency.thread.ThreadBundle
