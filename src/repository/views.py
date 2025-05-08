from sqlalchemy import text
from sqlalchemy.orm import Session

def refresh_materialized_view(db: Session, view_name: str, schema_name: str) -> None:
    """
    Refresh concurrently the materialized view in Postgres
    """
    query = f"REFRESH MATERIALIZED VIEW {schema_name}.{view_name} WITH DATA;"

    db.execute(text(query))
    db.commit()

def refresh_all_materialized_views(db: Session) -> None:
    """
    Refresh all materialized views in Postgres
    """
    query = """
        SELECT schemaname, matviewname
        FROM pg_matviews;
    """

    result = db.execute(text(query)).fetchall()

    for row in result:
        refresh_materialized_view(db, view_name=row[1], schema_name=row[0])
        print(f"Refreshed materialized view: {row[0]}.{row[1]}")
