Of Generators and Chainlets
===========================

The behaviour of all basic building blocks of :py:mod:`chainlet` is modeled after generators.
In turn, generators integrate seamlessly into chains.

Generators as data providers
----------------------------

As with functions, a ``chainlink`` can be created by promoting a *generator* using :py:func:`~chainlet.genlet`.
Using a :py:func:`~chainlet.genlet` is suitable when you need to preserve state between steps.

Simply decorate a regular generator, which

- produces the desired results via ``yield``.

.. code:: python

    >>> from chainlet import genlet
    >>> import random
    >>>
    >>> @genlet(prime=False)  # <= do not prime producing generators!
    ... def pseudo_random_trigger(chance_slope=0.1):          # (1)
    ...     misses = 1  # number of times no hit was triggered
    ...     while True:                                         # (2)
    ...         if misses * chance_slope > random.random():
    ...             yield True                                  # (3)
    ...             misses = 1
    ...         else:
    ...             yield False                                 # (3)
    ...             misses += 1

The core of a :py:func:`~chainlet.genlet` is a regular generator:
it requires no additional argument to receive data (1),
can loop and repeat arbitrarily (2),
and provides multiple results via ``yield`` (3).
A :py:func:`~chainlet.genlet` can also safely hold persistent resources -
for example an open file in a ``with`` context.

Interlude: If it  quacks like a generator...
--------------------------------------------

Our new :py:func:`~chainlet.genlet` behaves practically the same as a regular generator.
To use it, you must instantiate it, which allows you to fill in all parameters.

.. code:: python

    >>> chain = pseudo_random_trigger()  # use default ``chance_slope=0.1``
    >>> chain = pseudo_random_trigger(0.2)

The :py:func:`~chainlet.genlet` is fully compliant with the generator protocl.
In other words, you can still use your :py:func:`~chainlet.genlet` as if it were just a generator:

    >>> for is_hit in pseudo_random_trigger(0.2):
    ...     print('Hit!' if is_hit else 'Miss')
    ...     if is_hit:
    ...         break
