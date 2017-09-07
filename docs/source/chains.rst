Chainlet Data Flow
==================

Chains created via :py:mod:`chainlet` have two operation modes:
pulling at the end of the chain, and pushing to the top of the chain.
As both modes return the result, the only difference is whether the chain is given an input.

.. code:: python

    chain = chainlet1 >> chainlet2 >> chainlet3
    print('pull', next(chain))
    print('push', chain.send('input'))

Data cascades through chains:
output of each parent is passed to its children, which again provide output for their children.
At each step, an element may inspect, transform or replace the data it receives.

The data flow is thus dictated by several primitive steps:
Each individual :term:`chainlink` processes data.
Compound :term:`chains <chain>` pass data from element to element.
At :term:`forks <fork>` and :term:`joins <join>`, data is split or merged to further elements.

Single Element Processing
-------------------------

Each element, be it a primitive :term:`chainlet` or :term:`compound link`, implements the generator protocol [#genprot]_.
Most importantly, it allows to pull and push data from and to it:

* New data is *pulled from* an element using ``next(element)``.
  The element may produce a new data chunk and return it.

* Existing data is *pushed to* the element using ``element.send(data)``.
  The element may transform the data and return the result.

In accordance with the generator protocol, ``next(element)`` is equivalent to ``element.send(None)``.
Consequently, both operations are handled completely equivalently by *any* :term:`chainlink`, even complex ones.
Whether pulling, pushing or both is *sensible* depends on the use case -
for example, it cannot be inferred from the interface whether a :term:`chainlink` can operate without input.

Elements that work in pull mode can also be used in iteration.
For every iteration step, the equivalent of ``next(element)`` is called to produce a value.

.. code:: python

    for value in chain:
        print(value)

Both ``next(element)`` and ``element.send(None)`` form the *public* interface of an element.
They take care of unwinding chain complexities, such as multiple paths and skipping of values.
Custom :term:`chainlinks <chainlink>` should implement :py:meth:`~chainlet.ChainLink.chainlet_send` to change how data is processed.

Linear Flow -- Flat Chains
--------------------------

The simplest compound object is a :term:`flat chain`, which is a sequence of :term:`chainlinks <chainlink>`.
Data sent to the chain is transformed incrementally:
Input is passed to the first element, and its result to the second, and so on.
Once all elements have been traversed, the result is returned.

.. graphviz::

    digraph g {
        graph [rankdir=LR, bgcolor="transparent"]
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

Linear chains are special in that they always take a single input :term:`chunk` and return a single output :term:`chunk`.
Even when :term:`linking` flat chains, the result is flat linear chain with the same features.
This makes them a suitable replacement for generators in any way.

Concurrent Flow -- Chain Bundles
--------------------------------

Processing of data can be split to multiple sub-chains in a :term:`bundle`, a group of concurrent :term:`chainlinks <chainlink>`.
When a chain :term:`branches <branch>` to multiple sub-chains, data flows along each sub-chain independently.
In specific, the return value of the element *before* the :term:`branch` is passed to *each* sub-chain individually.

.. graphviz::

    digraph g {
        graph [rankdir=LR, bgcolor="transparent"]
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

In contrast to a :term:`flat chain`, a :term:`bundle` always returns multiple :term:`chunks <chunk>` at once:
its return value is an iterable over *all* :term:`chunks <chunk>` returned by sub-chains.
This holds true even if just one subchain returns anything.

.. note::

    To avoid unnecessary overhead, parallel chains **never** copy data for each pipeline.
    If an element changes a mutable data structure, it should explicitly create a copy.
    Otherwise, peers may see the changes as well.

Compound Flow - Generic Chains
------------------------------

Combinations of :term:`flat chains <flat chain>` and :term:`bundles <bundles>` automatically create a generic :term:`chain`.
This :term:`compound link` is aware of :term:`joining` and :term:`forking` of the data flow for processing.
:term:`Flat chains <flat chain>` and :term:`bundles <bundles>` implement a specific combination of these feature;
custom elements can freely provide other combinations.

Both :term:`flat chains <flat chain>` and :term:`bundles <bundles>` do not :term:`join`
- they process each :term:`data chunk` individually.
A :term:`flat chain` always produces one output :term:`chunk` for every input :term:`chunk`.
In contrast, a :term:`bundle` produces multiple output :term:`chunks <chunk>` for each input :term:`chunk`.

A statement such as the following:

.. code:: python

    name('a') >> name('b') >> (name('c'), name('d') >> name('e')) >> name('f')

Creates a :term:`chain` that :term:`branches <branch>` from ``f`` to both ``c`` and ``d >> e``.
For the data flow, ``f`` is visited *separately* for the results from ``c`` and ``e``.

.. graphviz::

    digraph graphname {
        graph [rankdir=LR, bgcolor="transparent"]
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

The traversal through a :term:`chain` is agnostic towards the type of elements:
Each element explicitly specifies whether it joins the data flow or forks it.
This is signaled via the attributes ``element.chain_join`` and ``element.chain_fork``, respectively.

A :term:`joining` element *receives* an iterable providing all data chunks produced by its preceding element.
A :term:`forking` element *produces* an iterable providing all valid data chunks.
These features can be combined to have an element :term:`join` the incoming data flow and
:term:`fork` it to another number of outgoing :term:`chunks <chunk>`.

============ =========== ==========
 Fork/\Join     False       True
============ =========== ==========
 **False**      1->1        n->1
 **True**       1->m        n->m
============ =========== ==========

A :term:`flat chain` is an example for a 1 -> 1 data flow, while a :term:`bundle` implements a 1 -> m data flow.
A generic :term:`chain` is adjusted depending on its elements.

.. [#genprot] See the `Generator-Iterator Methods <https://docs.python.org/3/reference/expressions.html#generator-iterator-methods>`_.
