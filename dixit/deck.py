"""Data for all card related objects."""

import random
from dixit.utils import hash_obj


class Card(object):
    """Data for a single card."""

    def __init__(self, cid, url):
        """Initializes a card with a given id and image url."""
        self.cid = cid
        self.url = url

    def to_json(self):
        """Returns the data in a JSON-serializable format."""
        return {
            'cid' : self.cid,
            'url' : self.url
        }


class CardSet(object):
    """Data for a static set of cards."""

    def __init__(self, name, card_paths, is_default=False):
        """Initalizes a set of distinct Card objects."""
        self.name = name
        prefix = hash_obj(name, add_random=True)[:5]  # must be unique
        self.cards = [Card('card%s%d' % (prefix, i), p)
                      for i, p in enumerate(card_paths)]
        self.is_default = is_default

    def __iter__(self):
        """Iterates over all Card objects in the set."""
        return iter(self.cards)

    def size(self):
        """Returns the number of cards in the set."""
        return len(self.cards)


class Deck(object):
    """Data for a deck of cards. Belongs to the scope of one game."""

    def __init__(self, card_sets, shuffle=True):
        """Builds a new deck of Card objects from a list of CardSet objects."""
        self.name = ', '.join(card_set.name for card_set in card_sets)
        self.cards = [card for card_set in card_sets for card in card_set]
        self.card_lookup = dict((card.cid, card) for card in self.cards)

        self.reset(shuffle)

    def reset(self, shuffle=True):
        """Collects and optionally reshuffles all cards."""
        self.dealt = 0
        if shuffle:
            random.shuffle(self.cards)

    def is_empty(self):
        """Returns true iff there are no cards left to deal."""
        return self.dealt == len(self.cards)

    def size(self):
        """Returns the total size of the deck."""
        return len(self.cards)

    def left(self):
        """Returns the number of cards left to be dealt."""
        return len(self.cards) - self.dealt

    def deal(self):
        """Deals out a new card, or returns None if nothing left."""
        if self.is_empty():
            return None
        self.dealt += 1
        return self.cards[self.dealt - 1]

    def get_card(self, cid):
        """Returns the Card with the corresponding card id."""
        return self.card_lookup[cid]
