import pytest
import pandas as pd
import pkgutil
import importlib
import responses
import fakeredis
from typing import Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.entity import Base

# Load all classes from src.entity
module = importlib.import_module('src.entity')

# Loop over all modules in the 'src.entity' package
package = importlib.import_module('src.entity')

for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
    module = importlib.import_module(module_name)

# ----------------------------------------------------------------
# Fixtures for Database
# ----------------------------------------------------------------
@pytest.fixture
def db_session(postgresql):
    """
    Create a new database session for each test
    and tear it down after the test.
    """
    # Create a new database connection
    host = postgresql.info.host
    port = postgresql.info.port
    user = postgresql.info.user
    dbname = postgresql.info.dbname

    dsn = f"postgresql+psycopg://{user}@{host}:{port}/{dbname}"
    engine = create_engine(dsn, echo=True)

    # Create schema and tables once
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS data"))
    
    Base.metadata.create_all(engine)

    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# Use of fixture to inject a fake Redis client into the tests
@pytest.fixture
def fake_redis():
    # Create a fake Redis instance
    fake_redis_instance = fakeredis.FakeStrictRedis()
    yield fake_redis_instance

# -----------------------------------------------------------------
# Fixtures for requests calls
# -----------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_responses():
    with responses.RequestsMock() as rsps:
        yield rsps

# ----------------------------------------------------------------
# Fixtures for Match Data
# ----------------------------------------------------------------
@pytest.fixture
def simple_match():
    return pd.DataFrame({
        'series': ['ATP250',],
        'surface': ['Clay',],
        'court': ['Indoor',],
        'round': ['Round Robin',],
        'w_rank': [5],
        'l_rank': [300],
        'w_points': [2000],
        'l_points': [40],
    })

@pytest.fixture
def simple_match_pairwise_data(simple_match: pd.DataFrame):
    return pd.DataFrame({
        'Series': ['ATP250', 'ATP250'],
        'Surface': ['Clay', 'Clay'],
        'Court': ['Indoor', 'Indoor'],
        'Round': ['Round Robin', 'Round Robin'],
        'diffRanking': [-295, 295],
        'diffPoints': [1960, -1960],
        'target': [1, 0]
    })

@pytest.fixture
def simple_match_empty():
    return pd.DataFrame({
        'Series': [],
        'Surface': [],
        'Court': [],
        'Round': [],
        'diffRanking': [],
        'diffPoints': [],
        'target': []
    })

@pytest.fixture
def raw_match():
    return {
        "Comment": "Completed",
        "Best of": 3,
        "Loser": "Djokovic N.",
        "Round": "The Final",
        "Winner": "Federer R.",
        "Court": "Outdoor",
        "Surface": "Grass",
        "Wsets": 3,
        "Lsets": 0,
        "Date": "2019-06-15",
        "WRank": 1,
        "WPts": 4000,
        "LPts": 3000,
        "Tournament": "Wimbledon",
        "LRank": 2,
        "Location": "London",
        "Series": "Grand Slam",
        "W1": 6,
        "W2": 6,
        "W3": 6,
        "W4": None,
        "W5": None,
        "L1": 3,
        "L2": 2,
        "L3": 0,
        "L4": None,
        "L5": None,
        "AvgW": 1.3,
        "AvgL": 2.3,
        "MaxW": 1.5,
        "MaxL": 1.8,
        "B365W": 1.2,
        "B365L": 4.5,
    }

@pytest.fixture
def raw_matches_batch(raw_match: Dict):
    return [
        raw_match,
        {
            "Comment": "Completed",
            "Best of": 3,
            "Loser": "Nadal R.",
            "Round": "The Final",
            "Winner": "Djokovic N.",
            "Court": "Outdoor",
            "Surface": "Hard",
            "Wsets": 3,
            "Lsets": 0,
            "Date": "2022-01-21",
            "WRank": 1,
            "WPts": 4000,
            "LPts": 3000,
            "Tournament": "Australian Open",
            "LRank": 2,
            "Location": "Melbourne",
            "Series": "Grand Slam",
            "W1": 6,
            "W2": 6,
            "W3": 6,
            "W4": None,
            "W5": None,
            "L1": 3,
            "L2": 2,
            "L3": 0,
            "L4": None,
            "L5": None,
            "AvgW": 1.3,
            "AvgL": 2.3,
            "MaxW": 1.5,
            "MaxL": 1.8,
            "B365W": 1.2,
            "B365L": 4.5,
        }
    ]

# ----------------------------------------------------------------
# Fixtures for Player Data
# ----------------------------------------------------------------
@pytest.fixture
def super_joueur(db_session):
    """
    Create a super player with caracteristics and add it to the database
    """
    from src.entity.player import Player, Caracteristics

    player = Player(
        name="Joueur S.",
        tennis_id='J001',
        caracteristics=Caracteristics(
            first_name="Super",
            last_name="Joueur",
            date_of_birth="1981-08-08",
            nationality="France",
            height_cm=185,
            weight_kg=85,
            play_hand="R",
            back_hand=1,
            pro_year=1998,
        )
    )

    db_session.add(player)
    db_session.commit()

    return player

@pytest.fixture
def tout_nouveau_joueur(db_session):
    """
    Create a new player without caracteristics nor tennis_id and add it to the database
    """
    from src.entity.player import Player

    player = Player(name="Joueur T.N.")

    db_session.add(player)
    db_session.commit()

    return player

@pytest.fixture
def nouveau_joueur(db_session):
    """
    Create a new player without caracteristics and add it to the database
    """
    from src.entity.player import Player

    player = Player(
        name="Joueur N.",
        tennis_id='J002',
    )

    db_session.add(player)
    db_session.commit()

    return player

@pytest.fixture
def roland_garros_final():
    """
    Create a Roland Garros final match with odds and new players
    """
    from src.entity.match import Match
    from src.entity.odds import Odds
    from src.entity.player import Player

    match = Match(
        date="2023-06-11",
        comment="Completed",
        winner=Player(name="Djokovic N."),
        loser=Player(name="Ruud C."),
        tournament_name="Roland Garros",
        tournament_series="Grand Slam",
        tournament_surface="Clay",
        tournament_court="Outdoor",
        tournament_round="The Final",
        tournament_location="Paris",
        winner_rank=3,
        winner_points=5955,
        loser_rank=4,
        loser_points=4960,
    )

    match.odds = [
        Odds(
            bookmaker="B365",
            winner=1.2,
            loser=4.8,
            match=match
        ),
        Odds(
            bookmaker="PS",
            winner=1.22,
            loser=4.92,
            match=match
        ),
        Odds(
            bookmaker="Max",
            winner=1.24,
            loser=5.15,
            match=match
        ),
        Odds(
            bookmaker="Avg",
            winner=1.21,
            loser=4.7,
            match=match
        ),
    ]

    return match
