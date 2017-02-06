from __future__ import division, absolute_import

from . import chainlink


class ChainDriver(chainlink.ChainLink):
    def run(self):
        while True:
            for child in self._children:
                child.send()
