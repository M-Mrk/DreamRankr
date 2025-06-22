from db import db, Players, OnGoingMatches, PlayerBonuses
from logger import log

class Bonus:
    def __init__(self, challenger=0, defender=0):
        self.challenger = challenger
        self.defender = defender

def compareFromStr(ranking, operator, limitRanking):
    if not operator:
        log(3, 'compareFromStrForBonus', f"Provided operator was empty: {operator}")
        return False
    
    if operator == "=":
        return ranking == limitRanking
        
    elif operator == "<":
        return ranking < limitRanking
        
    elif operator == "<=":
        return ranking <= limitRanking
    
    elif operator == ">":
        return ranking > limitRanking
        
    elif operator == ">=":
        return ranking >= limitRanking
        
    else:
        log(3, 'compareFromStrForBonus', f"Could not understand provided operator: {operator}")
        return False

def getBonus(match):
    challenger = db.session.get(Players, match.challengerId)
    defender = db.session.get(Players, match.defenderId)
    challengerBonusEntry = PlayerBonuses.query.filter_by(playerId=match.challengerId).first()
    defenderBonusEntry = PlayerBonuses.query.filter_by(playerId=match.defenderId).first()
    challengerBonus = 0
    defenderBonus = 0

    if challengerBonusEntry and compareFromStr(defender.ranking, challengerBonusEntry.logicOperator, challengerBonusEntry.limitRanking):
        challengerBonus = challengerBonusEntry.bonus
    if defenderBonusEntry and compareFromStr(challenger.ranking, defenderBonusEntry.logicOperator, defenderBonusEntry.limitRanking):
        defenderBonus = defenderBonusEntry.bonus
    
    return Bonus(challenger=challengerBonus, defender=defenderBonus)