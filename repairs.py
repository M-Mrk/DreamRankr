from db import db, Players, PlayerRankings
from logger import log

def checkForDeletedPlayers(rankingId):
    """
    Checks for deleted players in a ranking and removes their entries.

    Args:
        rankingId: ID of the ranking to check.
    """
    try:
        rankingEntries = PlayerRankings.query.filter_by(rankingId=rankingId).all()
        if not rankingEntries:
            log(3, "checkForDeletedPlayers", f"No ranking entries found for ranking ID {rankingId}")
            return False

        log(1, "checkForDeletedPlayers", f"Checking for deleted players in ranking ID {rankingId}")
        for entry in rankingEntries:
            try:
                player = db.session.get(Players, entry.playerId)
                if not player:
                    log(2, "checkForDeletedPlayers", f"Player with ID {entry.playerId} does not exist. Removing entry.")
                    db.session.delete(entry)
            except Exception as e:
                log(4, "checkForDeletedPlayers", f"Error while checking player ID {entry.playerId} in ranking ID {rankingId}: {e}")
                continue  # Continue checking other entries

        db.session.commit()
        log(1, "checkForDeletedPlayers", f"Successfully checked and cleaned up deleted players in ranking ID {rankingId}")
        return True

    except Exception as e:
        db.session.rollback()
        log(4, "checkForDeletedPlayers", f"Error while checking for deleted players in ranking ID {rankingId}: {e}")
        return False

def checkForGapInRanking(rankingId):
    """
    Checks for gaps in the ranking order and fixes them if necessary.
    
    Args:
        rankingId: ID of the ranking to check.
    """
    try:
        rankingEntries = PlayerRankings.query.filter_by(rankingId=rankingId).order_by(PlayerRankings.ranking.asc()).all()
        log(1, "checkForGapInRanking", f"Found {len(rankingEntries)} entries: {[r.ranking for r in rankingEntries]}")
        if not rankingEntries:
            log(3, "checkForGapInRanking", f"No ranking entries found for ranking ID {rankingId}")
            return False
        
        if rankingEntries[0].ranking != 1:
            rankingEntries[0].ranking = 1

        rankingEntryBefore = rankingEntries[0].ranking
        
        for ranking in rankingEntries[1:]:
            if rankingEntryBefore + 1 == ranking.ranking:
                rankingEntryBefore = ranking.ranking
                continue
            else:
                log(1, "checkForGapInRanking", f"Gap detected in ranking ID {rankingId}. Fixing...")
                difference = ranking.ranking - (rankingEntryBefore + 1)
                ranking.ranking -= difference
                if ranking.lastRanking:
                    ranking.lastRanking -= difference
                rankingEntryBefore = ranking.ranking

        db.session.commit()
        log(1, "checkForGapInRanking", f"Successfully checked and fixed gaps in ranking ID {rankingId}")
        return True

    except Exception as e:
        db.session.rollback()
        log(4, "checkForGapInRanking", f"Error while checking for gaps in ranking ID {rankingId}: {e}")
        return False

def checkRankingAndFix(rankingId):
    checkForDeletedPlayers(rankingId)
    checkForGapInRanking(rankingId)