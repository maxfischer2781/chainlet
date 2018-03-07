Getting Started
===============

Most of :py:mod:`chainlet` should feel familiar if you are used to Python.
This guide covers the two key concepts you need to learn:

- Defining a ``chainlink`` to perform a single transformation
- Chaining several ``chainlink``\ s to perform multiple transformations

Defining a simple ``chainlink``
-------------------------------

A simple way to create a ``chainlink`` is to promote a function using :py:func:`~chainlet.funclet`.
Using a :py:func:`~chainlet.funclet` is suitable whenever you can directly map input to output.

Simply decorate a regular function, which

- takes *at least* one positional argument ``value``, and
- produces the desired result via ``return``.

.. code:: python

    >>> from chainlet import funclet
    >>>
    >>> @funclet  # <== chainlet specific
    ... def multiply(value, by=4):
    ...    """Multiply all input"""
    ...    return value * by

There is practically no restriction by :py:mod:`chainlet` on what the wrapped function can do.
While it has its uses, it is generally good practice to avoid changing global state, though.

Interlude: Using your first ``chainlink``
-----------------------------------------

By applying :py:func:`~chainlet.funclet`, we have created a new *type* of :py:term:`link`.
To use it, you must instantiate it, which allows you to fill in all parameters.

.. code:: python

    >>> chain = multiply()  # use default `by=4`
    >>> chain = multiply(3)
    >>> chain = multiply(by=3)  # equivalent to the above

Note that ``value`` is automatically excluded:
You can use both positional and keyword parameters in a :py:func:`~chainlet.funclet`.

To get some actual output, you have to feed it input.
As with a generator, you can :py:meth:`~chainlet.ChainLink.send` individual values:

.. code:: python

    >>> chain.send(1)
    3
    >>> chain.send(3)
    9
    >>> chain.send('a')
    'aaa'

You can also bulk-process values by providing an iterable to :py:meth:`~chainlet.ChainLink.dispatch`.
This provides a lazily evaluated generator:

.. code:: python

    for result in chain.dispatch(range(5)):
        print(result) # prints 0, 3, 6, 9, 12

Dispatching is especially useful with :py:mod:`chainlet.concurrency`, which computes results in parallel.

Chaining individual links
-------------------------

Any ``chainlink`` can be composed with others to form a chain.
This is equivalent to feeding the result of each ``chainlink`` to the next [#chaincompose]_.

.. code:: python

    >>> chain_by12 = multiply(by=3) >> multiply(by=4)  # same result as `multiply(by=12)`

A chain can be used the same way as a single chainlink.
You can apply the same operations to send or dispatch input along a chain:

.. code:: python

    >>> chain_by12.send(1)
    12
    >>> chain_by12.send(3)
    36
    >>> chain_by12.send('a')
    'aaaaaaaaaaaa'

Notably, chains can also be chained with other chains and chainlinks.
This creates a new chain, containing the individual links of each:

.. code:: python

    >>> chain_by24 = chain_by12 >> multiply(by=2)  # same as multiply(by=3) >> multiply(by=4) >> multiply(by=2)
    >>> list(chain_by24.dispatch(range(5)))
    [0, 24, 48, 72, 96]

Epilogue: Pulling your chain
----------------------------

You can not just *push* input to a ``chainlet``, but also pull from it.
This requires a ``chainlink`` that returns data when receiving ``value=None`` [#noneproduce]_:

.. code:: python

    >>> import random
    >>>
    >>> @funclet
    ... def generate(value, maximum=4):
    ...    """Generate values"""
    ...    if value is None:  # indicator that a new value is desired
    ...        return random.random() * maximum
    ...    return min(value, maximum)  # chainlets may provide both transformation and generation

Such a producer can be linked into a chain the same way as other elements.
The resulting chain will produce values by itself if you ``send(None)`` to it:

.. code:: python

    >>> rand24 = generate(maximum=1) >> chain_by24
    >>> rand24.send(1)  # use explicit starting value
    24
    >>> rand24.send(None)  # use generated starting value
    12.013380549968177

On top of the explicit ``send(None)``, such a chain also supports regular iteration [#noneproduce]_.
You can ``iter`` over its values, and get the ``next`` value:

.. code:: python

    >>> next(rand24)
    3.6175271892905103
    >>> for count, result in enumerate(rand24):
    ...     print(count, ':', result)
    ...     if result > 12:
    ...        break
    0 : 10.786272495589447
    1 : 23.653323415316734

.. [#chaincompose] Depending on the elements used, ``chainlet`` will not actually execute this.
                   It merely provides the same result.

.. [#noneproduce] This replicates the generator interface, where ``next(gen)`` is equivalent to ``gen.send(None)``.
                  See the `Generator-Iterator Methods <https://docs.python.org/3/reference/expressions.html#generator-iterator-methods>`_.
