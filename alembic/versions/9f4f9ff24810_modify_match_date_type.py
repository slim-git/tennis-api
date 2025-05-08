"""add reference materialized views

Revision ID: 9f4f9ff24810
Revises: 141ff488c041
Create Date: 2025-04-22 09:53:12.677442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9f4f9ff24810'
down_revision: Union[str, None] = '141ff488c041'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Step 1 - Get the list of materialized views that are in the 'data' schema
    views = conn.execute(sa.text("""
        SELECT schemaname, matviewname
        FROM pg_matviews
    """)).fetchall()
    
    # Step 2 - For each view, get the definition and indexes
    # and store them in a list
    view_data = []

    for schema, view in views:
        # Fetch the view definition
        view_def = conn.execute(
            sa.text(f"SELECT pg_get_viewdef('{schema}.{view}', true)")
        ).scalar()

        # Récupérer les index de la vue
        indexes = conn.execute(
            sa.text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = :viewname AND schemaname = :schema
            """),
            {"viewname": view, "schema": schema}
        ).fetchall()

        view_data.append({
            "schema": schema,
            "view": view,
            "definition": view_def,
            "indexes": indexes
        })

        # Suppress the materialized view
        op.execute(f'DROP MATERIALIZED VIEW IF EXISTS {schema}.{view} CASCADE')
    
    # Step 3 - Modify the column type in the 'match' table
    op.alter_column('match', 'date',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.Date(),
                    existing_nullable=True,
                    schema='data')
    
    # Step 4 - Recreate the materialized views with the new column type
    # and the same definition and indexes
    for view in view_data:
        schema = view['schema']
        name = view['view']
        definition = view['definition']

        op.execute(f"""
            CREATE MATERIALIZED VIEW {schema}.{name} AS
            {definition}
        """)
        # Refresh the materialized view with data
        op.execute(f"REFRESH MATERIALIZED VIEW {schema}.{name}")

        # Recreate the indexes
        for index in view['indexes']:
            op.execute(index.indexdef)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    # Step 1 - Get the list of materialized views that are in the 'data' schema
    views = conn.execute(sa.text("""
        SELECT schemaname, matviewname
        FROM pg_matviews
    """)).fetchall()
    
    # Step 2 - For each view, get the definition and indexes
    # and store them in a list
    view_data = []

    for schema, view in views:
        # Fetch the view definition
        view_def = conn.execute(
            sa.text(f"SELECT pg_get_viewdef('{schema}.{view}', true)")
        ).scalar()

        # Récupérer les index de la vue
        indexes = conn.execute(
            sa.text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = :viewname AND schemaname = :schema
            """),
            {"viewname": view, "schema": schema}
        ).fetchall()

        view_data.append({
            "schema": schema,
            "view": view,
            "definition": view_def,
            "indexes": indexes
        })

        # Suppress the materialized view
        op.execute(f'DROP MATERIALIZED VIEW IF EXISTS {schema}.{view} CASCADE')
    
    # Step 3 - Modify the column type in the 'match' table
    op.alter_column('match', 'date',
               existing_type=sa.Date(),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True,
               schema='data')
    
    # Step 4 - Recreate the materialized views with the new column type
    # and the same definition and indexes
    for view in view_data:
        schema = view['schema']
        name = view['view']
        definition = view['definition']

        op.execute(f"""
            CREATE MATERIALIZED VIEW {schema}.{name} AS
            {definition}
        """)
        # Refresh the materialized view with data
        op.execute(f"REFRESH MATERIALIZED VIEW {schema}.{name}")

        # Recreate the indexes
        for index in view['indexes']:
            op.execute(index.indexdef)
