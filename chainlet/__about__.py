"""
++++++++
chainlet
++++++++

The ``chainlet`` library offers a lightweight model to create processing pipelines from
generators, coroutines, functions and custom objects.
Instead of requiring you to nest code or insert hooks, ``chainlet`` offers a concise, intuitive binding syntax:

.. code:: python

    # regular nested generators
    csv_writer(flatten(xml_reader(path='data.xml'), join='.'.join), path='data.csv')
    # chainlet pipeline
    xml_reader(path='data.xml') >> flatten(join='.'.join) >> csv_writer(path='data.csv')

Processing pipelines created with ``chainlet`` are an extension of generators and functions:
they can be iterated to pull results, called to push input or even used to get/fetch a stream of data.
The bindings of ``chainlet`` allow to compose complex processing chains from simple building blocks.

Creating new chainlets is simple, requiring you only to define the processing of data.
It is usually sufficient to use regular functions, generators or coroutines, and let ``chainlet`` handle the rest:

.. code:: python

    @chainlet.genlet
    def moving_average(window_size=8):
        buffer = collections.deque([(yield)], maxlen=window_size)
        while True:
            new_value = yield(sum(buffer)/len(buffer))
            buffer.append(new_value)

Features
========

We have designed ``chainlet`` to be a simple, intuitive library:

* Modularize your code with small, independent processing blocks.
* Intuitively compose processing chains from individual elements.
* Automatically integrate functions, generators and coroutines in your chains.
* Extend your processing capabilities with complex chains that fork and join as needed.

Under the hood, ``chainlet`` merges iterator and functional paradigms in a minimal fashion to stay lightweight.

* Fully compliant with the Generator interface to integrate with existing code.
* Implicit tail recursion elimination for linear pipelines, and premature end of chain traversal.
* Push and pull chains iteratively, continuously, or even asynchronously.
* Simple interface to extend or supersede pipeline traversal and processing.

At its heart ``chainlet`` strives to be as Pythonic as possible:
You write python, and you get python.
No trampolines, callbacks, stacks, handlers, ...

We take care of the ugly bits so you do not have to.

Looking to get started?
Check out our docs: |docs|

Found an issue or have suggestions?
Head straight to our issue tracker: |issues|

Status
======

The ``chainlet`` library originates from our need for accessible concurrency in data center administration.
We have since adopted the library in a production environment for a number of use cases:
* Modular monitoring suite using stream based data extraction and translation.
* Management scripts for concurrent operations on many files at once.

Both the grammar and general interfaces for processing chains, trees and graphs are stable.
Ongoing work is mainly focused on streamlining the parallel iteration interface.
A major focus is to add automatic concurrency, asynchronicity and parallelism.
Our target is an opt-in approach to features from functional programming and static optimisations.

Recent Changes
--------------

v1.3.0

    Thread-based concurrent traversal, improved single- and multi-stream distinction.

v1.2.0

    Synchronous concurrent traversal, chain slicing and merging, fully featured function and generator wrappers

v1.1.0

    Added chainlet versions of builtins and protocol interfaces

v1.0.0

    Initial release

.. |docs| image:: https://readthedocs.org/projects/chainlet/badge/?version=latest
   :target: http://chainlet.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. |issues| image:: https://img.shields.io/github/issues/maxfischer2781/chainlet.svg
   :target: https://github.com/maxfischer2781/chainlet/issues
   :alt: Open Issues
"""

__title__ = 'chainlet'
__summary__ = 'Framework for linking generators/iterators to processing chains, trees and graphs'
__url__ = 'https://github.com/maxfischer2781/chainlet'

__version__ = '1.3.1'
__author__ = 'Max Fischer'
__email__ = 'maxfischer2781@gmail.com'
__copyright__ = '2016 - 2018 %s' % __author__
