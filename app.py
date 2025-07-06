#flask
from flask import Flask, render_template, request, redirect, session, flash
from flask_migrate import Migrate

#Database
from db import db, Players, PlayerBonuses, Rankings, PlayerRankings, Authentication

#TT Ranking files
from bonuses import updateOrCreatePlayerBonus, validateBonusParameters
from services import getActiveMatchesOfRanking, getPlayersOfRanking, newPlayer, addPlayerToRanking, startMatch, endMatch, removePlayerFromRanking, deletePlayer, updatePlayerRanking, updatePlayerAttributes, startList, endList, deleteList, clearLogs, checkBeforeRendering, checkRankingAndFix
from authentication import requiresViewer, requiresTrainer, authenticate
from logger import log

#Third party libaries
from datetime import datetime, timezone, timedelta
import datetime as dt
import os
from werkzeug.security import generate_password_hash
import zoneinfo

# =============================================================================
# TIMEZONE CONFIGURATION
# =============================================================================
# Set your local timezone here - this will be used for all user inputs
# that don't explicitly specify a timezone (like date/time form inputs)
LOCAL_TIMEZONE = "Europe/Berlin"  # Change this to your actual timezone
LOCAL_TZ = zoneinfo.ZoneInfo(LOCAL_TIMEZONE)

def get_local_timezone():
    """Returns the configured local timezone for the application"""
    return LOCAL_TZ

def convert_local_to_utc(local_datetime):
    """
    Converts a local timezone-naive datetime to UTC
    Args:
        local_datetime: datetime object assumed to be in LOCAL_TIMEZONE
    Returns:
        datetime object in UTC timezone
    """
    if local_datetime.tzinfo is None:
        local_datetime = local_datetime.replace(tzinfo=LOCAL_TZ)
    return local_datetime.astimezone(dt.timezone.utc)

def convert_utc_to_local(utc_datetime):
    """
    Converts UTC datetime to local timezone for display
    Args:
        utc_datetime: datetime object in UTC
    Returns:
        datetime object in LOCAL_TIMEZONE
    """
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=dt.timezone.utc)
    return utc_datetime.astimezone(LOCAL_TZ)

# =============================================================================

# Initialize Flask application with database configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'K8sZt^cH6Brf@4seK&6C2kNqa6a7ve')
app.permanent_session_lifetime = timedelta(minutes=30)  # 30 minute timeout

# Initialize database and migration support
db.init_app(app)
migrate = Migrate(app, db)

# Add datetime utility to Jinja template globals for use in templates
app.jinja_env.globals['now'] = datetime.utcnow

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        password = request.form.get('password')
        print(password)
        if authenticate(password, request):
            flash(f"Logged in as {session['permissionLevel']}", "success")
            return redirect('/')
        else:
            return redirect('/login')

@app.route('/logout')
def logOut():
    session.clear()
    flash(f"Logged out", "success")
    return redirect('/login')

@app.route('/')
@requiresViewer
@checkBeforeRendering
def home():
    """
    Renders the home page displaying all available rankings.
    This is the main entry point for users to select which ranking to view.
    
    Returns:
        Rendered HTML template with list of all rankings
        
    Raises:
        Exception: Logs error if database query fails
    """
    try:
        rankings = Rankings.query.all()
    except Exception as e:
        log(4, "home", f"Error loading rankings for home page: {e}")
        flash("Can not show the rankings at the moment", "error")
        # Return empty rankings list as fallback
        return render_template('index.html', rankings=[], allPlayers=[])
    
    try:
        allPlayers = Players.query.order_by(Players.wins.desc()).all()
    except Exception as e:
        log(4, "home", f"Error loading players for home page: {e}")
        flash("Can not show the rankings at the moment", "error")
        # Return empty rankings list as fallback
        return render_template('index.html', rankings=rankings, allPlayers=[])
    return render_template('index.html', rankings=rankings, allPlayers=allPlayers)

