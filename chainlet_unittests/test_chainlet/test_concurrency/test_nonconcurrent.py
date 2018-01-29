import chainlet.concurrency.base

from . import testbase_primitives


# non-concurrent primitives
class NonConcurrentBundle(testbase_primitives.PrimitiveTestCases.ConcurrentBundle):
    test_concurrent = None


# dummy-concurrent primitives
class LocalBundle(testbase_primitives.PrimitiveTestCases.ConcurrentBundle):
    test_concurrent = None
    bundle_type = chainlet.concurrency.base.LocalBundle
