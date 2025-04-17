from sqlalchemy.orm import Session
from typing import Optional
from src.entity.match import Match
from src.entity.player import Player


def find_player_by_name(db: Session, name: str) -> Optional[Match]:
    """
    Find a player by his name
    """
    return db.query(Player).filter(Player.name == name).first()
