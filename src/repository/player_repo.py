from sqlalchemy.orm import Session
from typing import Optional, Dict
from src.entity.player import Player, Caracteristics


def find_player_by_name(db: Session, name: str) -> Optional[Player]:
    """
    Find a player by his name
    """
    return db.query(Player).filter(Player.name == name).first()

def add_caracteristics(db: Session, player: Player, caracs: Dict) -> Caracteristics:
    """
    Add caracteristics to a player
    """
    caracteristics = Caracteristics()
    caracteristics.nationality = caracs.get("nationality")
    caracteristics.last_name = caracs.get("last_name")
    caracteristics.first_name = caracs.get("first_name")
    caracteristics.play_hand = caracs.get("play_hand")
    caracteristics.back_hand = caracs.get("back_hand")
    caracteristics.height_cm = caracs.get("height_cm")
    caracteristics.weight_kg = caracs.get("weight_kg")
    caracteristics.date_of_birth = caracs.get("birth_date")
    caracteristics.pro_year = caracs.get("pro_year")
    caracteristics.player = player
    player.caracteristics = caracteristics

    db.add(caracteristics)
    db.commit()
    db.refresh(player)

    return caracteristics

def add_player_id(db: Session, player: Player, player_id: str) -> Player:
    """
    Add a player id to a player
    """
    player.tennis_id = player_id
    db.add(player)
    db.commit()
    db.refresh(player)

    return player