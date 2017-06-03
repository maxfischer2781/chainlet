# Chainlet

[![Documentation Status](https://readthedocs.org/projects/chainlet/badge/?version=latest)](http://chainlet.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/maxfischer2781/chainlet.svg?branch=master)](https://travis-ci.org/maxfischer2781/chainlet)
[![Code Health](https://landscape.io/github/maxfischer2781/chainlet/master/landscape.svg?style=flat)](https://landscape.io/github/maxfischer2781/chainlet/master)
[![codecov](https://codecov.io/gh/maxfischer2781/chainlet/branch/master/graph/badge.svg)](https://codecov.io/gh/maxfischer2781/chainlet)

Framework for linking generator/iterators to create processing chains and pipelines.
With its operator based syntax, it is easy to create complex sequences from simple building blocks.
Chainlets are suitable for incremental, iterative and stream processing and beyond.

## Simplistic Chains with Chainlets

Consider the following use case:
Read data from an XML, flatten it, then write to a csv.
This can be expressed with a chain of generators:

    csv_writer(flatten(xml_reader(path='data.xml'), join='.'.join), path='data.csv')

When written using chainlets, generator sequence and arguments are much easier to read.
The chainlets are joined using the `>>` operator:

    xml_reader(path='data.xml') >> flatten(join='.'.join) >> csv_writer(path='data.csv')

In addition, chainlets can be composed much more freely.
Instead of deeply nested call structures, chainlets have simple, flat call sequences.

## Custom Chainlets for Pipelines

Writing new chainlets does not require any special techniques or conventions.
You can directly convert existing coroutines, functions and objects.
Implementing a moving average requires exactly one line specific to the ``chainlet`` library:

    @chainlet.genlet
    def moving_average(window_size=8):
        buffer = collections.deque([(yield)], maxlen=window_size)
        while True:
            new_value = yield(sum(buffer)/len(buffer))
            buffer.append(new_value)

All the gluing and binding is done automatically for you.
Instead of bloating existing code, it is often easier to create and bind another simple chainlet.

## Extended Pipelines with Chainlets

Chainlets are not limited to 1-to-1 relations, but actually allow n-to-n links.
Each link can have multiple parents and children.
The following example reads XML messages via UDP, and logs them in two different verbosity levels. 

    udp_digest(port=31137) >> xml_converter()  >> (
            json_writer(path='raw.json'),
            moving_average(window_size=60) >> json_writer(path='avg1m.json'),
        )

## Quick Overview

* The *smallest* building blocks is a `ChainLink`, ready to be subclassed and made _**big**_
* Generate awesome *generator* pipelines, and let `GeneratorLink` put that awesome into use
* State is for wusses, real programmers use functions; real programmers use `FunctionLink`
* Don't wrap your head with wrappers, wrap with decorators - `linklet` and let link

## Tell me more!

Chainlets are simple at their core, and quick to understand.
If you want to know more, just read the fabulous manual:
[![Documentation Status](https://readthedocs.org/projects/chainlet/badge/?version=latest)](http://chainlet.readthedocs.io/en/latest/?badge=latest)

The module is hosted on [github](https://github.com/maxfischer2781/chainlet).
If you have issues or want to propose changes, check out the [issue tracker](https://github.com/maxfischer2781/chainlet/issues).
