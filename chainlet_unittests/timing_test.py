from __future__ import division
import unittest
import os
import collections
import math


ANSI_RED = "\033[31;1m"
ANSI_GREEN = "\033[32;1m"
ANSI_BLUE = "\033[34;1m"
ANSI_RESET = "\033[0m"


def get_times():
    """Return a tuple of (user, system, elapsed)"""
    times = os.times()
    return times[0], times[1], times[-1]


def format_seconds(secs):
    if secs < 60:
        if secs > 0.095:
            return '%4.1fs ' % secs
        elif secs > 0.000095:
            return '%4.1fms' % (secs * 1000.0)
        else:
            return '%4.1fus' % (secs * 1000.0 * 1000.0)
    elif secs < 60*60:
        return '%2dm%2ds' % (int(secs // 60), int(secs % 60))


def format_times(start, stop):
    deltas = [stop[idx] - start[idx] for idx in range(len(stop))]
    if not deltas[2]:
        return 'elapsed: %4s, pcpu: ---%%' % format_seconds(deltas[2])
    return 'elapsed: %4s, pcpu: %3d%%' % (format_seconds(deltas[2]), 100.0 * sum(deltas[:-1]) / deltas[2])


class TimingTextTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super(TimingTextTestResult, self).__init__(*args, **kwargs)
        self._timings = {}  # test => timing

    def startTest(self, test):
        self.stream.writeln("---")
        super(TimingTextTestResult, self).startTest(test)
        self._timings[test] = [get_times()]

    def _report_test(self, test, long_message, short_message, ansi_color):
        if self.showAll:
            self.stream.writeln("%s%s%s\n  %s" % (
                ansi_color, long_message, ANSI_RESET, format_times(*self._timings[test][:2])
            ))
        elif self.dots:
            self.stream.write('%s%s%s' % (ansi_color, short_message, ANSI_RESET))
            self.stream.flush()

    def addSuccess(self, test):
        self._timings[test].append(get_times())
        super(unittest.TextTestResult, self).addSuccess(test)
        self._report_test(test, long_message='OK', short_message='.', ansi_color=ANSI_GREEN)

    def addError(self, test, err):
        self._timings[test].append(get_times())
        super(unittest.TextTestResult, self).addSuccess(test)
        self._report_test(test, long_message='ERROR', short_message='E', ansi_color=ANSI_RED)

    def addFailure(self, test, err):
        self._timings[test].append(get_times())
        super(unittest.TextTestResult, self).addSuccess(test)
        self._report_test(test, long_message='FAIL', short_message='F', ansi_color=ANSI_RED)

    def addSkip(self, test, reason):
        self._timings[test].append(get_times())
        super(unittest.TextTestResult, self).addSuccess(test)
        self._report_test(test, long_message="skipped [%s]" % reason, short_message='s', ansi_color=ANSI_BLUE)

    def stopTestRun(self):
        durations = sorted(times[1][2] - times[0][2] for times in self._timings.values() if len(times) == 2)
        all_count, base = len(durations), 2
        max_exp, min_exp = int(2 * math.log(10, base)), int(-6 * math.log(10, base))
        if not hasattr(collections, 'Counter'):
            return
        bins = collections.Counter(round(math.log(val, base)) if val else -999 for val in durations)
        mean = sum(dur for dur in durations if dur > 1E-7) / sum(dur > 1E-7 for dur in durations)
        mean_bin = round(math.log(mean, base))
        # output
        bin_fmt = '%(val)6s |%(bin)-60s[ %(cnt)5s%(trl)7s'
        self.stream.writeln('')
        self.stream.writeln('       | Test Timing Summary')
        if any(key > max_exp for key in bins):
            bin_count = sum(value for key, value in bins.items() if key > max_exp)
            self.stream.writeln(bin_fmt % {
                'val': 'AAA',
                'bin': self._bin_str(bin_count, all_count, 60),
                'cnt': bin_count,
                'trl': '',
            })
        self.stream.writeln(bin_fmt % {'val': '-' * 5, 'bin': '-' * 60, 'cnt': '-' * 3, 'trl': ''})
        for key in range(max_exp, min_exp - 1, -1):
            self.stream.writeln(bin_fmt % {
                'val': format_seconds(base ** key),
                'bin': self._bin_str(bins.get(key, 0), all_count, 60),
                'cnt': bins.get(key, 0),
                'trl': '' if mean_bin != key else format_seconds(mean),
            })
        self.stream.writeln(bin_fmt % {'val': '-' * 5, 'bin': '-' * 60, 'cnt': '-' * 3, 'trl': ''})
        if any(key < min_exp for key in bins):
            bin_count = sum(value for key, value in bins.items() if key < min_exp)
            self.stream.writeln(bin_fmt % {
                'val': 'VVV',
                'bin': self._bin_str(bin_count, all_count, 60),
                'cnt': bin_count,
                'trl': '',
            })

    def _bin_str(self, value, max_value, max_length, symbols='#+:.'):
        chars = 1.0 * value / max_value * max_length
        if int(chars) == chars:
            return symbols[0] * int(chars)
        return symbols[0] * int(chars) + symbols[int(len(symbols) - (chars % 1 * len(symbols)))]


class TimingTextTestRunner(unittest.TextTestRunner):
    resultclass = TimingTextTestResult

    def __init__(self, *args, **kwargs):
        if len(args) < 3 and 'verbosity' not in kwargs:
            kwargs['verbosity'] = 3
        super(TimingTextTestRunner, self).__init__(*args, **kwargs)
