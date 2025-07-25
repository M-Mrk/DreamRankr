from db import db, PlayerRankings, Players, OnGoingMatches, PlayerBonuses, FinishedMatches, Rankings, LogEntries
from repairs import checkForGapInRanking
from playerStats import changeStats
from logger import log
import datetime as dt
from functools import wraps
from flask import flash

class RankingObj:
    def __init__(self, ranking=None, points=None, lastRanking=None, lastRankingChanged=None):
        self.ranking = ranking
        self.points = points
        self.lastRanking = lastRanking
        self.lastRankingChanged = lastRankingChanged

def checkIfChangedAndUpdate(formId, player, playerArgument, argumentName, request):
    formArgument = request.form.get(formId)
    if formArgument and not formArgument == playerArgument:
        oldArgument = getattr(player, argumentName)
        setattr(player, argumentName, formArgument)
        try:
            db.session.commit()
            # Log info for successful field update
            log(1, "player_edit", f"Changed {player.name}({player.id}) {argumentName} from {oldArgument} to {formArgument}")
        except Exception as e:
            # Log error if field could not be updated
            log(4, "player_edit", f"Could not change {argumentName} for {player.name}({player.id}) from {oldArgument} to {formArgument}, because of {e}")

def setRankingAndPointsToObj(playerObj, rankingId):
    """
    Sets ranking and points attributes to a player object for a specific ranking.
    """
    try:
        rankingObj = getRankingAndPoints(playerObj.id, rankingId)
        attributes = ["ranking", "points", "lastRanking", "lastRankingChanged"]
        for attribute in attributes:
            setattr(playerObj, attribute, getattr(rankingObj, attribute))
        log(1, "setRankingAndPointsToObj", f"Set ranking and points for player {playerObj.id} in ranking {rankingId}")
    except Exception as e:
        log(4, "setRankingAndPointsToObj", f"Could not get and set Stats, because of {e}")

def getRankingAndPoints(playerId, rankingId):
    """
    Retrieves ranking and points for a player in a specific ranking.
    """
    try:
        playerRankingObj = PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()
        if not playerRankingObj:
            log(3, "getRankingAndPoints", f"No ranking found for player {playerId} in ranking {rankingId}")
            return RankingObj()
        output = RankingObj(
            ranking = playerRankingObj.ranking,
            points = playerRankingObj.points,
            lastRanking = playerRankingObj.lastRanking,
            lastRankingChanged = playerRankingObj.lastRankingChanged
        )
        log(1, "getRankingAndPoints", f"Fetched ranking and points for player {playerId} in ranking {rankingId}")
        return output
    except Exception as e:
        log(4, "getRankingAndPoints", f"Error fetching ranking and points for player {playerId} in ranking {rankingId}: {e}")
        return RankingObj()

def getPlayersOfRanking(rankingId):
    """
    Returns all players in a ranking, ordered by their ranking.
    """
    try:
        ranking = db.session.get(Rankings, rankingId)
        if not ranking:
            log(3, "getPlayersOfRanking", f"Ranking with ID {rankingId} does not exist")
            return []
            
        if ranking.sortedBy == "points":
            order_column = PlayerRankings.points.desc()  # Descending for points
        elif ranking.sortedBy == "standard":
            order_column = PlayerRankings.ranking.asc()  # Ascending for ranking
        else:
            log(4, "getPlayersOfRanking", f"Invalid sorting option '{ranking.sortedBy}' for ranking {rankingId}")
            return []

        players = db.session.query(Players).join(
            PlayerRankings, Players.id == PlayerRankings.playerId
        ).filter(PlayerRankings.rankingId == rankingId).order_by(order_column).all()
        
        for player in players:
            setRankingAndPointsToObj(player, rankingId)
            
        log(1, "getPlayersOfRanking", f"Fetched players for ranking {rankingId}")
        return players
    except Exception as e:
        log(4, "getPlayersOfRanking", f"Error fetching players for ranking {rankingId}: {e}")
        return []

