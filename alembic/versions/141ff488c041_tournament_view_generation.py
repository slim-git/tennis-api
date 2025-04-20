"""view generation

Revision ID: 141ff488c041
Revises: 1891eeeaa700
Create Date: 2025-04-20 18:53:07.272272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '141ff488c041'
down_revision: Union[str, None] = '1891eeeaa700'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    sql_view = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS data.tournaments_list_m_view
        TABLESPACE pg_default
        AS
        SELECT tournament_name AS name,
            min(date_part('year'::text, date)) AS first_year,
            max(date_part('year'::text, date)) AS last_year
        FROM data.match
        WHERE tournament_name IS NOT NULL
        GROUP BY tournament_name
        ORDER BY (lower(tournament_name::text))
        WITH DATA;

        ALTER TABLE IF EXISTS data.tournaments_list_m_view
            OWNER TO tennis_admin;
    """

    sql_index = """
        CREATE INDEX IF NOT EXISTS idx_tournaments_list_m_view_name
            ON data.tournaments_list_m_view USING btree
            (name COLLATE pg_catalog."default" ASC NULLS LAST)
            WITH (deduplicate_items=True)
            TABLESPACE pg_default;
    """
    op.execute(sa.text(sql_view))
    op.execute(sa.text(sql_index))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    
    sql_view = """
        DROP MATERIALIZED VIEW IF EXISTS data.tournaments_list_m_view;
    """

    sql_index = """
        DROP INDEX IF EXISTS data.idx_tournaments_list_m_view_name;
    """
    op.execute(sa.text(sql_view))
    op.execute(sa.text(sql_index))
    # ### end Alembic commands ###