@app.route('/view/<int:rankingId>')
@requiresViewer
@checkBeforeRendering
def view(rankingId):
    """
    Renders the viewer page for a specific ranking.
    Displays read-only view of players in the ranking for public viewing.
    
    Args:
        rankingId: ID of the ranking to display
        
    Returns:
        Rendered HTML template with players in the specified ranking
        
    Raises:
        Exception: Logs error if ranking data cannot be retrieved
    """
    try:
        players = getPlayersOfRanking(rankingId)
        log(1, "view", f"Successfully loaded {len(players)} players for ranking {rankingId}")
        return render_template('viewer.html', players=players, ranking=db.session.get(Rankings, rankingId))
    except Exception as e:
        log(4, "view", f"Error loading players for ranking {rankingId}: {e}")
        flash("Can not show the players at the moment", "error")
        # Return empty players list as fallback
        return render_template('viewer.html', players=[], ranking=[])

@app.route('/trainer/<int:rankingId>')
@requiresTrainer
@checkBeforeRendering
def trainer(rankingId):
    """
    Renders the trainer page for managing a specific ranking.
    Provides full administrative interface for managing players, matches, and bonuses.
    
    Args:
        rankingId: ID of the ranking to manage
        
    Returns:
        Rendered HTML template with players, active matches, and management tools
        
    Raises:
        Exception: Logs error if ranking data cannot be retrieved
    """
    try:
        # Get players in the ranking with their bonus information
        players = getPlayersOfRanking(rankingId)
        ranking = db.session.get(Rankings, rankingId)
        
        # Add bonus information to each player for display in the interface
        for player in players:
            try:
                player.bonus = PlayerBonuses.query.filter_by(playerId=player.id).first()
            except Exception as e:
                log(3, "trainer", f"Error loading bonus for player {player.id}: {e}")
                player.bonus = None
        
        # Get active matches for this ranking
        activeMatches = getActiveMatchesOfRanking(rankingId)
        
        # Get all players for import functionality
        allPlayers = Players.query.all()
        
        log(1, "trainer", f"Successfully loaded trainer page for ranking {rankingId} with {len(players)} players and {len(activeMatches)} active matches")
        
        return render_template('trainer.html', 
                             players=players, 
                             activeMatches=activeMatches, 
                             rankingId=rankingId,
                             ranking=ranking, 
                             allPlayers=allPlayers)
                             
    except Exception as e:
        log(4, "trainer", f"Error loading trainer page for ranking {rankingId}: {e}")
        flash("Can not show the players at the moment", "error")
        # Return minimal template with empty data as fallback
        return render_template('trainer.html', 
                             players=[], 
                             activeMatches=[], 
                             rankingId=rankingId, 
                             allPlayers=[])

@app.route('/trainer/start', methods=['GET', 'POST'])
@requiresTrainer
def startListTrainer():
    if request.method == 'GET':
        allPlayers = Players.query.all()
        return render_template('startList.html', allPlayers=allPlayers)
    elif request.method == 'POST':
        listName = request.form.get('listName')
        description = request.form.get('description')
        startingPlayers = request.form.getlist('startingPlayers')
        isTournament = request.form.get('isTournament')
        typeOfTournament = request.form.get('typeOfTournament')
        sortedBy = request.form.get('sortedBy')
        endsOnDate = request.form.get('endsOnDate')
        endsOnTime = request.form.get('endsOnTime')
        if isTournament and typeOfTournament:
            #Do something
            print("")
        else:
            isTournament == False
            typeOfTournament == ""

        if endsOnDate and endsOnTime:
            try:
                # Combine date and time into datetime with proper timezone handling
                datetime_str = f"{endsOnDate} {endsOnTime}"
                end_datetime = dt.datetime.fromisoformat(datetime_str)
                
                # Convert from local timezone to UTC using the configured timezone
                end_datetime_utc = convert_local_to_utc(end_datetime)
                
                # Validate that end date is in the future
                if end_datetime_utc <= dt.datetime.now(dt.timezone.utc):
                    end_datetime_utc = None
                    flash("End date must be in the future. Could not set ending time and date. Set later in settings", "error")
            except ValueError as e:
                end_datetime_utc = None
                log(3, "startListTrainer", f"Invalid date/time format provided: {e}")
                flash("Invalid date/time format. Could not set ending time and date. Set later in settings", "error")

        startList(listName, description, startingPlayers, isTournament, typeOfTournament, sortedBy, end_datetime_utc)
        flash("Started Ranking/Tournament", "success")
        return redirect('/')
    
@app.route('/deleteLogs')
def deleteLogs():
    clearLogs()
    flash("Cleared Logs", "success")
    return redirect('/')

