import pandas as pd
from typing import Literal
from datetime import datetime
from src.repository.common import get_session
from sqlalchemy import text

def load_matches_from_postgres(
        table_name: Literal['atp_data', 'wta_data'],
        from_date: str = None,
        to_date: str = None) -> pd.DataFrame:
    """
    Load data from Postgres
    """
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    
    if not from_date:
        from_date = "1900-01-01"
    
    query = f"SELECT * FROM {table_name} WHERE date BETWEEN :from_date AND :to_date"
    query_params = {'from_date': from_date, 'to_date': to_date}

    with next(get_session()) as session:
        data = session.execute(
            text(query),
            query_params
        ).fetchall()

        description = session.execute(text(query), query_params).cursor.description

    data = pd.DataFrame(data, columns=[desc[0] for desc in description])

    return data

def list_tournaments(circuit: Literal["atp", "wta"]):
    """
    List the tournaments of the circuit
    """
    with next(get_session()) as session:
        query = f"""
            SELECT DISTINCT
                tournament as name,
                series,
                court,
                surface
            FROM {circuit}_data;
        """
        tournaments = session.execute(text(query)).fetchall()

    tournaments = [{'name': row[0], 'series': row[1], 'court': row[2], 'surface': row[3]} for row in tournaments]

    return tournaments