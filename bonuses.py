from db import db, Players, OnGoingMatches, PlayerBonuses, PlayerRankings
from logger import log

class Bonus:
    """
    Simple data class to hold bonus points for challenger and defender.
    Used to return calculated bonus points from bonus determination functions.
    """
    def __init__(self, challenger=0, defender=0):
        """
        Initialize bonus object with default values of 0.
        
        Args:
            challenger: Bonus points for the challenging player
            defender: Bonus points for the defending player
        """
        self.challenger = challenger
        self.defender = defender

def compareFromStr(ranking, operator, limitRanking):
    """
    Compares two ranking values using a string operator.
    Used to determine if bonus conditions are met based on opponent's ranking.
    
    Args:
        ranking: Current player's ranking position (integer)
        operator: Comparison operator as string ("=", "<", "<=", ">", ">=")
        limitRanking: Threshold ranking for comparison (integer)
        
    Returns:
        bool: True if comparison condition is met, False otherwise
    """
    try:
        if not operator:
            log(3, 'compareFromStrForBonus', f"Provided operator was empty: {operator}")
            return False
        
        # Convert rankings to integers for comparison
        ranking = int(ranking)
        limitRanking = int(limitRanking)
        
        # Perform comparison based on operator
        if operator == "=":
            result = ranking == limitRanking
        elif operator == "<":
            result = ranking < limitRanking
        elif operator == "<=":
            result = ranking <= limitRanking
        elif operator == ">":
            result = ranking > limitRanking
        elif operator == ">=":
            result = ranking >= limitRanking
        else:
            log(3, 'compareFromStrForBonus', f"Unknown operator: {operator}")
            return False
            
        log(1, 'compareFromStrForBonus', 
            f"Comparison: {ranking} {operator} {limitRanking} = {result}")
        return result
        
    except (ValueError, TypeError) as e:
        log(4, 'compareFromStrForBonus', f"Error in ranking comparison: {e}")
        return False
    except Exception as e:
        log(4, 'compareFromStrForBonus', f"Unexpected error in bonus comparison: {e}")
        return False

def getBonus(match):
    """
    Calculates bonus points for both players in a match based on their bonus conditions.
    Evaluates each player's bonus rules against their opponent's ranking.
    
    Args:
        match: OnGoingMatch object containing challenger and defender information
        
    Returns:
        Bonus: Object containing calculated bonus points for challenger and defender
    """
    try:
        if not match:
            log(3, 'getBonus', "Match object is None")
            return Bonus()
            
        # Get bonus entries for both players
        challengerBonusEntry = PlayerBonuses.query.filter_by(playerId=match.challengerId).first()
        defenderBonusEntry = PlayerBonuses.query.filter_by(playerId=match.defenderId).first()
        
        # Initialize bonus amounts
        challengerBonus = 0
        defenderBonus = 0

        # Get ranking information for both players in this specific ranking
        challengerRanking = PlayerRankings.query.filter_by(
            playerId=match.challengerId, 
            rankingId=match.rankingId
        ).first()
        defenderRanking = PlayerRankings.query.filter_by(
            playerId=match.defenderId, 
            rankingId=match.rankingId
        ).first()

        if not challengerRanking or not defenderRanking:
            log(3, 'getBonus', 
                f"Missing ranking data - Challenger: {match.challengerId}, Defender: {match.defenderId}, Ranking: {match.rankingId}")
            return Bonus()

        challenger_rank = challengerRanking.ranking
        defender_rank = defenderRanking.ranking

        # Check challenger's bonus condition against defender's ranking
        if challengerBonusEntry:
            try:
                if compareFromStr(defender_rank, challengerBonusEntry.logicOperator, challengerBonusEntry.limitRanking):
                    challengerBonus = challengerBonusEntry.bonus
                    log(1, 'getBonus', 
                        f"Challenger bonus activated: {challengerBonus} points "
                        f"(defender rank {defender_rank} {challengerBonusEntry.logicOperator} {challengerBonusEntry.limitRanking})")
            except Exception as e:
                log(4, 'getBonus', f"Error evaluating challenger bonus: {e}")
                
        # Check defender's bonus condition against challenger's ranking
        if defenderBonusEntry:
            try:
                if compareFromStr(challenger_rank, defenderBonusEntry.logicOperator, defenderBonusEntry.limitRanking):
                    defenderBonus = defenderBonusEntry.bonus
                    log(1, 'getBonus', 
                        f"Defender bonus activated: {defenderBonus} points "
                        f"(challenger rank {challenger_rank} {defenderBonusEntry.logicOperator} {defenderBonusEntry.limitRanking})")
            except Exception as e:
                log(4, 'getBonus', f"Error evaluating defender bonus: {e}")
        
        return Bonus(challenger=challengerBonus, defender=defenderBonus)
        
    except Exception as e:
        log(4, 'getBonus', f"Unexpected error calculating bonuses: {e}")
        return Bonus()