@app.route('/trainer/end', methods=['POST'])
@requiresTrainer
def endListTrainer():
    rankingId = request.form.get('rankingId')
    endOrDelete = request.form.get('endOrDelete')
    if endOrDelete == "delete":
        deleteList(rankingId)
        flash("Deleted Ranking/Tournament", "success")
    elif endOrDelete == "end":
        endList(rankingId)
        flash("Ended Ranking/Tournament", "success")
    else:
        log(4, "/trainer/end", f"Could not determin if user wanted to stop or end list({rankingId}): {endOrDelete}")
        flash("Could not end or stop the ranking", "warning")
    return redirect('/')

@app.route('/trainer/settings', methods=['GET', 'POST'])
@requiresTrainer
@checkBeforeRendering
def selectSettingsTrainer():
    return render_template(
            'selectRankingForSettings.html',
            rankings=Rankings.query.all(),
            allPlayers=[]
        )

@app.route('/trainer/settings/<int:rankingId>', methods=['GET', 'POST'])
@requiresTrainer
@checkBeforeRendering
def settingsTrainer(rankingId):
    if request.method == 'POST':
        # Parse form arguments correctly based on the HTML form fields
        rankingSystem = request.form.get('rankingSystem')  # select dropdown
        autoEndDate = request.form.get('autoEndDate')  # date input
        autoEndTime = request.form.get('autoEndTime')  # time input
        disableAutoEnd = request.form.get('disableAutoEnd')  # checkbox
        
        # Update ranking settings based on parsed form data
        if rankingId:
            ranking = db.session.get(Rankings, rankingId)
            if ranking and (rankingSystem or autoEndDate or autoEndTime or disableAutoEnd):
                # Handle ranking system
                if rankingSystem:
                    ranking.sortedBy = rankingSystem
                
                # Handle auto-end date/time
                if disableAutoEnd:
                    ranking.endsOn = None
                elif autoEndDate and autoEndTime:
                    try:
                        # Combine date and time into datetime with proper timezone handling
                        datetime_str = f"{autoEndDate} {autoEndTime}"
                        end_datetime = dt.datetime.fromisoformat(datetime_str)
                        
                        # Convert from local timezone to UTC using the configured timezone
                        end_datetime_utc = convert_local_to_utc(end_datetime)
                        
                        # Validate that end date is in the future
                        if end_datetime_utc <= dt.datetime.now(dt.timezone.utc):
                            flash("End date must be in the future", "error")
                            return redirect(f'/trainer/settings/{rankingId}')
                            
                        ranking.endsOn = end_datetime_utc
                    except ValueError as e:
                        flash("Invalid date/time format", "error")
                        return redirect(f'/trainer/settings/{rankingId}')
                
                db.session.commit()
                flash("Saved settings", "success")
        
        return redirect(f'/trainer/settings/{rankingId}')

    try:
        currentRanking = db.session.get(Rankings, rankingId)
        if not currentRanking:
            flash("Ranking not found", "error")
            return redirect('/trainer/settings')
        
        # Convert UTC times to local timezone for display
        currentRankingWithLocalTime = None
        if currentRanking and currentRanking.endsOn:
            # Create a copy of the ranking object with local time. May find better way
            import copy
            currentRankingWithLocalTime = copy.copy(currentRanking)
            currentRankingWithLocalTime.endsOn = convert_utc_to_local(currentRanking.endsOn)
        elif currentRanking:
            currentRankingWithLocalTime = currentRanking
        
        return render_template(
            'settingsTrainer.html',
            rankingId=rankingId,
            currentRanking=currentRankingWithLocalTime  # Pass the version with local time
        )
    except Exception as e:
        log(4, "settingsTrainer", f"Error loading ranking {rankingId}: {e}")
        flash("Can not show the ranking at the moment", "error")
        return redirect('/trainer/settings')

@app.route('/trainer/fix', methods=['POST'])
@requiresTrainer
def fixRankingTrainer():
    rankingId = request.form.get('rankingId')
    checkRankingAndFix(rankingId)
    flash("Performed maintenance", "success")
    return redirect(f'/trainer/settings/{rankingId}')

