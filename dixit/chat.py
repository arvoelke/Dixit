"""Data for a chat log."""

import time

from dixit.utils import hash_obj


class ChatLog(object):
    """Data for a chat log."""

    MAX_HISTORY = 1024  # default number of messages to store

    def __init__(self, max_history=MAX_HISTORY):
        """Initialzes an empty chat log with a given size."""
        self.log = [None]*max_history  # circular array
        self.size = max_history
        self.tail = 0

    def add(self, name, msg):
        """Appends a new msg for a user with the given name."""
        cur_time = time.time()
        self.log[self.tail] = {
            'user' : name,
            'mid' : hash_obj(cur_time, add_random=True),
            'msg' : msg,
            't' : cur_time,
        }
        self.tail = (self.tail + 1) % self.size

    def dump_since(self, last_time):
        """Returns all messages posted since the given timestamp."""
        head = (self.tail - 1) % self.size
        dump = []
        while self.log[head] and self.log[head]['t'] > last_time:
            dump.append(self.log[head])
            head = (head - 1) % self.size
            if head == self.tail:  # avoid infinite loop
                break
        return list(reversed(dump))  # increasing time order
