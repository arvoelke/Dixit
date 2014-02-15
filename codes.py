"""Error codes and presentation."""


class APIError(Exception):
    """Generic server-side exceptions for when the API is used incorrectly."""

    def __init__(self, code, exc=None, *args, **kwargs):
        self.code = code
        self.exc = exc
        super(APIError, self).__init__(exc, *args, **kwargs)

    def __str__(self):
        tag = ': "%s"' % self.exc if self.exc is not None else ''
        return '%s%s' % (self.code, tag)


class Codes(object):
    """Codes for an APIError."""

    JOIN_FULL_ROOM = 0
    JOIN_BANNED = 1
    NOT_ENOUGH_PLAYERS = 2
    COLOUR_TAKEN = 3
    NOT_A_COLOUR = 4
    KICK_BAD_STATE = 5
    KICK_UNKNOWN_USER = 6
    DECK_TOO_SMALL = 7
    BEGIN_BAD_STATE = 8
    CLUE_BAD_STATE = 9
    CLUE_NOT_TURN = 10
    CLUE_TOO_LONG = 11
    CLUE_TOO_SHORT = 12
    PLAY_BAD_STATE = 13
    PLAY_NOT_TURN = 14
    PLAY_UNKNOWN_USER = 15
    PLAY_ALREADY = 16
    VOTE_BAD_STATE = 17
    VOTE_NOT_TURN = 18
    VOTE_UNKNOWN_USER = 19
    VOTE_INVALID = 20
    VOTE_ALREADY = 21
    NOT_HAVE_CARD = 22
    NOT_AN_INTEGER = 23
    ILLEGAL_RANGE = 24
