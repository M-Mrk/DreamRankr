from flask import Flask, render_template, request, redirect
from flask_migrate import Migrate
from db import db, Players, OnGoingMatches, FinishedMatches, PlayerBonuses, Rankings, PlayerRankings
from bonuses import getBonus
from logger import log
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Import stat functions from playerStats module
from playerStats import changeStats

# Add this after creating your Flask app
app.jinja_env.globals['now'] = datetime.utcnow

# def getRankingObj(playerId, rankingId):
#     return PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()

def getRankingAndPoints(playerObj, rankingId):
    playerRankingObj = PlayerRankings.query.filter_by(playerId=playerObj.id, rankingId=rankingId).first()
    playerObj.ranking = playerRankingObj.ranking
    playerObj.points = playerRankingObj.points
    playerObj.lastRanking = playerRankingObj.lastRanking
    playerObj.lastRankingChanged = playerRankingObj.lastRankingChanged

def getPlayersOfRanking(rankingId):
    players = db.session.query(Players).join(
        PlayerRankings, Players.id == PlayerRankings.playerId
    ).filter(PlayerRankings.rankingId == rankingId).order_by(
        PlayerRankings.ranking
    ).all()

    for player in players:
        getRankingAndPoints(player, rankingId)

    return players

def getActiveMatchesOfRanking(rankingId):
    activeMatches = OnGoingMatches.query.filter_by(rankingId=rankingId).order_by(OnGoingMatches.timeStarted.asc()).all()
    return activeMatches

@app.route('/')
def home():
    rankings = Rankings.query.all()
    if Rankings.query.count() == 1:
        return redirect(f'/view/{rankings[0].id}')
    
    return render_template('index.html', rankings=rankings)

@app.route('/view/<int:rankingId>')
def view(rankingId):
    players = getPlayersOfRanking(rankingId)
    return render_template('viewer.html', players=players)

@app.route('/trainer/<int:rankingId>')
def trainer(rankingId):
    players = getPlayersOfRanking(rankingId)
    allPlayers = Players.query.all()
    # Add bonus information to each player
    for player in players:
        player.bonus = PlayerBonuses.query.filter_by(playerId=player.id).first()
    activeMatches = getActiveMatchesOfRanking(rankingId)
    return render_template('trainer.html', players=players, activeMatches=activeMatches, rankingId=rankingId, allPlayers=allPlayers)

@app.route('/trainer/start_match', methods=['POST'])
def start_match():
    rankingId = int(request.form.get('rankingId'))
    challengerId = request.form.get('challenger_id')
    defenderId = request.form.get('defender_id')
    if not challengerId or not defenderId:
        log(3, "start_match", f"Challenger or defender ID is missing. challengerId: {challengerId}, defenderId: {defenderId}")
        return redirect(f'/trainer/{rankingId}')
    challenger = db.session.get(Players, challengerId)
    defender = db.session.get(Players, defenderId)
    new_match = OnGoingMatches(
        rankingId = rankingId,
        challenger = challenger.name,
        challengerId = challengerId,
        defender = defender.name,
        defenderId = defenderId,
        timeStarted = db.func.now()
    )
    try:
        bonus = getBonus(new_match)
        print(f"{bonus.challenger} and {bonus.defender}")
        if bonus.challenger:
            new_match.challengerBonus = bonus.challenger
        if bonus.defender:
            new_match.defenderBonus = bonus.defender
        db.session.add(new_match)
        db.session.commit()
        log(1, "start_match", f"Starting match from {challenger.name}({challengerId}) against {defender.name}({defenderId})")
    except Exception as e:
        log(4, "start_match", f"Couldnt start match from {challenger.name}({challengerId}) against {defender.name}({defenderId}), because of: {e}")

    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/finish_match', methods=['POST'])