@app.route('/trainer/start_match', methods=['POST'])
@requiresTrainer
def start_match():
    """
    Initiates a new match between two players in a ranking.
    Creates an ongoing match record with calculated bonus points.
    
    Form Parameters:
        rankingId: ID of the ranking where the match takes place
        challenger_id: ID of the challenging player
        defender_id: ID of the defending player
        
    Returns:
        Redirect to trainer page for the ranking
        
    Raises:
        Exception: Logs error if match cannot be started
    """
    try:
        # Extract and validate form parameters
        rankingId = request.form.get('rankingId')
        challengerId = request.form.get('challenger_id')
        defenderId = request.form.get('defender_id')
        
        # Validate required parameters
        if not rankingId:
            log(3, "start_match", "Missing rankingId parameter")
            return redirect('/trainer/1')  # Fallback to default ranking
            
        rankingId = int(rankingId)
        
        if not challengerId or not defenderId:
            log(3, "start_match", f"Challenger or defender ID is missing. challengerId: {challengerId}, defenderId: {defenderId}")
            return redirect(f'/trainer/{rankingId}')
            
        # Validate that challenger and defender are different
        if challengerId == defenderId:
            log(3, "start_match", f"Challenger and defender cannot be the same player: {challengerId}")
            return redirect(f'/trainer/{rankingId}')
        
        # Start the match
        startMatch(challengerId, defenderId, rankingId)
        log(1, "start_match", f"Started match in ranking {rankingId} between challenger {challengerId} and defender {defenderId}")

    except ValueError as e:
        log(4, "start_match", f"Invalid parameter values: {e}")
        flash("Input is invalid", "warning")
    except Exception as e:
        log(4, "start_match", f"Could not start match: {e}")
        flash("Could not start match", "error")
    
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/finish_match', methods=['POST'])
@requiresTrainer
def finish_match():
    """
    Completes an ongoing match and records the results.
    Updates player statistics, rankings, and moves match to finished status.
    
    Form Parameters:
        rankingId: ID of the ranking where the match took place
        match_id: ID of the ongoing match to finish
        winner_id: ID of the winning player (optional if scores provided)
        challenger_score: Sets won by challenger (optional)
        defender_score: Sets won by defender (optional)
        
    Returns:
        Redirect to trainer page for the ranking
        
    Raises:
        Exception: Logs error if match cannot be finished
    """
    try:
        # Extract and validate form parameters
        rankingId = request.form.get('rankingId')
        matchId = request.form.get('match_id')
        winnerId = request.form.get('winner_id')
        challengerScore = request.form.get('challenger_score')
        defenderScore = request.form.get('defender_score')
        
        # Validate required parameters
        if not rankingId or not matchId:
            log(3, "finish_match", f"Missing required parameters - rankingId: {rankingId}, matchId: {matchId}")
            flash("Missing required parameters", "error")
            return redirect('/trainer/1')  # Fallback to default ranking
            
        rankingId = int(rankingId)
        matchId = int(matchId)
        
        # Convert scores to integers if provided
        if challengerScore:
            challengerScore = int(challengerScore)
        if defenderScore:
            defenderScore = int(defenderScore)
            
        # Validate that either winner is specified or scores are provided
        if not winnerId and (challengerScore is None or defenderScore is None):
            log(3, "finish_match", f"Either winner_id or both scores must be provided for match {matchId}")
            flash("Either winner or both scores must be provided", "error")
            return redirect(f'/trainer/{rankingId}')
        
        # Finish the match
        endMatch(matchId, rankingId, winnerId, challengerScore, defenderScore)
        log(1, "finish_match", f"Finished match {matchId} in ranking {rankingId}, winner: {winnerId}")
       
    except ValueError as e:
        log(4, "finish_match", f"Invalid parameter values: {e}")
        flash("Invalid parameter values", "error")
    except Exception as e:
        log(4, "finish_match", f"Could not finish match {matchId}: {e}")
        flash("Could not finish match", "error")
    
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/player_add', methods=['POST'])
@requiresTrainer
def player_add():
    """
    Creates a new player and adds them to a ranking with optional bonus settings.
    Validates input parameters and handles database transaction safely.
    
    Form Parameters:
        rankingId: ID of the ranking to add the player to
        name: Name of the new player
        bonus: Bonus points amount (optional)
        logic_operator: Comparison operator for bonus condition (optional)
        limit_ranking: Ranking threshold for bonus activation (optional)
        
    Returns:
        Redirect to trainer page for the ranking
        
    Raises:
        Exception: Logs error if player cannot be created
    """
    try:
        # Extract and validate form parameters
        rankingId = request.form.get('rankingId')
        name = request.form.get('name')
        
        # Validate required parameters
        if not rankingId:
            flash("Ranking ID is missing", "error")
            log(3, "player_add", "Missing rankingId parameter")
            return redirect('/trainer/1')  # Fallback to default ranking
            
        rankingId = int(rankingId)
        
        if not name or name.strip() == "":
            flash("Player name is missing or empty", "error")
            log(3, "player_add", f"Name is missing or empty for ranking {rankingId}")
            return redirect(f'/trainer/{rankingId}')
        
        # Sanitize player name
        name = name.strip()
        
        # Extract optional bonus parameters
        bonus = request.form.get('bonus')
        logicOperator = request.form.get('logic_operator')
        limitRanking = request.form.get('limit_ranking')
        
        # Create the new player
        newPlayer(name, rankingId, bonus, logicOperator, limitRanking)
        flash(f"Added new player '{name}' to ranking", "success")
        log(1, "player_add", f"Added new player {name} to ranking {rankingId}")
        
    except ValueError as e:
        db.session.rollback()
        flash("Invalid input values for new player", "error")
        log(4, "player_add", f"Invalid parameter values for new player: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not add new player due to an error", "error")
        log(4, "player_add", f"New player: {name} couldn't be added, because of {e}")
    
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/player_import', methods=['POST'])
@requiresTrainer
def player_import():
    """
    Imports an existing player into a ranking.
    Adds a player who already exists in the system to a new ranking.
    
    Form Parameters:
        rankingId: ID of the ranking to import the player to
        import_player_id: ID of the existing player to import
        
    Returns:
        Redirect to trainer page for the ranking
        
    Raises:
        Exception: Logs error if player cannot be imported
    """
    try:
        # Extract and validate form parameters
        rankingId = request.form.get('rankingId')
        importPlayerId = request.form.get('import_player_id')
        
        # Validate required parameters
        if not rankingId:
            flash("Ranking ID is missing", "error")
            log(3, "player_import", "Missing rankingId parameter")
            return redirect('/trainer/1')  # Fallback to default ranking
            
        rankingId = int(rankingId)
        
        if not importPlayerId:
            flash("Player ID to import is missing", "error")
            log(3, "player_import", f"Missing import_player_id for ranking {rankingId}")
            return redirect(f'/trainer/{rankingId}')
            
        importPlayerId = int(importPlayerId)
        
        # Import the player
        addPlayerToRanking(importPlayerId, rankingId)
        flash(f"Successfully imported player to ranking", "success")
        log(1, "player_import", f"Imported player {importPlayerId} to ranking {rankingId}")
        
    except ValueError as e:
        flash("Invalid input values for player import", "error")
        log(4, "player_import", f"Invalid parameter values for player import: {e}")
    except Exception as e:
        flash("Could not import player due to an error", "error")
        log(4, "player_import", f"Could not import player {importPlayerId} to ranking {rankingId}: {e}")
    
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/player_edit', methods=['POST'])
@requiresTrainer
def player_edit():
    """
    Updates player information including attributes, ranking, and bonus settings.
    Handles multiple types of updates in a single transaction.
    
    Form Parameters:
        player_id: ID of the player to edit
        rankingId: ID of the current ranking
        ranking: New ranking position (optional)
        name: New player name (optional)
        wins: New win count (optional)
        losses: New loss count (optional)
        setsWon: New sets won count (optional)
        setsLost: New sets lost count (optional)
        bonus: Bonus points amount (optional)
        logic_operator: Comparison operator for bonus (optional)
        limit_ranking: Ranking threshold for bonus (optional)
        
    Returns:
        Redirect to trainer page for the ranking
        
    Raises:
        Exception: Logs error if player cannot be updated
    """
    try:
        # Extract and validate form parameters
        playerId = request.form.get('player_id')
        rankingId = request.form.get('rankingId')
        
        # Validate required parameters
        if not rankingId:
            flash("Ranking ID is missing", "error")
            log(3, "player_edit", "Missing rankingId parameter")
            return redirect('/trainer/1')  # Fallback to default ranking
            
        rankingId = int(rankingId)
        
        if not playerId:
            flash("Player ID is missing", "error")
            log(3, "player_edit", f"Could not edit player because the submitted Id was empty")
            return redirect(f'/trainer/{rankingId}')
        
        playerId = int(playerId)
        
        # Get the player object
        player = db.session.get(Players, playerId)
        if not player:
            flash("Player not found", "error")
            log(3, "player_edit", f"Player with ID {playerId} not found")
            return redirect(f'/trainer/{rankingId}')
    
        # Handle ranking update
        new_ranking = request.form.get('ranking')
        if new_ranking and new_ranking.strip():
            try:
                new_ranking = int(new_ranking)
                player_ranking_entry = PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()
                
                if player_ranking_entry and player_ranking_entry.ranking != new_ranking:
                    updatePlayerRanking(playerId, rankingId, new_ranking)
                    flash(f"Updated ranking for player {player.name} to {new_ranking}", "success")
                    log(1, "player_edit", f"Updated ranking for player {player.name} to {new_ranking}")
            except ValueError as e:
                flash("Invalid ranking value", "error")
                log(3, "player_edit", f"Invalid ranking value: {new_ranking}")
        
        # Handle player attribute updates
        attribute_mappings = [
            ("name", "name"),
            ("wins", "wins"),
            ("losses", "losses"),
            ("setsWon", "sets_won"),
            ("setsLost", "sets_lost")
        ]
        updatePlayerAttributes(player, attribute_mappings, request)
        flash(f"Updated attributes for player {player.name}", "success")
        
        # Handle bonus update/creation
        bonus = request.form.get('bonus')
        logicOperator = request.form.get('logic_operator')
        limitRanking = request.form.get('limit_ranking')
        
        if validateBonusParameters(bonus, logicOperator, limitRanking):
            success = updateOrCreatePlayerBonus(playerId, bonus, logicOperator, limitRanking)
            if success:
                flash(f"Updated bonus for player {player.name}", "success")
                log(1, "player_edit", f"Updated bonus for player {player.name}")
            else:
                flash(f"Failed to update bonus for player {player.name}", "error")
                log(3, "player_edit", f"Failed to update bonus for player {player.name}")
        
        flash(f"Successfully edited player {player.name}", "success")
        log(1, "player_edit", f"Successfully edited player {player.name} (ID: {playerId})")
        
    except ValueError as e:
        flash("Invalid input values", "error")
        log(4, "player_edit", f"Invalid parameter values for player edit: {e}")
    except Exception as e:
        flash("Could not edit player due to an error", "error")
        log(4, "player_edit", f"Could not edit player {playerId}: {e}")
    
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/player_remove', methods=['POST'])
@requiresTrainer
def player_remove():
    """
    Removes a player from a specific ranking without deleting the player entirely.
    The player remains in the system and can be added to other rankings.
    
    Form Parameters:
        player_id: ID of the player to remove
        rankingId: ID of the ranking to remove the player from
        
    Returns:
        Redirect to trainer page for the ranking
        
    Raises:
        Exception: Logs error if player cannot be removed
    """
    try:
        # Extract and validate form parameters
        playerId = request.form.get('player_id')
        rankingId = request.form.get('rankingId')
        
        # Validate required parameters
        if not rankingId:
            flash("Ranking ID is missing", "error")
            log(3, "player_remove", "Missing rankingId parameter")
            return redirect('/trainer/1')  # Fallback to default ranking
            
        rankingId = int(rankingId)
        
        if not playerId:
            flash("Player ID is missing", "error")
            log(3, "player_remove", f"Could not remove player because the submitted Id was empty")
            return redirect(f'/trainer/{rankingId}')
            
        playerId = int(playerId)
        
        # Remove the player from the ranking
        removePlayerFromRanking(playerId, rankingId)
        flash(f"Successfully removed player {playerId} from ranking", "success")
        log(1, "player_remove", f"Removed Player {playerId} from Ranking with Id:{rankingId}")
        
    except ValueError as e:
        flash("Invalid input values for player removal", "error")
        log(4, "player_remove", f"Invalid parameter values for player removal: {e}")
    except Exception as e:
        flash("Could not remove player due to an error", "error")
        log(4, "player_remove", f"Could not remove Player {playerId} from Ranking {rankingId}: {e}")
    
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/player_delete', methods=['POST'])
@requiresTrainer
def player_delete():
    """
    Permanently deletes a player from the entire system.
    Removes the player from all rankings and deletes all associated data.
    
    Form Parameters:
        player_id: ID of the player to delete
        rankingId: ID of the current ranking (for redirect)
        
    Returns:
        Redirect to trainer page for the ranking
        
    Raises:
        Exception: Logs error if player cannot be deleted
    """
    try:
        # Extract and validate form parameters
        playerId = request.form.get('player_id')
        rankingId = request.form.get('rankingId')
        
        # Validate required parameters
        if not rankingId:
            flash("Ranking ID is missing", "error")
            log(3, "player_delete", "Missing rankingId parameter")
            return redirect('/trainer/1')  # Fallback to default ranking
            
        rankingId = int(rankingId)
        
        if not playerId:
            flash("Player ID is missing", "error")
            log(3, "player_delete", f"Could not delete player because the submitted Id was empty")
            return redirect(f'/trainer/{rankingId}')
            
        playerId = int(playerId)
        
        # Delete the player entirely
        deletePlayer(playerId)
        flash(f"Successfully deleted player {playerId}", "success")
        log(1, "player_delete", f"Deleted Player {playerId}")
        
    except ValueError as e:
        flash("Invalid input values for player deletion", "error")
        log(4, "player_delete", f"Invalid parameter values for player deletion: {e}")
    except Exception as e:
        flash("Could not delete player due to an error", "error")
        log(4, "player_delete", f"Could not delete Player {playerId}: {e}")
    
    return redirect(f'/trainer/{rankingId}')

