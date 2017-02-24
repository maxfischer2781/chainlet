Chainlet Data Flow
==================

Chains created via :py:mod:`chainlet` have two operation modes [#mode]_:
pulling at the end of the chain, and pushing to the top of the chain.
The major difference is whether the chain is given an input, or produces output.

.. code::

    chain = chainlet1 >> chainlet2 >> chainlet3

Pulling Chains
--------------

When pulling data from chains, they act like generators and iterators.
Simply call ``next`` on the chain to receive a value.
It is also possible to use them like iterators in loops and similar constructs.

.. code::

    value = next(chain)
    print(value)
    for value in chain:
        print(value)

When pulling on a chain, each child in turn pulls from its parent until the end of the chain.
On returning values, each node processes the value from its parent before returning the result to its child.

.. graphviz::

    digraph g {
        graph [rankdir=LR]
        chainlet1 -> chainlet2 -> chainlet3 [arrowhead=veevee]
        chainlet3 -> consumer [arrowhead=none,style=dotted]
        consumer -> chainlet3 -> chainlet2 -> chainlet1 [label=next,constraint=false]
    }


.. [#mode] The data flow modes are designed to be as robust as possible.
           They can be overwritten if different behaviour is desired, for example
           to pull from many parents at once.
