"""Entry point for running the Dixit server.

Usage: python server.py [config.json]

See https://github.com/arvoelke/dixit or README.md for more information.

Refer to LICENSE.txt for terms of modification and redistribution.
"""

import tornado.ioloop
import tornado.web

import json
import os
import sys
import time

from dixit.chat import ChatLog
from dixit.codes import APIError, Codes
from dixit.core import Limits, States, StringClue, Game
from dixit.deck import CardSet
from dixit.users import Users
from dixit.utils import INFINITY, hash_obj, get_sorted_positions, url_join, \
    capture_stdout
import dixit.config as config
import dixit.display as display


class RequestHandler(tornado.web.RequestHandler):
    """Base class for all request handlers. Injects authenticated self.user."""

    USER_COOKIE_NAME = 'dixit_user'

    def prepare(self):
        """Sets self.user based off hash in existing cookie, or a new cookie."""
        uid = self.get_cookie(self.USER_COOKIE_NAME)
        if not self.application.users.has_user(uid):
            if uid is None:
                uid = hash_obj(id(self), add_random=True)
                self.set_cookie(self.USER_COOKIE_NAME, uid)
            puid = hash_obj(uid, add_random=True)
            self.user = self.application.users.add_user(uid, puid)
        else:
            self.user = self.application.users.get_user(uid)
            self.user.ping()


class MainHandler(RequestHandler):
    """Handler for rendering main.html with the server's template variables."""

    def get(self):
        self.render('main.html',
            card_sets=self.application.card_sets,
            display=display,
            user=self.user,
            limits=self.application.limits)


class MainJSHandler(tornado.web.RequestHandler):
    """Handler for rendering main.js with the server's template variables."""

    def get(self):
        self.set_header('Content-Type', 'text/javascript')
        self.render('main.js',
            display=display,
            states=States,
            commands=Commands,
            limits=self.application.limits)


class MainCSSHandler(tornado.web.RequestHandler):
    """Handler for rendering main.css with the server's template variables."""

    def get(self):
        self.set_header('Content-Type', 'text/css')
        self.render('main.css',
            display=display,
            cards_per_person=Game.CARDS_PER_PERSON)


class AdminHandler(RequestHandler):
    """Handler for executing arbitrary code on the server in real time."""

    def get(self):
        if not self.application.admin_enable:
            raise tornado.web.HTTPError(404)
        self.render('admin.html', display=display)

    def post(self):
        if not self.application.admin_enable:
            raise tornado.web.HTTPError(404)
        admin_password = hash_obj(self.get_argument('password'))
        if admin_password != self.application.admin_password:
            stdout = ''
            stderr = 'Invalid password'
        else:
            try:
                with capture_stdout() as stdout_context:
                    exec(self.get_argument('code').replace('\r', ''))
                stdout = stdout_context.getvalue()
                stderr = ''
            except Exception as exc:
                stdout = ''
                stderr = unicode(exc).encode('utf-8')
        self.write({
            'stdout' : stdout,
            'stderr' : stderr,
        })


class SetUsernameHandler(RequestHandler):
    """Handler for changing your own username."""

    def post(self):
        username = self.get_argument('username', default=None)
        new_name = self.user.set_name(username) if username else self.user.name
        self.write(new_name)


class CreateHandler(RequestHandler):
    """Handler for creating a new game."""

    def post(self):
        try:
            card_set_indices = list(map(int, self.request.arguments['card_sets']))
        except ValueError as exc:
            raise APIError(Codes.NOT_AN_INTEGER, exc)
        if min(card_set_indices) < 0 or \
           max(card_set_indices) >= len(self.application.card_sets):
            raise APIError(Codes.ILLEGAL_RANGE, card_set_indices)
        card_sets = [self.application.card_sets[i] for i in card_set_indices]

        password = self.get_argument('password', '')  # not yet implemented
        if password:
            password = hash_obj(password)
        name = self.get_argument('name', '')
        if not name:
            name = 'Game %d' % (len(self.application.games) + 1)

        max_score = self.get_argument('max_score')
        if not max_score:
            max_score = INFINITY
        try:
            max_score = int(max_score)
            max_players = int(self.get_argument('max_players'))
            max_clue_length = int(self.get_argument('max_clue_length'))
        except ValueError as exc:
            raise APIError(Codes.NOT_AN_INTEGER, exc)

        limits = self.application.limits
        if (not limits.min_name <= len(name) <= limits.max_name) or \
           (not limits.min_players <= max_players <= limits.max_players) or \
           (not limits.min_score <= max_score <= limits.max_score) or \
           (not limits.min_clue_length <= max_clue_length <= limits.max_clue_length):
            raise APIError(Codes.ILLEGAL_RANGE)

        game = Game(self.user, card_sets, password, name,
                    max_players, max_score, max_clue_length, limits)
        self.application.games.append(game)
        self.write(str(len(self.application.games) - 1))