if __name__ == '__main__':
    """
    Application entry point that initializes the database and starts the Flask development server.
    Creates test data if the database is empty to facilitate development and testing.
    """
    try:
        with app.app_context():
            # Note: Database table creation is now handled by Flask-Migrate
            # Only add test data if none exists to avoid duplicates
            
            # Create test players if database is empty
            if Players.query.count() == 0:
                log(1, "startup", "Creating test players")
                test_players = [
                    Players(name="Alice", wins=12, losses=3, setsWon=25, setsLost=10, ranking=1, points=27),
                    Players(name="Bob", wins=10, losses=4, setsWon=22, setsLost=11, ranking=2, points=24),
                    Players(name="Charlie", wins=8, losses=6, setsWon=18, setsLost=15, ranking=3, points=20),
                ]
                for player in test_players:
                    db.session.add(player)
                db.session.commit()
                log(1, "startup", f"Created {len(test_players)} test players")

            # Create test rankings if database is empty
            if Rankings.query.count() == 0:
                log(1, "startup", "Creating test rankings")
                test_rankings = [
                    Rankings(name="Junior"),
                    Rankings(name="Hobby"),
                    Rankings(name="Turnier")
                ]
                for ranking in test_rankings:
                    db.session.add(ranking)
                db.session.commit()
                log(1, "startup", f"Created {len(test_rankings)} test rankings")

            # Create PlayerRankings for each player in each ranking if none exist
            if PlayerRankings.query.count() == 0:
                log(1, "startup", "Creating test player rankings")
                players = Players.query.all()
                rankings = Rankings.query.all()
                
                ranking_entries_created = 0
                for ranking in rankings:
                    for player in players:
                        player_ranking = PlayerRankings(
                            playerId=player.id,
                            rankingId=ranking.id,
                            ranking=player.ranking,
                            lastRanking=player.ranking,
                            lastRankingChanged=datetime.now(timezone.utc),
                            points=player.points
                        )
                        db.session.add(player_ranking)
                        ranking_entries_created += 1
                
                db.session.commit()
                log(1, "startup", f"Created {ranking_entries_created} player ranking entries")

            if Authentication.query.count() == 0:
                viewerAuthentication = Authentication(
                    name = 'viewer',
                    passwordHash = generate_password_hash("viewerPassword2")
                )

                trainerAuthentication = Authentication(
                    name = 'trainer',
                    passwordHash = generate_password_hash("trainerPassword3")
                )

                db.session.add(viewerAuthentication)
                db.session.add(trainerAuthentication)

                db.session.commit()

            # Log startup completion within the application context
            log(1, "startup", "Database initialization completed successfully")

        # Start the Flask development server (outside app context, use print instead of log)
        print("Starting Flask application on port 5001...")
        app.run(debug=True, port=5001, host='0.0.0.0')
        
    except Exception as e:
        # Use print instead of log since we're outside application context
        print(f"Critical error during application startup: {e}")
        # Try to log within app context if possible
        try:
            with app.app_context():
                log(4, "startup", f"Failed to start application: {e}")
        except Exception as log_error:
            print(f"Could not log error to database: {log_error}")