'''
Created on 29 May 2012

@author: krav
'''
import random
import sys
import os
import glob
     

PLAYERS = "players.txt"
PLAYERS_HEADER = "#id, email, name, pass"

GAMES = "games.txt"
GAMES_HEADER = "#id, map, budget, turn, active_player_id, finished"

GAME_PLAYERS = "game_players.txt"
GAME_PLAYERS_HEADER = "#id, game_id, ply_id, team_id, order_num"


class DBProxyApi():
    
    def __init__(self):
        
        self.players = self.loadFile(PLAYERS)
        self.games = self.loadFile(GAMES)
        self.game_players = self.loadFile(GAME_PLAYERS)
        
        
    def loadFile(self, fname):
        lst = []
        player_file = open("./../db/" + fname, "r")
        for line in player_file:
            if line[0] == '#':
                continue
            
            line = line.strip()
            line = line.split(',')
            
            #print line
            lst.append(line)
            
        player_file.close()
        return lst
        
    
    def close(self):
        pass
    
    
    def createPlayer(self, email, username, password):
        rnd = random.randint( 1000, sys.maxint )
        self.players.append( [rnd,email,username,password] )
        self.saveToFile(self.players, PLAYERS, PLAYERS_HEADER)
    
    
    def saveToFile(self, list, fname,header):
        f = open("./../db/" + fname, "w")
        f.write(header)
        #f.write('\n')
        for a in list:
            line = "\n"
            for b in a:
                line += str(b)
                line += ','
            line = line[:-1]
            #line += '\n'
            #print line
            f.write( line )
        f.close()
        
    
    def deletePlayer(self, username):
        pass
    
    
    def returnPlayer(self, username):
        for p in self.players:
            if p[2] == username:
                return [p]
    
    
    def returnLevel(self, name):
        pass
    
    
    def getMyActiveGames(self, player_id):
        lst = []
        for g in self.game_players:
            if int(g[2]) == int(player_id):
                game = self.getGame(g[1])
                if game:
                    if int(game[0][5]):
                        lst.append( game )
        return lst
    
    
    def getAllFinishedGames(self):
        lst = []
        for game in self.games:
            if int(game[5]):
                lst.append(game)
        return lst

    
    def getGame(self, game_id):
        for g in self.games:
            
            if int(g[0]) == int(game_id):
                return [g]

    
    def getAllLevels(self):
        path = os.getcwd() + './../server/data/levels/*.txt'
        lst = []
        for infile in glob.glob( path ):
            infile = infile.split('\\')[-1]
            lst.append( infile.split(".")[0] )
        return lst
    
    
    def getAllPlayers(self):
        ret_lst = []
        for p in self.players:
            print p
            ret_lst.append( [ p[0], p[2] ] )
            
        return ret_lst
    
    
    def createGame(self, level_name, army_size, first_player_id):
        id = int(self.games[-1][0]) + 1
        self.games.append( [id, level_name, army_size, 0, first_player_id, 0] )
        self.saveToFile(self.games, GAMES, GAMES_HEADER)
        return id

        
    def addPlayerToGame(self, game_id, player_id, team, order):
        id = int(self.game_players[-1][0]) + 1
        self.game_players.append( [id, game_id, player_id, team, order] )
        self.saveToFile(self.game_players, GAME_PLAYERS, GAME_PLAYERS_HEADER)

                
    def returnPlayerInGame(self, game_id, player_name):
        pass
    
    
    def addMessage(self, game_id, player_name, message_type, message, turn_number):
        pass
    
    
if __name__ == "__main__":
    dbapi = DBProxyApi()
    #dbapi.createPlayer("emailv@@@vvv", "ihaaa", "po")
    #print dbapi.returnPlayer('ogi')
    #print dbapi.getGame(100)
    #game_id = dbapi.createGame("test", 1000)
    #dbapi.addPlayerToGame(game_id, dbapi.returnPlayer('Red')[0], 0, 0)
    #dbapi.addPlayerToGame(game_id, dbapi.returnPlayer('ogi')[0], 1, 1)
    #print dbapi.getAllLevels()
    #all_players = dbapi.getAllPlayers()
    #print [ x for x,y in all_players ]
    #dbapi.getMyGames( 17 ) 
    print dbapi.getAllFinishedGames()
    
    dbapi.close()
#MAIN
#dbapi = DBApi()
#print dbapi.returnPlayer('ogi')
#dbapi.addMessage(6, 'ogi', 1, 'asd', 1)
#dbapi.createPlayer('ogi@loshdev', 'ogi', 'ogi')
#dbapi.createPlayer('krav@loshdev', 'krav', 'krav')
#dbapi.createPlayer('vjeko@loshdev', 'vjeko', 'vjeko')
#id = dbapi.createGame('base2', 1000)
#dbapi.addPlayerToGame(int(id), 'ogi', 1, 1)
#dbapi.addPlayerToGame(int(id), 'krav', 2, 1)