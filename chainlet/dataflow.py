from __future__ import absolute_import, division
import itertools
import collections
import numbers

from . import chainlink


class NoOp(chainlink.ChainLink):
    """
    A noop element that returns any input unchanged

    This element is useful when an element is syntactically required, but no
    action is desired. For example, it can be used to split a pipeline into
    a modified and unmodifed version:

    .. code:: python

        translator = find_language >> (NoOp(), to_french, to_german) >>
    """
    def chainlet_send(self, value=None):
        return value


def joinlet(chainlet):
    """
    Decorator to mark a chainlet as joining

    :param chainlet: a chainlet to mark as joining
    :type chainlet: chainlink.ChainLink
    :return: the chainlet modified inplace
    :rtype: chainlink.ChainLink
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
        base_value = next(iter_values)
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

try:
    Counter = collections.Counter
except AttributeError:
    pass
else:
    MergeLink.default_merger.insert(1, (Counter, merge_numerical))
