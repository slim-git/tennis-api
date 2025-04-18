from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped
from src.entity.odds import Odds
from src.entity.player import Player

from . import Base

class Match(Base):
    """
    Match table
    """
    __tablename__ = "match"
    __table_args__ = (
        UniqueConstraint('date', 'fk_winner_id', 'fk_loser_id', name='uq_date_fk_winner_id_fk_loser_id'),
        {'schema': 'data'},
    )

    # Match table columns
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    comment: Mapped[str] = mapped_column(String, nullable=True)
    winner_rank: Mapped[int] = mapped_column(Integer, nullable=True)
    winner_points: Mapped[int] = mapped_column(Integer, nullable=True)
    loser_rank: Mapped[int] = mapped_column(Integer, nullable=True)
    loser_points: Mapped[int] = mapped_column(Integer, nullable=True)
    tournament_name: Mapped[str] = mapped_column(String, nullable=True)
    tournament_series: Mapped[str] = mapped_column(String, nullable=True)
    tournament_surface: Mapped[str] = mapped_column(String, nullable=True)
    tournament_court: Mapped[str] = mapped_column(String, nullable=True)
    tournament_round: Mapped[str] = mapped_column(String, nullable=True)
    tournament_location: Mapped[str] = mapped_column(String, nullable=True)

    # Dependent table
    odds: Mapped[list["Odds"]] = relationship("Odds", back_populates="match", cascade="all, delete-orphan", passive_deletes=True)

    fk_winner_id: Mapped[int] = mapped_column(ForeignKey("data.player.id", ondelete="CASCADE", name='match_fk_winner_id_fkey'), nullable=False)
    fk_loser_id: Mapped[int] = mapped_column(ForeignKey("data.player.id", ondelete="CASCADE", name='match_fk_loser_id_fkey'), nullable=False)

    winner: Mapped["Player"] = relationship("Player", foreign_keys=[fk_winner_id])
    loser: Mapped["Player"] = relationship("Player", foreign_keys=[fk_loser_id])
