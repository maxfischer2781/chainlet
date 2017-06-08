#!/usr/bin/env python
import os
import sys
from setuptools import setup, find_packages

repo_base_dir = os.path.abspath(os.path.dirname(__file__))
# pull in the packages metadata
package_about = {}
with open(os.path.join(repo_base_dir, "chainlet", "__about__.py")) as about_file:
    exec(about_file.read(), package_about)

long_description = """
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
* Intuitively compose processing pipelines from individual elements.
* Automatically integrate functions, generators and coroutines in your pipelines.
* Extend your processing with complex pipelines that fork and join as needed.

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

We use the ``chainlet`` library in a production environment.
It serves to configure and drive stream based data extraction and translation for monitoring.
Both the grammar and general interfaces for processing chains, trees and graphs are stable.

Ongoing work is mainly focused on the iteration interface.
We plan to add automatic concurrency, asynchronicity and parallelism.
Our target is an opt-in approach to features from functional programming and static optimisations.

Recent Changes
--------------

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

if __name__ == '__main__':
    setup(
        name=package_about['__title__'],
        version=package_about['__version__'],
        description=package_about['__summary__'],
        long_description=long_description.strip(),
        author=package_about['__author__'],
        author_email=package_about['__email__'],
        url=package_about['__url__'],
        packages=find_packages(),
        # dependencies
        install_requires=[],
        # metadata for package seach
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Topic :: System :: Monitoring',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.4',
            'Programming Language :: Python :: 2.5',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],
        keywords='chaining generator coroutine stream pipeline chain bind tree graph',
        # unit tests
        test_suite='chainlet_unittests',
        # use unittest backport to have subTest etc.
        tests_require=['unittest2'] if sys.version_info < (3, 4) else [],
    )
