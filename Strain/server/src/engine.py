from xml.dom import minidom
import unit
#from level import Level
#import level
import math
from server_messaging import *
from threading import Thread
import time
import logging
import logging.handlers
import sys, traceback
import cPickle as pickle
import util
from player import Player
from util import compileEnemyUnit, compileUnit, compileState
import copy
from util import OBSERVER_ID
from strain.share import *

notify = util.Notify()


LEVELS_ROOT = "./data/levels/"


class Engine( Thread ):
    
        
    __index_uid = 0

    def getUID(self):
        Engine.__index_uid += 1
        return Engine.__index_uid -1
    

        
    #====================================init======================================0
    def __init__(self):
        Thread.__init__(self)
        notify.info("------------------------Engine Starting------------------------")

        self.stop = False
        self.level = None         
        self.players = []
        self.units = {}
        
        self.turn = 0
        self.active_player = None
                
        self.name = "EngineThread"

        self.observer = Player( OBSERVER_ID, 'observer', None )
        self.observer.defeated = True


    def run(self):
        engine._instance = self
        print "Engine started"
        EngMsg.startServer( notify )
        
        lvl = "level2.txt"
        self.level = Level( LEVELS_ROOT + lvl )
        notify.info("Loaded level:%s", lvl )

        self.loadArmyList()
      
        self.firstTurn()

        
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        while( self.stop == False ):

            time.sleep( 0.1 )

            #see if there is a new client connected
            EngMsg.handleConnections()

            #get a message if there is one
            msg = EngMsg.readMsg()
            if msg:
                self.handleMsg( msg[0], msg[1] )
        
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        #+++++++++++++++++++++++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++++++++++++++++++
        
        #we are shutting down everything   
        EngMsg.stopServer()       
        
        notify.info( "++++++++++++++++++++++++Engine stopped!++++++++++++++++++++++++" )
        
        #restart server 
        Engine().start()
        
        return 0


    def handleMsg(self, msg, source):
        """This method is the main method for handling incoming messages to the Engine"""     
        
        if( msg[0] == ENGINE_SHUTDOWN ):
            EngMsg.error("Server is shutting down")
            self.stop = True
            
        elif( msg[0] == MOVE ):            
            self.moveUnit( msg[1]['unit_id'], msg[1]['new_position'], msg[1]['orientation'], source )
            
        elif( msg[0] == LEVEL ):                
            EngMsg.sendLevel( util.compileLevel( self.level ), source )
                        
        elif( msg[0] == ENGINE_STATE ):                
            EngMsg.sendState( util.compileState( self, self.findPlayer( source ) ), source )
            
        elif( msg[0] == END_TURN ):
            self.endTurn( source )
                        
        elif( msg[0] == CHAT ):
            self.chat( msg[1], source, msg[2] )
                        
        elif( msg[0] == OVERWATCH ):
            self.unitUpdate( msg[1], OVERWATCH, source)
                        
        elif( msg[0] == SET_UP ):
            self.unitUpdate( msg[1], SET_UP, source)
                        
        elif( msg[0] == SHOOT ):
            self.handleShoot( msg[1]['shooter_id'], msg[1]['target_id'], source )
                        
        else:
            notify.error( "Unknown message Type: %s", msg )
        
 
        
    def unitUpdate(self, unit_id, param, source ):

        unit = self.findAndValidateUnit( unit_id, source )
        player = self.findPlayer( source )
        
        if player != self.active_player:
            EngMsg.error( "It is not your turn.", source )
            return                    
        
        if param == OVERWATCH:
            if unit.ap >= 2:
                unit.overwatch = not unit.overwatch
            else:
                EngMsg.error("Not enough AP for overwatch.", source)
            
        if param == SET_UP:
            if not unit.hasHeavyWeapon():
                EngMsg.error( "The unit does not have any heavy weapons.", source )
                return

            if unit.set_up:
                msg = unit.tearDown()
                if msg:
                    EngMsg.error( msg, source )
                    return
            else:
                msg = unit.setUp()
                if msg:
                    EngMsg.error( msg, source )
                    return
                    
        player.addUnitMsg( compileUnit(unit) )
        self.observer.addUnitMsg( compileUnit(unit) )
        
        
        
    def chat(self, msg, source, to_allies):
        sender = self.findPlayer( source )
        
        for p in self.players:
            if p == sender:
                continue
            if to_allies:
                if p.team == sender.team:
                    p.addChatMsg( msg, sender.name )
            else:                    
                p.addChatMsg( msg, sender.name )
            
        if not to_allies:
            self.observer.addChatMsg( msg, sender.name )
                
                
    def loadArmyList(self):
        
        notify.debug( "Army lists loading" )
        
        xmldoc = minidom.parse('data/base/armylist.xml')
        #print xmldoc.firstChild.toxml()
        
        self.players = []
        self.units = {}
        
        
        for p in xmldoc.getElementsByTagName( 'player' ):
            player = Player( p.attributes['id'].value, p.attributes['name'].value, p.attributes['team'].value )                        
            
            for u in p.getElementsByTagName( 'unit' ):
                
                x = int( u.attributes['x'].value )
                y = int( u.attributes['y'].value )
                
                unittype = u.attributes['type'].value
                
                #check to see level boundaries
                if( self.level.outOfBounds(x, y) ):
                    print "This unit is out of level bounds", unittype, x, y
                    continue
                
                
                tmpUnit = unit.loadUnit(unittype)
                tmpUnit.init( self.getUID(), player, x, y )                
                tmpUnit.heading = util.getHeading(tmpUnit.pos, self.level.center)

                
                if not self.level.putUnit( tmpUnit ):
                    continue                            
                
                player.units.append( tmpUnit )                
                self.units[tmpUnit.id] = tmpUnit
                
                
            self.players.append( player )
    
        xmldoc.unlink()
        
        notify.info( "Army lists loaded OK" )
                

    def endTurn(self, source):
        
