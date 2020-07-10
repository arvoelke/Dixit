"""Common utilities for this project."""

import contextlib
import hashlib
import random
import sys
import io

INFINITY = 1e9
SALT = '1c(R$p{Gsjk/5'


def hash_obj(obj, salt=SALT, add_random=False, algo=hashlib.sha256):
    """Returns a salted, optionally randomized, hash of str(obj)."""
    data = '%s%s%s' % (obj, salt, random.random() if add_random else '')
    return algo(data.encode('utf-8')).hexdigest()


def get_sorted_positions(lst, key):
    """Returns the index of each sorted element, allowing for ties."""
    std_lst = sorted((key(x), i) for i, x in enumerate(lst))
    new_lst = lst[:]
    pos = 0
    i = 0
    while i < len(std_lst):
        new_lst[std_lst[i][1]] = pos
        while i + 1 < len(std_lst) and std_lst[i][0] == std_lst[i+1][0]:
            i += 1
            new_lst[std_lst[i][1]] = pos
        pos += 1
        i += 1
    return new_lst


def url_join(*args):
    """Joins a list of string arguments by the '/' separator."""
    return '/'.join(args)


@contextlib.contextmanager
def capture_stdout(stdout=None):
    """Usage: with capture_stdout() as s:...; s.getValue()"""
    oldout = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = oldout
