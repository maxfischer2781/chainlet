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
        graph [rankdir=LR]
        a -> b
        b -> c -> d
        b -> e -> f
        f -> g
        d -> g
    }

Single Link
-----------

The most fundamental operation is the directed link between parent and child.
The direction of the link is defined by the operator.

.. code:: python

    parent >> child
    child << parent

This creates and returns a chain linking parent and child.

Chained Link
------------

A chain can be linked again to extend the chain.
Adding a parent to a chain links it to the initial parent, while a new child is linked to the initial child.
Chains do not preserve syntactic orientation, so a ``>>``-linked chain can be linked via ``<<`` and vice versa.

.. code:: python

    chain_a = parent >> child
    chain_b = chain_a << parent2
    chain_c = chain_b >> child2

Links can be chained directly, so there is no need to store intermediate subchains.

.. code:: python

    chain_c = parent2 >> parent >> child >> child2

The above examples create the same underlying links between objects.

Chains represent only the link they have been created with.
Subsequent changes and links are not propagated.
Each of the objects ``chain_a``, ``chain_b`` and ``chain_c`` represent another part of the chain.

.. code::

               /-- chain_a --\
    /------------- chain_b --\
    /------------- chain_c ------------\
    parent2 >> parent >> child >> child2

Links follow standard operation order, i.e. they are evaluated from left to right.
This can be confusing when mixing ``>>`` and ``<<`` in a single chain.
The following chain is equivalent to ``chain_c``.

.. code::

    chain_d = child << parent >> child2 << parent2

Forking and Joining Links
-------------------------

Any node can have an arbitrary number of parents and children.
This allows forking and joining elements.
Simply use a :py:func:`tuple`, :py:func:`list` or :py:func:`set` as child or parent.

.. code::

    chain = a >> (b >> c, d)



.. [#linkop] These are the ``__rshift__`` and ``__lshift__`` operators.
             Overwriting these operators on objects changes their linking behaviour.
