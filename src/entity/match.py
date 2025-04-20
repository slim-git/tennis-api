from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped
from src.entity.odds import Odds, OddsApi
from src.entity.player import Player, PlayerApiDetail
from typing import Literal, Optional, ClassVar, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

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

# -----------------------------------------------------------
# Pydantic Model for Match
# -----------------------------------------------------------

class MatchApiBase(BaseModel):
    id: int
    date: Optional[datetime]
    comment: Optional[str]
    winner_rank: Optional[int]
    winner_points: Optional[int]
    loser_rank: Optional[int]
    loser_points: Optional[int]
    tournament_name: Optional[str]
    tournament_series: Optional[str]
    tournament_surface: Optional[str]
    tournament_court: Optional[str]
    tournament_round: Optional[str]
    tournament_location: Optional[str]
    fk_winner_id: int
    fk_loser_id: int

    model_config: ClassVar[ConfigDict] = ConfigDict(orm_mode=True)

class MatchApiDetail(MatchApiBase):
    winner: Optional[PlayerApiDetail]
    loser: Optional[PlayerApiDetail]
    odds: Optional[List[OddsApi]]

# -------------------------------------------------------
class RawMatch(BaseModel):
    Comment: Literal['Completed', 'Retired', 'Walkover'] = 'Completed'
    Loser: str = Field(description="The name of the loser.", json_schema_extra={"example": "'Djokovic N.'"})
    Winner: str = Field(description="The name of the winner.", json_schema_extra={"example": "'Federer R.'"})
    Round: Literal['1st Round', '2nd Round', '3rd Round', '4th Round', 'Quarterfinals', 'Semifinals', 'The Final', 'Round Robin'] = '1st Round'
    Court: Literal['Outdoor', 'Indoor'] = 'Outdoor'
    Surface: Literal['Grass', 'Carpet', 'Clay', 'Hard'] = 'Grass'
    Wsets: int = Field(description="The number of sets won by the winner.", json_schema_extra={"example": "3"})
    Lsets: int = Field(description="The number of sets won by the loser.", json_schema_extra={"example": "0"})
    Date: str = Field(description="The date of the match.", json_schema_extra={"example": "'2019-06-15'"})
    WRank: int = Field(description="The rank of the winner.", json_schema_extra={"example": "1"})
    WPts: int = Field(description="The number of points of the winner.", json_schema_extra={"example": "4000"})
    LPts: int = Field(description="The number of points of the loser.", json_schema_extra={"example": "3000"})
    LRank: int = Field(description="The rank of the loser.", json_schema_extra={"example": "2"})
    Location: str = Field(description="The location of the tournament.", json_schema_extra={"example": "'London'"})
    Series: Literal['ATP250', 'ATP500', 'Grand Slam', 'Masters 1000', 'Masters', 'Masters Cup', 'International Gold', 'International'] = 'Grand Slam'
    W1: Optional[int] = Field(description="The score of the winner in the first set.", json_schema_extra={"example": "6"})
    W2: Optional[int] = Field(description="The score of the winner in the second set.", json_schema_extra={"example": "6"})
    W3: Optional[int] = Field(description="The score of the winner in the third set.", json_schema_extra={"example": "6"})
    W4: Optional[int] = Field(description="The score of the winner in the fourth set.", json_schema_extra={"example": "None"})
    W5: Optional[int] = Field(description="The score of the winner in the fifth set.", json_schema_extra={"example": "None"})
    L1: Optional[int] = Field(description="The score of the loser in the first set.", json_schema_extra={"example": "3"})
    L2: Optional[int] = Field(description="The score of the loser in the second set.", json_schema_extra={"example": "2"})
    L3: Optional[int] = Field(description="The score of the loser in the third set.", json_schema_extra={"example": "0"})
    L4: Optional[int] = Field(description="The score of the loser in the fourth set.", json_schema_extra={"example": "None"})
    L5: Optional[int] = Field(description="The score of the loser in the fifth set.", json_schema_extra={"example": "None"})
    Tournament: str = Field(description="The name of the tournament.", json_schema_extra={"example": "Wimbledon"})
    
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
    