.. chainlet documentation master file, created by
   sphinx-quickstart on Wed Feb 22 14:45:32 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

chainlet - blocks for processing chains
=======================================

.. image:: https://readthedocs.org/projects/chainlet/badge/?version=latest
    :target: http://chainlet.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/chainlet.svg
    :alt: Available on PyPI
    :target: https://pypi.python.org/pypi/chainlet/

.. image:: https://img.shields.io/github/license/maxfischer2781/chainlet.svg
    :alt: License
    :target: https://github.com/maxfischer2781/chainlet/blob/master/LICENSE

.. image:: https://img.shields.io/github/commits-since/maxfischer2781/chainlet/v1.3.1.svg
    :alt: Repository
    :target: https://github.com/maxfischer2781/chainlet/tree/master

.. image:: https://travis-ci.org/maxfischer2781/chainlet.svg?branch=master
    :target: https://travis-ci.org/maxfischer2781/chainlet
    :alt: Build Status

.. image:: https://landscape.io/github/maxfischer2781/chainlet/master/landscape.svg?style=flat
    :target: https://landscape.io/github/maxfischer2781/chainlet/master
    :alt: Code Health

.. image:: https://codecov.io/gh/maxfischer2781/chainlet/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/maxfischer2781/chainlet
    :alt: Test Coverage


.. toctree::
    :maxdepth: 2
    :caption: Documentation Topics

    source/tutorial_main
    source/spec_main
    source/glossary

.. toctree::
    :maxdepth: 1
    :caption: Library Overview

    Basic Building Blocks <source/api/chainlet>
    Builtin and Protocol Wrappers <source/api/chainlet.protolink>
    Changelog <source/changelog>
    Module Index <source/api/modules>

A Short Introduction to ``chainlet``
------------------------------------

The :py:mod:`chainlet` library lets you quickly build iterative processing sequences.
At its heart, it is built for chaining generators/coroutines, but supports arbitrary objects.
It offers an easy, readable way to link elements using a concise mini language:

.. code:: python

    data_chain = read('data.txt') >> filterlet(preserve=bool) >> convert(apply=ast.literal_eval)
    for element in chain:
        print(element)

The same interface can be used to create chains that push data from the start downwards, or to pull from the end upwards.

.. code:: python

    push_chain = uppercase >> encode_r13 >> mark_of_insanity >> printer
    push_chain.send('uryyb jbeyq')  # outputs 'Hello World!!!'

    pull_chain = word_maker >> cleanup >> encode_r13 >> lowercase
    print(next(pull_chain))  # outputs 'uryyb jbeyq'

Creating new elements is intuitive and simple, as :py:mod:`chainlet` handles all the gluing and binding for you.
Most functionality can be created from regular functions, generators and coroutines:

.. code:: python

    @chainlet.genlet
    def moving_average(window_size=8):
        buffer = collections.deque([(yield)], maxlen=window_size)
        while True:
            new_value = yield(sum(buffer)/len(buffer))
            buffer.append(new_value)

Quick Overview to Get You Started
---------------------------------

If you are new to ``chainlet``, check out the :doc:`tutorials and guides <source/tutorial_main>`.
To just plug together existing chainlets, have a look at the :doc:`source/spec/grammar`.
To port existing Python code, the :doc:`source/api/chainlet.protolink` provides simple helpers and equivalents of builtins.

Writing new chainlets is easily done with generators, coroutines and functions, promoted as :py:func:`~chainlet.genlet` or :py:func:`~chainlet.funclet`.
A :py:func:`chainlet.genlet` is best when state must be preserved between calls.
A :py:func:`chainlet.funclet` allows resuming even after exceptions.

Advanced chainlets are best implemented as a subclass of :py:class:`chainlet.ChainLink`.
Overwrite instantiation and :py:meth:`~chainlet.ChainLink.chainlet_send` to change their behaviour [#wrapperdetail]_.

Contributing and Feedback
-------------------------

The project is hosted on `github <https://github.com/maxfischer2781/chainlet>`_.
If you have issues or suggestion, check the issue tracker: |issues|
For direct contributions, feel free to fork the `development branch <https://github.com/maxfischer2781/chainlet/tree/devel>`_ and open a pull request.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

----------

.. [#wrapperdetail] Both :py:func:`chainlet.genlet` and :py:func:`chainlet.funclet` implement instantiation and :py:meth:`~chainlet.ChainLink.chainlet_send` for the most common use case.
                    They simply bind their callables on instantitation, then call them on :py:meth:`~chainlet.ChainLink.chainlet_send`.

.. |issues| image:: https://img.shields.io/github/issues-raw/maxfischer2781/chainlet.svg
   :target: https://github.com/maxfischer2781/chainlet/issues
   :alt: Open Issues

Documentation built from chainlet |version| at |today|.
