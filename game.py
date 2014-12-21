TAVERN = 0
AIR = -1
WALL = -2

PLAYER1 = 1
PLAYER2 = 2
PLAYER3 = 3
PLAYER4 = 4

AIM = {'North': (-1, 0),
       'East': (0, 1),
       'South': (1, 0),
       'West': (0, -1)}


class HeroTile:
    def __init__(self, id):
        self.id = id


class MineTile:
    def __init__(self, heroId=None):
        self.heroId = heroId


class Game:
    def __init__(self, state):
        self.state = state
        self.board = Board(state['game']['board'])
        self.heroes = [Hero(state['game']['heroes'][i]) for i in range(len(state['game']['heroes']))]
        self.mines_locs = {}
        self.heroes_locs = {}
        self.taverns_locs = set([])
        for row in range(len(self.board.tiles)):
            for col in range(len(self.board.tiles[row])):
                obj = self.board.tiles[row][col]
                if isinstance(obj, MineTile):
                    try:
                        owner = int(obj.heroId)
                    except ValueError:
                        owner = None
                    self.mines_locs[(row, col)] = owner
                elif isinstance(obj, HeroTile):
                    self.heroes_locs[(row, col)] = obj.id
                elif (obj == TAVERN):
                    self.taverns_locs.add((row, col))


class Board:
    def __parseTile(self, str):
        if (str == '  '):
            return AIR
        elif (str == '##'):
            return WALL
        elif (str == '[]'):
            return TAVERN
        elif (str.startswith('$')):
            return MineTile(str[1])
        elif (str.startswith('@')):
            return HeroTile(str[1])

    def __parseTiles(self, tiles):
        vector = [tiles[i:i + 2] for i in range(0, len(tiles), 2)]
        matrix = [vector[i:i + self.size] for i in range(0, len(vector), self.size)]

        return [[self.__parseTile(x) for x in xs] for xs in matrix]

    def __init__(self, board):
        self.size = board['size']
        self.tiles = self.__parseTiles(board['tiles'])

    def on_board(self, loc):
        x, y = loc
        if x > self.size - 1 or y > self.size - 1 or x < 0 or y < 0:
            return False
        return True

    def is_wall(self, loc):
        'true if can not walk through'
        x, y = loc
        return (self.tiles[x][y] == WALL)

    def is_end(self, loc):
        'true if can not walk through'
        x, y = loc
        pos = self.tiles[x][y]
        return (pos != TAVERN) and not isinstance(pos, MineTile)


    def passable(self, loc):
        'true if can not walk through'
        x, y = loc
        pos = self.tiles[x][y]
        return (pos != WALL) and (pos != TAVERN) and not isinstance(pos, MineTile)

    def to(self, loc, direction):
        'calculate a new location given the direction'
        row, col = loc
        d_row, d_col = AIM[direction]
        n_row = row + d_row
        if (n_row < 0): n_row = 0
        if (n_row > self.size): n_row = self.size
        n_col = col + d_col
        if (n_col < 0): n_col = 0
        if (n_col > self.size): n_col = self.size
        return (n_row, n_col)

    def possible_dirs(self, loc):
        for d in AIM:
            check = self.to(loc, d)
            if not self.on_board(check) or \
                    self.is_wall(check):
                continue
            yield check, d


class Hero:
    def __init__(self, hero):
        pos = hero['pos']
        self.pos = (pos['x'], pos['y'])
        self.id = hero['id']
        self.name = hero['name']
        self.life = hero['life']
        self.gold = hero['gold']