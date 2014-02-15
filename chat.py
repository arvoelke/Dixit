import time

from utils import hash_obj
        
class ChatLog(object):
    
    MAX_HISTORY = 1024
    
    def __init__(self, max_history=MAX_HISTORY):
        self.log = [None]*max_history
        self.size = max_history
        self.i = 0
        
    def add(self, name, msg):
        t = time.time()
        self.log[self.i] = {
            'user' : name,
            'mid' : hash_obj(t, add_random=True),
            'msg' : msg,
            't' : t
        }
        self.i = (self.i + 1) % self.size
        
    def dump_until(self, t):
        j = (self.i - 1) % self.size
        dump = []
        while self.log[j] and self.log[j]['t'] > t:
            dump.append(self.log[j])
            j = (j - 1) % self.size
            if j == self.i:  # infinity loop
                break
        return list(reversed(dump))       