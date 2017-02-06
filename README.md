# Chainlet

Toolbox for linking generator/iterators to create processing chains.
With its operator based syntax, one may build complex sequences from simple building blocks.
Chainlets are suitable for incremental, iterative and stream processing and beyond.

## Creating Chains with Chainlets

Consider the following use case:
Read data from an XML, flatten it, then write to as a csv.
This can be expressed with a chain of generators:

    csv_writer(flatten(xml_reader(path='data.xml'), join='.'.join), path='data.csv')

When written using chainlets, generator sequence and arguments are much easier to read.
The chainlets are joined using the `>>` operator:

    xml_reader(path='data.xml') >> flatten(join='.'.join) >> csv_writer(path='data.csv')