def getRankingOfPlayer(playerId, rankingId):
    """
    Retrieves the ranking of a player in a specific ranking.

    Args:
        playerId: ID of the player.
        rankingId: ID of the ranking.

    Returns:
        The ranking position of the player or None if an error occurs.
    """
    try:
        ranking = db.session.get(Rankings, rankingId)
        if not ranking:
            log(3, "getRankingOfPlayer", f"Ranking with ID {rankingId} does not exist")
            return None

        rankingEntry = getRankingAndPoints(playerId, rankingId)
        if not rankingEntry:
            log(3, "getRankingOfPlayer", f"No ranking entry found for player {playerId} in ranking {rankingId}")
            return None

        if ranking.sortedBy == "standard":
            log(1, "getRankingOfPlayer", f"Returning standard ranking for player {playerId} in ranking {rankingId}")
            return rankingEntry.ranking
        elif ranking.sortedBy == "points":
            allRankingEntries = getPlayersOfRanking(rankingId)
            allRankingEntries.sort(key=lambda player: player.points, reverse=True)
            for index, player in enumerate(allRankingEntries, start=1):
                # Convert both to int to ensure proper comparison
                if int(player.id) == int(playerId):
                    return index
            log(3, "getRankingOfPlayer", f"Player {playerId} not found in points-based ranking for ranking {rankingId}")
            return None
        else:
            log(4, "getRankingOfPlayer", f"Invalid sortedBy option '{ranking.sortedBy}' for ranking {rankingId}")
            return None
    except Exception as e:
        log(4, "getRankingOfPlayer", f"Error retrieving ranking for player {playerId} in ranking {rankingId}: {e}")
        return None

def getActiveMatchesOfRanking(rankingId):
    """
    Returns all active matches for a ranking.
    """
    try:
        activeMatches = OnGoingMatches.query.filter_by(rankingId=rankingId).order_by(OnGoingMatches.timeStarted.asc()).all()
        log(1, "getActiveMatchesOfRanking", f"Fetched active matches for ranking {rankingId}")
        return activeMatches
    except Exception as e:
        log(4, "getActiveMatchesOfRanking", f"Error fetching active matches for ranking {rankingId}: {e}")
        return []

def newPlayer(name, rankingId, bonus, logicOperator, limitRanking):
    """
    Creates a new player and optionally assigns them to a ranking and bonus.
    """
    log(1, "newPlayer", f"Starting to create new player: {name}")
    if not name:
        log(3, "newPlayer", "No name provided for new player")
        return
    try:
        allPlayers = Players.query.all()
        if name in [player.name for player in allPlayers]:
            log(3, "newPlayer", f"Player '{name}' already exists")
            return
        log(1, "newPlayer", f"Creating new player: {name}")
        new_player = Players(
            name=name,
            wins=0,
            losses=0,
            setsWon=0,
            setsLost=0
        )
        db.session.add(new_player)
        db.session.flush()  # Assigns the ID without committing
        log(1, "newPlayer", f"Player '{name}' created with ID: {new_player.id}")
        if rankingId:
            currentRankings = PlayerRankings.query.filter_by(rankingId=rankingId).order_by(PlayerRankings.ranking).all()
            next_ranking = currentRankings[-1].ranking + 1 if currentRankings else 1
            new_ranking = PlayerRankings(
                playerId=new_player.id,
                rankingId=rankingId, 
                ranking=next_ranking, 
                points=0
            )
            db.session.add(new_ranking)
            log(1, "newPlayer", f"Created ranking entry for player '{name}' with ranking {next_ranking}")
        if bonus and logicOperator and limitRanking:
            new_bonus = PlayerBonuses(
                playerId=new_player.id,
                bonus=int(bonus),
                logicOperator=logicOperator,
                limitRanking=int(limitRanking)
            )
            db.session.add(new_bonus)
            log(1, "newPlayer", f"Created bonus entry for player '{name}': {bonus} {logicOperator} {limitRanking}")
        db.session.commit()
        log(1, "newPlayer", f"Successfully created player '{name}' with all associated data")
    except Exception as e:
        db.session.rollback()
        log(4, "newPlayer", f"Failed to create player '{name}': {e}")

