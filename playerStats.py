from db import db, Players, PlayerRankings
from logger import log
from datetime import datetime, timezone

def checkIfWinnerIsLower(winner, loser, rankingId):
    """
    Determines if the winning player has a lower (worse) ranking than the losing player.
    Used to decide if ranking positions should be swapped after a match.
    
    Args:
        winner: Player object of the match winner
        loser: Player object of the match loser
        rankingId: ID of the ranking where the match took place
        
    Returns:
        bool: True if winner's ranking is numerically higher (worse position), False otherwise
        
    Raises:
        Exception: Logs error if ranking information cannot be retrieved
    """
    try:
        # Get ranking positions for both players in the specific ranking
        winner_ranking = PlayerRankings.query.filter_by(playerId=winner.id, rankingId=rankingId).first()
        loser_ranking = PlayerRankings.query.filter_by(playerId=loser.id, rankingId=rankingId).first()
        
        if not winner_ranking or not loser_ranking:
            log(3, "checkIfWinnerIsLower", 
                f"Missing ranking data - Winner: {winner_ranking}, Loser: {loser_ranking}")
            return False
            
        # Lower ranking number = better position, so winner is "lower" if their number is higher
        is_lower = winner_ranking.ranking > loser_ranking.ranking
        
        log(1, "checkIfWinnerIsLower", 
            f"Winner {winner.name}(rank {winner_ranking.ranking}) vs Loser {loser.name}(rank {loser_ranking.ranking}) - Lower: {is_lower}")
            
        return is_lower
        
    except Exception as e:
        log(4, "checkIfWinnerIsLower", f"Error checking rankings: {e}")
        return False

def rankPlayerUp(player, rankingId):
    """
    Moves a player up one position in the ranking by swapping with the next higher-ranked player.
    Updates both players' ranking history and timestamps.
    
    Args:
        player: Player object to move up in ranking
        rankingId: ID of the ranking to update
        
    Returns:
        None
        
    Raises:
        Exception: Logs error if ranking update fails
    """
    try:
        # Get current player's ranking information
        playerRanking = PlayerRankings.query.filter_by(playerId=player.id, rankingId=rankingId).first()
        if not playerRanking:
            log(3, "rankPlayerUp", f"Player ranking not found for player {player.id} in ranking {rankingId}")
            return
            
        currentRanking = playerRanking.ranking
        newRanking = currentRanking - 1  # Moving up means lower number
        
        # Cannot move up from position 1
        if newRanking < 1:
            log(3, "rankPlayerUp", f"Cannot move player {player.name} above position 1")
            return
            
        # Find the player currently at the target position
        otherPlayerRanking = PlayerRankings.query.filter_by(ranking=newRanking, rankingId=rankingId).first()
        if not otherPlayerRanking:
            log(3, "rankPlayerUp", 
                f"No player found at ranking {newRanking} in rankingId {rankingId}")
            return
        
        # Get the other player's information for logging
        otherPlayer = Players.query.filter_by(id=otherPlayerRanking.playerId).first()
        if not otherPlayer:
            log(3, "rankPlayerUp", 
                f"Other player not found with ID: {otherPlayerRanking.playerId}")
            return
        
        # Update both players' ranking history before swapping
        playerRanking.lastRanking = currentRanking
        playerRanking.lastRankingChanged = datetime.now(timezone.utc)
        otherPlayerRanking.lastRanking = otherPlayerRanking.ranking
        otherPlayerRanking.lastRankingChanged = datetime.now(timezone.utc)
        
        # Perform the ranking swap
        playerRanking.ranking = newRanking
        otherPlayerRanking.ranking = currentRanking
        
        db.session.commit()
        
        log(1, "rankPlayerUp", 
            f"{player.name}({player.id}) moved up from {currentRanking} to {playerRanking.ranking}")
        log(1, "rankPlayerUp", 
            f"{otherPlayer.name}({otherPlayer.id}) moved down from {newRanking} to {otherPlayerRanking.ranking}")
            
    except Exception as e:
        db.session.rollback()
        log(4, "rankPlayerUp", f"Failed to rank up player {player.id}: {e}")

def getMatchesPlayed(player):
    """
    Calculates the total number of matches played by a player across all rankings.
    
    Args:
        player: Player object with wins and losses attributes
        
    Returns:
        int: Total matches played (wins + losses)
    """
    try:
        if not hasattr(player, 'wins') or not hasattr(player, 'losses'):
            log(3, "getMatchesPlayed", f"Player object missing wins/losses attributes")
            return 0
            
        total_matches = (player.wins or 0) + (player.losses or 0)
        log(1, "getMatchesPlayed", f"Player {getattr(player, 'name', 'Unknown')} has played {total_matches} matches")
        return total_matches
        
    except Exception as e:
        log(4, "getMatchesPlayed", f"Error calculating matches for player: {e}")
        return 0

def increaseWinsLosses(winner, loser):
    """
    Increments win count for winner and loss count for loser by 1.
    Updates the players' overall statistics.
    
    Args:
        winner: Player object who won the match
        loser: Player object who lost the match
        
    Returns:
        None
        
    Raises:
        Exception: Logs error if update fails
    """
    try:
        if not winner or not loser:
            log(3, "increaseWinsLosses", "Winner or loser object is None")
            return
            
        # Update win/loss counts
        winner.wins = (winner.wins or 0) + 1
        loser.losses = (loser.losses or 0) + 1
        
        log(1, "increaseWinsLosses", 
            f"Updated stats - Winner {getattr(winner, 'name', 'Unknown')}: {winner.wins} wins, "
            f"Loser {getattr(loser, 'name', 'Unknown')}: {loser.losses} losses")
            
    except Exception as e:
        log(4, "increaseWinsLosses", f"Error updating win/loss stats: {e}")

