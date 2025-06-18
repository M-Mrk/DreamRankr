from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Players(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    ranking = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, nullable=False) #1 Match = +1 Point and 1 Win = +1 Point
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    setsWon = db.Column(db.Integer, nullable=False)
    setsLost = db.Column(db.Integer, nullable=False)
    lastRanking = db.Column(db.Integer, nullable=True) #To indicate changes in the rankings

class OnGoingMatches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenger = db.Column(db.String(100), nullable=False)
    challengerId = db.Column(db.Integer, nullable=False)
    defender = db.Column(db.String(100), nullable=False)
    defenderId = db.Column(db.Integer, nullable=False)
    timeStarted = db.Column(db.DateTime, nullable=False)

class FinishedMatches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenger = db.Column(db.String(100), nullable=False)
    challengerId = db.Column(db.Integer, nullable=False)
    defender = db.Column(db.String(100), nullable=False)
    defenderId = db.Column(db.Integer, nullable=False)
    timeStarted = db.Column(db.DateTime, nullable=False)
    timeFinished = db.Column(db.DateTime, nullable=False)
    winner = db.Column(db.String(100), nullable=False)
    winnerId = db.Column(db.Integer, nullable=False)
    challengerScore = db.Column(db.Integer, nullable=True)
    defenderScore = db.Column(db.Integer, nullable=True)

def checkIfWinnerIsLower(winnerId, looserId):
    winner = db.session.get(Players, winnerId)
    looser = db.session.get(Players, looserId)
    if winner.ranking < looser.ranking:
        return True
    else:
        return False

def rankPlayerUp(playerId): #Ranks given Player one higher and deranks other Player, who is above the given Player, basically swaps ranking between them
    player = db.session.get(Players, playerId)
    currentRanking = player.ranking
    if currentRanking == 1: #Stops if Player is already highest ranking
        return
    newRanking = currentRanking + 1
    player.lastRanking = currentRanking #Update Players last Ranking to the currentRanking before updating
    player.ranking = newRanking
    otherPlayer = Players.query.filter_by(ranking=newRanking).first()
    otherPlayer.lastRanking = otherPlayer.ranking #Update otherPlayers last Ranking to current Ranking before updating ranking
    otherPlayer.ranking = currentRanking

    db.session.commit()

def getMatchesPlayed(playerId):
    player = db.session.get(Players, playerId)
    wins = player.wins
    losses = player.losses
    return wins + losses

def increaseWinsLosses(winnerId, looserId):
    winner = db.session.get(Players, winnerId)
    looser = db.session.get(Players, looserId)
    winner.wins = winner.wins + 1
    looser.wins = looser.wins + 1
    db.session.commit()

def updatePoints(playerId, won):
    player = db.session.get(Players, playerId)
    if won == True:
        player.points = player.points + 2
    else:
        player.points = player.points + 1
    db.session.commit()

def changeSetStats(playerId, wonSets, lostSets):
    player = db.session.get(Players, playerId)
    player.setsWon = player.setsWon + wonSets
    player.setsLost = player.setsLost + lostSets
    db.session.commit()

def changeStats(winnerId, looserId, winnerSetsWon, looserSetsWon):
    if checkIfWinnerIsLower(winnerId, looserId):
        rankPlayerUp(winnerId)
    increaseWinsLosses(winnerId, looserId)
    updatePoints(winnerId, won=True)
    updatePoints(looserId, won=False)
    if winnerSetsWon and looserSetsWon:
        changeSetStats(winnerId, winnerSetsWon, looserSetsWon)
        changeSetStats(looserId, looserSetsWon, winnerSetsWon)


@app.route('/')
def home():
    players = Players.query.order_by(Players.ranking).all()  # Use capital P for the class
    return render_template('index.html', players=players)

@app.route('/trainer')
def trainer():
    players = Players.query.order_by(Players.ranking).all()  # Use capital P for the class
    activeMatches = OnGoingMatches.query.order_by(OnGoingMatches.timeStarted.asc()).all()  # Use capital O for the class
    return render_template('trainer.html', players=players, activeMatches=activeMatches)

@app.route('/trainer/start_match', methods=['POST'])
def start_match():
    challengerId = request.form.get('challenger_id')
    defenderId = request.form.get('defender_id')
    if not challengerId or not defenderId:
        print("Challenger or defender ID is missing.")
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
    db.session.add(new_match)
    db.session.commit()
    print(f"Starting match from {challenger.name} against {defender.name}")

    return redirect('/trainer')

@app.route('/trainer/finish_match', methods=['POST'])
def finish_match():
    matchId = request.form.get('match_id')
    match = db.session.get(OnGoingMatches, matchId)
    challenger = db.session.get(Players, match.challengerId)
    defender = db.session.get(Players, match.defenderId)
    if request.form.get('challenger_score') and request.form.get('defender_score'): #Sets Looser and Winner | check if Score was provided
        challengerScore = request.form.get('challenger_score')
        defenderScore = request.form.get('defender_score')
        if challengerScore > defenderScore: #decide based on score who won | challengers score is higher = challenger won
            winner = challenger.name
            winnerId = challenger.id
            winnerSetsWon = challengerScore
            looserSetsWon = defenderScore
            looserId = defender.id
        elif defenderScore > challengerScore: #defender Won
            winner = defender.name
            winnerId = defender.id 
            winnerSetsWon = defenderScore
            looserSetsWon = challengerScore
            looserId = challenger.id
    else: #alternative logic if only who won is provided
        winnerId = request.form.get('winnerId')
        if winnerId == challenger.id: 
            winner = challenger.name
            looserId = defender.id
        else:
            winner = defender.name
            looserId = challenger.id
    if not winner or not winnerId:
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

    try:
        changeStats(winnerId=winnerId, looserId=looserId, winnerSetsWon=winnerSetsWon, looserSetsWon=looserSetsWon)
        db.session.add(new_finishedmatch)
        db.session.delete(match)
        db.session.commit()
        return redirect('/trainer')
    except:
        return redirect('/trainer') #WIP: Error message
    

@app.route('/trainer/player_add', methods=['POST'])
def player_add():
    name = request.form.get('name')
    print(f"Adding player: {name}")
    if name:
        currentPlayers = Players.query.order_by(Players.ranking).all()
        if name in [player.name for player in currentPlayers]:
            print(f"Player {name} already exists.")
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
                setsWon=0,
                setsLost=0
            )
            db.session.add(new_player)
            db.session.commit()
    return redirect('/trainer')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
        # Add some test data if none exists
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