class GetGamesHandler(RequestHandler):
    """Handler for getting the list of all games."""

    def get(self):
        blob = []
        cur_time = time.time()
        for gid, game in enumerate(self.application.games):
            blob.append({
                'gid' : gid,
                'name' : game.name,
                'relLastActive' : cur_time - game.last_active,
                'host' : game.host.name,
                'players' : [user.name for user in game.players],
                'maxPlayers' : game.max_players,
                'state' : game.state,
                'left' : game.deck.left(),
                'size' : game.deck.size(),
                'topScore' : max(p.score for p in list(game.players.values())) \
                    if game.players else 0,
                'maxScore' : game.max_score \
                    if game.max_score != INFINITY else None,
                'deckName' : game.deck.name,
                'isHost' : self.user == game.host,
                'isPlayer' : self.user in game.players,
            })
        self.write(json.dumps(sorted(blob, key=lambda x: x['relLastActive'])))


class GetUsersHandler(RequestHandler):
    """Handler for getting the list of all users."""

    def get(self):
        blob = []
        cur_time = time.time()
        for user in self.application.users:
            blob.append({
                'name' : user.name,
                'relLastActive' : cur_time - user.last_active,
            })
        self.write(json.dumps(sorted(blob, key=lambda x: x['relLastActive'])))


class ChatHandler(RequestHandler):
    """Handler for posting to and reading from the chat log."""

    def get(self):
        last_time = float(self.get_argument('t'))
        self.write({
            'log' : self.application.chat_log.dump_since(last_time),
            't' : time.time(),
        })

    def post(self):
        msg = self.get_argument('msg')[:self.application.limits.max_message]
        self.application.chat_log.add(self.user.name, msg)


class Commands(object):
    """Possible commands for the GameHandler, to be used in the JavaScript."""

    GET_BOARD = 0
    JOIN_GAME = 1
    START_GAME = 2
    CREATE_CLUE = 3
    PLAY_CARD = 4
    CAST_VOTE = 5
    KICK_PLAYER = 6


