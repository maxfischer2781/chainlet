Getting Started
===============

Most of :py:mod:`chainlet` should feel familiar if you are used to Python.
This guide covers the two key concepts you need to learn:

- Defining a ``chainlink`` to perform a single transformation
- Chaining several ``chainlink``s to perform multiple transformations

Defining a simple ``chainlink``
-------------------------------

A ``chainlink`` can be created by promoting a function using :py:func:`~chainlet.funclet`.
Using a :py:func:`~chainlet.funclet` is suitable whenever you can directly map input to output.

Simply decorate a regular function, which

- takes *at least* one positional argument ``value``.
- produces the desired result via ``return``.

.. code:: python

    from chainlet import funclet

    @funclet  # <== chainlet specific
    def multiply(value, by=4):
        """Square all input"""
        return value * by

Using your first ``chainlink``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By applying :py:func:`~chainlet.funclet`, we have created a new *type* of :py:term:`link`.
To use it, you must instantiate it, which allows you to fill in all parameters.

.. code:: python

    chain = multiply(3)
    chain = multiply(by=3)  # equivalent to the above

Note that ``value`` is automatically excluded:
You can use both positional and keyword parameters in a :py:func:`~chainlet.funclet`.

To get some actual output, you have to feed it input.
As with a generator, you can :py:meth:`~chainlet.ChainLink.send` individual values:

.. code:: python

    chain.send(1)  # -> 3
    chain.send(3)  # -> 9
    chain.send('a')  # -> 'aaa'

You can also bulk-process values by providing an iterable to :py:meth:`~chainlet.ChainLink.dispatch`.
This provides a lazily evaluated generator:

.. code:: python

    for result in chain.dispatch(range(5)):
        print(result) # prints 0, 3, 6, 9, 12

Dispatching is especially useful with :py:mod:`~chainlet.concurrency`, which computes results in parallel.

Chaining individual links
-------------------------

Any ``chainlink`` can be composed with others to form a chain.
This is equivalent to feeding the result of each ``chainlink`` to the next [#chaincompose]_.

.. code:: python

    chain = multiply(by=3) >> multiply(by=4)  # same as multiply(by=12)

A chain behaves the same as a single chainlink.
You can apply the same operations to send or dispatch input along a chain:

.. code:: python

    chain.send(1)  # -> 12
    chain.send(3)  # -> 36
    chain.send('a')  # -> 'aaaaaaaaaaaa'

.. [#chaincompose] Depending on the elements used, ``chainlet`` will not actually execute this.
                   It merely guarantees the same result.
