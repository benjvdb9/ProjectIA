#!/usr/bin/env python3
# kingandassassins.py
# Author: Sébastien Combéfis
# Version: April 29, 2016

import argparse
import json
import random
import socket
import sys
from math import hypot
from time import sleep

from lib import game

BUFFER_SIZE = 2048

CARDS = (
    # (AP King, AP Knight, Fetter, AP Population/Assassins)
    (1, 6, True, 5),
    (1, 5, False, 4),
    (1, 6, True, 5),
    (1, 6, True, 5),
    (1, 5, True, 4),
    (1, 5, False, 4),
    (2, 7, False, 5),
    (2, 7, False, 4),
    (1, 6, True, 5),
    (1, 6, True, 5),
    (2, 7, False, 5),
    (2, 5, False, 4),
    (1, 5, True, 5),
    (1, 5, False, 4),
    (1, 5, False, 4)
)

POPULATION = {
    'monk', 'plumwoman', 'appleman', 'hooker', 'fishwoman', 'butcher',
    'blacksmith', 'shepherd', 'squire', 'carpenter', 'witchhunter', 'farmer'
}

BOARD = (
    ('R', 'R', 'R', 'R', 'R', 'G', 'G', 'R', 'R', 'R'),
    ('R', 'R', 'R', 'R', 'R', 'G', 'G', 'R', 'R', 'R'),
    ('R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'R'),
    ('R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'),
    ('R', 'G', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('G', 'G', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G')
)

# Coordinates of pawns on the board
KNIGHTS = {(1, 3), (3, 0), (7, 8), (8, 7), (8, 8), (8, 9), (9, 8)}
VILLAGERS = {
    (1, 7), (2, 1), (3, 4), (3, 6), (5, 2), (5, 5),
    (5, 7), (5, 9), (7, 1), (7, 5), (8, 3), (9, 5)
}

# Separate board containing the position of the pawns
PEOPLE = [[None for column in range(10)] for row in range(10)]

# Place the king in the right-bottom corner
PEOPLE[9][9] = 'king'

# Place the knights on the board
for coord in KNIGHTS:
    PEOPLE[coord[0]][coord[1]] = 'knight'

# Place the villagers on the board
# random.sample(A, len(A)) returns a list where the elements are shuffled
# this randomizes the position of the villagers
for villager, coord in zip(random.sample(POPULATION, len(POPULATION)), VILLAGERS):
    PEOPLE[coord[0]][coord[1]] = villager

KA_INITIAL_STATE = {
    'board': BOARD,
    'people': PEOPLE,
    'castle': [(2, 2, 'N'), (4, 1, 'W')],
    'card': None,
    'king': 'healthy',
    'lastopponentmove': [],
    'arrested': [],
    'killed': {
        'knights': 0,
        'assassins': 0
    }
}


class KingAndAssassinsState(game.GameState):
    '''Class representing a state for the King & Assassins game.'''
    
    DIRECTIONS = {
        'E': (0, 1),
        'W': (0, -1),
        'S': (1, 0),
        'N': (-1, 0)
    }

    def __init__(self, initialstate=KA_INITIAL_STATE):
        super().__init__(initialstate)
    
    def _nextfree(self, x, y, dir):
        nx, ny = self._getcoord((x, y, dir))

    def update(self, moves, player):
        visible = self._state['visible']
        hidden = self._state['hidden']
        people = visible['people']
        for move in moves:
            # ('move', x, y, dir): moves person at position (x,y) of one cell in direction dir
            if move[0] == 'move':
                x, y, d = int(move[1]), int(move[2]), move[3]
                p = people[x][y]
                if p is None:
                    raise game.InvalidMoveException('{}: there is no one to move'.format(move))
                nx, ny = self._getcoord((x, y, d))
                new = people[nx][ny]
                # King, assassins, villagers can only move on a free cell
                if p != 'knight' and new is not None:
                    raise game.InvalidMoveException('{}: cannot move on a cell that is not free'.format(move))
                if p == 'king' and BOARD[nx][ny] == 'R':
                    raise game.InvalidMoveException('{}: the king cannot move on a roof'.format(move))
                if p in {'assassin'} and p in POPULATION and player != 0:
                    raise game.InvalidMoveException('{}: villagers and assassins can only be moved by player 0'.format(move))
                if p in {'king', 'knight'} and player != 1:
                    raise game.InvalidMoveException('{}: the king and knights can only be moved by player 1'.format(move))
                # Move granted if cell is free
                if new is None:
                    people[x][y], people[nx][ny] = people[nx][ny], people[x][y]
                # If cell is not free, check if the knight can push villagers
                else:
                    pass
            # ('arrest', x, y, dir): arrests the villager in direction dir with knight at position (x, y)
            elif move[0] == 'arrest':
                if player != 1:
                    raise game.InvalidMoveException('arrest action only possible for player 1')
                x, y, d = int(move[1]), int(move[2]), move[3]
                arrester = people[x][y]
                if arrester != 'knight':
                    raise game.InvalidMoveException('{}: the attacker is not a knight'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target not in POPULATION:
                    raise game.InvalidMoveException('{}: only villagers can be arrested'.format(move))
                visible['arrested'].append(people[tx][ty])
                people[tx][ty] = None
            # ('kill', x, y, dir): kills the assassin/knight in direction dir with knight/assassin at position (x, y)
            elif move[0] == 'kill':
                x, y, d = int(move[1]), int(move[2]), move[3]
                killer = people[x][y]
                if killer == 'assassin' and player != 0:
                    raise game.InvalidMoveException('{}: kill action for assassin only possible for player 0'.format(move))
                if killer == 'knight' and player != 1:
                    raise game.InvalidMoveException('{}: kill action for knight only possible for player 1'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target is None:
                    raise game.InvalidMoveException('{}: there is no one to kill'.format(move))
                if killer == 'assassin' and target == 'knight':
                    visible['killed']['knights'] += 1
                    people[tx][tx] = None
                elif killer == 'knight' and target == 'assassin':
                    visible['killed']['assassins'] += 1
                    people[tx][tx] = None
                else:
                    raise game.InvalidMoveException('{}: forbidden kill'.format(move))
            # ('attack', x, y, dir): attacks the king in direction dir with assassin at position (x, y)
            elif move[0] == 'attack':
                if player != 0:
                    raise game.InvalidMoveException('attack action only possible for player 0')
                x, y, d = int(move[1]), int(move[2]), move[3]
                attacker = people[x][y]
                if attacker != 'assassin':
                    raise game.InvalidMoveException('{}: the attacker is not an assassin'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target != 'king':
                    raise game.InvalidMoveException('{}: only the king can be attacked'.format(move))
                visible['king'] = 'injured' if visible['king'] == 'healthy' else 'dead'
            # ('reveal', x, y): reveals villager at position (x,y) as an assassin
            elif move[0] == 'reveal':
                if player != 0:
                    raise game.InvalidMoveException('raise action only possible for player 0')
                x, y = int(move[1]), int(move[2])
                p = people[x][y]
                if p not in hidden['assassins']:
                    raise game.InvalidMoveException('{}: the specified villager is not an assassin'.format(move))
                people[x][y] = 'assassin'
        # If assassins' team just played, draw a new card
        if player == 0:
            visible['card'] = hidden['cards'].pop()

    def _getcoord(self, coord):
        return tuple(coord[i] + KingAndAssassinsState.DIRECTIONS[coord[2]][i] for i in range(2))

    def winner(self):
        visible = self._state['visible']
        hidden = self._state['hidden']
        # The king reached the castle
        for doors in visible['castle']:
            coord = self._getcoord(doors)
            if visible['people'][coord[0]][coord[1]] == 'king':
                return 1
        # The are no more cards
        if len(hidden['cards']) == 0:
            return 0
        # The king has been killed
        if visible['king'] == 'dead':
            return 0
        # All the assassins have been arrested or killed
        if visible['killed']['assassins'] + len(set(visible['arrested']) & hidden['assassins']) == 3:
            return 1
        return -1

    def isinitial(self):
        return self._state['hidden']['assassins'] is None
    
    def setassassins(self, assassins):
        self._state['hidden']['assassins'] = set(assassins)

    def prettyprint(self):
        visible = self._state['visible']
        hidden = self._state['hidden']
        result = ''
        if hidden is not None:
            result += '   - Assassins: {}\n'.format(hidden['assassins'])
            result += '   - Remaining cards: {}\n'.format(len(hidden['cards']))
        result += '   - Current card: {}\n'.format(visible['card'])
        result += '   - King: {}\n'.format(visible['king'])
        result += '   - People:\n'
        result += '   +{}\n'.format('----+' * 10)
        for i in range(10):
            result += '   | {} |\n'.format(' | '.join(['  ' if e is None else e[0:2] for e in visible['people'][i]]))
            result += '   +{}\n'.format(''.join(['----+' if e == 'G' else '^^^^+' for e in visible['board'][i]]))
        print(result)

    @classmethod
    def buffersize(cls):
        return BUFFER_SIZE


class KingAndAssassinsServer(game.GameServer):
    '''Class representing a server for the King & Assassins game'''

    def __init__(self, verbose=False):
        super().__init__('King & Assassins', 2, KingAndAssassinsState(), verbose=verbose)
        self._state._state['hidden'] = {
            'assassins': None,
            'cards': random.sample(CARDS, len(CARDS))
        }

    def _setassassins(self, move):
        state = self._state
        if 'assassins' not in move:
            raise game.InvalidMoveException('The dictionary must contain an "assassins" key')
        if not isinstance(move['assassins'], list):
            raise game.InvalidMoveException('The value of the "assassins" key must be a list')
        for assassin in move['assassins']:
            if not isinstance(assassin, str):
                raise game.InvalidMoveException('The "assassins" must be identified by their name')
            if not assassin in POPULATION:
                raise game.InvalidMoveException('Unknown villager: {}'.format(assassin))
        state.setassassins(move['assassins'])
        state.update([], 0)

    def applymove(self, move):
        try:
            state = self._state
            move = json.loads(move)
            if state.isinitial():
                self._setassassins(move)
            else:
                self._state.update(move['actions'], self.currentplayer)
        except game.InvalidMoveException as e:
            raise e
        except Exception as e:
            print(e)
            raise game.InvalidMoveException('A valid move must be a dictionary')


class KingAndAssassinsClient(game.GameClient):
    '''Class representing a client for the King & Assassins game'''

    def __init__(self, name, server, verbose=False):
        super().__init__(server, KingAndAssassinsState, verbose=verbose)
        self.__name = name
        self.laststate= []

    def _handle(self, message):
        pass

    def _nextmove(self, state):
        # Two possible situations:
        # - If the player is the first to play, it has to select his/her assassins
        #   The move is a dictionary with a key 'assassins' whose value is a list of villagers' names
        # - Otherwise, it has to choose a sequence of actions
        #   The possible actions are:
        #   ('move', x, y, dir): moves person at position (x,y) of one cell in direction dir
        #   ('arrest', x, y, dir): arrests the villager in direction dir with knight at position (x, y)
        #   ('kill', x, y, dir): kills the assassin/knight in direction dir with knight/assassin at position (x, y)
        #   ('attack', x, y, dir): attacks the king in direction dir with assassin at position (x, y)
        #   ('reveal', x, y): reveals villager at position (x,y) as an assassin
        state = state._state['visible']
        if state['card'] is None:
            poplist= list(POPULATION)
            self._KRIM= [poplist[0], poplist[1], poplist[2]]
            return json.dumps({'assassins': self._KRIM}, separators=(',', ':'))
        else:
            if self._playernb == 0:
                for i in range(10):
                    for j in range(10):
                        if state['people'][i][j] in set(self._KRIM):
                            return json.dumps({'actions': [('reveal', i, j)]}, separators=(',', ':'))
                return json.dumps({'actions': self._guessassassins(state)}, separators=(',', ':'))
            else:
                return json.dumps({'actions': self._guessking(state)}, separators=(',', ':'))

    def _getP1coords(self, state):
        knightcoords= []
        for i in range(10):
            for j in range(10):
                if state['people'][i][j]=='king':
                    king= (i, j)
                elif state['people'][i][j]== 'knight':
                    knightcoords += [(i, j)]
        return (king, knightcoords)

    def _verdir(self, state, coord):
        try:
            #print('NORD', state['people'][coord[0]-1][coord[1]])
            verN= None==state['people'][coord[0]-1][coord[1]]
        except:
            verN= False
        try:
            #print('EST', state['people'][coord[0]][coord[1]+1])
            verE= None==state['people'][coord[0]][coord[1]+1]
        except:
            verE= False
        try:
            #print('SUD', state['people'][coord[0]+1][coord[1]])
            verS= None==state['people'][coord[0]+1][coord[1]]
        except:
            verS= False
        try:
            #print('OUEST', state['people'][coord[0]][coord[1]-1])
            verW= None==state['people'][coord[0]][coord[1]-1]
        except:
            verW= False
        #print(verN, verE, verS, verW)
        return verN, verE, verS, verW

    def _checkground(self, coord):
        try:
            if BOARD[coord[0]][coord[1]]== 'G':
                return True
            else:
                return False
        except:
            return False

                
    def _guessking(self, state):
        j=0
        running= True
        card= state['card']
        movelist= []
        king, knights= self._getP1coords(state)
        target= state['castle'][0]
        posdir= []
        while running:
            if card[0] != 0:
                N, E, S, W = self._verdir(state, king)
                dirs= [N, E, S, W, 'N', 'E', 'S', 'W']
                if N or E or S or W:
                    i=0
                    while i < 4:
                        if dirs[i]:
                            nx, ny= KingAndAssassinsState._getcoord(self, (king[0], king[1], dirs[i+4]))
                            Db= hypot(target[0]-king[0], target[1]-king[1])
                            Da= hypot(target[0]-nx, target[1]-ny)
                            if Da < Db and self._checkground((nx, ny)) and card[0]!=0 and state['people'][nx][ny]==None:
                                card[0]-=1
                                movelist += [('move', king[0], king[1], dirs[i+4])]
                                state['people'][nx][ny]= 'king'
                                state['people'][king[0]][king[1]]= None
                                #print('1st: King from', king, 'to', (nx, ny), card[0], 'moves left')
                                king= (nx, ny)
                                N, E, S, W= self._verdir(state, king)
                        i+=1
                    if card[1]== 0:
                        i=0
                        while i < 4:
                            if dirs[i]:
                                posdir += [dirs[i+4]]
                            i+=1
                        try:
                            direction= random.choice(posdir)
                        except:
                            running= False
                        nx, ny= KingAndAssassinsState._getcoord(self, (king[0], king[1], direction))
                        if self._checkground((nx, ny)) and card[0]!=0:
                            card[0]-=1
                            movelist += [('move', king[0], king[1], direction)]
                            state['people'][nx][ny]= 'king'
                            state['people'][king[0]][king[1]]= None
                            #print('2nd: King from', king, 'to', (nx, ny), card[0], 'moves left')
                            king, knights= self._getP1coords(state)
                        else:
                            if j>25:
                                card[0]-=1

                if j>25:
                    #print('J > 25', movelist)
                    running= False
                    if len(movelist)==0:
                        return []
                    else:
                        return movelist
            if card[1] != 0:
                l= len(knights)
                try:
                    o= random.randint(0, l-1)
                except:
                    o=0
                p= ['N', 'E', 'S', 'W']
                a, b, c, d = self._verdir(state, knights[o])
                i=0
                dirg= []
                ver= False
                for elm in [a, b, c, d]:
                    if elm:
                        ver= True
                        dirg+= [p[i]]
                    i+=1
                if ver:
                    dirc= random.choice(dirg)
                    nxx, nyy= KingAndAssassinsState._getcoord(self, (knights[o][0], knights[o][1], dirc))
                if ver and self._checkground((nxx, nyy)):
                    card[1]-=1
                    movelist += [('move', knights[o][0], knights[o][1], dirc)]
                    #print(knights[o][0], knights[o][1], dirc)
                    #print('Knight from', knights[o], 'to', (nxx, nyy), card[1], 'moves left')
                    state['people'][nxx][nyy]= 'knight'
                    state['people'][knights[o][0]][knights[o][1]]= None
                    king, knights= self._getP1coords(state)
                    dirc = None
                    dirg = []
            if card[0]==0 and card[1]==0:
                running= False
                return movelist
            j+=1

    def _GetPopList(self, state):
        poplist= []
        for i in range(10):
            for j in range(10):
                if state['people'][i][j] in POPULATION:
                    poplist += [(i, j)]
        return poplist

    def _guessassassins(self, state):
        AP= state['card'][3]
        poplist= []
        movelist=[]
        poplist= self._GetPopList(state)
        p= ['N', 'E', 'S', 'W']
        while AP != 0:
            rd= random.randint(0, len(poplist)-1)
            x, y= poplist[rd]
            a, b, c, d= self._verdir(state, (x, y))
            if a or b or c or d:
                i=0
                truelm= []
                for elem in [a, b, c, d]:
                    if elem:
                        truelm += [p[i]]
                    i+=1
                choice = random.choice(truelm)
                nx, ny= KingAndAssassinsState._getcoord(self, (x, y, choice))
                if self._checkground((nx, ny)):
                    AP-=1
                    #print(x, y, choice)
                    movelist += [('move', x, y, choice)]
                    #print('commoner went from ({},{}) to ({},{})'.format(x,y,nx,ny))
                    state['people'][nx][ny]= state['people'][x][y]
                    state['people'][x][y]= None
                    poplist= self._GetPopList(state)
            else:
                rd= random.randint(0, len(poplist)-1)
                x, y= poplist[rd]
                p= ['N', 'E', 'S', 'W']
                a, b, c, d= self._verdir(self, poplist[rd])
        return movelist

if __name__ == '__main__':
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='King & Assassins game')
    subparsers = parser.add_subparsers(
        description='server client',
        help='King & Assassins game components',
        dest='component'
    )

    # Create the parser for the 'server' subcommand
    server_parser = subparsers.add_parser('server', help='launch a server')
    server_parser.add_argument('--host', help='hostname (default: localhost)', default='localhost')
    server_parser.add_argument('--port', help='port to listen on (default: 5000)', default=5000)
    server_parser.add_argument('-v', '--verbose', action='store_true')
    # Create the parser for the 'client' subcommand
    client_parser = subparsers.add_parser('client', help='launch a client')
    client_parser.add_argument('name', help='name of the player')
    client_parser.add_argument('--host', help='hostname of the server (default: localhost)',
                               default=socket.gethostbyname(socket.gethostname()))
    client_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    client_parser.add_argument('-v', '--verbose', action='store_true')
    # Parse the arguments of sys.args
    args = parser.parse_args()

    if args.component == 'server':
        KingAndAssassinsServer(verbose=args.verbose).run()
    else:
        KingAndAssassinsClient(args.name, (args.host, args.port), verbose=args.verbose)
        
