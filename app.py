from flask import Flask, render_template, request, redirect
from flask_migrate import Migrate
from db import db, Players, OnGoingMatches, FinishedMatches
from logger import log
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Import stat functions from playerStats module
from playerStats import changeStats

# Add this after creating your Flask app
app.jinja_env.globals['now'] = datetime.utcnow

@app.route('/')
def home():
    players = Players.query.order_by(Players.ranking).all()
    return render_template('index.html', players=players)

@app.route('/trainer')
def trainer():
    players = Players.query.order_by(Players.ranking).all()
    activeMatches = OnGoingMatches.query.order_by(OnGoingMatches.timeStarted.asc()).all()
    return render_template('trainer.html', players=players, activeMatches=activeMatches)

@app.route('/trainer/start_match', methods=['POST'])
def start_match():
    challengerId = request.form.get('challenger_id')
    defenderId = request.form.get('defender_id')
    if not challengerId or not defenderId:
        log(3, "start_match", f"Challenger or defender ID is missing. challengerId: {challengerId}, defenderId: {defenderId}")
        return redirect('/trainer')
    challenger = db.session.get(Players, challengerId)
    defender = db.session.get(Players, defenderId)
    new_match = OnGoingMatches(
        challenger = challenger.name,
        challengerId = challengerId,
        defender = defender.name,
        defenderId = defenderId,
        timeStarted = db.func.now()
    )
    try:
        db.session.add(new_match)
        db.session.commit()
        log(1, "start_match", f"Starting match from {challenger.name}({challengerId}) against {defender.name}({defenderId})")
    except Exception as e:
        log(4, "start_match", f"Couldnt start match from {challenger.name}({challengerId}) against {defender.name}({defenderId}), because of: {e}")

    return redirect('/trainer')

@app.route('/trainer/finish_match', methods=['POST'])
def finish_match():
    print("got finish_match Form")
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
            return redirect('/trainer') #WIP: Error message: Winner couldnt be decided/wasnt transmitted, ties arent allowed
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
        return redirect('/trainer') #WIP: Error message: Winner couldnt be decided/wasnt transmitted, ties arent allowed

    new_finishedmatch = FinishedMatches(
        challenger = challenger.name,
        challengerId = challenger.id,
        defender = defender.name,
        defenderId = defender.id,
        timeStarted = match.timeStarted,
        timeFinished = db.func.now(),
        winner = winner,
        winnerId = winnerId,
        challengerScore = challengerScore if challengerScore and defenderScore else None,
        defenderScore = defenderScore if challengerScore and defenderScore else None
    )

    print(f"Match finished: {challenger.name} vs {defender.name}")
    print(f"Winner: {winner} (ID: {winnerId})") #Temporary Debugging
    print(f"Scores - Challenger: {challengerScore if 'challengerScore' in locals() else 'N/A'}, Defender: {defenderScore if 'defenderScore' in locals() else 'N/A'}")

    try:
        changeStats(winnerId=winnerId, loserId=loserId, winnerSetsWon=winnerSetsWon, loserSetsWon=loserSetsWon)
        db.session.add(new_finishedmatch) #Works
        db.session.delete(match) #Works
        db.session.commit()
        log(1, "finish_match", f"Finished match with now id: {new_finishedmatch.id}, winnerId: {winnerId}")
        return redirect('/trainer')
    except Exception as e:
        log(4, "finish_match", f"Could not finish match with id: {matchId}, because of: {e}")
        return redirect('/trainer') #WIP: Error message
    

@app.route('/trainer/player_add', methods=['POST'])
def player_add():
    name = request.form.get('name')
    if name:
        currentPlayers = Players.query.order_by(Players.ranking).all()
        if name in [player.name for player in currentPlayers]:
            log(3, "player_add", "Submitted new player through /player_add already exists")
        else:
            # Determine the next ranking
            if currentPlayers:
                next_ranking = currentPlayers[-1].ranking + 1 if currentPlayers else 1
            else:
                next_ranking = 1
            # Add the new player
            new_player = Players(
                ranking=next_ranking,
                name=name,
                wins=0,
                losses=0,
                points=0,
                setsWon=0,
                setsLost=0
            )
            db.session.add(new_player)
            try:
                db.session.commit()
                log(1, "player_add", f"Added new player: {name}. Now has Id: {new_player.id}")
            except Exception as e:
                log(4, "player_add", f"New player: {name} couldnt be added, because of {e}")
    return redirect('/trainer')

def checkIfChangedAndUpdate(formId, player, playerArgument, argumentName):
    formArgument = request.form.get(formId)
    if formArgument and not formArgument == playerArgument:
        print("Ding")
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
    if not playerId:
        log(3, "player_edit", f"Could not edit player because the submitted Id was empty")
        return redirect('/trainer') #WIP: Add error message

    try:
        player = db.session.get(Players, playerId)
    except Exception as e:
        log(4, "player_edit", f"Could not get Player from playerId: {playerId}, because of {e}")
        return redirect('/trainer') #WIP: Add error message
    
    dbArguments = ["ranking", "name", "wins", "losses", "setsWon", "setsLost"]
    formArguments = ['ranking', 'name', 'wins', 'losses', 'sets_won', 'sets_lost']

    for i in range(len(dbArguments)):
        checkIfChangedAndUpdate(formArguments[i], player, player.name, dbArguments[i])

    return redirect('/trainer')

    

@app.route('/trainer/player_delete', methods=['POST'])
def player_delete():
    playerId = request.form.get('player_id')
    if not playerId:
        log(3, "player_delete", f"Could not delete player because the submitted Id was empty")
        return redirect('/trainer') #WIP: Add error message
    
    try:
        player = db.session.get(Players, playerId)
    except Exception as e:
        log(4, "player_delete", f"Could not get Player from playerId: {playerId}, because of {e}")
        return redirect('/trainer') #WIP: Add error message
    
    try:
        db.session.delete(player)
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
                Players(ranking=1, name="Alice", wins=12, points=15, losses=3, setsWon=25, setsLost=10),
                Players(ranking=2, name="Bob", wins=10, points=14, losses=4, setsWon=22, setsLost=1),
                Players(ranking=3, name="Charlie", wins=8, points=14, losses=6, setsWon=18, setsLost=15),
            ]
            for player in test_players:
                db.session.add(player)
            db.session.commit()
    
    app.run(debug=True, port=5001, host='0.0.0.0')