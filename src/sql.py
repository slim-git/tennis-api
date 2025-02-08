import pandas as pd
import psycopg2
from typing import Literal
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")
PG_SSLMODE = os.getenv("PG_SSLMODE")

def _get_connection() -> psycopg2.extensions.connection:
    """
    Get a connection to the Postgres database
    """
    conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT,
        sslmode=PG_SSLMODE,
    )
    return conn

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
    
    query = f"SELECT * FROM {table_name} WHERE date BETWEEN %s AND %s"
    vars = [from_date, to_date]
    
    with _get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, vars)
            data = cursor.fetchall()

    data = pd.DataFrame(data, columns=[desc[0] for desc in cursor.description])

    return data

def list_tournaments(circuit: Literal["atp", "wta"]):
    """
    List the tournaments of the circuit
    """
    query = f"""
        SELECT DISTINCT
            tournament as name,
            series,
            court,
            surface
        FROM {circuit}_data;
    """
    with _get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            tournaments = [{'name': row[0], 'series': row[1], 'court': row[2], 'surface': row[3]} for row in cursor.fetchall()]

    return tournaments