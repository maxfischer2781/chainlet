Traversal Synchronicity
=======================

By default, :py:mod:`chainlet` operates in synchronous mode:
there is a fixed ordering by which elements are traversed.
Both :term:`chains <chain>` and :term:`bundles <bundle>` are traversed one element at a time.

However, :py:mod:`chainlet` also allows for asynchronous mode:
any elements which do not explicitly depend on each other can be traversed in parallel.

Synchronous Traversal
---------------------

Synchronous mode follows the order of elements in :term:`chains <chain>` and :term:`bundles <bundle>` [#setorder]_.
Consider the following setup:

.. code::

     a >> b >> [c >> d, e >> f] >> g >> h

This is broken down into four :term:`chains <chain>`, two of which are part of a :term:`bundle`.
Every :term:`chain` is simply traversed according to its ordering - ``a`` before ``b``, ``c`` before ``d`` and so on.

The :term:`bundle` implicitly :term:`forks <fork>` the data stream to *both* ``c`` and ``e``.
This :term:`fork` is traversed in definition order, in this case ``c >> d`` before ``e >> f``.

Synchronous traversal only guarantees consistency in each stream - but not about the ordering of
:term:`chainlinks <chainlink>` *across* the forked data stream.
That is, the final :term:`sequence` ``g >> h`` is always traversed after its respective source :term:`chain` ``c >> d`` or ``e >> f``.
However, the *first* traversal of ``g >> h`` may or may not occur before ``e >> f``, the *second* element of the :term:`bundle`.

.. graphviz::

    digraph graphname {
        graph [rankdir=LR, splines=lines, bgcolor="transparent"]
        a -> b
        b -> c -> d -> g [color=red]
        b -> e -> f -> g [color=blue]
        g -> h [color=cyan]
        g -> h [color=magenta]
    }

In other words, the traversal always picks black over red, red over blue, red over magenta and blue over cyan.
This implies that magenta is traversed before cyan.
However, it does *not* imply an ordering between blue and magenta.

Finally, synchronous traversal always respects the ordering of complete traversals.
For every input, the *entire* :term:`chain`

.. [#setorder] In some cases, such as bundles from a :py:class:`set`, traversal order may be arbitrary.
               However, it is still fixed and stable.
