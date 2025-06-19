from db import db, Players

def checkIfWinnerIsLower(winnerId, loserId):
    winner = db.session.get(Players, winnerId)
    loser = db.session.get(Players, loserId)
    if winner.ranking > loser.ranking:
        return True
    else:
        return False

def rankPlayerUp(playerId): #Ranks given Player one higher and deranks other Player, who is above the given Player, basically swaps ranking between them
    player = db.session.get(Players, playerId)
    currentRanking = player.ranking
    if currentRanking == 1: #Stops if Player is already highest ranking
        print("Player is already highest Ranking")
        return
    newRanking = currentRanking - 1  # Fix: ranking should decrease (1 is better than 2)
    print(f"currentRanking: {currentRanking}, newRanking: {newRanking}")
    
    # Find the other player BEFORE making any changes
    otherPlayer = Players.query.filter_by(ranking=newRanking).first()
    if not otherPlayer:
        print("otherPlayer doesnt exist/couldnt be found")
        return
    
    # Update both players' lastRanking before swapping
    player.lastRanking = currentRanking
    otherPlayer.lastRanking = otherPlayer.ranking
    
    # Swap rankings
    player.ranking = newRanking
    otherPlayer.ranking = currentRanking
    
    db.session.commit()

def getMatchesPlayed(playerId): #returns total played matches in this ranking
    player = db.session.get(Players, playerId)
    wins = player.wins
    losses = player.losses
    return wins + losses

def increaseWinsLosses(winnerId, loserId): #increases wins and losses by 1 for winner and loser
    winner = db.session.get(Players, winnerId)
    loser = db.session.get(Players, loserId)
    winner.wins = winner.wins + 1
    loser.losses = loser.losses + 1  # Fix: should increase losses, not wins
    db.session.commit()

def updatePoints(playerId, won): #updates points. 1 point for playing and another point if player won
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

def changeStats(winnerId, loserId, winnerSetsWon, loserSetsWon):
    if checkIfWinnerIsLower(winnerId, loserId):
        print("Winner is lower ranked than loser")
        rankPlayerUp(winnerId)
    increaseWinsLosses(winnerId, loserId) #Seems to work
    updatePoints(winnerId, won=True)
    updatePoints(loserId, won=False)
    if winnerSetsWon and loserSetsWon:
        changeSetStats(winnerId, winnerSetsWon, loserSetsWon)
        changeSetStats(loserId, loserSetsWon, winnerSetsWon)