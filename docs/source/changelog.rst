++++++++++++++++++
chainlet Changelog
++++++++++++++++++

v1.3.0
------

    **New Features**

        * The ``>>`` and ``<<`` operators use experimental reflection precedence based on domains.

        * Added a future based ``concurrency`` module.

        * Added a ``threading`` based chain domain offering concurrent bundles.

        * Added a ``multiprocessing`` based ``Driver``.

    **Major Changes**

        * Due to inconsistent semantics, stopping a chain with ``StopTraversal`` no longer allows for a return value.
          Aligned ``chainlet.send`` to ``generator.send``,
          returning ``None`` or an empty iterable instead of blocking indefinitely.
          See `issue #8 <https://github.com/maxfischer2781/chainlet/issues/8>`_ for details.

        * Added ``chainlet.dispatch(iterable)`` to ``send`` an entire stream slice at once.
          This allows for internal lazy and concurrent evaluation.

        * Deprecated the use of external linkers in favour of operator+constructor.

        * Linking to chains ignores elements which are ``False`` in a boolean sense, e.g. an empty ``CompoundLink``.

    **Minor Changes**

        * ``CompoundLink`` objects are now considered boolean ``False`` based on elements.

        * Added a neutral element for internal use.

    **Bug Fixes**

        * A ``Bundle`` will now properly ``join`` the stream if any of its elements does so.

        * Correctly unwrapping return value for any ``Chain`` which does not ``fork``.

        * ``FunctionLink`` and ``funclet`` support positional arguments

v1.2.0
------

    **New Features**

        * Decorator/Wrapper versions of ``FunctionLink`` and ``GeneratorLink`` are proper subclasses of their class.
          This allows setting attributes and inspection.
          Previously, they were factory functions.

        * Instances of ``FunctionLink`` can be copied and pickled.

        * Instances of ``GeneratorLink`` can be copied and pickled.

        * Subchains can be extracted from a ``Chain`` via slicing.

    **Major Changes**

        * Renamed compound chains and simplified inheritance to better reflect their structure:

            * ``Chain`` has been renamed to ``CompoundLink``

            * ``ConcurrentChain`` has been removed

            * ``MetaChain`` has been renamed to ``Chain``

            * ``LinearChain`` has been renamed to ``FlatChain``

            * ``ParallelChain`` has been renamed to ``Bundle``

        * A ``Chain`` that never forks or definitely joins yields raw data chunks, instead of nesting each in a ``list``

        * A ``Chain`` whose first element does a ``fork`` inherits this.

    **Minor Changes**

        * The top-level namespace ``chainlet`` has been cleared from some specialised aliases.

    **Fixes**

        * Chains containing any ``chainlet_fork`` elements but no ``Bundle`` are properly built

v1.1.0 2017-06-08
-----------------

    **New Features**

        * Protolinks: chainlet versions of builtins and protocols

    **Minor Changes**

        * Removed outdated sections from documentation

v1.0.0 2017-06-03
-----------------

    **Notes**

        * Initial release

    **New Features**

        * Finalized definition of chainlet element interface on ``chainlet.ChainLink``

        * Wrappers for generators, coroutines and functions as ``chainlet.genlet`` and ``chainlet.funclet``

        * Finalized dataflow definition for chains, fork and join

        * Drivers for sequential and threaded driving of chains