def updateOrCreatePlayerBonus(playerId, bonus, logicOperator, limitRanking):
    """
    Updates an existing player bonus or creates a new one if none exists.
    Validates all parameters before database operations.
    
    Args:
        playerId: ID of the player to update bonus for
        bonus: Bonus points amount (integer as string)
        logicOperator: Comparison operator for bonus condition
        limitRanking: Ranking threshold for bonus activation (integer as string)
    
    Returns:
        bool: True if successful, False if validation fails or error occurs
    """
    try:
        # Validate all required parameters are provided
        if not (bonus and logicOperator and limitRanking):
            log(3, "updateOrCreatePlayerBonus", f"Missing bonus parameters for player {playerId}")
            return False
            
        # Check for empty string values
        if bonus == "" or logicOperator == "" or limitRanking == "":
            log(3, "updateOrCreatePlayerBonus", f"Empty bonus parameters for player {playerId}")
            return False
            
        # Validate player exists
        player = db.session.get(Players, playerId)
        if not player:
            log(3, "updateOrCreatePlayerBonus", f"Player {playerId} not found")
            return False
            
        # Check for existing bonus entry
        existing_bonus = PlayerBonuses.query.filter_by(playerId=playerId).first()
        
        if existing_bonus:
            # Update existing bonus
            existing_bonus.bonus = int(bonus)
            existing_bonus.logicOperator = logicOperator
            existing_bonus.limitRanking = int(limitRanking)
            log(1, "updateOrCreatePlayerBonus", 
                f"Updated bonus for player {player.name}({player.id}): {bonus} {logicOperator} {limitRanking}")
        else:
            # Create new bonus entry
            new_bonus = PlayerBonuses(
                playerId=int(playerId),
                bonus=int(bonus),
                logicOperator=logicOperator,
                limitRanking=int(limitRanking)
            )
            db.session.add(new_bonus)
            log(1, "updateOrCreatePlayerBonus", 
                f"Created bonus for player {player.name}({player.id}): {bonus} {logicOperator} {limitRanking}")
        
        # Commit changes to database
        db.session.commit()
        return True
        
    except (ValueError, TypeError) as e:
        db.session.rollback()
        log(4, "updateOrCreatePlayerBonus", f"Invalid data types for player {playerId}: {e}")
        return False
    except Exception as e:
        db.session.rollback()
        log(4, "updateOrCreatePlayerBonus", f"Could not update/create bonus for player {playerId}: {e}")
        return False

def validateBonusParameters(bonus, logicOperator, limitRanking):
    """
    Validates that all bonus parameters are provided and not empty.
    Used for form validation before attempting database operations.
    
    Args:
        bonus: Bonus points value
        logicOperator: Comparison operator
        limitRanking: Ranking limit value
    
    Returns:
        bool: True if all parameters are valid, False otherwise
    """
    try:
        # Check that all parameters exist and are not empty strings
        valid = (bonus and logicOperator and limitRanking and 
                bonus != "" and logicOperator != "" and limitRanking != "")
        
        log(1, "validateBonusParameters", 
            f"Validation result: {valid} for bonus: {bonus}, operator: {logicOperator}, limit: {limitRanking}")
        
        return valid
        
    except Exception as e:
        log(4, "validateBonusParameters", f"Error validating bonus parameters: {e}")
        return False