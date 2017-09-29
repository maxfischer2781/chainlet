++++++++++++++++++
chainlet Changelog
++++++++++++++++++

v1.3.0
------

    **New Features**

        * The ``>>`` and ``<<`` operators use reflection precedence to if the left-hand-side element's Linker
          is a subclass of the right-hand-side Linker.

    **Major Changes**

        * Deprecated the use of external linkers in favour of operator+constructor.

        * Linking to chains ignores elements which are ``False`` in a boolean sense, e.g. an empty ``CompoundLink``.

    **Minor Changes**

        * ``CompoundLink`` objects are now considered boolean ``False``.

        * Added a neutral element for internal use.

    **Bug Fixes**

        * Correctly unwrapping return value for any ``Chain`` which does not ``fork``.

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
