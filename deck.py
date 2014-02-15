import random
from utils import hash_obj


class Card(object):
    """A single card."""

    def __init__(self, cid, url):
        self.cid = cid
        self.url = url

    def to_json(self):
        return {
            'cid' : self.cid,
            'url' : self.url
        }


class CardSet(object):
    """A static set of cards."""

    def __init__(self, name, card_paths, is_default=False):
        self.name = name
        prefix = hash_obj(name, add_random=True)[:5]  # must be unique
        self.cards = [Card('card%s%d' % (prefix, i), p)
                      for i, p in enumerate(card_paths)]
        self.is_default = is_default

    def __iter__(self):
        return iter(self.cards)

    def size(self):
        return len(self.cards)


class Deck(object):
    """A deck of cards built from multiple card sets."""

    def __init__(self, card_sets, shuffle=True):
        self.name = ', '.join(card_set.name for card_set in card_sets)
        self.cards = [card for card_set in card_sets for card in card_set]
        self.card_lookup = dict((card.cid, card) for card in self.cards)
        self.reset(shuffle)

    def reset(self, shuffle=True):
        self.dealt = 0
        if shuffle:
            self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def is_empty(self):
        return self.dealt == len(self.cards)

    def size(self):
        return len(self.cards)

    def left(self):
        return len(self.cards) - self.dealt

    def deal(self):
        if self.is_empty():
            return None
        self.dealt += 1
        return self.cards[self.dealt - 1]

    def get_card(self, cid):
        return self.card_lookup[cid]
