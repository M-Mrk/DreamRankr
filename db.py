from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# Initialize SQLAlchemy database instance
db = SQLAlchemy()

class Players(db.Model):
    """
    Represents individual players in the ranking system.
    Stores basic player information and overall statistics across all rankings.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Player's display name
    wins = db.Column(db.Integer, nullable=False)      # Total wins across all rankings
    losses = db.Column(db.Integer, nullable=False)    # Total losses across all rankings
    setsWon = db.Column(db.Integer, nullable=False)   # Total sets won across all rankings
    setsLost = db.Column(db.Integer, nullable=False)  # Total sets lost across all rankings
    lastRanking = db.Column(db.Integer, nullable=True)        # Previous ranking position for change tracking
    lastRankingChanged = db.Column(db.DateTime, nullable=True) # Timestamp of last ranking change

class Rankings(db.Model):
    """
    Represents different ranking categories (e.g., Junior, Hobby, Tournament).
    Each ranking can have multiple players with their own positions and points.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)        # Ranking category name
    description = db.Column(db.Text, nullable=True)       # Optional description of the ranking
    sortedBy = db.Column(db.String(20), nullable=False, default="standard")
    tournament = db.Column(db.Boolean, nullable=False, default=False)
    typeTournament = db.Column(db.String(15), nullable=True)
    endsOn = db.Column(db.DateTime, nullable=True)
    ended = db.Column(db.Boolean, nullable=False, default=False)

class PlayerRankings(db.Model):
    """
    Junction table linking players to rankings with their specific position and points.
    Each row represents one player's standing in one specific ranking.
    """
    id = db.Column(db.Integer, primary_key=True)
    playerId = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    rankingId = db.Column(db.Integer, db.ForeignKey('rankings.id'), nullable=False)
    ranking = db.Column(db.Integer, nullable=False)                    # Current position in this ranking
    lastRanking = db.Column(db.Integer, nullable=True)                 # Previous position for change tracking
    lastPoints = db.Column(db.Integer, nullable=True)
    lastRankingChanged = db.Column(db.DateTime, nullable=True)         # When the ranking position last changed
    points = db.Column(db.Integer, nullable=False)                     # Points earned in this ranking
    __table_args__ = (
        db.UniqueConstraint('playerId', 'rankingId', name='uq_player_ranking'),  # One entry per player per ranking
    )

class PlayerBonuses(db.Model):
    """
    Stores bonus point conditions for individual players.
    Bonuses are applied based on the opponent's ranking relative to the condition.
    """
    id = db.Column(db.Integer, primary_key=True)
    playerId = db.Column(db.Integer, nullable=False)           # Player who receives the bonus
    bonus = db.Column(db.Integer, nullable=False)              # Bonus points amount
    logicOperator = db.Column(db.String(2), nullable=False)    # Comparison operator (=, <, <=, >, >=)
    limitRanking = db.Column(db.Integer, nullable=False)       # Ranking threshold for bonus activation

class OnGoingMatches(db.Model):
    """
    Tracks currently active matches between players.
    Contains all necessary information to finish and score the match.
    """
    id = db.Column(db.Integer, primary_key=True)
    challenger = db.Column(db.String(100), nullable=False)     # Name of challenging player
    challengerId = db.Column(db.Integer, nullable=False)       # ID of challenging player
    challengerBonus = db.Column(db.Integer)                    # Bonus points for challenger if they win
    defender = db.Column(db.String(100), nullable=False)       # Name of defending player
    defenderId = db.Column(db.Integer, nullable=False)         # ID of defending player
    defenderBonus = db.Column(db.Integer)                      # Bonus points for defender if they win
    timeStarted = db.Column(db.DateTime, nullable=False)       # When the match was started
    rankingId = db.Column(db.Integer, db.ForeignKey('rankings.id'), nullable=False)  # Which ranking this match belongs to

class FinishedMatches(db.Model):
    """
    Archive of completed matches with full results and scoring information.
    Used for historical tracking and statistics.
    """
    id = db.Column(db.Integer, primary_key=True)
    challenger = db.Column(db.String(100), nullable=False)     # Name of challenging player
    challengerId = db.Column(db.Integer, nullable=False)       # ID of challenging player
    defender = db.Column(db.String(100), nullable=False)       # Name of defending player
    defenderId = db.Column(db.Integer, nullable=False)         # ID of defending player
    timeStarted = db.Column(db.DateTime, nullable=False)       # When the match was started
    timeFinished = db.Column(db.DateTime, nullable=False)      # When the match was completed
    winner = db.Column(db.String(100), nullable=False)         # Name of the winning player
    winnerId = db.Column(db.Integer, nullable=False)           # ID of the winning player
    challengerScore = db.Column(db.Integer, nullable=True)     # Sets won by challenger (optional)
    defenderScore = db.Column(db.Integer, nullable=True)       # Sets won by defender (optional)
    rankingId = db.Column(db.Integer, db.ForeignKey('rankings.id'), nullable=False)  # Which ranking this match belonged to

class LogEntries(db.Model):
    """
    System logging table for tracking application events, errors, and debugging information.
    Provides audit trail and troubleshooting capabilities.
    """
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # When the log entry was created
    level = db.Column(db.String(15))        # Log level (Debug, Information, Warning, Error, etc.)
    origin = db.Column(db.String(25))       # Function or module that generated the log
    message = db.Column(db.Text)            # Log message content

class Authentication(db.Model):
    """
    System table for passwords
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    passwordHash = db.Column(db.String(128), nullable=False)