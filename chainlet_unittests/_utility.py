import chainlet.chainlink


class Consumer(chainlet.chainlink.ChainLink):
    def __init__(self):
        super(Consumer, self).__init__()
        self.send_buffer = []
        self.next_buffer = []

    def __next__(self):
        next_val = self._next_of_parents()
        self.next_buffer.append(next_val)
        return next_val

    def send(self, value=None):
        self.send_buffer.append(value)
        return value
