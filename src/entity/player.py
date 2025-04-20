
from datetime import date
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import List, Optional
from pydantic import BaseModel

from . import Base

class Player(Base):
    """
    Player table
    """
    __tablename__ = "player"
    __table_args__ = {'schema': 'data'}

    # Player table columns
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    tennis_id: Mapped[str] = mapped_column(String, nullable=True)

    caracteristics: Mapped["Caracteristics"] = relationship("Caracteristics", back_populates="player", cascade="all, delete-orphan")

    matches_won: Mapped[List["Match"]] = relationship("Match", back_populates="winner", foreign_keys='Match.fk_winner_id')
    matches_lost: Mapped[List["Match"]] = relationship("Match", back_populates="loser", foreign_keys='Match.fk_loser_id')

class Caracteristics(Base):
    """
    Caracteristics table
    """
    __tablename__ = "caracteristics"
    __table_args__ = {'schema': 'data'}

    # Caracteristics table columns
    id: Mapped[int] = mapped_column(primary_key=True)
    nationality: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    play_hand: Mapped[str] = mapped_column(String, nullable=True)
    back_hand: Mapped[int] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[int] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[int] = mapped_column(Integer, nullable=True)
    date_of_birth: Mapped[date] = mapped_column(String, nullable=True)
    pro_year: Mapped[Integer] = mapped_column(Integer, nullable=True)

    fk_player_id: Mapped[int] = mapped_column(ForeignKey("data.player.id", ondelete="CASCADE", name='caracteristics_fk_player_id_fkey'), nullable=False)
    player: Mapped["Player"] = relationship("Player", back_populates="caracteristics")


# -----------------------------------------------------------
# Pydantic Model for Player
# -----------------------------------------------------------
class PlayerApiBase(BaseModel):
    id: int
    name: str
    tennis_id: Optional[str]

class PlayerApiDetail(PlayerApiBase):
    caracteristics: Optional['CaracteristicsApi']

# -----------------------------------------------------------
# Pydantic Model for Caracteristics
# -----------------------------------------------------------
class CaracteristicsApi(BaseModel):
    id: int
    nationality: Optional[str]
    last_name: Optional[str]
    first_name: Optional[str]
    play_hand: Optional[str]
    back_hand: Optional[int]
    height_cm: Optional[int]
    weight_kg: Optional[int]
    date_of_birth: Optional[date]
    pro_year: Optional[int]
