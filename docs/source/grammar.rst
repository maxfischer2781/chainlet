Chainlet Mini Language
======================

Linking chainlets can be done using a simple grammar based on ``>>`` and ``<<`` operators [#linkop]_.
These are used to create a directed connection between nodes.
You can even include forks and joins easily.

.. code:: python

    a >> b >> (c >> d, e >> f) >> g

This example links elements to form a directed graph:

.. graphviz::

    digraph graphname {
        graph [rankdir=LR, bgcolor="transparent"]
        a -> b
        b -> c -> d
        b -> e -> f
        f -> g
        d -> g
    }

Single Link - Pairs
-------------------

The most fundamental operation is the directed link between parent and child.
The direction of the link is defined by the direction of the operator.

.. code:: python

    parent >> child
    child << parent

This creates and returns a :term:`chain` linking parent and child.

Chained Link - Flat Chains
--------------------------

A pair can be linked again to extend the :term:`chain`.
Adding a parent to a :term:`chain` links it to the initial parent, while a new child is linked to the initial child.
Note that :term:`chains <chain>` preserve only *logical*, but not *syntactic* orientation:
a ``>>``-linked chain can be extended via ``<<`` and vice versa.

.. code:: python

    chain_a = parent >> child
    chain_b = chain_a << parent2
    chain_c = chain_b >> child2

Links can be chained directly; there is no need to store intermediate subchains if you do not use them.

.. code:: python

    chain_c = parent2 >> parent >> child >> child2

The above examples create the same underlying links between objects.

Chains represent only the link they have been created with.
Subsequent changes and links are not propagated.
Each of the objects ``chain_a``, ``chain_b`` and ``chain_c`` represent another part of the chain.

.. code:: python

    chain_d = parent2 >> parent >> child >> child2
    #                    \-- chain_a --/
    #         \------------- chain_b --/
    #         \------------- chain_c ------------/

:note: Linking automatically flattens :term:`chains <chain>` to create the longest possible :term:`chain`.
       This preserves equality but not identity of sub-chains.
       This is similar to using the ``+`` operator on a :py:class:`list`.

Links follow standard operation order, i.e. they are evaluated from left to right.
This can be confusing when mixing ``>>`` and ``<<`` in a single chain.
The following chain is equivalent to ``chain_c``.

.. code:: python

    chain_d = child << parent >> child2 << parent2

:danger: Mixing ``<<`` and ``>>`` is generally a bad idea.
         The use of ``>>`` is suggested, as it conforms to public and private interface implementations.

Forking and Joining Links
-------------------------

Any :term:`chainlink` can have an arbitrary number of parents and children.
This allows :term:`forking` and :term:`joining` the :term:`data stream`.
Simply use a :py:func:`tuple`, :py:func:`list` or :py:func:`set` as child or parent [#typefork]_.

.. code:: python

    fork_chain = a >> (b >> c, d)
    join_chain = (a, b >> c) >> d

The resulting chains are actually fully featured, directed graphs.

.. graphviz::

    digraph graphname {
        graph [rankdir=LR, bgcolor="transparent"]
        a -> d
        b -> c -> d
    }

.. graphviz::

    digraph graphname {
        graph [rankdir=LR, bgcolor="transparent"]
        a -> b -> c
        a -> d
    }

Links are agnostic with regard to *how* a group of elements is created.
This allows you to use comprehensions and calls to generate forks and joins dynamically.

.. code:: python

    a >> {node(idx) for idx in range(3)}

.. graphviz::

    digraph graphname {
        graph [rankdir=LR, bgcolor="transparent"]
        a -> "node(1)"
        a -> "node(2)"
        a -> "node(3)"
    }

.. [#linkop] These are the ``__rshift__`` and ``__lshift__`` operators.
             Overwriting these operators on objects changes their linking behaviour.

.. [#typefork] There may be additional implications to using different types in the future.