def finish_match():
    rankingId = int(request.form.get('rankingId'))
    matchId = int(request.form.get('match_id'))
    match = db.session.get(OnGoingMatches, matchId)
    challenger = db.session.get(Players, match.challengerId)
    defender = db.session.get(Players, match.defenderId)
    
    # Initialize variables
    challengerScore = None
    defenderScore = None
    winnerSetsWon = None
    loserSetsWon = None
    
    if request.form.get('challenger_score') and request.form.get('defender_score'): #Sets loser and Winner | check if Score was provided
        challengerScore = int(request.form.get('challenger_score'))
        defenderScore = int(request.form.get('defender_score'))
        if challengerScore > defenderScore: #decide based on score who won | challengers score is higher = challenger won
            winner = challenger.name
            winnerId = challenger.id
            winnerSetsWon = challengerScore
            loserSetsWon = defenderScore
            loserId = defender.id
        elif defenderScore > challengerScore: #defender Won
            winner = defender.name
            winnerId = defender.id 
            winnerSetsWon = defenderScore
            loserSetsWon = challengerScore
            loserId = challenger.id
    else: #alternative logic if only who won is provided
        winnerId = request.form.get('winner_id')
        if winnerId == "" or not winnerId:
            return redirect(f'/trainer/{rankingId}') #WIP: Error message: Winner couldnt be decided/wasnt transmitted, ties arent allowed
        winnerId = int(winnerId)
        if winnerId == challenger.id:
            winner = challenger.name
            loserId = defender.id
        else:
            winner = defender.name
            loserId = challenger.id
    if not winner or not winnerId:
        if challengerScore or defenderScore:
            error = f"Winner or WinnerId could not be resolved when finishing a match. ChallengerScore: {challengerScore} and defenderScore: {defenderScore}"
        else:
            error = f"Winner or WinnerId could not be resolved when finishing a match"
        log(3, "finish_match", error)
        return redirect(f'/trainer/{rankingId}') #WIP: Error message: Winner couldnt be decided/wasnt transmitted, ties arent allowed

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
        challengerScore = challengerScore if challengerScore and defenderScore else None,
        defenderScore = defenderScore if challengerScore and defenderScore else None,
    )

    try:
        changeStats(winnerId=winnerId, loserId=loserId, winnerSetsWon=winnerSetsWon, loserSetsWon=loserSetsWon, rankingId=rankingId)
        db.session.add(new_finishedmatch) #Works
        db.session.delete(match) #Works
        db.session.commit()
        log(1, "finish_match", f"Finished match with now id: {new_finishedmatch.id}, winnerId: {winnerId}")
        return redirect(f'/trainer/{rankingId}')
    except Exception as e:
        log(4, "finish_match", f"Could not finish match with id: {matchId}, because of: {e}")
        return redirect(f'/trainer/{rankingId}') #WIP: Error message
    
@app.route('/trainer/player_add', methods=['POST'])
def player_add():
    rankingId = int(request.form.get('rankingId'))
    name = request.form.get('name')
    
    if not name or not rankingId:
        return redirect(f'/trainer/{rankingId}')
    
    # Check if player already exists
    currentPlayers = Players.query.all()
    if name in [player.name for player in currentPlayers]:
        log(3, "player_add", "Submitted new player already exists")
        return redirect(f'/trainer/{rankingId}')
    
    # Create new player
    new_player = Players(
        name=name,
        wins=0,
        losses=0,
        setsWon=0,
        setsLost=0
    )
    
    # Determine next ranking
    currentRankings = PlayerRankings.query.filter_by(rankingId=rankingId).order_by(PlayerRankings.ranking).all()
    next_ranking = currentRankings[-1].ranking + 1 if currentRankings else 1
    
    # Add player first to get ID
    db.session.add(new_player)
    db.session.flush()  # This assigns the ID without committing
    
    # Create ranking entry
    new_ranking = PlayerRankings(
        playerId=new_player.id,
        rankingId=rankingId, 
        ranking=next_ranking, 
        points=0
    )
    db.session.add(new_ranking)
    
    # Handle bonus if provided
    bonus = request.form.get('bonus')
    logicOperator = request.form.get('logic_operator')
    limitRanking = request.form.get('limit_ranking')
    
    if bonus and logicOperator and limitRanking:
        new_bonus = PlayerBonuses(
            playerId=new_player.id,
            bonus=int(bonus),
            logicOperator=logicOperator,
            limitRanking=int(limitRanking)
        )
        db.session.add(new_bonus)
    
    try:
        db.session.commit()
        log(1, "player_add", f"Added new player: {name}. Now has Id: {new_player.id}")
    except Exception as e:
        db.session.rollback()
        log(4, "player_add", f"New player: {name} couldn't be added, because of {e}")
        return redirect(f'/trainer/{rankingId}')
    
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/player_import', methods=['POST'])
def player_import():
    rankingId = request.form.get('rankingId')
    importPlayerId = request.form.get('import_player_id')

    if not rankingId or not importPlayerId:
        log(3, "player_import", f"RankingId or importPlayerId is missing. rankingId: {rankingId}, importPlayerId: {importPlayerId}")
        return redirect(f'/trainer/{rankingId}')

    # Check if player exists
    player = db.session.get(Players, importPlayerId)
    if not player:
        log(3, "player_import", f"Player with ID {importPlayerId} does not exist")
        return redirect(f'/trainer/{rankingId}')

    # Check if player is already in this ranking
    existing_ranking = PlayerRankings.query.filter_by(playerId=importPlayerId, rankingId=rankingId).first()
    if existing_ranking:
        log(3, "player_import", f"Player {player.name}({importPlayerId}) is already in ranking {rankingId}")
        return redirect(f'/trainer/{rankingId}')

    # Determine next ranking position
    currentRankings = PlayerRankings.query.filter_by(rankingId=rankingId).order_by(PlayerRankings.ranking).all()
    next_ranking = currentRankings[-1].ranking + 1 if currentRankings else 1

    # Create ranking entry for existing player
    new_ranking = PlayerRankings(
        playerId=importPlayerId,
        rankingId=rankingId,
        ranking=next_ranking,
        points=0
    )

    try:
        db.session.add(new_ranking)
        db.session.commit()
        log(1, "player_import", f"Imported player {player.name}({importPlayerId}) to ranking {rankingId}")
    except Exception as e:
        db.session.rollback()
        log(4, "player_import", f"Could not import player {player.name}({importPlayerId}) to ranking {rankingId}, because of {e}")

    return redirect(f'/trainer/{rankingId}')

