"""
Debugging facilities for features specific to :py:mod:`chainlet`
"""
from __future__ import print_function
import sys
import traceback

import chainlet


def chainlet_excepthook(etype, evalue, tb):
    print('Traceback (most recent call last):', file=sys.stderr)
    while tb is not None:
        chainlet_print_traceback(tb, sys.stderr)
        tb = tb.tb_next
    for line in traceback.format_exception_only(etype, evalue):
        print(line, file=sys.stderr)


def chainlet_print_traceback(tb, file=None):
    traceback.print_tb(tb, limit=1, file=file)
    frame_name = tb.tb_frame.f_code.co_name
    frame_locals = dict(tb.tb_frame.f_locals)
    if isinstance(frame_locals.get('self'), chainlet.ChainLink):
        self = frame_locals['self']
        cls = type(self)
        print('  for chainlet "%s:%s"' % (cls.__module__, cls.__name__), file=file, end='')
        try:
            print(', step %d state' % (self.elements.index(frame_locals['element'])), file=file)
        except (IndexError, AttributeError, KeyError):
            print(', static state', file=file)
        for key in sorted(k for k in frame_locals if k != 'self'):
            print('    %s: %r' % (key, frame_locals[key]), file=file)

sys.excepthook = chainlet_excepthook

if __name__ == "__main__":
    import chainlet.dataflow

    @chainlet.funclet
    def fail(value):
        raise ValueError(value)


    noop = chainlet.dataflow.NoOp()
    chn = noop >> noop >> (fail(),) >> noop
    chn.send('initial value')
