
from datetime import date
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import List

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
    height: Mapped[float] = mapped_column(Float, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=True)
    handedness: Mapped[str] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[date] = mapped_column(String, nullable=True)
    date_turned_pro: Mapped[date] = mapped_column(String, nullable=True)

    fk_player_id: Mapped[int] = mapped_column(ForeignKey("data.player.id", ondelete="CASCADE", name='caracteristics_fk_player_id_fkey'), nullable=False)
    player: Mapped["Player"] = relationship("Player", back_populates="caracteristics")