def addPlayerToRanking(playerId, rankingId):
    """
    Adds an existing player to a ranking.
    """
    if not rankingId or not playerId:
        log(3, "addPlayerToRanking", f"playerId or rankingId is missing. playerId: {playerId}, rankingId: {rankingId}")
        return
    try:
        player = db.session.get(Players, playerId)
        if not player:
            log(3, "addPlayerToRanking", f"Player with ID {playerId} does not exist")
            return
        existing_ranking = PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()
        if existing_ranking:
            log(3, "addPlayerToRanking", f"Player {player.name}({playerId}) is already in ranking {rankingId}")
            return
        currentRankings = PlayerRankings.query.filter_by(rankingId=rankingId).order_by(PlayerRankings.ranking).all()
        next_ranking = currentRankings[-1].ranking + 1 if currentRankings else 1
        new_ranking = PlayerRankings(
            playerId=playerId,
            rankingId=rankingId,
            ranking=next_ranking,
            points=0
        )
        db.session.add(new_ranking)
        db.session.commit()
        log(1, "addPlayerToRanking", f"Imported player {player.name}({playerId}) to ranking {rankingId}")
    except Exception as e:
        db.session.rollback()
        log(4, "addPlayerToRanking", f"Could not import player {playerId} to ranking {rankingId}, because of {e}")

def removePlayerFromRanking(playerId, rankingId):
    """
    Removes a player from a ranking.
    """
    try:
        player = db.session.get(Players, playerId)
        if not player:
            log(3, "removePlayerFromRanking", f"Player with ID {playerId} does not exist")
            return
    except Exception as e:
        log(4, "removePlayerFromRanking", f"Could not get Player from playerId: {playerId}, because of {e}")
        return
    try:
        playerRankingEntry = PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()
    except Exception as e:
        log(3, "removePlayerFromRanking", f"Could not find ranking entry for player {playerId} in ranking {rankingId}, because of {e}")
        return
    if not playerRankingEntry:
        log(3, "removePlayerFromRanking", f"Could not find ranking entry for player {playerId} in ranking {rankingId}")
        return
    try:
        db.session.delete(playerRankingEntry)
        db.session.commit()
        checkForGapInRanking(rankingId)
        log(1, "removePlayerFromRanking", f"Removed player {playerId} from ranking {rankingId}")
    except Exception as e:
        db.session.rollback()
        log(4, "removePlayerFromRanking", f"Could not remove Player {playerId}, because of {e}")
        return

def deleteMatchesByPlayer(playerId):
    """
    Deletes all ongoing matches where the player is either challenger or defender.
    
    Args:
        playerId: ID of the player whose matches should be deleted
    """
    if not playerId:
        log(3, "deleteMatchesByPlayer", "No playerId provided")
        return False
        
    try:
        player = db.session.get(Players, playerId)
        if not player:
            log(3, "deleteMatchesByPlayer", f"Player with ID {playerId} does not exist")
            return False
            
        challengerMatches = OnGoingMatches.query.filter_by(challengerId=playerId).all()
        defenderMatches = OnGoingMatches.query.filter_by(defenderId=playerId).all()
        
        total_matches = len(challengerMatches) + len(defenderMatches)
        
        if total_matches == 0:
            log(1, "deleteMatchesByPlayer", f"No ongoing matches found for player {player.name}({playerId})")
            return True
            
        for match in challengerMatches:
            db.session.delete(match)
            
        for match in defenderMatches:
            db.session.delete(match)
            
        db.session.commit()
        log(1, "deleteMatchesByPlayer", f"Successfully deleted {total_matches} ongoing matches for player {player.name}({playerId})")
        return True
        
    except Exception as e:
        db.session.rollback()
        log(4, "deleteMatchesByPlayer", f"Could not delete matches for player {playerId}: {e}")
        return False

def deletePlayer(playerId):
    """
    Deletes a player and all their ranking entries.
    """
    try:
        playerRanking = PlayerRankings.query.filter_by(playerId=playerId).all()
        rankingIds = []
        for ranking in playerRanking:
            rankingIds.append(ranking.rankingId)
            db.session.delete(ranking)
        player = db.session.get(Players, playerId)
        if not player:
            log(3, "deletePlayer", f"Player with ID {playerId} does not exist")
            return
        deleteMatchesByPlayer(playerId)
        db.session.delete(player)
        db.session.commit()

        for rankingId in rankingIds:
            checkForGapInRanking(rankingId)
        log(1, "deletePlayer", f"Deleted player {playerId} and their rankings")
    except Exception as e:
        db.session.rollback()
        log(4, "deletePlayer", f"Could not delete player {playerId}: {e}")

