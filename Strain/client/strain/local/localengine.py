from panda3d.core import *
from strain.share import *

class LocalEngine():
    def __init__(self, parent):
        self.parent = parent
        self.level = None
    
    def refreshUnit(self, unit):
        if unit['alive'] == False:
            if self.parent.sel_unit_id == unit['id']:
                self.parent.sel_unit_id = None
            
            self.parent.render_manager.deleteUnit(unit['id'])

            if self.units.has_key(unit['id']):
                self.units.pop(unit['id'])
            self.level.removeUnitDict(unit)
        else:
            self.units[unit['id']] = unit
            self.level.removeUnitId(unit['id'])
            self.level.putUnitDict(unit)
            
    def refreshLevelUnitDict(self):
        for unit in self.units.itervalues():
            self.level.removeUnitDict(unit)
            self.level.putUnitDict(unit)
            

    def deleteUnit(self, unit_id):
        self.level.removeUnitId(unit_id)
        self.units.pop(unit_id)
        
    def isUnitAlive(self, unit_id):
        return self.units[unit_id]['alive']
    
    def isThisEnemyUnit(self, unit_id):
        if self.units.has_key(unit_id):
            if self.units[unit_id]['owner_id'] != self.parent.player_id:
                return True
            else:
                return False
        else:
            return False 
        
    def isThisMyUnit(self, unit_id):
        if self.units.has_key(unit_id):
            if self.units[unit_id]['owner_id'] == self.parent.player_id:
                return True
            else:
                return False
        else:
            return False
        
    def getCoordsByUnit(self, unit_id):
        if self.units.has_key(unit_id):
            unit = self.units[unit_id]
        return Point2(unit['pos'][0], unit['pos'][1])  
        