def checkIfChangedAndUpdate(formId, player, playerArgument, argumentName):
    formArgument = request.form.get(formId)
    if formArgument and not formArgument == playerArgument:
        oldArgument = getattr(player, argumentName)
        setattr(player, argumentName, formArgument)
        try:
            db.session.commit()
        except Exception as e:
            log(4, "player_edit", f"Could not change {argumentName} for {player.name}({player.id}) from {oldArgument} to {formArgument}, because of {e}")
        log(1, "player_edit", f"Changed {player.name}({player.id}) {argumentName} from {oldArgument} to {formArgument}")

@app.route('/trainer/player_edit', methods=['POST'])
def player_edit():
    playerId = request.form.get('player_id')
    rankingId = request.form.get('rankingId')
    if not playerId:
        log(3, "player_edit", f"Could not edit player because the submitted Id was empty")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message

    try:
        player = db.session.get(Players, playerId)
    except Exception as e:
        log(4, "player_edit", f"Could not get Player from playerId: {playerId}, because of {e}")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message
    
    dbArguments = ["ranking", "name", "wins", "losses", "setsWon", "setsLost"]
    formArguments = ['ranking', 'name', 'wins', 'losses', 'sets_won', 'sets_lost']

    for i in range(len(dbArguments)):
        checkIfChangedAndUpdate(formArguments[i], player, player.name, dbArguments[i])

    # Handle bonus editing
    bonus = request.form.get('bonus')
    logicOperator = request.form.get('logic_operator')
    limitRanking = request.form.get('limit_ranking')
    
    if bonus and logicOperator and limitRanking and not bonus == "" and not logicOperator == "" and not limitRanking == "":
        # Check if player already has a bonus
        existing_bonus = PlayerBonuses.query.filter_by(playerId=playerId).first()
        
        if existing_bonus:
            # Update existing bonus
            existing_bonus.bonus = int(bonus)
            existing_bonus.logicOperator = logicOperator
            existing_bonus.limitRanking = int(limitRanking)
            try:
                db.session.commit()
                log(1, "player_edit", f"Updated bonus for player {player.name}({player.id}): {bonus} {logicOperator} {limitRanking}")
            except Exception as e:
                log(4, "player_edit", f"Could not update bonus for player {player.name}({player.id}), because of {e}")
        else:
            # Create new bonus
            new_bonus = PlayerBonuses(
                playerId = int(playerId),
                bonus = int(bonus),
                logicOperator = logicOperator,
                limitRanking = int(limitRanking)
            )
            try:
                db.session.add(new_bonus)
                db.session.commit()
                log(1, "player_edit", f"Updated/Added bonus for player {player.name}({player.id}): {bonus} {logicOperator} {limitRanking}")
            except Exception as e:
                log(4, "player_edit", f"Could not add bonus for player {player.name}({player.id}), because of {e}")

    return redirect(f'/trainer/{rankingId}')
    
