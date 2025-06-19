from flask import Flask, render_template, request, redirect
from db import db, Players, OnGoingMatches, FinishedMatches

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Import stat functions from playerStats module
from playerStats import changeStats


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
        print("score was submitted")
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
        print("no score submitted")
        winnerId = request.form.get('winner_id')
        if winnerId == "" or not winnerId:
            return redirect('/trainer') #WIP: Error message: Winner couldnt be decided/wasnt transmitted, ties arent allowed
        winnerId = int(winnerId)
        if winnerId == challenger.id:
            print("challengerWon")
            winner = challenger.name
            loserId = defender.id
        else:
            winner = defender.name
            loserId = challenger.id
    if not winner or not winnerId:
        print("Error couldnt get winner or winnerId")
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
    print(f"Winner: {winner} (ID: {winnerId})")
    print(f"Scores - Challenger: {challengerScore if 'challengerScore' in locals() else 'N/A'}, Defender: {defenderScore if 'defenderScore' in locals() else 'N/A'}")

    try:
        changeStats(winnerId=winnerId, loserId=loserId, winnerSetsWon=winnerSetsWon, loserSetsWon=loserSetsWon)
        db.session.add(new_finishedmatch) #Works
        db.session.delete(match) #Works
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
                points=0,
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