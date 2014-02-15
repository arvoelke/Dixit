from collections import defaultdict
import random
import time

from codes import APIError, Codes
from deck import Deck

from utils import INFINITY


class Limits(object):

    MIN_NAME = 3
    MAX_NAME = 20

    MIN_PLAYERS = 3
    MAX_PLAYERS = 6

    MIN_SCORE = 1
    MAX_SCORE = INFINITY

    MIN_CLUE_LENGTH = 5
    MAX_CLUE_LENGTH = 100000

    MAX_MESSAGE = 1024


class States(object):

    BEGIN = 0
    CLUE = 1
    PLAY = 2
    VOTE = 3
    END = 4


class StringClue(object):

    def __init__(self, clue):
        self.clue = clue

    def __str__(self):
        return self.clue.encode('utf-8')

    def __len__(self):
        return len(self.clue)


class Player(object):
    """Manages a user with respect to a particular game (hand/score)."""

    def __init__(self, user):
        self.user = user
        self.hand = []
        self.score = 0

    def deal(self, card):
        if card is not None:
            self.hand.append(card)

    def remove_card(self, card):
        if not card in self.hand:
            raise APIError(Codes.NOT_HAVE_CARD)
        self.hand.remove(card)


class Round(object):
    """Manages all player states across one turn (state.VOTE -> state.VOTE)."""

    def __init__(self, players, clue, clue_maker):
        self.players = players
        self.clue = clue
        self.clue_maker = clue_maker
        self.cards = []
        self.user_to_card = dict()
        self.user_to_vote = dict()
        self.card_to_voted_users = defaultdict(list)  # ignores self-votes
        self.scores = defaultdict(int)

        # Determine the random card order ahead of time
        self.card_index_to_user = players.keys()
        random.shuffle(self.card_index_to_user)

    @classmethod
    def make_zeroeth(cls):
        # Use a non-empty list of players so that has_everyone_* returns False.
        return cls({None: None}, None, None)

    def play_card(self, user, card):
        self.players[user].remove_card(card)
        self.user_to_card[user] = card

    def cast_vote(self, user, card):
        self.user_to_vote[user] = card
        if card != self.user_to_card[user]:
            self.card_to_voted_users[card].append(user)

    def has_card(self, card):
        return card in self.user_to_card.itervalues()

    def has_played(self, user):
        return self.user_to_card.has_key(user)

    def has_voted(self, user):
        return self.user_to_vote.has_key(user)

    def has_everyone_played(self):
        return len(self.user_to_card) == len(self.players)

    def has_everyone_voted(self):
        return len(self.user_to_vote) == len(self.players)

    def get_cards(self):
        return [self.user_to_card[user] for user in self.card_index_to_user]

    def score(self, user, score):
        self.players[user].score += score
        self.scores[user] += score


