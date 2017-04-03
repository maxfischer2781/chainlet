Chainlet Data Flow
==================

Chains created via :py:mod:`chainlet` have two operation modes:
pulling at the end of the chain, and pushing to the top of the chain.
As both modes return the result, the only difference is whether the chain is given an input.

.. code:: python

    chain = chainlet1 >> chainlet2 >> chainlet3
    print(next(chain))  # pull from chain
    chain.send('input')  # push to chain

Data cascades through chains:
output of each parent is passed to its children, which again provide output for their children.
At each step, an element may inspect, transform or replace the data it receives.

The data flow is thus dicated by several primitive steps:
Individual elements process data.
Linear chains pass data from element to element.
Forks and joins split or merge data to chains.

Single Element Processing
-------------------------

Each element, be it a single chainlet or chain of chainlets, implements the generator protocol [#genprot]_.
Most importantly, it allows to pull and push data from and to it:

* New data is *pulled from* an element using ``next(element)``.
  The element may produce a new data chunk and return it.

* Existing data is *pushed to* the element using ``element.send(data)``.
  The element may transform the data and return a result.

In accordance with the generator protocol, ``next(element)`` is equivalent to ``element.send(None)``.
Consequently, both operations are handled completely equivalently by *any* chainlet, even complex ones.
Whether pulling, pushing or both is *sensible* depends on the element - it cannot be inferred from the interface.

Elements that work in pull mode can also be used in iteration.
For every iteration step, ``next(element)`` is called to produce a value.

.. code:: python

    for value in element:
        print(value)

Both ``next(element)`` and ``element.send(None)`` form the *public* interface of an element.
They take care of unwinding chain complexities, such as multiple paths and skipping of values.
Custom elements should implement :py:meth:`chainlet.ChainLink.chainlet_send` to change how data is processed.

Linear Chains -- Processing Sequence
------------------------------------

The simplest compound object is a *linear chain*, which is a flat sequence of elements.
Data sent to the chain is transformed iteratively:
Input is passed to the first element, and its result to the second, and so on.
Once all elements have been traversed, the result is returned.

.. graphviz::

    digraph g {
        graph [rankdir=LR]
        compound=true;
        subgraph cluster_c {
            ranksep=0;
            style=rounded;
            c1 -> c2 -> c3 -> c4 [style=dotted, arrowhead="veevee"];
            c1, c2, c3, c4 [shape=box, style=rounded, label=""];
            c1 -> c1 [label=send];
            c2 -> c2 [label=send];
            c3 -> c3 [label=send];
            c4 -> c4 [label=send];
        }
        in, out [style=invis]
        in -> c1 [label=send, lhead=cluster_c]
        c4 -> out [label=return, ltail=cluster_c]
    }

Linear chains are special in that they always take a single input and return a single output.
Even when joining linear chains, the result is always another linear chain with the same features.
This makes them a suitable replacement for generators in any way.

Parallel Chains -- Processing Splitting
---------------------------------------

Processing of data can be split to multiple sub-chains in a *parallel chain*, a concurrent sequence of chains.
When a chain forks to multiple sub-chains, data is passed along each sub-chain separately.
In specific, the return value of the element *before* the fork is passed to each sub-chain.

.. graphviz::

    digraph g {
        graph [rankdir=LR]
        compound=true;
        a1 [shape=box, style=rounded, label=""];
        a1 -> a1 [label=send];
        subgraph cluster_b {
            ranksep=0;
            style=rounded;
            b1 -> b2 -> b3 [style=dotted, arrowhead="veevee"];
            b1, b2 [shape=box, style=rounded, label=""];
            b3 [style=invis]
            b1 -> b1 [label=send];
            b2 -> b2 [label=send];
        }
        subgraph cluster_c {
            ranksep=0;
            style=rounded;
            c1 -> c2 -> c3 [style=dotted, arrowhead="veevee"];
            c1, c2 [shape=box, style=rounded, label=""];
            c3 [style=invis]
            c1 -> c1 [label=send];
            c2 -> c2 [label=send];
        }
        in, out [style=invis]
        in -> a1 [label=send]
        a1 -> c1 [style=dotted, arrowhead="veevee", lhead=cluster_c]
        a1 -> b1 [style=dotted, arrowhead="veevee", lhead=cluster_b]
        b3 -> out [label=return, ltail=cluster_b, constraint=false]
        c3 -> out [label=return, ltail=cluster_c]
    }

In contrast to linear chains, parallel chains always return multiple values at once:
their return value is an iterable over *all* values returned by subchains.
This holds true even if just one subchain returns anything.

.. note::

    To avoid unnecessary overhead, parallel chains **never** copy data for each pipeline.
    If an element changes a mutable data structure, it should explicitly create a copy.
    Otherwise, peers may see the changes as well.

Meta Chains -- Sequences and Forking
------------------------------------

Combinations of linear and parallel chains automatically create a meta chain.
This compound element is aware of :py:mod:`chainlet`\ 's capability to conditionally join and fork data for processing.
Linear and parallel chains implement a specific combination of these feature;
custom elements can freely provide other combinations.

Both linear and parallel chains do not *join* - they take on every data chunk individually.
A linear chain always produces one output data chunk for every input data chunk.
Instead, a parallel chain produces multiple output chunks for each input chunk.

Each output chunk is passed individually to linear and parallel chains.
This means that parallel chains fork the data flow.

A chain such as the following:

.. code:: python

    name('a') >> name('b') >> (name('c'), name('d') >> name('e')) >> name('f')

Creates a meta chain that connects ``f`` to *both* ``c`` and ``e``.
For the data flow, ``f`` is visited *separately* for the results from ``c`` and ``e``.

.. graphviz::

    digraph graphname {
        graph [rankdir=LR]
        a -> b
        b -> c -> f1
        b -> d -> e -> f2
        f1, f2 [label=f]
    }

.. note::

    Stay aware of object identity when linking, especially if objects carry state.
    There is a difference in connecting nodes to the same objects,
    and connecting nodes to equivalent but separate objects.

Generic Join and Fork
^^^^^^^^^^^^^^^^^^^^^

The iteration through meta-chains is agnostic towards the type of elements:
Each element explicitly specifies whether it joins the data flow or forks it.
This is signaled via the attributes ``element.chain_join == True`` and ``element.chain_fork == True``, respectively.

A *joining* element receives an iterable providing all data chunks produced by its preceding element.
A *forking* element produces an iterable providing all applicable data chunks.
These features can be combined to have an element joining incoming chunks but forking to multiple outgoing chunks.

============ =========== ==========
 Fork/\Join     False       True
============ =========== ==========
 **False**      1->1        n->1
 **True**       1->m        n->m
============ =========== ==========

Linear chains are examples for a 1 -> 1 data flow, while parallel chains implement a 1 -> m data flow.

.. [#genprot] See the `Generator-Iterator Methods <https://docs.python.org/3/reference/expressions.html#generator-iterator-methods>`_.
