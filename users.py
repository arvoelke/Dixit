import time

class User(object):
    
    MIN_NAME = 3
    MAX_NAME = 20
    
    def __init__(self, uid, puid):
        """Makes a new user with the given uid (private) and puid (public)."""
        self.uid = uid
        self.puid = puid
        self.ping()
        self.set_name('player.%s' % puid[:4])
        
    def set_name(self, name):
        if len(name) >= self.MIN_NAME:
            self.name = name[:self.MAX_NAME]
        return self.name
        
    def ping(self):
        self.last_active = time.time()
        
    def __str__(self):
        return str(self.uid)
    
class Users(object):
    
    def __init__(self):
        self.users = {}
        self.users_by_puid = {}
        
    def __iter__(self):
        return self.users.itervalues()
        
    def has_user(self, uid):
        return uid in self.users

    def get_user(self, uid):
        return self.users[uid]
        
    def get_user_by_puid(self, puid):
        return self.users_by_puid[puid]
        
    def add_user(self, uid, puid):
        user = User(uid, puid)
        self.users[uid] = user
        self.users_by_puid[puid] = user
        return user