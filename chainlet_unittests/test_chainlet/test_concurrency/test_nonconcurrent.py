from . import testbase_primitives


class NonConcurrentBundle(testbase_primitives.PrimitiveTestCases.ConcurrentBundle):
    test_concurrent = None
