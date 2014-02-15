import tornado.ioloop
import tornado.web

import json
import os
import time

from codes import APIError, Codes
from deck import CardSet
from core import Limits, States, StringClue, Game
from users import Users
from utils import INFINITY, hash_obj, get_sorted_positions, url_join, sysstd
from chat import ChatLog
import display


class RequestHandler(tornado.web.RequestHandler):

    USER_COOKIE_NAME = 'dixit_user'

    def prepare(self):
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

    def get(self):
        self.render('main.html',
            card_sets=self.application.card_sets,
            display=display,
            user=self.user,
            limits=Limits)


class MainCSSHandler(tornado.web.RequestHandler):

    def get(self):
        self.set_header('Content-Type', 'text/css')
        self.render('main.css',
            display=display,
            cards_per_person=Game.CARDS_PER_PERSON)


class MainJSHandler(tornado.web.RequestHandler):

    def get(self):
        self.set_header('Content-Type', 'text/javascript')
        self.render('main.js',
            display=display,
            states=States,
            commands=Commands,
            limits=Limits)


class AdminHandler(RequestHandler):

    ADMIN_PASSWORD = '4a4fd0c6d7ec87b9c52732fc63fa0549e4824edc7d0514f47747fa315f1d075a'

    def get(self):
        self.render('admin.html',
            display=display)

    def post(self):
        if hash_obj(self.get_argument('password')) != self.ADMIN_PASSWORD:
            stdout = ''
            stderr = 'Invalid password'
        else:
            try:
                with sysstd() as s:
                    exec self.get_argument('code').replace('\r', '')
                stdout = s.getvalue()
                stderr = ''
            except Exception as e:
                stdout = ''
                stderr = unicode(e).encode('utf-8')
        self.write({
            'stdout' : stdout,
            'stderr' : stderr,
        })


class SetUsernameHandler(RequestHandler):

    def post(self):
        username = self.get_argument('username', default=None)
        new_name = self.user.set_name(username) if username else self.user.name
        self.write(new_name)


class CreateHandler(RequestHandler):

    def post(self):
        print self.request.arguments['card_sets']
        try:
            card_set_indices = [int(i) for i in self.request.arguments['card_sets']]
        except ValueError as e:
            raise APIError(Codes.NOT_AN_INTEGER, e)
        if False in (0 <= i < len(self.application.card_sets) for i in card_set_indices):
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
        except ValueError as e:
            raise APIError(Codes.NOT_AN_INTEGER, e)

        if (not Limits.MIN_NAME <= len(name) <= Limits.MAX_NAME) or \
           (not Limits.MIN_PLAYERS <= max_players <= Limits.MAX_PLAYERS) or \
           (not Limits.MIN_SCORE <= max_score <= Limits.MAX_SCORE) or \
           (not Limits.MIN_CLUE_LENGTH <= max_clue_length <= Limits.MAX_CLUE_LENGTH):
            raise APIError(Codes.ILLEGAL_RANGE)

        game = Game(self.user, card_sets, password, name,
                    max_players, max_score, max_clue_length)
        self.application.games.append(game)
        self.write(str(len(self.application.games) - 1))


class GetGamesHandler(RequestHandler):

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
                'topScore' : max(p.score for p in game.players.values()) if game.players else 0,
                'maxScore' : game.max_score if game.max_score != INFINITY else None,
                'deckName' : game.deck.name,
                'isHost' : self.user == game.host,
                'isPlayer' : self.user in game.players,
            })
        self.write(json.dumps(sorted(blob, key=lambda x:x['relLastActive'])))


class GetUsersHandler(RequestHandler):

    def get(self):
        blob = []
        cur_time = time.time()
        for user in self.application.users:
            blob.append({
                'name' : user.name,
                'relLastActive' : cur_time - user.last_active,
            })
        self.write(json.dumps(sorted(blob, key=lambda x: x['relLastActive'])))


class Commands(object):

    GET_BOARD = 0
    JOIN_GAME = 1
    START_GAME = 2
    CREATE_CLUE = 3
    PLAY_CARD = 4
    CAST_VOTE = 5
    KICK_PLAYER = 6


