from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

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
    lastRankingChanged = db.Column(db.DateTime, nullable=True) #When the ranking change occurred

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

class LogEntries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    level = db.Column(db.String(15))
    origin = db.Column(db.String(25))
    message = db.Column(db.Text)