def startMatch(challengerId, defenderId, rankingId):
    """
    Starts a new match between two players in a ranking.
    """
    from bonuses import getBonus
    try:
        challenger = db.session.get(Players, challengerId)
        defender = db.session.get(Players, defenderId)
        if not challenger or not defender:
            log(3, "startMatch", f"Challenger or defender does not exist. ChallengerId: {challengerId}, DefenderId: {defenderId}")
            return
        new_match = OnGoingMatches(
            rankingId = rankingId,
            challenger = challenger.name,
            challengerId = challengerId,
            defender = defender.name,
            defenderId = defenderId,
            timeStarted = db.func.now()
        )
        bonus = getBonus(new_match)
        if bonus.challenger:
            new_match.challengerBonus = bonus.challenger
        if bonus.defender:
            new_match.defenderBonus = bonus.defender
        db.session.add(new_match)
        db.session.commit()
        log(1, "startMatch", f"Starting match from {challenger.name}({challengerId}) against {defender.name}({defenderId})")
    except Exception as e:
        db.session.rollback()
        log(4, "startMatch", f"Couldnt start match from {challengerId} against {defenderId}, because of: {e}")

def endMatch(matchId, rankingId, winnerId, challengerScore, defenderScore):
    """
    Ends a match, records the result, updates stats, and moves the match to finished.
    """
    try:
        match = db.session.get(OnGoingMatches, matchId)
        if not match:
            log(3, "endMatch", f"Match with ID {matchId} does not exist")
            return
        challenger = db.session.get(Players, match.challengerId)
        defender = db.session.get(Players, match.defenderId)
        if not challenger or not defender:
            log(3, "endMatch", f"Challenger or defender does not exist for match {matchId}")
            return

        winner = None
        loserId = None
        winnerSetsWon = None
        loserSetsWon = None

        # Determine winner and scores
        if challengerScore is not None and defenderScore is not None:
            if challengerScore > defenderScore:
                winner = challenger.name
                winnerId = challenger.id
                winnerSetsWon = challengerScore
                loserSetsWon = defenderScore
                loserId = defender.id
            elif defenderScore > challengerScore:
                winner = defender.name
                winnerId = defender.id
                winnerSetsWon = defenderScore
                loserSetsWon = challengerScore
                loserId = challenger.id
            else:
                log(3, "endMatch", f"Draw detected in match {matchId}, which is not supported")
                return
        else:
            if not winnerId:
                log(3, "endMatch", f"No winnerId provided for match {matchId}")
                return
            winnerId = int(winnerId)
            if winnerId == challenger.id:
                winner = challenger.name
                loserId = defender.id
            elif winnerId == defender.id:
                winner = defender.name
                loserId = challenger.id
            else:
                log(3, "endMatch", f"WinnerId {winnerId} does not match challenger or defender in match {matchId}")
                return

        if not winner or not winnerId:
            log(3, "endMatch", f"Winner or WinnerId could not be resolved for match {matchId}")
            return

        new_finishedmatch = FinishedMatches(
            rankingId = rankingId,
            challenger = challenger.name,
            challengerId = challenger.id,
            defender = defender.name,
            defenderId = defender.id,
            timeStarted = match.timeStarted,
            timeFinished = db.func.now(),
            winner = winner,
            winnerId = winnerId,
            challengerScore = challengerScore if challengerScore is not None and defenderScore is not None else None,
            defenderScore = defenderScore if challengerScore is not None and defenderScore is not None else None,
        )

        changeStats(winnerId=winnerId, loserId=loserId, winnerSetsWon=winnerSetsWon, loserSetsWon=loserSetsWon, rankingId=rankingId)
        db.session.add(new_finishedmatch)
        db.session.delete(match)
        db.session.commit()
        log(1, "endMatch", f"Finished match with new id: {new_finishedmatch.id}, winnerId: {winnerId}")
        return
    except Exception as e:
        db.session.rollback()
        log(4, "endMatch", f"Could not finish match with id: {matchId}, because of: {e}")
        return