class GameHandler(RequestHandler):

    def get(self, gid, cmd):
        gid = int(gid)
        if not (0 <= gid < len(self.application.games)):
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

    @classmethod
    def _get_board(cls, user, game):
        players = dict((u.puid, u.name) for u in game.players)
        scores = dict((u.puid, p.score) for u, p in game.players.items())
        is_player = user in game.players

        requires_action = {}
        for u in game.players:
            requires_action[u.puid] = {
                States.BEGIN: game.host == u and len(players) >= Limits.MIN_PLAYERS,
                States.CLUE: game.clue_maker() == u,
                States.PLAY: not game.round.has_played(u),
                States.VOTE: not game.round.has_voted(u),
                States.END: False,  # game.host == u,
            }[game.state]

        uids = players.keys()
        ranked = get_sorted_positions(uids, key=lambda uid:scores[uid])

        rnd = {}
        if game.round.has_everyone_played():
            rnd['cards'] = [card.to_json()
                for card in game.round.get_cards()]
            rnd['cardsHash'] = hash_obj(rnd['cards'])
        if game.round.has_everyone_voted():
            rnd['votes'] = dict((u.puid, card.cid)
                for u, card in game.round.user_to_vote.items())
            rnd['owners'] = dict((u.puid, card.cid)
                for u, card in game.round.user_to_card.items())
            rnd['votesHash'] = hash_obj(rnd['votes'])
        if game.round.clue:
            rnd['clue'] = str(game.round.clue)
        if game.round.clue_maker:
            rnd['clueMaker'] = game.round.clue_maker.puid
        rnd['scores'] = dict((u.puid, score)
            for u, score in game.round.scores.items() if score > 0)

        plr = {}
        if is_player and game.players[user].hand:
            plr['hand'] = [card.to_json() for card in game.players[user].hand]
            plr['handHash'] = hash_obj(plr['hand'])

        blob = {
            'name' : game.name,
            'user' : user.puid,
            'host' : game.host.puid,
            'players' : players,
            'colours' : dict((u.puid, col) for u, col in game.colours.items()),
            'isHost' : user == game.host,
            'isPlayer' : user in game.players,
            'maxPlayers' : game.max_players,
            'maxScore' : game.max_score if game.max_score != INFINITY else None,
            'maxClueLength' : game.max_clue_length,
            'scores' : scores,
            'order' : [u.puid for u in game.order],
            'turn' : game.turn,
            'ranked' : dict((uid, rank) for uid, rank in zip(uids, ranked)),
            'left' : game.deck.left(),
            'size' : game.deck.size(),
            'state' : game.state,
            'requiresAction' : requires_action,
            'round' : rnd,
            'player' : plr,
        }

        return blob


class ChatHandler(RequestHandler):

    def get(self):
        t = float(self.get_argument('t'))
        self.write(json.dumps({
            'log' : self.application.chat_log.dump_until(t),
            't' : time.time(),
        }))

    def post(self):
        msg = self.get_argument('msg')[:Limits.MAX_MESSAGE]
        self.application.chat_log.add(self.user.name, msg)


def has_suffix(s, suffixes):
    return True in (s.endswith(suffix) for suffix in suffixes)


def find_cards(folder, suffixes=('.jpg',)):
    path = os.path.join(display.WebPaths.CARDS, folder)
    return [url_join(display.WebPaths.CARDS, folder, name)
        for name in os.listdir(os.path.join(os.path.dirname(__file__), path))
        if has_suffix(name, suffixes)]


class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        self.users = Users()
        self.games = []
        self.chat_log = ChatLog()

        print display.WebPaths.IMAGES

        self.card_sets = [
            CardSet('Dixit', find_cards('dixit'), True),
            CardSet('IMDB Posters', find_cards('imdb')),
        ]

        super(Application, self).__init__(*args, **kwargs)


settings = {
    'static_path' : os.path.join(os.path.dirname(__file__), 'static'),
    'template_path' : os.path.join(os.path.dirname(__file__), 'templates'),
    'debug' : True,
}


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


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
