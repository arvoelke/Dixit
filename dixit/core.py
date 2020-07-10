"""Core logic and validation to handle one particular game."""

from collections import defaultdict
import random
import time

from dixit.codes import APIError, Codes
from dixit.deck import Deck
from dixit.display import BunnyPalette
from dixit.utils import INFINITY


class Limits(object):
    """Static parameter limits for validation."""

    def __init__(self, limit_config):
        self.min_name = self._get_int(limit_config, 'min_name')
        self.max_name = self._get_int(limit_config, 'max_name')

        self.min_players = self._get_int(limit_config, 'min_players')
        self.max_players = self._get_int(limit_config, 'max_players')

        self.min_score = self._get_int(limit_config, 'min_score')
        self.max_score = self._get_int(limit_config, 'max_score')

        self.min_clue_length = self._get_int(limit_config, 'min_clue_length')
        self.max_clue_length = self._get_int(limit_config, 'max_clue_length')

        self.max_message = self._get_int(limit_config, 'max_message')

        self.min_user_name = self._get_int(limit_config, 'min_user_name')
        self.max_user_name = self._get_int(limit_config, 'max_user_name')

    def _get_int(self, limit_config, key):
        val = limit_config.get(key)
        if val is None:
            raise Exception(f"Missing limit configuration: {key}")
        try:
            val = int(val)
        except ValueError:
            raise Exception(f"Limit configuration is invalid: {key}={val}")

        return INFINITY if val == -1 else val


class States(object):
    """Possible states for the game."""

    BEGIN = 0  # Waiting for players to start the game.
    CLUE = 1   # A clue is being made.
    PLAY = 2   # Cards are being collected.
    VOTE = 3   # Voting is occurring.
    END = 4    # The game is over.


class StringClue(object):
    """Simple clue container. Returns the encoded text with str()."""

    def __init__(self, clue):
        """Initializes the clue with a given string."""
        self.clue = clue

    def __str__(self):
        return self.clue

    def __len__(self):
        return len(self.clue)


class Player(object):
    """Manages a user with respect to a particular game (hand/score)."""

    def __init__(self, user):
        """Initializes the player for the given user with no hand or score."""
        self.user = user
        self.hand = []
        self.score = 0

    def deal(self, card):
        """Appends a card (if not None) to the hand."""
        if card is not None:
            self.hand.append(card)

    def has_card(self, card):
        """Returns true iff the user has the given card in their hand."""
        return card in self.hand

    def remove_card(self, card):
        """Removes the card from the user's hand or raises ValueError."""
        self.hand.remove(card)


class Round(object):
    """Handles all player state across one turn (state.VOTE -> state.VOTE)."""

    def __init__(self, players, clue, clue_maker):
        """Initializes the round for the given players, clue, and clue maker."""
        self.players = players
        self.clue = clue
        self.clue_maker = clue_maker
        self.user_to_card = dict()  # User -> Card
        self.user_to_vote = dict()  # User -> Card
        self.card_to_voted_users = defaultdict(list)  # Card -> list(User)
        self.scores = defaultdict(int)  # User -> int

        # Determine the random card order ahead of time
        self.card_index_to_user = list(players.keys())
        random.shuffle(self.card_index_to_user)

    @classmethod
    def make_zeroeth(cls):
        """Creates a round object suitable for the very beginning."""
        # Use a non-empty list of players so that has_everyone_* returns False.
        return cls({None: None}, None, None)  # no clues/cards/votes

    def play_card(self, user, card):
        """Removes the card from the user's hand, and remembers the action."""
        self.players[user].remove_card(card)
        self.user_to_card[user] = card

    def cast_vote(self, user, card):
        """Makes the given user vote for the given card."""
        self.user_to_vote[user] = card
        if card != self.user_to_card[user]:  # ignore self-votes
            self.card_to_voted_users[card].append(user)

    def has_card(self, card):
        """Returns true iff the card has been played."""
        return card in iter(self.user_to_card.values())

    def has_played(self, user):
        """Returns true iff the user has already played a card this round."""
        return user in self.user_to_card

    def has_voted(self, user):
        """Returns true iff the user has already voted for a card this round."""
        return user in self.user_to_vote

    def has_everyone_played(self):
        """Returns true iff every player has_played(...)."""
        return len(self.user_to_card) == len(self.players)

    def has_everyone_voted(self):
        """Returns true iff every player has_voted(...)."""
        return len(self.user_to_vote) == len(self.players)

    def get_cards(self):
        """Gets the played cards in a fixed random order."""
        return [self.user_to_card[user] for user in self.card_index_to_user]

    def score(self, user, score):
        """Increments the user's score for this round."""
        self.players[user].score += score
        self.scores[user] += score


