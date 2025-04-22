"""add reference materialized views

Revision ID: 875478faea59
Revises: 9f4f9ff24810
Create Date: 2025-04-22 10:34:27.169987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '875478faea59'
down_revision: Union[str, None] = '9f4f9ff24810'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    sql_views = [
        # ref_surface_m_view
        """
            CREATE MATERIALIZED VIEW IF NOT EXISTS data.ref_surface_m_view
            TABLESPACE pg_default
            AS
            SELECT DISTINCT tournament_surface AS name
            FROM data.match m
            ORDER BY tournament_surface
            WITH DATA;

            ALTER TABLE IF EXISTS data.ref_surface_m_view
                OWNER TO tennis_admin;
        """,
        # ref_court_m_view
        """
            CREATE MATERIALIZED VIEW IF NOT EXISTS data.ref_court_m_view
            TABLESPACE pg_default
            AS
            SELECT DISTINCT tournament_court AS name
            FROM data.match m
            ORDER BY tournament_court
            WITH DATA;

            ALTER TABLE IF EXISTS data.ref_court_m_view
                OWNER TO tennis_admin;
        """,
        # ref_series_m_view
        """
            CREATE MATERIALIZED VIEW IF NOT EXISTS data.ref_series_m_view
            TABLESPACE pg_default
            AS
            SELECT DISTINCT tournament_series AS name
            FROM data.match m
            ORDER BY tournament_series
            WITH DATA;

            ALTER TABLE IF EXISTS data.ref_series_m_view
                OWNER TO tennis_admin;
        """
    ]

    for sql_view in sql_views:
        op.execute(sa.text(sql_view))


def downgrade() -> None:
    """Downgrade schema."""
    sql_views = [
        "DROP MATERIALIZED VIEW IF EXISTS data.ref_surface_m_view;",
        "DROP MATERIALIZED VIEW IF EXISTS data.ref_court_m_view;",
        "DROP MATERIALIZED VIEW IF EXISTS data.ref_series_m_view;"
    ]

    for sql_view in sql_views:
        op.execute(sa.text(sql_view))
