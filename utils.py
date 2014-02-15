import contextlib
import hashlib
import random
import sys
import StringIO

INFINITY = 1e9
SALT = '1c(R$p{Gsjk/5'


def hash_obj(obj, salt=SALT, add_random=False, algo=hashlib.sha256):
    s = '%s%s%s' % (obj, salt, random.random() if add_random else '')
    return algo(s.encode('utf-8')).hexdigest()


def get_sorted_positions(l, key):
    """Returns index of each sorted element, allowing for ties."""
    d = [(key(x), i) for i, x in enumerate(l)]
    d.sort()
    new_l = l[:]
    pos = 0
    i = 0
    while i < len(d):
        new_l[d[i][1]] = pos
        while i + 1 < len(d) and d[i][0] == d[i+1][0]:
            i += 1
            new_l[d[i][1]] = pos
        pos += 1
        i += 1
    return new_l


def url_join(*args):
    return '/'.join(args)


@contextlib.contextmanager
def sysstd(stdout=None):
    oldout = sys.stdout
    if stdout is None:
        stdout = StringIO.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = oldout
