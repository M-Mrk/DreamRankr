from db import db, Players, OnGoingMatches, PlayerBonuses, PlayerRankings
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

    # Get the correct rankings for the specific ranking context
    challengerRanking = PlayerRankings.query.filter_by(playerId=match.challengerId, rankingId=match.rankingId).first()
    defenderRanking = PlayerRankings.query.filter_by(playerId=match.defenderId, rankingId=match.rankingId).first()

    if not challengerRanking or not defenderRanking:
        log(3, 'getBonus', f"Could not find ranking for challenger {match.challengerId} or defender {match.defenderId} in ranking {match.rankingId}")
        return Bonus()

    challenger_rank = challengerRanking.ranking
    defender_rank = defenderRanking.ranking

    if challengerBonusEntry and compareFromStr(defender_rank, challengerBonusEntry.logicOperator, challengerBonusEntry.limitRanking):
        challengerBonus = challengerBonusEntry.bonus
    if defenderBonusEntry and compareFromStr(challenger_rank, defenderBonusEntry.logicOperator, defenderBonusEntry.limitRanking):
        defenderBonus = defenderBonusEntry.bonus
    
    return Bonus(challenger=challengerBonus, defender=defenderBonus)