def updatePoints(player, rankingId, won):
    """
    Updates a player's points in a specific ranking.
    Awards 2 points for winning, 1 point for participating.
    
    Args:
        player: Player object to update points for
        rankingId: ID of the ranking to update points in
        won: Boolean indicating if the player won the match
        
    Returns:
        None
        
    Raises:
        Exception: Logs error if point update fails
    """
    try:
        if not player:
            log(3, "updatePoints", "Player object is None")
            return
            
        # Get player's ranking entry for this specific ranking
        playerRanking = PlayerRankings.query.filter_by(playerId=player.id, rankingId=rankingId).first()
        if not playerRanking:
            log(3, "updatePoints", f"No ranking entry found for player {player.id} in ranking {rankingId}")
            return
            
        # Award points based on match outcome
        points_to_add = 2 if won else 1
        oldPoints = playerRanking.points or 0
        playerRanking.lastPoints = oldPoints
        playerRanking.points = oldPoints + points_to_add
        
        log(1, "updatePoints", 
            f"Player {getattr(player, 'name', 'Unknown')} points updated from {oldPoints} to {playerRanking.points} "
            f"in ranking {rankingId} ({'won' if won else 'participated'})")
            
    except Exception as e:
        log(4, "updatePoints", f"Error updating points for player {getattr(player, 'id', 'Unknown')}: {e}")

def changeSetStats(player, wonSets, lostSets):
    """
    Updates a player's set statistics by adding won and lost sets.
    
    Args:
        player: Player object to update set stats for
        wonSets: Number of sets won to add
        lostSets: Number of sets lost to add
        
    Returns:
        None
        
    Raises:
        Exception: Logs error if set stats update fails
    """
    try:
        if not player:
            log(3, "changeSetStats", "Player object is None")
            return
            
        if wonSets is None or lostSets is None:
            log(3, "changeSetStats", f"Invalid set counts - won: {wonSets}, lost: {lostSets}")
            return
            
        # Update set statistics
        old_sets_won = player.setsWon or 0
        old_sets_lost = player.setsLost or 0
        
        player.setsWon = old_sets_won + int(wonSets)
        player.setsLost = old_sets_lost + int(lostSets)
        
        log(1, "changeSetStats", 
            f"Player {getattr(player, 'name', 'Unknown')} sets updated - "
            f"Won: {old_sets_won} + {wonSets} = {player.setsWon}, "
            f"Lost: {old_sets_lost} + {lostSets} = {player.setsLost}")
            
    except (ValueError, TypeError) as e:
        log(4, "changeSetStats", f"Invalid set values for player {getattr(player, 'id', 'Unknown')}: {e}")
    except Exception as e:
        log(4, "changeSetStats", f"Error updating set stats: {e}")

def changeStats(winnerId, loserId, winnerSetsWon, loserSetsWon, rankingId):
    """
    Comprehensive function to update all player statistics after a match.
    Handles ranking changes, win/loss records, points, and set statistics.
    
    Args:
        winnerId: ID of the winning player
        loserId: ID of the losing player
        winnerSetsWon: Number of sets won by winner (optional)
        loserSetsWon: Number of sets won by loser (optional)
        rankingId: ID of the ranking where the match took place
        
    Returns:
        None
        
    Raises:
        Exception: Logs error if any stat update fails
    """
    try:
        # Validate input parameters
        if not winnerId or not loserId or not rankingId:
            log(3, "changeStats", f"Invalid parameters - winnerId: {winnerId}, loserId: {loserId}, rankingId: {rankingId}")
            return
            
        # Get player objects
        winner = db.session.get(Players, winnerId)
        loser = db.session.get(Players, loserId)
        
        if not winner:
            log(3, "changeStats", f"Winner with ID {winnerId} not found")
            return
        if not loser:
            log(3, "changeStats", f"Loser with ID {loserId} not found")
            return
            
        log(1, "changeStats", f"Processing match result - Winner: {winner.name}, Loser: {loser.name}")
        
        # Check if winner should move up in ranking
        if checkIfWinnerIsLower(winner, loser, rankingId):
            log(1, "changeStats", "Winner ranked lower than loser - initiating rank up")
            rankPlayerUp(winner, rankingId)
        
        # Update win/loss records
        increaseWinsLosses(winner, loser)
        
        # Update points for both players
        updatePoints(winner, rankingId, won=True)
        updatePoints(loser, rankingId, won=False)
        
        # Update set statistics if provided
        if winnerSetsWon is not None and loserSetsWon is not None:
            changeSetStats(winner, winnerSetsWon, loserSetsWon)
            changeSetStats(loser, loserSetsWon, winnerSetsWon)
        
        # Commit all changes
        db.session.commit()
        log(1, "changeStats", f"Successfully updated all stats for match between {winner.name} and {loser.name}")
        
    except Exception as e:
        db.session.rollback()
        log(4, "changeStats", f"Error updating match stats: {e}")