def updatePlayerRanking(playerId, rankingId, newRanking):
    """
    Updates a player's ranking in a specific ranking.
    """
    try:
        player_ranking_entry = PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()
        if not player_ranking_entry:
            log(3, "updatePlayerRanking", f"No ranking entry found for player {playerId} in ranking {rankingId}")
            return False
            
        old_ranking = player_ranking_entry.ranking
        player_ranking_entry.ranking = int(newRanking)
        db.session.commit()
        
        player = db.session.get(Players, playerId)
        log(1, "updatePlayerRanking", f"Changed ranking for player {player.name}({player.id}) in ranking {rankingId} from {old_ranking} to {newRanking}")
        return True
    except Exception as e:
        db.session.rollback()
        log(4, "updatePlayerRanking", f"Could not change ranking for player {playerId} in ranking {rankingId}: {e}")
        return False

def updatePlayerAttributes(player, attribute_mappings, request):
    """
    Updates multiple player attributes based on form data.
    
    Args:
        player: Player object to update
        attribute_mappings: List of tuples (db_attribute, form_field)
        request: Flask request object
    """
    for db_attr, form_field in attribute_mappings:
        current_value = getattr(player, db_attr)
        checkIfChangedAndUpdate(form_field, player, current_value, db_attr, request)

def startList(name, description, startingPlayers, isTournament, typeOfTournament, sortedBy, endsOn):
    """
    Creates a new ranking list with optional tournament settings and starting players.
    
    Args:
        name: Name of the ranking list.
        description: Description of the ranking list.
        startingPlayers: List of player IDs to add to the ranking.
        isTournament: Boolean indicating if the ranking is a tournament.
        typeOfTournament: Type of tournament (if applicable).
        sortedBy: Sorting method for the ranking.
        endsOn: End date for the ranking (datetime object or ISO format string).
    """
    log(1, "startList", f"Starting to create new list: {name}")
    
    if not name:
        log(3, "startList", "No name provided for the ranking list")
        flash("Ranking list name is required.", 'error')
        return False
    
    if Rankings.query.filter_by(name=name).first():
        log(3, "startList", f"List name: '{name}' is already used")
        flash(f"Ranking list name '{name}' is already in use. Please choose a different name.", 'error')
        return False
    
    try:
        if not isTournament:
            isTournament = False
            typeOfTournament = None

        if validateSortingOption(sortedBy) == False:
            sortedBy = "ranking"
            flash("Defined sorting setting is invalid. Falling back to the standard. You can change the sorting in the settings.", 'error')
            log(2, "startList", f"Invalid sorting option '{sortedBy}' provided. Defaulting to 'ranking'.")

        # Ensure endsOn is a valid datetime object
        if endsOn and not isinstance(endsOn, dt.datetime):
            if isinstance(endsOn, str):
                try:
                    endsOn = dt.datetime.fromisoformat(endsOn)
                    log(1, "startList", f"Converted string datetime to datetime object for endsOn")
                except ValueError as e:
                    log(3, "startList", f"Invalid datetime format provided for endsOn: {e}")
                    flash("Invalid end date format provided. Please use a valid ISO format string.", 'error')
                    return False
            else:
                log(3, "startList", f"Invalid endsOn type provided. Expected datetime or string, got {type(endsOn)}")
                flash("Invalid end date type provided. Please use a valid datetime object or ISO format string.", 'error')
                return False

        # Ensure endsOn is timezone-aware
        if endsOn and endsOn.tzinfo is None:
            log(2, "startList", "End date is timezone-naive. Assuming UTC.")
            endsOn = endsOn.replace(tzinfo=dt.timezone.utc)

        new_Ranking = Rankings(
            name=name,
            description=description,
            tournament=isTournament,
            typeTournament=typeOfTournament,
            endsOn=endsOn,
            ended=False,
            sortedBy=sortedBy
        )
        db.session.add(new_Ranking)
        
        if startingPlayers:
            db.session.flush()  # Flush to get the new ranking ID
            for player in startingPlayers:
                try:
                    addPlayerToRanking(player, new_Ranking.id)
                except Exception as e:
                    log(4, "startList", f"Failed to add player {player} to ranking {new_Ranking.id}: {e}")
                    flash(f"Failed to add player with ID {player} to the ranking list.", 'error')

        db.session.commit()
        log(1, "startList", f"Successfully created new List: {name}")
        return True
    except Exception as e:
        db.session.rollback()
        log(4, "startList", f"Could not create List '{name}', because of {e}")
        flash(f"An error occurred while creating the ranking list '{name}'. Please try again.", 'error')
        return False

