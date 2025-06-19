from db import db, Players
from logger import log
from datetime import datetime, timezone

def checkIfWinnerIsLower(winner, loser):
    if winner.ranking > loser.ranking:
        return True
    else:
        return False

def rankPlayerUp(player): #Ranks given Player one higher and deranks other Player, who is above the given Player, basically swaps ranking between them
    currentRanking = player.ranking
    if currentRanking == 1: #Stops if Player is already highest ranking
        log(3, "rankPlayerUp", f"{player.name}({player.id}) is already highest Ranking")
        return
    newRanking = currentRanking - 1  # Fix: ranking should decrease (1 is better than 2)
    print(f"currentRanking: {currentRanking}, newRanking: {newRanking}")
    
    # Find the other player BEFORE making any changes
    otherPlayer = Players.query.filter_by(ranking=newRanking).first()
    if not otherPlayer:
        log(3, "rankPlayerUp", f"otherPlayer doesnt exist/couldnt be found. Searched for player with Ranking: {newRanking}")
        return
    
    # Update both players' lastRanking and timestamp before swapping
    player.lastRanking = currentRanking
    player.lastRankingChanged = datetime.now(timezone.utc)
    otherPlayer.lastRanking = otherPlayer.ranking
    otherPlayer.lastRankingChanged = datetime.now(timezone.utc)
    
    # Swap rankings
    player.ranking = newRanking
    otherPlayer.ranking = currentRanking
    db.session.commit()
    log(1, "rankPlayerUp", f"{player.name}({player.id}) ranking changes up from {currentRanking} to {player.ranking}")
    log(1, "rankPlayerUp", f"{otherPlayer.name}({otherPlayer.id}) ranking changes down from {newRanking} to {otherPlayer.ranking}")

def getMatchesPlayed(player): #returns total played matches in this ranking
    wins = player.wins
    losses = player.losses
    return wins + losses

def increaseWinsLosses(winner, loser): #increases wins and losses by 1 for winner and loser
    winner.wins = winner.wins + 1
    loser.losses = loser.losses + 1  # Fix: should increase losses, not wins

def updatePoints(player, won): #updates points. 1 point for playing and another point if player won
    if won == True:
        player.points = player.points + 2
    else:
        player.points = player.points + 1

def changeSetStats(player, wonSets, lostSets):
    player.setsWon = player.setsWon + wonSets
    player.setsLost = player.setsLost + lostSets

def changeStats(winnerId, loserId, winnerSetsWon, loserSetsWon):
    winner = db.session.get(Players, winnerId)
    loser = db.session.get(Players, loserId)
    if checkIfWinnerIsLower(winner, loser):
        print("Winner is lower ranked than loser")
        rankPlayerUp(winner)
    increaseWinsLosses(winner, loser) #Seems to work
    updatePoints(winner, won=True)
    updatePoints(loser, won=False)
    if winnerSetsWon and loserSetsWon:
        changeSetStats(winner, winnerSetsWon, loserSetsWon)
        changeSetStats(loser, loserSetsWon, winnerSetsWon)
    db.session.commit()