from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Players(db.Model):  # Inherit from db.Model and capitalize class name
    id = db.Column(db.Integer, primary_key=True)
    ranking = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    setsWon = db.Column(db.Integer, nullable=False)
    setsLost = db.Column(db.Integer, nullable=False)

@app.route('/')
def home():
    players = Players.query.order_by(Players.ranking).all()  # Use capital P for the class
    return render_template('index.html', players=players)

@app.route('/trainer')
def trainer():
    players = Players.query.order_by(Players.ranking).all()  # Use capital P for the class
    activeGames = [] # Placeholder for active games, if any !!Temprorary!!
    return render_template('trainer.html', players=players, activeGames=activeGames)

@app.route('/player_add', methods=['POST'])
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
    return trainer()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
        # Add some test data if none exists
        if Players.query.count() == 0:
            test_players = [
                Players(ranking=1, name="Alice", wins=12, losses=3, setsWon=25, setsLost=10),
                Players(ranking=2, name="Bob", wins=10, losses=4, setsWon=22, setsLost=12),
                Players(ranking=3, name="Charlie", wins=8, losses=6, setsWon=18, setsLost=15),
            ]
            for player in test_players:
                db.session.add(player)
            db.session.commit()
    
    app.run(debug=True, port=5001, host='0.0.0.0')