def endList(rankingId):
    log(1, "endList", f"Starting to end ranking {rankingId}")
    if db.session.get(Rankings, rankingId):
        try:
            ranking = db.session.get(Rankings, rankingId)
            ranking.ended = True
            db.session.commit()
            log(1, "endList", f"Successfully ended ranking {rankingId}")
        except Exception as e:
            db.session.rollback()
            log(4, "endList", f"Could not end ranking {rankingId}, because of {e}")

def deleteList(rankingId):
    log(1, "deleteList", f"Starting to delete ranking {rankingId}")
    if db.session.get(Rankings, rankingId):
        try:
            ranking = db.session.get(Rankings, rankingId)
            db.session.delete(ranking)
            relatedRankingEntries = PlayerRankings.query.filter_by(rankingId=rankingId)
            for entry in relatedRankingEntries:
                db.session.delete(entry)
            db.session.commit()
            log(1, "deleteList", f"Successfully deleted ranking {rankingId}")
        except Exception as e:
            db.session.rollback()
            log(4, "deleteList", f"Could not delete ranking {rankingId}, because of {e}")

def changeEndingDate(rankingId, datetime_input):
    """
    Changes the ending date for a ranking with proper timezone handling.
    
    Args:
        rankingId: ID of the ranking to update
        datetime_input: New ending date (datetime object or ISO format string)
    """
    try:
        ranking = db.session.get(Rankings, rankingId)
        if not ranking:
            log(3, "changeEndingDate", f"Ranking with ID {rankingId} does not exist")
            return False
            
        if not isinstance(datetime_input, dt.datetime):
            # Try to convert if it's an ISO format string
            if isinstance(datetime_input, str):
                try:
                    datetime_input = dt.datetime.fromisoformat(datetime_input)
                    log(1, "changeEndingDate", f"Converted string datetime to datetime object for ranking {rankingId}")
                except ValueError as e:
                    log(3, "changeEndingDate", f"Invalid datetime format provided for ranking {rankingId}: {e}")
                    return False
            else:
                log(3, "changeEndingDate", f"Invalid datetime object type provided for ranking {rankingId}. Expected datetime or string, got {type(datetime_input)}")
                return False
        
        # Ensure timezone awareness
        if datetime_input.tzinfo is None:
            log(2, "changeEndingDate", f"Datetime is timezone-naive for ranking {rankingId}, assuming UTC")
            datetime_input = datetime_input.replace(tzinfo=dt.timezone.utc)
        
        # Convert to UTC for consistent storage
        if datetime_input.tzinfo != dt.timezone.utc:
            datetime_input = datetime_input.astimezone(dt.timezone.utc)
        
        old_date = ranking.endsOn
        ranking.endsOn = datetime_input
        db.session.commit()
        log(1, "changeEndingDate", f"Successfully changed ending date for ranking {rankingId} from {old_date} to {datetime_input}")
        return True
        
    except Exception as e:
        db.session.rollback()
        log(4, "changeEndingDate", f"Could not change ending date for ranking {rankingId}: {e}")
        return False
    