class Game(object):
    """Handles all data over the lifetime of a single game."""

    CARDS_PER_PERSON = 6
    SCORE_FOR_TRICK = 1
    SCORE_FOR_LOSS = 2
    SCORE_FOR_CORRECT = 3

    def __init__(self, host, card_sets, password, name, max_players,
                 max_score, max_clue_length, limits):
        """Initializes the game with the parameters from CreateHandler."""
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

        self.limits = limits

        self.init_game()
        self.ping()

    def init_game(self):
        """Initializes the game into a BEGIN state."""
        self.state = States.BEGIN
        self.round = Round.make_zeroeth()
        self.turn = 0
        self.deck.reset()

    def ping(self):
        """Updates the game to appear currently active."""
        self.last_active = time.time()

    def clue_maker(self):
        """Returns the User who made, or is making, the current clue."""
        return self.order[self.turn]

    def get_card(self, cid):
        """Returns the Card from the deck with the given card id."""
        return self.deck.get_card(cid)

    def add_player(self, user, colour):
        """Adds a user with a given colour to the game, or throws APIError."""
        if self.state != States.BEGIN:
            raise APIError(Codes.BEGIN_BAD_STATE)
        if len(self.players) >= self.max_players:
            raise APIError(Codes.JOIN_FULL_ROOM)
        if not BunnyPalette.is_colour(colour):
            raise APIError(Codes.NOT_A_COLOUR, colour)
        if colour in list(self.colours.values()):
            raise APIError(Codes.COLOUR_TAKEN)
        if user in self.perma_banned:
            raise APIError(Codes.JOIN_BANNED)
        if not user in self.players:  # idempotent
            self.players[user] = Player(user)
            self.order.append(user)
        self.colours[user] = colour  # alow colour changing

    def kick_player(self, user, is_permanent=False):
        """Kicks a user from the game, or throws APIError."""
        if not user in self.players:
            raise APIError(Codes.KICK_UNKNOWN_USER)
        if len(self.players) <= self.limits.min_players and \
           self.state != States.BEGIN:
            raise APIError(Codes.NOT_ENOUGH_PLAYERS)
        if self.state in (States.PLAY, States.VOTE):
            raise APIError(Codes.KICK_BAD_STATE)
        self.players.pop(user)
        turn = self.order.index(user)
        self.order.remove(user)
        # Readjust turn in case game is currently running
        if self.turn > turn:
            self.turn -= 1
        self.turn %= len(self.players)
        if is_permanent:
            self.perma_banned.add(user)

    def start_game(self):
        """Transitions from BEGIN to CLUE, or throws APIError."""
        if self.state != States.BEGIN:
            raise APIError(Codes.BEGIN_BAD_STATE)
        if len(self.players) < self.limits.min_players:
            raise APIError(Codes.NOT_ENOUGH_PLAYERS)
        random.shuffle(self.order)
        for user in self.players:
            for _ in range(self.CARDS_PER_PERSON):
                card = self.deck.deal()
                if card is None:
                    self.init_game()  # rewind the dealing
                    raise APIError(Codes.DECK_TOO_SMALL)
                self.players[user].deal(card)
        self.state = States.CLUE
        self.ping()

    def create_clue(self, user, clue, card):
        """Transitions from CLUE to PLAY, or throws APIError."""
        if self.state != States.CLUE:
            raise APIError(Codes.CLUE_BAD_STATE)
        if user != self.clue_maker():
            raise APIError(Codes.CLUE_NOT_TURN)
        if len(clue) < self.limits.min_clue_length:
            raise APIError(Codes.CLUE_TOO_SHORT)
        if len(clue) > self.max_clue_length:
            raise APIError(Codes.CLUE_TOO_LONG)
        if not self.players[user].has_card(card):
            raise APIError(Codes.NOT_HAVE_CARD)
        self.round = Round(self.players, clue, self.clue_maker())
        self.round.play_card(user, card)
        self.players[user].deal(self.deck.deal())
        self.state = States.PLAY
        self.ping()

    def play_card(self, user, card):
        """Makes the given user play a card, or throws APIError."""
        if self.state != States.PLAY:
            raise APIError(Codes.PLAY_BAD_STATE)
        if user == self.clue_maker():
            raise APIError(Codes.PLAY_NOT_TURN)
        if not user in self.players:
            raise APIError(Codes.PLAY_UNKNOWN_USER)
        if self.round.has_played(user):
            raise APIError(Codes.PLAY_ALREADY)
        if not self.players[user].has_card(card):
            raise APIError(Codes.NOT_HAVE_CARD)
        self.round.play_card(user, card)
        self.players[user].deal(self.deck.deal())
        if self.round.has_everyone_played():
            # Transition from PLAY to VOTE.
            self.round.cast_vote(self.clue_maker(),
                                 self.round.user_to_card[self.clue_maker()])
            self.state = States.VOTE
        self.ping()

    def cast_vote(self, user, card):
        """Make the given user vote for a card, or throws APIError."""
        if self.state != States.VOTE:
            raise APIError(Codes.VOTE_BAD_STATE)
        if user == self.clue_maker():
            raise APIError(Codes.VOTE_NOT_TURN)
        if not user in self.players:
            raise APIError(Codes.VOTE_UNKNOWN_USER)
        if not self.round.has_card(card):
            raise APIError(Codes.VOTE_INVALID)
        if self.round.has_voted(user):
            raise APIError(Codes.VOTE_ALREADY)
        self.round.cast_vote(user, card)
        if self.round.has_everyone_voted():
            # Transition from VOTE to CLUE or END.
            self._do_scoring()
            self.turn = (self.turn + 1) % len(self.players)
            self.state = States.CLUE
            if self.deck.is_empty():
                self.state = States.END
            for p in self.players.values():
                if p.score >= self.max_score:
                    self.state = States.END
        self.ping()

    def _do_scoring(self):
        """Increments the scores of all players for this Round."""
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
