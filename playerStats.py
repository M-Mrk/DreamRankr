from db import db, Players
from logger import log
from datetime import datetime, timezone
from db import PlayerRankings, Players

def checkIfWinnerIsLower(winner, loser, rankingId):
    # Use PlayerRankings to compare rankings in the correct ranking context
    winnerRanking = PlayerRankings.query.filter_by(playerId=winner.id, rankingId=rankingId).first()
    loserRanking = PlayerRankings.query.filter_by(playerId=loser.id, rankingId=rankingId).first()
    if not winnerRanking or not loserRanking:
        log(3, "checkIfWinnerIsLower", f"Could not find ranking for winner {winner.id} or loser {loser.id} in ranking {rankingId}")
        return False
    return winnerRanking.ranking > loserRanking.ranking

def rankPlayerUp(player, rankingId): #Ranks given Player one higher and deranks other Player, who is above the given Player, basically swaps ranking between them
    playerRanking = PlayerRankings.query.filter_by(playerId=player.id, rankingId=rankingId).first()
    if not playerRanking:
        log(3, "rankPlayerUp", f"Player ranking not found for player {player.id} in ranking {rankingId}")
        return
    
    currentRanking = playerRanking.ranking
    if currentRanking == 1: #Stops if Player is already highest ranking
        log(3, "rankPlayerUp", f"{player.name}({player.id}) is already highest Ranking")
        return
    newRanking = currentRanking - 1  # Fix: ranking should decrease (1 is better than 2)
    print(f"currentRanking: {currentRanking}, newRanking: {newRanking}")
    
    # Find the other player BEFORE making any changes
    otherPlayerRanking = PlayerRankings.query.filter_by(ranking=newRanking, rankingId=rankingId).first()
    if not otherPlayerRanking:
        log(3, "rankPlayerUp", f"otherPlayerRanking doesn't exist/couldn't be found. Searched for ranking: {newRanking} in rankingId: {rankingId}")
        return
    
    otherPlayer = Players.query.filter_by(id=otherPlayerRanking.playerId).first()
    if not otherPlayer:
        log(3, "rankPlayerUp", f"otherPlayer doesn't exist/couldn't be found. Searched for player with ID: {otherPlayerRanking.playerId}")
        return
    
    # Update both players' lastRanking and timestamp before swapping
    playerRanking.lastRanking = currentRanking
    playerRanking.lastRankingChanged = datetime.now(timezone.utc)
    otherPlayerRanking.lastRanking = otherPlayerRanking.ranking
    otherPlayerRanking.lastRankingChanged = datetime.now(timezone.utc)
    
    # Swap rankings
    playerRanking.ranking = newRanking
    otherPlayerRanking.ranking = currentRanking
    db.session.commit()
    log(1, "rankPlayerUp", f"{player.name}({player.id}) ranking changes up from {currentRanking} to {playerRanking.ranking}")
    log(1, "rankPlayerUp", f"{otherPlayer.name}({otherPlayer.id}) ranking changes down from {newRanking} to {otherPlayerRanking.ranking}")

def getMatchesPlayed(player): #returns total played matches in this ranking
    wins = player.wins
    losses = player.losses
    return wins + losses

def increaseWinsLosses(winner, loser): #increases wins and losses by 1 for winner and loser
    winner.wins = winner.wins + 1
    loser.losses = loser.losses + 1  # Fix: should increase losses, not wins

def updatePoints(player, rankingId, won): #updates points. 1 point for playing and another point if player won
    playerRanking = PlayerRankings.query.filter_by(playerId=player.id, rankingId=rankingId).first()
    if won == True:
        playerRanking.points = playerRanking.points + 2
    else:
        playerRanking.points = playerRanking.points + 1

def changeSetStats(player, wonSets, lostSets):
    player.setsWon = player.setsWon + wonSets
    player.setsLost = player.setsLost + lostSets

def changeStats(winnerId, loserId, winnerSetsWon, loserSetsWon, rankingId):
    winner = db.session.get(Players, winnerId)
    loser = db.session.get(Players, loserId)
    if checkIfWinnerIsLower(winner, loser, rankingId):
        print("Winner is lower ranked than loser")
        rankPlayerUp(winner, rankingId)
    increaseWinsLosses(winner, loser) #Seems to work
    updatePoints(winner, rankingId, won=True)
    updatePoints(loser, rankingId, won=False)
    if winnerSetsWon and loserSetsWon:
        changeSetStats(winner, winnerSetsWon, loserSetsWon)
        changeSetStats(loser, loserSetsWon, winnerSetsWon)
    db.session.commit()