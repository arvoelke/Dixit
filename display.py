from os.path import join

"""Holds template variables for HTML/JS/CSS."""


class Labels(object):
    """Text labels."""
    
    TITLE = 'Dixit'
    NEW_GAME = 'New Game'
    DEFAULT_TEXT = 'Say something!'
    
    
class WebPaths(object):
    """Client-side paths to resource directories."""
    
    STATIC    = 'static'
    IMAGES    = join(STATIC, 'images')
    JS        = join(STATIC, 'js')
    CSS       = join(STATIC, 'css')
    CARDS     = join(STATIC, 'cards')
    SMILIES   = join(IMAGES, 'smilies')
    JQUERY_UI = join(JS, 'jquery-ui-1.10.4')


class Images(object):
    """Client-side paths to images."""
    
    BANNER      = join(WebPaths.IMAGES, 'banner.png')
    BUNNY_READY = join(WebPaths.IMAGES, 'bunnyready.png')
    BUNNY_RUN   = join(WebPaths.IMAGES, 'bunnyrun.png')
    THINKING    = join(WebPaths.IMAGES, 'thinking.gif')
    CARD_BACK   = join(WebPaths.IMAGES, 'cardback.png')
    VOTE_TOKEN  = join(WebPaths.IMAGES, 'votetoken.png')
    YOUR_TURN   = join(WebPaths.IMAGES, 'arrow.ico')
    ICON_ACTIVE = join(WebPaths.IMAGES, 'bunnyicongreen.png')
    ICON_AWAY   = join(WebPaths.IMAGES, 'bunnyiconyellow.png')
    ICON_ASLEEP = join(WebPaths.IMAGES, 'bunnyicongrey.png')


class Sizes(object):
    """Display sizes for images."""
    
    PIECE        = 45
    BUNNY_PICKER = 70
    CARD_WIDTH   = 250
    CARD_HEIGHT  = 380
    YOUR_TURN    = 24
    TOKEN        = 80


class BunnyPalette(object):
    """Bunny colours to choose from."""
    
    RED    = 'c52828'
    ORANGE = 'e59100'
    YELLOW = 'e2e05d'
    GREEN  = '12751b'
    BLUE   = '214ddc'
    PURPLE = 'a41bf3'
    PINK   = 'd2638d'
    WHITE  = 'd3ceca'
    BLACK  = '3a363b'
    
    @classmethod
    def is_colour(cls, cid):
        """Determines if the given colour id is valid."""
        return cid in (cls.RED, cls.ORANGE, cls.YELLOW,
                        cls.GREEN, cls.BLUE, cls.PURPLE,
                        cls.PINK, cls.WHITE, cls.BLACK)