#        player = self.findPlayer( source )       
#        if player != self.active_player:
#            EngMsg.error( "It's not your turn.", source)
#            return
        
        if self.checkVictoryConditions():
            EngMsg.error( "Server restarting" )
            self.observer.saveMsgs()
            time.sleep(3)
            self.stop = True
            return

        self.beginTurn()
        
        
        
    def checkVictoryConditions(self):
        
        #mark all defeated players
        for p in self.players:
            if p.defeated:
                continue
            if not p.units:
                p.addErrorMsg( 'U have no more units... hahahhhah' )
                EngMsg.error( p.name + ' was defeated!!!' )
                p.defeated = True
                
        
        #find a player who is alive, and check if only he/his team are alive
        for p in self.players:
            if not p.defeated:                
                for p2 in self.players:
                    if p == p2 or p.team == p2.team:
                        continue
                    if not p2.defeated:
                        return False
                
                
        #if we came to here, than we have a winning player/team
        #find a winner
        winner = None
        winning_team = None
        for p in self.players:
            if not p.defeated:
                if not winner:
                    winner = p
                else:
                    winning_team = p.team
                    break

        #draw!?
        if not winner and not winning_team:
            for p in self.players:
                p.addErrorMsg( 'a draw.... pathetic...' )
                return True
                if p == self.players[-1]:
                    self.observer.addErrorMsg( 'a draw.... pathetic...' )

        #send derogatory messages to losers
        for p in self.players:
            
            #a team won
            if winning_team:            
                if p.team == winning_team:
                    p.addErrorMsg( 'YOU WIN!!!' )
                else:
                    p.addErrorMsg( 'team ' + winning_team + ' WINS! ...and you lose!' )
            #just one player won
            else:
                if p == winner:
                    p.addErrorMsg( 'YOU WIN!!!' )
                else:
                    p.addErrorMsg( 'player ' + winner.name + ' WINS! ...and you lose!' )

        if winning_team:
            print "winning team:", winning_team
            self.observer.addErrorMsg( "winning team:" + str(winning_team) )
        else:
            print "winner:", winner.name
            self.observer.addErrorMsg( "winner:" + winner.name )
        return True



    def firstTurn(self):
        self.active_player = self.players[0]
        self.turn = 1

        print "turn:", self.turn, "\tplayer:", self.active_player.name

        #check visibility
        self.updateVisibilityAndSendVanishAndSpotMessages()

        #go through all units of active player and reset them
        for unit in self.units.itervalues():   
            if unit.owner == self.active_player:            
                unit.newTurn( self.turn )
                
        for p in self.players:
            #delete all previous msgs (like vanish and spot)
            p.msg_lst = []
            p.addEngineStateMsg( util.compileState(self, p) )
            p.addNewTurnMsg( util.compileNewTurn(self, p) )        
                                     
        self.observer.addEngineStateMsg( util.compileState(self, p) )
        self.observer.addNewTurnMsg( util.compileNewTurn(self, p) )        


    def findNextPlayer(self):
        
        i = 0
        
        if self.active_player == self.players[-1]:
            i = -1
            self.turn += 1
        else:
            i = self.players.index( self.active_player )
        
        tmp_p = None

        for p in self.players[i+1:]:
            if p.defeated:
                continue
            tmp_p = p
            break
        
        if not tmp_p:
            self.turn += 1
            for p in self.players:
                if p.defeated:
                    continue
                self.active_player = p
                return
        else:
            self.active_player = tmp_p
        
             

    def beginTurn(self):

        self.findNextPlayer()

        print "turn:", self.turn, "\tplayer:", self.active_player.name

        #check visibility
        self.updateVisibilityAndSendVanishAndSpotMessages()
        
        #go through all units of active player and reset them
        for unit in self.active_player.units:               
            unit.newTurn( self.turn )

        #send new turn messages       
        for p in self.players:
            p.addNewTurnMsg( util.compileNewTurn(self, p) )
        
        self.observer.addNewTurnMsg( util.compileNewTurn(self, p) )
        

    def getLOS(self, beholder, target ):
        return getLOSOnLevel( beholder.__dict__, target.__dict__, self.level )     

    def _giveDictUnits(self):
        tmp_units = {}
        
        for unt in self.units.itervalues():
            tmp_units[unt.id] = unt.__dict__ 

        return tmp_units


    def _mvdict(self, unit, returnOriginTile):
        
        return getMoveDict(unit.__dict__, self.level, self._giveDictUnits(), returnOriginTile)



    def getPath(self, unit, target_tile ):
        
        #if we are trying to find a path to the tile we are on
        if( target_tile == unit.pos ):
            return[]
        
        moveDict = self._mvdict(unit, True)

        #if target_tile tile is not in the move list
        if target_tile not in moveDict:
            notify.critical("getPath() got an invalid target tile:%s", target_tile )
            raise Exception( "Trying to move to an invalid target_tile:%s", target_tile )
        
        x = target_tile[0]
        y = target_tile[1]
        
        path_list = [ (target_tile, moveDict[target_tile]) ]
        
        tmp_dict_units = self._giveDictUnits()
        
        while( 1 ):
        
            biggest_ap = ( 0, 0 )
            
            #find a tile with biggest remaining AP next to this one
            for dx in xrange(-1,2):
                for dy in xrange(-1,2):
                    
                    if( dx == 0 and dy == 0 ):
                        continue
                    
                    pt = ( x+dx, y+dy )
                    
                    #check if the point is even in the list
                    if (pt in moveDict) == False:
                        continue
                    
                    #if we can't move here just skip
                    if( canIMoveHere( unit.__dict__, (x,y), dx, dy, self.level, tmp_dict_units ) == False ):
                        continue
                    
                    #if we are looking at the origin, and we can move there, we just checked that, stop
                    if( x + dx == unit.pos[0] and y + dy == unit.pos[1] ):
                        path_list.reverse()
                        return path_list
                    
                    #finally we can check the tile 
                    if( moveDict[pt] > biggest_ap[1] ):
                        biggest_ap =  (pt, moveDict[pt])
                    
            
            path_list.append( biggest_ap )
            x = biggest_ap[0][0]
            y = biggest_ap[0][1]
        
      
        raise Exception( "hahahah how did you get to this part of code?" )
        
                
    def findAndValidateUnit(self, unit_id, source):
        if( unit_id in self.units ) == False:
            notify.critical( "Got wrong unit id:%s", unit_id )
            EngMsg.error( "Wrong unit id.", source )
            return None

        unit = self.units[unit_id]

        #check to see if this is the owner
        if unit.owner.connection != source:
            notify.critical( "Client:%s\ttried to do an action with unit that he does not own" % source.getAddress() )
            EngMsg.error( "You cannot do this to a unit you do not own.", source )
            return None

        return unit
        
        
    def validatePlayer(self, source):
        if self.active_player.connection == source:
            return True
        
        EngMsg.error( 'It is not your turn.', source )
        return False
        
        
    def moveUnit(self, unit_id, new_position, new_heading, source ):

        if not self.validatePlayer( source ):
            return

        unit = self.findAndValidateUnit( unit_id, source )
        if not unit:
            return
        
        #check if we are unable to move
        if unit.pos != new_position:
            msg = unit.amIStuck()
            if msg:
                EngMsg.error( msg, source )            
                return 
        
        #list that we will send to owning player        
        my_actions = []
        
        #this is for parsing overwatch msgs
        res_overwatch = None
        
        #dict where we will fill out actions for other players that they see
        actions_for_others = {}
        #fill it up with empty lists
        for p in self.players:
            if p.connection == source:
                continue
            actions_for_others[p] = []                                    
                                    
        #special case if we just need to rotate the unit
        if unit.pos == new_position:
            
            #see if we actually need to rotate the unit
            if unit.rotate( new_heading ):
                my_actions.append( (ROTATE, new_heading) )
                for p in self.players:
                    if unit in p.visible_enemies:
                        actions_for_others[p].append( (ROTATE, new_heading) )
            #if not, than do nothing
            else:
                return
            
        #otherwise do the whole moving thing
        else:
            try:
                path = self.getPath( unit, new_position )
            except Exception:
                notify.critical( "Exception:%s", sys.exc_info()[1] )
                EngMsg.error( sys.exc_info()[1], source )
                return   
            
            #everything checks out, do the actual moving
            for tile, ap_remaining in path:
                
                self.level.removeUnit( unit )
                unit.rotate( tile )                
                unit.move( tile, ap_remaining )
                self.level.putUnit( unit )            
                                    
                my_actions.append( (MOVE, tile ) )              
                                 
                for p in self.players:
                    if unit in p.visible_enemies: 
                        actions_for_others[p].append( (MOVE, tile ) )
                 
                self.checkEnemyVision( unit, actions_for_others )
                
                res_spot = self.didISpotAnyone( unit )
                res_overwatch = self.checkForOverwatch( unit ) 
                if res_spot or res_overwatch:
                    if res_spot:
                        my_actions.extend( res_spot )
                    if res_overwatch:
                        my_actions.extend( res_overwatch )
                    break

                
                #if this is the last tile than apply last orientation change
                if( tile == path[-1][0] ):
                    if unit.rotate( new_heading ):
                        my_actions.append( ( ROTATE, new_heading) )
                    
                    for p in self.players:
                        if unit in p.visible_enemies: 
                            actions_for_others[p].append( (ROTATE, new_heading) )

        #so we know which units to update with UNIT msgs            
        unit_ids_involved = { unit.id:0 }
                    
        if res_overwatch:          
            for p in self.players:
                #skip the owner of unit  
                if p.connection == source:
                    continue
                
                for ov_msg in res_overwatch:                
                    tmp_shoot_msg = copy.deepcopy( ov_msg[1] )
                    for m in tmp_shoot_msg[:]:
                        if m[0] == ROTATE:
                            tmp_unit_id = m[1]
                            tmp_unit = self.units[tmp_unit_id]
                            #if we dont see this unit, remove the rotate msg                    
                            if tmp_unit.owner != p and tmp_unit not in p.visible_enemies:
                                tmp_shoot_msg.remove( m )
        
                        elif m[0] == SHOOT or m[0] == 'melee':
                            sht, tmp_unit_id, pos, wpn, lst = m
                            tmp_unit = self.units[tmp_unit_id]
                            #if we dont see the shooter, remove him and his position
                            if p != tmp_unit.owner and tmp_unit not in p.visible_enemies:
                                tmp_unit_id = -1
                                pos = None
                            #go through list of targets and if we dont see the target, remove it from the list
                            for effect in lst[:]:
                                tmp_target_id = effect[1]
                                trgt = self.units[tmp_target_id]
                                if trgt.owner != p and trgt not in p.visible_enemies:
                                    lst.remove( effect )
                                    
                            i = tmp_shoot_msg.index(m)
                            tmp_shoot_msg.pop( i )
                            new = (sht, tmp_unit_id, pos, wpn, lst)
                            tmp_shoot_msg.insert( i, new )
                            
                            if tmp_unit_id == -1 and not lst:
                                #if you dont see anyone, u just need to get message that someone fired a weapon
                                actions_for_others[p].append( tmp_shoot_msg[0] )
                            else:
                                actions_for_others[p].append( ('overwatch', tmp_shoot_msg) )
                            
            
            #find all units involved in this mess: moving unit and multiple shooters and targets
            for cmd2 in res_overwatch:
                for cmd in cmd2[1]:
                    if cmd[0] == ROTATE:
                        unit_ids_involved[ cmd[1] ] = 0
                    elif cmd[0] == SHOOT:
                        unit_ids_involved[ cmd[1] ] = 0
                        for trgt in cmd[4]:
                            unit_ids_involved[ trgt[1] ] = 0
            
        #send everything to owner of moving unit
        player = self.findPlayer( source )
        player.addMoveMsg( unit.id, my_actions )
        self.observer.addMoveMsg( unit.id, my_actions )
        
        #send stuff that other players need to see
        for plyr in actions_for_others:
            if actions_for_others[plyr]:
                plyr.addMoveMsg( unit.id, actions_for_others[plyr] )

        
        for tmp_unit_id in unit_ids_involved:
            tmp_unit = self.units[tmp_unit_id] 
            for p in self.players:
                if tmp_unit.owner == p or tmp_unit.owner.team == p.team:
                    p.addUnitMsg( util.compileUnit(tmp_unit) )                                        
                else:
                    if tmp_unit in p.visible_enemies:
                        p.addUnitMsg( util.compileEnemyUnit(tmp_unit) )
                        
            self.observer.addUnitMsg( util.compileUnit(tmp_unit) )                     
            
        self.removeDeadUnits()
        
            
    def checkForOverwatch(self, unit ):
        
        ret_actions = []
        
        for p in self.players:
            if p == unit.owner:
                continue
            
            for enemy in p.units:
                vis = self.getLOS( enemy, unit ) 
                if vis:
                    if enemy.overwatch and enemy.inFront( unit.pos ) and enemy.alive:
                        res = enemy.doOverwatch( unit, vis )
                        if res:
                            ret_actions.append( ('overwatch', res ) )
                        if not unit.alive:
                            break
        
        
        return ret_actions
    
    
    def checkEnemyVision(self, unit, actions_for_others ):
            
        #go through all enemy players, if we see this unit we need to spot or vanish someone
        for p in self.players:
            if p == unit.owner:
                continue
            
            seen = 0
            
            for enemy in p.units:
                if self.getLOS( enemy, unit ):
                    seen = 1
                    break
            
            if seen:
                if unit not in p.visible_enemies:
                    p.visible_enemies.append( unit )
                    actions_for_others[ p ].append( ( SPOT, compileEnemyUnit(unit) ) )
            else:
                if unit in p.visible_enemies:
                    p.visible_enemies.remove( unit )
                    actions_for_others[ p ].append( ( VANISH, unit.id ) )
                
    
    
    def didISpotAnyone(self, unit ):
        spotted = self.checkMyVision( unit )        
        ret_actions = []        
        
        if spotted:
            for enemy in spotted:
                unit.owner.visible_enemies.append( enemy )
                ret_actions.append( ( SPOT, util.compileEnemyUnit(enemy)) )
                        
        return ret_actions
    
    
    def checkMyVision(self, unit):
        
        #we moved this unit, so we need visibility to every enemy unit, and stop movement if this unit
        #sees anything or if an enemy unit on overwatch sees this unit
        spotted = []

        for player in self.players:
            if player == unit.owner or player.team == unit.owner.team:
                continue        
        
            for enemy in player.units:
                if enemy not in unit.owner.visible_enemies and self.getLOS( unit, enemy ):
                    spotted.append( enemy )
                            
        return spotted
            

    def handleShoot(self, shooter_id, target_id, source ):
        
        if not self.validatePlayer( source ):
            return
        
        shooter = self.findAndValidateUnit( shooter_id, source )
        
        if not shooter:
            return
        
        if( target_id in self.units ) == False:
            notify.critical( "Got wrong target id:%s", target_id )
            EngMsg.error( "Wrong target id.", source )
            return

        target = self.units[target_id]

        #check to see if the owner is trying to shoot his own units
        if target.owner.connection == source:
            notify.critical( "Client:%s\ttried to shoot his own unit." % source.getAddress() )
            EngMsg.error( "You cannot shoot you own units.", source )
            return
        
        
        vis = self.getLOS( shooter, target )
        if not vis:
            EngMsg.error( "No line of sight to target.", source)
            return
                 
        
        if shooter.hasHeavyWeapon() and shooter.set_up == False:
            if util.distanceTupple(shooter.pos, target.pos) > 2:
                EngMsg.error( "Need to set up heavy weapon before shooting.", source )
                return
        
        #---------------- main shoot event ------------------------
        shoot_msg = shooter.shoot( target, vis )
         
        #if nothing happened, just return
        if not shoot_msg:
            return
                
                
        res = self.checkForOverwatch( shooter )
        if res:
            shoot_msg.extend( res )
                
                            
                
        #check visibility for each player
        for p in self.players:

            #if this player is the one doing the shooting send him everything
            if shooter.owner == p:
                p.addShootMsg( shoot_msg )
                self.observer.addShootMsg( shoot_msg )
                
            else:
                #example message = [(ROTATE, 0, 3), (SHOOT, 0, (4, 7), u'Bolt Pistol', [('bounce', 6)])]
                tmp_shoot_msg = copy.deepcopy(shoot_msg)
                for m in tmp_shoot_msg[:]:

                    if m[0] == ROTATE:
                        unit_id = m[1]
                        #if we dont see this unit, remove the rotate msg                    
                        if self.units[unit_id].owner != p and self.units[unit_id] not in p.visible_enemies:
                            tmp_shoot_msg.remove( m )

                    elif m[0] == SHOOT or m[0] == 'melee':
                        sht, unit_id, pos, wpn, lst = m

                        #if we dont see the shooter, remove him and his position
                        if self.units[unit_id] not in p.visible_enemies:
                            unit_id = -1
                            pos = None
                        #go through list of targets and if we dont see the target, remove it from the list
                        for effect in lst[:]:
                            tmp_target_id = effect[1]
                            if self.units[tmp_target_id].owner != p and self.units[tmp_target_id] not in p.visible_enemies:
                                lst.remove( effect )
                                
                        i = tmp_shoot_msg.index(m)
                        tmp_shoot_msg.pop( i )
                        new = (sht, unit_id, pos, wpn, lst)
                        tmp_shoot_msg.insert( i, new )
                        
                        p.addShootMsg( tmp_shoot_msg )


        #find all units involved in shooting: shooter and (multiple) targets, and update them
        unit_ids_involved = { shooter.id:0, target.id:0 }
        for cmd in shoot_msg:
            if cmd[0] == SHOOT: 
                for trgt in cmd[4]:
                    unit_ids_involved[ trgt[1] ] = 0
            elif cmd[0] == 'overwatch': 
                for cmd2 in cmd[1]:
                    if cmd2[0] == ROTATE:
                        unit_ids_involved[ cmd2[1] ] = 0
                    elif cmd2[0] == SHOOT:
                        for trgt in cmd2[4]:
                            unit_ids_involved[ trgt[1] ] = 0
                        
        for unit_id in unit_ids_involved:
            unit = self.units[unit_id] 
            for p in self.players:
                if unit.owner == p or unit.owner.team == p.team:
                    p.addUnitMsg( util.compileUnit(unit) )                                        
                else:
                    if unit in p.visible_enemies:
                        p.addUnitMsg( util.compileEnemyUnit(unit) )
                        
            self.observer.addUnitMsg( util.compileUnit(unit) )

        self.removeDeadUnits()
        
        self.updateVisibilityAndSendVanishAndSpotMessages()
        
            
        
        
    def updateVisibilityAndSendVanishAndSpotMessages(self):
        
        #remove enemies that we don't see anymore, and send vanish messages
        for p in self.players:
            
            tmp_enemy_list = []
            for enemy in p.visible_enemies:
                for myunit in p.units:
                    if enemy not in tmp_enemy_list and self.getLOS( myunit, enemy ):
                        tmp_enemy_list.append( enemy )
                        
            #compare tmp_enemy_list with old enemy list
            for enemy in p.visible_enemies[:]:
                
                #if there is an enemy that vanished, send a message to player and remove it from visible list 
                if enemy not in tmp_enemy_list:
                    p.addMsg( (VANISH, enemy.id) )
                    p.visible_enemies.remove( enemy )
                    
        
        #add new enemies
        for p in self.players:
            for enemy in self.units.itervalues():
                if enemy.owner == p or enemy.owner.team == p.team:
                    continue
                
                for myunit in p.units:
                    if enemy not in p.visible_enemies and self.getLOS( myunit, enemy ):
                        p.visible_enemies.append( enemy )
                        p.addMsg( ( SPOT, util.compileEnemyUnit(enemy)) )
        
        
    def removeDeadUnits(self):
        
        for unit in self.units.values():
            if unit.alive:
                continue
                
            notify.info("Unit:%s died", unit.id )
            print "unit died:", unit.id
            
            del self.units[unit.id]
            
            self.level.removeUnit( unit )
            
            for p in self.players:            
                if unit in p.units:
                    p.units.remove( unit )
                if unit in p.visible_enemies:
                    p.visible_enemies.remove( unit )
                if unit in p.detected_enemies:
                    p.detected_enemies.remove( unit )


    def findPlayer( self, source ):
        for p in self.players:
            if p.connection == source:
                return p


if __name__ == "__main__":
    Engine().start()
