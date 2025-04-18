from sqlalchemy import String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped

from . import Base

class Odds(Base):
    """
    Odds table
    """
    __tablename__ = "odds"
    __table_args__ = (
        UniqueConstraint('fk_match_id', 'bookmaker', name='uq_odds_match_bookmaker'),
        {'schema': 'data', 'extend_existing': True}
    )

    # Odds table columns
    id: Mapped[int] = mapped_column(primary_key=True)
    bookmaker: Mapped[str] = mapped_column(String, nullable=True)
    winner: Mapped[float] = mapped_column(Float, nullable=True)
    loser: Mapped[float] = mapped_column(Float, nullable=True)

    fk_match_id: Mapped[int] = mapped_column(ForeignKey("data.match.id", ondelete="CASCADE", name='odds_fk_match_id_fkey'), nullable=False)
    match: Mapped["Match"] = relationship("Match", back_populates="odds")  # type: ignore # noqa: F821
