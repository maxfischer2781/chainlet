.. chainlet documentation master file, created by
   sphinx-quickstart on Wed Feb 22 14:45:32 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

chainlet - blocks for processing chains
=======================================

.. image:: https://travis-ci.org/maxfischer2781/chainlet.svg?branch=master
   :target: https://travis-ci.org/maxfischer2781/chainlet
   :alt: Build Status
.. image:: https://landscape.io/github/maxfischer2781/chainlet/master/landscape.svg?style=flat
   :target: https://landscape.io/github/maxfischer2781/chainlet/master
   :alt: Code Health
.. image:: https://codecov.io/gh/maxfischer2781/chainlet/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/maxfischer2781/chainlet
   :alt: Test Coverage
.. image:: https://readthedocs.org/projects/chainlet/badge/?version=latest
   :target: http://chainlet.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. toctree::
    :maxdepth: 1
    :caption: Documentation Topics Overview:

    source/grammar
    source/chains
    Module Index <source/api/modules>

The :py:mod:`chainlet` library lets you quickly build iterative processing sequences.
At its heart, it is built for chaining generators/coroutines, but supports arbitrary objects.
It offers an easy, readable way to link elements using a simple mini language:

.. code::

    chain = a >> b >> c >> d >> f

The same interface can be used to create chains that push data from the start downwards, or to pull from the end upwards.

.. code::

    push_chain = uppercase >> encode_r13 >> mark_of_insanity >> printer
    push_chain.send('uryyb jbeyq')  # outputs 'Hello World!!!'

    pull_chain = word_maker >> cleanup >> encode_r13 >> lowercase
    print(next(pull_chain))  # outputs 'uryyb jbeyq'

If you just want to plug together existing chainlets, have a look at the :doc:`source/grammar`.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
