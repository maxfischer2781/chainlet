++++++++
Glossary
++++++++

.. glossary::

    chunk
    data chunk
        The smallest piece of data passed along individually.
        There is no restriction on the size or type of chunks:
        A :term:`chunk` may be a primitive, such as an :py:class:`int`,
        a container, such as a :py:class:`dict`,
        or an arbitrary :py:class:`object`.

    chainlet
        An atomic :term:`chainlink`.
        The most primitive elements capable of forming chains and bundles.

    chainlink
        Primitive and compound elements from which chains can be formed.

    chain
        A :term:`chainlink` consisting of a sequence of elements to be processed one after another.
        The output of a :term:`chain` is one :term:`data chunk` for every successful traversal.

    bundle
        A :term:`chainlink` forming a group of elements which process each :term:`data chunk` concurrently.
        The output of a :term:`bundle` are zero or many :term:`data chunks <data chunk>` for every successful traversal.

    flat chain
        A :term:`chain` consisting only of primitive elements.

    fork
    forking
        Splitting of the data flow by a :term:`chainlink`.
        A :term:`chainlink` which forks may produce multiple :term:`data chunks <data chunk>`, each of which are passed
        on individually.
