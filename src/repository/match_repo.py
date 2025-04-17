from typing import Optional
from sqlalchemy.orm import Session
from src.entity.match import Match
from src.repository import player_repo

def insert_match(db: Session, match: Match) -> Optional[Match]:
    """
    Insert a match into the database
    """
    # Check if players exist
    winner = player_repo.find_player_by_name(db, match.winner.name)
    loser = player_repo.find_player_by_name(db, match.loser.name)

    # Create new players if they don't exist
    if not winner:
        winner = match.winner
        db.add(winner)
    else:
        match.winner = winner

    if not loser:
        loser = match.loser
        db.add(loser)
    else:
        match.loser = loser

    # Add the match
    db.add(match)

    # Add the odds
    for odds in match.odds:
        odds.match = match
        db.add(odds)

    db.commit()
    db.refresh(match)
    
    return match
