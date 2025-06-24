from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Players(db.Model): #Actual list of Players
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    wins = db.Column(db.Integer, nullable=False)
    losses = db.Column(db.Integer, nullable=False)
    setsWon = db.Column(db.Integer, nullable=False)
    setsLost = db.Column(db.Integer, nullable=False)
    lastRanking = db.Column(db.Integer, nullable=True) #To indicate changes in the rankings
    lastRankingChanged = db.Column(db.DateTime, nullable=True) #When the ranking change occurred

class Rankings(db.Model): #List of all currently ongoing Rankings
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.Text)

class PlayerRankings(db.Model): #Table with one row per player per ranking - tracks each player's position and points in different rankings
    id = db.Column(db.Integer, primary_key=True)
    playerId = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    rankingId = db.Column(db.Integer, db.ForeignKey('rankings.id'), nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    lastRanking = db.Column(db.Integer, nullable=True) #To indicate changes in the rankings
    lastRankingChanged = db.Column(db.DateTime, nullable=True) #When the ranking change occurred
    points = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('playerId', 'rankingId', name='uq_player_ranking'),
    )

class PlayerBonuses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playerId = db.Column(db.Integer, nullable=False)
    bonus = db.Column(db.Integer, nullable=False)
    logicOperator = db.Column(db.String(2), nullable=False)
    limitRanking = db.Column(db.Integer, nullable=False)

class OnGoingMatches(db.Model): #List of all curent matches
    id = db.Column(db.Integer, primary_key=True)
    challenger = db.Column(db.String(100), nullable=False)
    challengerId = db.Column(db.Integer, nullable=False)
    challengerBonus = db.Column(db.Integer)
    defender = db.Column(db.String(100), nullable=False)
    defenderId = db.Column(db.Integer, nullable=False)
    defenderBonus = db.Column(db.Integer)
    timeStarted = db.Column(db.DateTime, nullable=False)
    rankingId = db.Column(db.Integer, db.ForeignKey('rankings.id'), nullable=False)

class FinishedMatches(db.Model): #List of all finished matches
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
    rankingId = db.Column(db.Integer, db.ForeignKey('rankings.id'), nullable=False)

class LogEntries(db.Model): #List of Log Entries
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    level = db.Column(db.String(15))
    origin = db.Column(db.String(25))
    message = db.Column(db.Text)