def changeSortingRanking(rankingId, setting):
    """
    Changes the sorting setting for a ranking.
    
    Args:
        rankingId: ID of the ranking to update
        setting: New sorting option ("standard", "points", or "wins")
    """
    try:
        if not rankingId or not setting:
            log(3, "changeSortingRanking", f"Missing required parameters. rankingId: {rankingId}, setting: {setting}")
            return False
            
        ranking = db.session.get(Rankings, rankingId)
        if not ranking:
            log(3, "changeSortingRanking", f"Ranking with ID {rankingId} does not exist")
            return False
            
        changed = False

        if validateSortingOption(setting) == False:
            log(3, "changeSortingRanking", f"Invalid sorting option '{setting}' for ranking {rankingId}.")
            return False
        else:
            ranking.sortedBy = validateSortingOption(setting)

        old_setting = getattr(ranking, 'sortedBy', None)
        
        if changed:
            db.session.commit()
            log(1, "changeSortingRanking", f"Successfully changed sorting for ranking {rankingId} from '{old_setting}' to '{setting}'")
            return True
        else:
            db.session.rollback()
            log(3, "changeSortingRanking", f"No changes made to sorting for ranking {rankingId}")
            return False
            
    except Exception as e:
        db.session.rollback()
        log(4, "changeSortingRanking", f"Could not change sorting for ranking {rankingId}: {e}")
        return False
    
def clearLogs():
    """
    Clears all log entries from the database.
    """
    try:
        allLogs = LogEntries.query.all()
        log_count = len(allLogs)
        
        if log_count == 0:
            log(1, "clearLogs", "No logs found to clear")
            return True
            
        for log_entry in allLogs:
            db.session.delete(log_entry)
            
        db.session.commit()
        log(1, "clearLogs", f"Successfully cleared {log_count} log entries")
        return True
        
    except Exception as e:
        db.session.rollback()
        log(4, "clearLogs", f"Could not clear logs: {e}")
        return False
    
def checkIfRankingEnded(rankingId):
    """
    Checks if a ranking has ended based on its end date and updates the status accordingly.
    
    Args:
        rankingId: ID of the ranking to check
    """
    try:
        if not rankingId:
            log(3, "checkIfRankingEnded", "No rankingId provided")
            return False
            
        ranking = db.session.get(Rankings, rankingId)
        if not ranking:
            log(3, "checkIfRankingEnded", f"Ranking with ID {rankingId} does not exist")
            return False
            
        if not ranking.endsOn:
            log(1, "checkIfRankingEnded", f"Ranking {rankingId} has no end date set")
            return False
        
        # Ensure ranking.endsOn is timezone-aware
        if ranking.endsOn.tzinfo is None:
            log(1, "checkIfRankingEnded", f"Ranking {rankingId} end date is timezone-naive, assuming UTC")
            ranking.endsOn = ranking.endsOn.replace(tzinfo=dt.timezone.utc)
            db.session.commit()
            
        current_time = dt.datetime.now(dt.timezone.utc)
        
        # Convert ranking.endsOn to UTC if it is timezone-naive
        if ranking.endsOn.tzinfo is None:
            ranking.endsOn = ranking.endsOn.replace(tzinfo=dt.timezone.utc)
        
        if ranking.endsOn <= current_time and not ranking.ended:
            old_status = ranking.ended
            ranking.ended = True
            db.session.commit()
            log(1, "checkIfRankingEnded", f"Ranking {rankingId} has ended. Status changed from {old_status} to {ranking.ended}")
            return True
        elif ranking.endsOn > current_time:
            log(1, "checkIfRankingEnded", f"Ranking {rankingId} is still active. Ends on: {ranking.endsOn}")
            return False
        else:
            log(1, "checkIfRankingEnded", f"Ranking {rankingId} was already marked as ended")
            return False
            
    except Exception as e:
        db.session.rollback()
        log(4, "checkIfRankingEnded", f"Could not check if ranking {rankingId} has ended: {e}")
        return False
    
def checkAllRankings():
    allRankings = Rankings.query.all()
    for ranking in allRankings:
        if ranking.endsOn:
            checkIfRankingEnded(ranking.id)

def checkBeforeRendering(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        checkAllRankings()
        return f(*args, **kwargs)
    return decorated_function

def validateSortingOption(str):
    OPTIONS = ["standard", "points"]
    output = False
    for option in OPTIONS:
        if str == option:
            output = str
    return output