class Game(object):

    CARDS_PER_PERSON = 6
    SCORE_FOR_TRICK = 1
    SCORE_FOR_LOSS = 2
    SCORE_FOR_CORRECT = 3

    def __init__(self, host, card_sets, password, name, max_players,
                 max_score, max_clue_length):
        self.host = host
        self.deck = Deck(card_sets)
        self.password = password
        self.name = name
        self.max_players = max_players
        self.max_score = max_score
        self.max_clue_length = max_clue_length

        self.players = {}
        self.order = []
        self.colours = dict()
        self.perma_banned = set()
        self.init_game()
        self.ping()

    def ping(self):
        self.last_active = time.time()

    def add_player(self, user, colour):
        if self.state != States.BEGIN:
            raise APIError(Codes.BEGIN_BAD_STATE)
        if len(self.players) >= self.max_players:
            raise APIError(Codes.JOIN_FULL_ROOM)
        if colour in self.colours.values():
            raise APIError(Codes.COLOUR_TAKEN)
        if user in self.perma_banned:
            raise APIError(Codes.JOIN_BANNED)
        if not user in self.players:  # idempotent
            self.players[user] = Player(user)
            self.order.append(user)
        self.colours[user] = colour  # alow colour changing

    def kick_player(self, user, is_permanent=False):
        if not user in self.players:
            raise APIError(Codes.KICK_UNKNOWN_USER)
        if len(self.players) <= Limits.MIN_PLAYERS and self.state != States.BEGIN:
            raise APIError(Codes.NOT_ENOUGH_PLAYERS)
        if self.state in (States.PLAY, States.VOTE):
            raise APIError(Codes.KICK_BAD_STATE)
        self.players.pop(user)
        turn = self.order.index(user)
        self.order.remove(user)
        # readjust turn in case game is currently running
        if self.turn > turn:
            self.turn -= 1
        self.turn %= len(self.players)
        if is_permanent:
            self.perma_banned.add(user)

    def init_game(self):
        self.state = States.BEGIN
        self.round = Round.make_zeroeth()
        self.turn = 0
        self.deck.reset()

    def clue_maker(self):
        return self.order[self.turn]

    def get_card(self, cid):
        return self.deck.get_card(cid)

    def start_game(self):
        if self.state != States.BEGIN:
            raise APIError(Codes.BEGIN_BAD_STATE)
        if len(self.players) < Limits.MIN_PLAYERS:
            raise APIError(Codes.NOT_ENOUGH_PLAYERS)
        random.shuffle(self.order)
        for user in self.players:
            for i in range(self.CARDS_PER_PERSON):
                card = self.deck.deal()
                if card is None:
                    self.init_game()  # rewind the dealing
                    raise APIError(Codes.DECK_TOO_SMALL)
                self.players[user].deal(card)
        self.state = States.CLUE
        self.ping()

    def create_clue(self, user, clue, card):
        if self.state != States.CLUE:
            raise APIError(Codes.CLUE_BAD_STATE)
        if user != self.clue_maker():
            raise APIError(Codes.CLUE_NOT_TURN)
        if len(clue) < Limits.MIN_CLUE_LENGTH:
            raise APIError(Codes.CLUE_TOO_SHORT)
        if len(clue) > self.max_clue_length:
            raise APIError(Codes.CLUE_TOO_LONG)
        self.round = Round(self.players, clue, self.clue_maker())
        self.round.play_card(user, card)
        self.players[user].deal(self.deck.deal())
        self.state = States.PLAY
        self.ping()

    def play_card(self, user, card):
        if self.state != States.PLAY:
            raise APIError(Codes.PLAY_BAD_STATE)
        if user == self.clue_maker():
            raise APIError(Codes.PLAY_NOT_TURN)
        if not user in self.players:
            raise APIError(Codes.PLAY_UNKNOWN_USER)
        self.round.play_card(user, card)
        self.players[user].deal(self.deck.deal())
        if self.round.has_everyone_played():
            self.round.cast_vote(self.clue_maker(),
                                 self.round.user_to_card[self.clue_maker()])
            self.state = States.VOTE
        self.ping()

    def cast_vote(self, user, card):
        if self.state != States.VOTE:
            raise APIError(Codes.VOTE_BAD_STATE)
        if user == self.clue_maker():
            raise APIError(Codes.VOTE_NOT_TURN)
        if not user in self.players:
            raise APIError(Codes.VOTE_UNKNOWN_USER)
        if not self.round.has_card(card):
            raise APIError(Codes.VOTE_INVALID)
        self.round.cast_vote(user, card)
        if self.round.has_everyone_voted():
            # Remember this in case someone gets kicked
            self._do_scoring()
            self.state = States.CLUE
            self.turn = (self.turn + 1) % len(self.players)
            if self.deck.is_empty():
                self.state = States.END
            for p in self.players.itervalues():
                if p.score >= self.max_score:
                    self.state = States.END
        self.ping()

    def _do_scoring(self):
        for user in self.players:
            v = self.round.card_to_voted_users[self.round.user_to_card[user]]
            if user == self.clue_maker():
                if len(v) == 0 or len(v) == len(self.players) - 1:
                    for u in self.players:
                        if u != user:
                            self.round.score(u, self.SCORE_FOR_LOSS)
                else:
                    self.round.score(user, self.SCORE_FOR_CORRECT)
                    for u in v:
                        self.round.score(u, self.SCORE_FOR_CORRECT)
            else:
                self.round.score(user, self.SCORE_FOR_TRICK*len(v))
