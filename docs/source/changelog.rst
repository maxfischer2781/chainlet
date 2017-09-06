++++++++++++++++++
chainlet Changelog
++++++++++++++++++

v1.2.0a
-------

    **New Features**

        * Decorator/Wrapper versions of ``FunctionLink`` and ``GeneratorLink`` are proper subclasses of their class.
          This allows setting attributes and inspection.
          Previously, they were factory functions.

        * Instances of ``FunctionLink`` can be copied and pickled.

        * Instances of ``GeneratorLink`` can be copied and pickled.

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
