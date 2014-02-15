class APIError(Exception):
    
    def __init__(self, code, data=None):
        self.code = code
        self.data = data
        
    def __str__(self):
        tag = ': "%s"' % self.data if self.data is not None else ''
        return '%s%s' % (self.code, tag)
        
class Codes(object):
    
    JOIN_FULL_ROOM = 0
    JOIN_BANNED = 1
    NOT_ENOUGH_PLAYERS = 2
    
    KICK_BAD_STATE = 3
    KICK_UNKNOWN_USER = 4
    
    BEGIN_BAD_STATE = 5
    
    CLUE_BAD_STATE = 6
    CLUE_NOT_TURN = 7
    CLUE_TOO_LONG = 8
    CLUE_TOO_SHORT = 9
    
    PLAY_BAD_STATE = 10
    PLAY_NOT_TURN = 11
    PLAY_UNKNOWN_USER = 12
    
    VOTE_BAD_STATE = 13
    VOTE_NOT_TURN = 14
    VOTE_UNKNOWN_USER = 15
    VOTE_INVALID = 16
    
    NOT_HAVE_CARD = 17
    
    DECK_TOO_SMALL = 18
    COLOUR_TAKEN = 19

    NOT_AN_INTEGER = 20
    ILLEGAL_RANGE = 21
    NOT_A_COLOUR = 22