"""
Helpers to modify the flow of data through a :term:`chain`
"""
from __future__ import absolute_import, division
import itertools
import collections
import numbers

import chainlet.signals
from . import chainlink
from . import utility

__all__ = ['NoOp', 'joinlet', 'forklet', 'MergeLink', 'either']


class NoOp(chainlink.NeutralLink):
    """
    A noop element that returns any input unchanged

    This element is useful when an element is syntactically required, but no
    action is desired. For example, it can be used to split a pipeline into
    a modified and unmodifed version:

    .. code:: python

        translate = parse_english >> (NoOp(), to_french, to_german)

    :note: Unlike the :py:class:`~chainlink.NeutralLink`, this element is not optimized
           away by linking.
    """
    def __bool__(self):
        return True

    __nonzero__ = __bool__


def joinlet(chainlet):
    """
    Decorator to mark a chainlet as joining

    :param chainlet: a chainlet to mark as joining
    :type chainlet: chainlink.ChainLink
    :return: the chainlet modified inplace
    :rtype: chainlink.ChainLink

    Applying this decorator is equivalent to setting :py:attr:`~chainlet.chainlink.ChainLink.chain_join`
    on ``chainlet``:
    every :term:`data chunk` is an :term:`iterable` containing all data returned by the parents.
    It is primarily intended for use with decorators that implicitly create a new
    :py:class:`~chainlet.chainlink.ChainLink`.

    .. code:: python

        @joinlet
        @funclet
        def average(value: Iterable[Union[int, float]]):
            "Reduce all data of the last step to its average"
            values = list(value)  # value is an iterable of values due to joining
            if not values:
                return 0
            return sum(values) / len(values)
    """
    chainlet.chain_join = True
    return chainlet


def forklet(chainlet):
    """
    Decorator to mark a chainlet as forking

    :param chainlet: a chainlet to mark as forking
    :type chainlet: chainlink.ChainLink
    :return: the chainlet modified inplace
    :rtype: chainlink.ChainLink

    See the note on :py:func:`joinlet` for general features.
    This decorator sets :py:attr:`~chainlet.chainlink.ChainLink.chain_fork`, and implementations *must* provide an
    iterable.

    .. code:: python

        @forklet
        @funclet
        def friends(value):
            "Split operations for every friend of a person"
            return (person for person in persons if person.is_friend(value))
    """
    chainlet.chain_fork = True
    return chainlet


def merge_numerical(base_value, iter_values):
    return sum(iter_values, base_value)


def merge_iterable(base_value, iter_values):
    """
    Merge flat iterables from an iterable

    :param base_value: base value to merge into
    :param iter_values: values to merge
    :return: merged iterable
    """
    return type(base_value)(itertools.chain(base_value, *iter_values))


def merge_mappings(base_value, iter_values):
    """
    Merge mappings from an iterable

    :param base_value: base value to merge into
    :type base_value: dict
    :param iter_values: values to merge
    :type iter_values: iterable[dict]
    :return: merged mapping
    :rtype: dict
    """
    for element in iter_values:
        base_value.update(element)
    return base_value


class MergeLink(chainlink.ChainLink):
    """
    Element that joins the data flow by merging individual data chunks

    :param mergers: pairs of ``type, merger`` to merge subclasses of ``type`` with ``merger``
    :type mergers: tuple[type, callable]

    Merging works on the assumption that all :term:`data chunks <data chunk>`
    from the previous step are of the same type.
    The type is deduced by peeking at the first :term:`chunk`,
    based on which a ``merger`` is selected to perform the actual merging.
    The choice of a ``merger`` is re-evaluated at every step;
    a single :py:class:`MergeLink` can handle a different type
    on each step.

    Selection of a ``merger`` is based on testing ``issubclass(type(first), merger_type)``.
    This check is evaluated in order, iterating through ``mergers``
    before using :py:attr:`default_merger`.
    For example, :py:class:`~collections.Counter` precedes :py:class:`dict` to use a
    summation based merge strategy.

    Each ``merger`` must implement the call signature

    .. py:function:: merger(base_value: T, iter_values: Iterable[T]) -> T

    where ``base_value`` is the value used for selecting the ``merger``.
    """
    chain_join = True
    chain_fork = False

    #: type specific merge function mapping of the form ``(type, merger)``
    default_merger = [
        (numbers.Number, merge_numerical),
        (collections.MutableSequence, merge_iterable),
        (collections.MutableSet, merge_iterable),
        (collections.MutableMapping, merge_mappings),
    ]

    def __init__(self, *mergers):
        self._cache_mapping = {}
        self._custom_mergers = mergers

    def chainlet_send(self, value=None):
        iter_values = iter(value)
        try:
            base_value = next(iter_values)
        except StopIteration:
            raise chainlet.signals.StopTraversal
        sample_type = type(base_value)
        try:
            merger = self._cache_mapping[sample_type]
        except KeyError:
            self._cache_mapping[sample_type] = merger = self._get_merger(sample_type)
        return merger(base_value, iter_values)

    def _get_merger(self, value_type):
        for merger_type, merger in itertools.chain(self._custom_mergers, self.default_merger):
            if issubclass(value_type, merger_type):
                return merger
        raise ValueError('No compatible merger for %s' % value_type)

# add Count support for newer versions
try:
    Counter = collections.Counter
except AttributeError:
    pass
else:
    MergeLink.default_merger.insert(1, (Counter, merge_numerical))


class Either(chainlink.ChainLink):
    """
    Select the first successful chain from a number of choices

    :param choices: chains to choose from
    :type choices: iterable[chainlink.ChainLink]
    :param default: default value to provide if no chain produces a result

    For every :term:`data chunk`, the first chain from ``choices`` to
    produce a result is chosen. Success is determined by not raising
    :py:exc:`~chainlink.StopTraversal`; there is no special casing of
    ``[]`` or :py:const:`None`.

    A simple switch statement can be implemented as

    .. code:: python

        either(
            condition_a >> instruction_a,
            condition_b >> instruction_b,
            condition_c >> instruction_c,
            ...
        )

    .. note:: All ``choices`` must have the same behaviour with respect
              to :term:`forking` and :term:`joining`.
    """
    NO_DEFAULT = utility.Sentinel('NO DEFAULT')

    def __init__(self, *choices, **kwargs):
        self.choices = tuple(choices)
        self.default = kwargs.pop('default', self.NO_DEFAULT)
        if len(set((choice.chain_fork, choice.chain_join) for choice in self.choices)) != 1:
            raise ValueError('all choices must have consistent fork/join behaviour')
        self.chain_fork = self.choices[0].chain_fork
        self.chain_join = self.choices[0].chain_join

    def chainlet_send(self, value=None):
        for choice in self.choices:
            try:
                return choice.chainlet_send(value)
            except chainlet.signals.StopTraversal:
                continue
        if self.default is not self.NO_DEFAULT:
            return self.default
        raise chainlet.signals.StopTraversal

    def __repr__(self):
        if self.default:
            return 'either(%s, default=%r)' % (', '.join(repr(choice) for choice in self.choices), self.default)
        return 'either(%s)' % ', '.join(repr(choice) for choice in self.choices)

either = Either