class GameHandler(RequestHandler):
    """Handler for getting the game board and routing actions."""

    def get(self, gid, cmd):
        """Delegates the request to the corresponding core game operation."""
        gid = int(gid)
        if not 0 <= gid < len(self.application.games):
            raise APIError(Codes.ILLEGAL_RANGE, gid)
        game = self.application.games[gid]

        cmd = int(cmd)
        if cmd == Commands.GET_BOARD:
            self.write(self._get_board(self.user, game))
        elif cmd == Commands.JOIN_GAME:
            colour = self.get_argument('colour')
            game.add_player(self.user, colour)
        elif cmd == Commands.START_GAME:
            game.start_game()
        elif cmd == Commands.CREATE_CLUE:
            clue = StringClue(self.get_argument('clue'))
            card = game.get_card(self.get_argument('cid'))
            game.create_clue(self.user, clue, card)
        elif cmd == Commands.PLAY_CARD:
            card = game.get_card(self.get_argument('cid'))
            game.play_card(self.user, card)
        elif cmd == Commands.CAST_VOTE:
            card = game.get_card(self.get_argument('cid'))
            game.cast_vote(self.user, card)
        elif cmd == Commands.KICK_PLAYER:
            puid = self.get_argument('puid')
            game.kick_player(self.application.users.get_user_by_puid(puid))
        else:
            raise APIError(Codes.ILLEGAL_RANGE, cmd)

    def _get_board(self, user, game):
        """Returns a JSON dictionary summarizing the entire game board."""
        players = dict((u.puid, u.name) for u in game.players)
        scores = dict((u.puid, p.score) for u, p in list(game.players.items()))
        is_player = user in game.players

        requires_action = {}
        for u in game.players:
            requires_action[u.puid] = {
                States.BEGIN: game.host == u and \
                    len(players) >= self.application.limits.min_players,
                States.CLUE: game.clue_maker() == u,
                States.PLAY: not game.round.has_played(u),
                States.VOTE: not game.round.has_voted(u),
                States.END: False,  # game.host == u,
            }[game.state]

        puids = list(players.keys())
        ranked = get_sorted_positions(puids, key=lambda puid: scores[puid])

        rnd = {}
        if game.round.has_everyone_played():
            rnd['cards'] = [card.to_json()
                for card in game.round.get_cards()]
            rnd['cardsHash'] = hash_obj(rnd['cards'])
        if game.round.has_everyone_voted():
            rnd['votes'] = dict((u.puid, card.cid)
                for u, card in list(game.round.user_to_vote.items()))
            rnd['owners'] = dict((u.puid, card.cid)
                for u, card in list(game.round.user_to_card.items()))
            rnd['votesHash'] = hash_obj(rnd['votes'])
        if game.round.clue:
            rnd['clue'] = str(game.round.clue)
        if game.round.clue_maker:
            rnd['clueMaker'] = game.round.clue_maker.puid
        rnd['scores'] = dict((u.puid, score)
            for u, score in list(game.round.scores.items()) if score > 0)

        plr = {}
        if is_player and game.players[user].hand:
            plr['hand'] = [card.to_json() for card in game.players[user].hand]
            plr['handHash'] = hash_obj(plr['hand'])

        blob = {
            'name' : game.name,
            'user' : user.puid,
            'host' : game.host.puid,
            'players' : players,
            'colours' : dict((u.puid, col) for u, col in list(game.colours.items())),
            'isHost' : user == game.host,
            'isPlayer' : user in game.players,
            'maxPlayers' : game.max_players,
            'maxScore' : game.max_score if game.max_score != INFINITY else None,
            'maxClueLength' : game.max_clue_length,
            'scores' : scores,
            'order' : [u.puid for u in game.order],
            'turn' : game.turn,
            'ranked' : dict((uid, rank) for uid, rank in zip(puids, ranked)),
            'left' : game.deck.left(),
            'size' : game.deck.size(),
            'state' : game.state,
            'requiresAction' : requires_action,
            'round' : rnd,
            'player' : plr,
        }

        return blob


def has_suffix(name, suffixes):
    """Returns true iff name ends with at least one of the given suffixes."""
    return True in (name.endswith(suffix) for suffix in suffixes)


def find_cards(folder, suffixes=('.jpg',)):
    """Returns all urls for a given folder, matching the given suffixes."""
    path = os.path.join(
        os.path.dirname(__file__), display.WebPaths.CARDS, folder)
    return [url_join(display.WebPaths.CARDS, folder, name)
        for name in os.listdir(path) if has_suffix(name, suffixes)]


class Application(tornado.web.Application):
    """Main application class for holding all state."""

    def __init__(self, *args, **kwargs):
        """Initializes the users, games, chat log, and cards."""
        self.limits = Limits(kwargs['limits'])

        self.users = Users(self.limits)
        self.games = []
        self.chat_log = ChatLog()

        # Specifies where to find all the card images for each set.
        self.card_sets = [CardSet(name, find_cards(folder), enabled)
            for name, (folder, enabled) in kwargs['card_sets'].items()]
        self.admin_password = kwargs['admin_password']
        self.admin_enable = kwargs['admin_enable']

        super(Application, self).__init__(*args, **kwargs)


settings = {
    'static_path' : os.path.join(os.path.dirname(__file__), 'static'),
    'template_path' : os.path.join(os.path.dirname(__file__), 'templates'),
    'debug' : False,
}

configFilename = os.path.join(os.path.dirname(__file__), "config.json")
settings.update(config.parse(configFilename))

application = Application([
    (r'/', MainHandler),
    (r'/admin', AdminHandler),
    (r'/main.js', MainJSHandler),
    (r'/main.css', MainCSSHandler),
    (r'/setusername', SetUsernameHandler),
    (r'/create', CreateHandler),
    (r'/getgames', GetGamesHandler),
    (r'/getusers', GetUsersHandler),
    (r'/game/([0-9]+)/(.+)', GameHandler),
    (r'/chat', ChatHandler),
], **settings)


def start():
    application.listen(settings['port'])
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    start()
