from collections import defaultdict
import numpy as np

from sklearn.preprocessing import scale

from game import Game


class Bot:
    def __init__(self):
        self.game = None
        self.dirs = ['Stay', 'West', 'North', 'South', 'East']

    def get_my_hero(self):
        for hero in self.game.heroes:
            if hero.name == 'tejasm':
                return hero

    def move(self, state):
        self.game = Game(state)
        self.hero = self.get_my_hero()

    def routeGenerator(self, avoid_locs=set()):
        routes = defaultdict(list)
        to_check_locs = list()
        to_check_locs.append(self.hero.pos)
        while True:
            try:
                cursor = to_check_locs.pop(0)
            except IndexError:
                break
            for loc, d in self.game.board.possible_dirs(cursor):
                if loc in routes:
                    continue
                if self.game.board.passable(loc):
                    to_check_locs.append(loc)
                route = routes[cursor][:]
                route.append(d)
                if route[0] in avoid_locs:
                    print(route[0])
                    continue
                yield (loc, route)
                routes[loc] = route


class RandomBot(object, Bot):
    def __init__(self, net):
        super(RandomBot, self).__init__()
        self.n = net

    def move(self, state):
        super(RandomBot, self).move(state)
        interesting_mines = [locs for locs, owner in self.game.mines_locs.items() if owner != self.hero.id]
        number_of_owned = len(self.game.mines_locs.keys()) - len(interesting_mines)
        enemies = [e for e in self.game.heroes if e and e.id != self.hero.id]
        avoid = set()
        routes = list(self.routeGenerator(avoid))
        routes_to_taverns = [r for loc, r in routes if loc in self.game.taverns_locs]
        routes_to_taverns.sort(key=lambda z: len(z))
        route_t = routes_to_taverns.pop(0)
        routes_to_mines = [r for loc, r in routes if loc in interesting_mines]
        routes_to_mines.sort(key=lambda z: len(z))
        try:
            route_m = routes_to_mines.pop(0)
        except IndexError:
            return 'Stay'
        routes_enemies = []
        for e in enemies:
            routes_e = [r for loc, r in routes if loc == e.pos]
            routes_e.sort(key=lambda z: len(z))
            routes_enemies.append((e.life, routes_e.pop(0)))
        try:
            x = np.asarray([self.hero.life, number_of_owned, len(route_m), len(route_t), routes_enemies[0][0],
                            len(routes_enemies[0][1]),
                            routes_enemies[1][0], len(routes_enemies[1][1]), routes_enemies[2][0],
                            len(routes_enemies[2][1])], dtype=float)
            self.n.Input(list(scale(x, with_mean=False)))
            self.n.Activate()
            options = list(self.n.Output())
            index_max = options.index(max(options))
            if index_max == 0:
                return route_m.pop(0)
            elif index_max == 1:
                return route_t.pop(0)
            elif index_max == 2:
                return routes_enemies[0][1].pop(0)
            elif index_max == 3:
                return routes_enemies[1][1].pop(0)
            elif index_max == 4:
                return routes_enemies[2][1].pop(0)
        except Exception as e:
            print e
        return route_m.pop(0)
