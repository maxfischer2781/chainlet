++++++++
Glossary
++++++++

.. glossary::

    link
    linking
        The combination of multiple :term:`chainlinks <chainlink>` to form a :term:`compound link`.

    chunk
    data chunk
        The smallest piece of data passed along individually.
        There is no restriction on the size or type of chunks:
        A :term:`chunk` may be a primitive, such as an :py:class:`int`,
        a container, such as a :py:class:`dict`,
        or an arbitrary :py:class:`object`.

    stream
    data stream
        An :term:`iterable` of :term:`data chunks <data chunk>`.
        It is implicitly passed along a :term:`chain`,
        as :term:`chainlinks <chainlink>` operate on its individual :term:`chunks <chunk>`.

        The :term:`stream` is an abstract object and never implicitly materialized by :py:mod:`chainlet`.
        For example, it can be an actual :term:`sequence`, an (in)finite :term:`generator`,
        or created piecewise via :py:meth:`~chainlet.ChainLink.send`.

    chainlet
        An atomic :term:`chainlink`.
        The most primitive elements capable of forming chains and bundles.

    chainlink
        Primitive and compound elements from which chains can be formed.

    compound link
        A group of :term:`chainlinks <chainlink>`, which can be used as a whole as elements in chains and bundles.

        The :term:`chain` and :term:`bundle` are the most obvious forms, created implicitly by the ``>>`` operator.

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
        A :term:`chainlink` which forks may *produce* multiple :term:`data chunks <data chunk>`, each of which are passed
        on individually.

    join
    joining
        Merging of the data flow by a :term:`chainlink`.
        A :term:`chainlink` which joins may *receive* multiple :term:`data chunks <data chunk>`, all of which are passed
        to it at once.

    branch
    branching
        Splitting of the processing sequence into multiple subsequences.
        Usually implies a :term:`fork`.