@app.route('/trainer/player_remove', methods=['POST'])
def player_remove():
    playerId = request.form.get('player_id')
    rankingId = request.form.get('rankingId')
    if not playerId:
        log(3, "player_remove", f"Could not remove player because the submitted Id was empty")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message

    try:
        player = db.session.get(Players, playerId)
    except Exception as e:
        log(4, "player_remove", f"Could not get Player from playerId: {playerId}, because of {e}")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message
    
    try:
        playerRankingEntry = PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()
    except Exception as e:
        log(3, "player_remove", f"Could not find ranking entry for player {player.name}({playerId}) in ranking {rankingId}, because of {e}")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message
    
    if not playerRankingEntry:
        log(3, "player_remove", f"Could not find ranking entry for player {player.name}({playerId}) in ranking {rankingId}")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message

    try:
        db.session.delete(playerRankingEntry)
        db.session.commit()
    except Exception as e:
        log(4, "player_remove", f"Could not remove Player {player.name}({playerId}), because of {e}")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message
    
    log(1, "player_remove", f"Removed Player {player.name}({playerId}) from Ranking with Id:{rankingId}")
    return redirect(f'/trainer/{rankingId}')

@app.route('/trainer/player_delete', methods=['POST'])
def player_delete():
    playerId = request.form.get('player_id')
    rankingId = request.form.get('rankingId')
    if not playerId:
        log(3, "player_delete", f"Could not delete player because the submitted Id was empty")
        return redirect('/trainer') #WIP: Add error message
    
    try:
        player = db.session.get(Players, playerId)
    except Exception as e:
        log(4, "player_delete", f"Could not get Player from playerId: {playerId}, because of {e}")
        return redirect('/trainer') #WIP: Add error message
    
    try:
        playerRankingEntry = PlayerRankings.query.filter_by(playerId=playerId, rankingId=rankingId).first()
    except Exception as e:
        log(3, "player_delete", f"Could not find ranking entry for player {player.name}({playerId}) in ranking {rankingId}, because of {e}")
        return redirect(f'/trainer/{rankingId}') #WIP: Add error message

    try:
        db.session.delete(player)
        db.session.delete(playerRankingEntry)
        db.session.commit()
    except Exception as e:
        log(4, "player_delete", f"Could not delete Player {player.name}({playerId}), because of {e}")
        return redirect('/trainer') #WIP: Add error message
    
    log(1, "player_delete", f"Deleted Player {player.name}({playerId})")
    return redirect('/trainer')

if __name__ == '__main__':
    with app.app_context():

        # Note: db.create_all() is now handled by Flask-Migrate
        # Only add test data if none exists
        if Players.query.count() == 0:
            test_players = [
                Players(name="Alice", wins=12, losses=3, setsWon=25, setsLost=10, ranking=1, points=27),
                Players(name="Bob", wins=10, losses=4, setsWon=22, setsLost=11, ranking=2, points=24),
                Players(name="Charlie", wins=8, losses=6, setsWon=18, setsLost=15, ranking=3, points=20),
            ]
            for player in test_players:
                db.session.add(player)
            db.session.commit()

        if Rankings.query.count() == 0:
            test_rankings = [
                Rankings(name="Junior"),
                Rankings(name="Hobby"),
                Rankings(name="Turnier")
            ]
            for ranking in test_rankings:
                db.session.add(ranking)
            db.session.commit()

        # Add PlayerRankings for each player in each ranking
        if PlayerRankings.query.count() == 0:
            players = Players.query.all()
            rankings = Rankings.query.all()
            for ranking in rankings:
                for player in players:
                    db.session.add(
                        PlayerRankings(
                            playerId=player.id,
                            rankingId=ranking.id,
                            ranking=player.ranking,
                            lastRanking=player.ranking,
                            lastRankingChanged=datetime.now(timezone.utc),
                            points=player.points
                        )
                    )
            db.session.commit()

    app.run(debug=True, port=5001, host='0.0.0.0')