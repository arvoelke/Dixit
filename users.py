"""Data for all User objects across all games."""

import time


class User(object):
    """Data for one user across multiple games."""

    MIN_NAME = 3
    MAX_NAME = 25

    def __init__(self, uid, puid):
        """Creates a new user with the given uid (private) and puid (public)."""
        self.uid = uid  # this id should never be exposed to the user
        self.puid = puid  # this id is exposed to all users

        self.ping()
        self.set_name('player.%s' % puid[:4])

    def ping(self):
        """Updates the user to appear currently active."""
        self.last_active = time.time()

    def set_name(self, name):
        """Modifies the user's name."""
        if len(name) >= self.MIN_NAME:
            self.name = name[:self.MAX_NAME]
        return self.name


class Users(object):
    """Data for all users."""

    def __init__(self):
        """Initializes an empty data structure."""
        self.users = {}
        self.users_by_puid = {}

    def __iter__(self):
        """Iterates over all User objects."""
        return self.users.itervalues()

    def has_user(self, uid):
        """Returns true iff there exists a User with the given private uid."""
        return uid in self.users

    def get_user(self, uid):
        """Returns the User with the given private uid, or raises KeyError."""
        return self.users[uid]

    def get_user_by_puid(self, puid):
        """Returns the User with the given public puid, or raises KeyError."""
        return self.users_by_puid[puid]

    def add_user(self, uid, puid):
        """Adds and returns a new user with a given private uid and puid."""
        user = User(uid, puid)
        self.users[uid] = user
        self.users_by_puid[puid] = user
        return user
