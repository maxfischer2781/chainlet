Chainlet Data Flow
==================

Chains created via :py:mod:`chainlet` have two operation modes [#mode]_:
pulling at the end of the chain, and pushing to the top of the chain.
The only difference is whether the chain is given an input, or produces it by itself.

.. code:: python

    chain = chainlet1 >> chainlet2 >> chainlet3
    print(next(chain))  # pull from chain
    chain.send('input')  # push to chain

Data cascades through chains:
output of each parent is passed to its children, which again provide output for their children.
At each step, an element may transform the data it receives.

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
Consequently, both operations are handled completely equivalently by *any* chainlet, even complex one.
Whether pulling, pushing or both is *sensible* depends on the element - it cannot be inferred from the interface.

Elements that work in pull mode can also be used in iteration.
For every iteration step, ``next(element)`` is called to produce a value.

.. code:: python

    for value in element:
        print(value)

Linear Chains
-------------

The simplest compound object is a linear chain, which is a flat sequence of elements.
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
This makes them a suitable replacement for generators in any way.

Pipeline Splitting
------------------

If a chain forks to multiple sub-chains, data is passed along each sub-chain separately.
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


.. note::

    To avoid unnecessary overhead, splitting chains **never** copy data for each pipeline.
    If an element changes a mutable data structure, it should explicitly create a copy.

.. [#mode] The data flow modes are designed to be as robust as possible.
           They can be overwritten if different behaviour is desired, for example
           to change data flow depending on intermittent values.

.. [#genprot] See the `Generator-Iterator Methods <https://docs.python.org/3/reference/expressions.html#generator-iterator-methods>`_.
