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
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            rsps.GET,
            "https://www.atptour.com/en/-/www/players/hero/F324",
            json={
                "LastName": "Federer",
                "FirstName": "Roger",
                "MidInitial": None,
                "BirthCity": "Basel, Switzerland",
                "Residence": None,
                "Coach": "Ivan Ljubicic, Severin Luthi",
                "Pronunciation": None,
                "BirthDate": "1981-08-08T00:00:00",
                "Age": None,
                "NatlId": "SUI",
                "Nationality": "Switzerland",
                "HeightIn": 73,
                "HeightFt": "6'1\"",
                "HeightCm": 185,
                "WeightLb": 187,
                "WeightKg": 85,
                "PlayHand": {
                    "Id": "R",
                    "Description": "Right-Handed"
                },
                "BackHand": {
                    "Id": "1",
                    "Description": "One-Handed"
                },
                "ProYear": 1998,
                "Active": {
                    "Id": "I",
                    "Description": "Inactive"
                },
                "DblSpecialist": False,
                "SglRank": None,
                "SglHiRank": 1,
                "SglRankMove": 0,
                "SglRankTie": False,
                "DblRank": None,
                "DblHiRank": 24,
                "DblRankMove": 0,
                "DblRankTie": False,
                "ScRelativeUrlPlayerProfile": "/en/players/roger-federer/f324/overview",
                "ScRelativeUrlPlayerCountryFlag": "/en/~/media/images/flags/sui.svg",
                "GladiatorImageUrl": None,
                "SglCareerWon": 1251,
                "SglCareerLost": 275,
                "SglYtdWon": 0,
                "SglYtdLost": 0,
                "SglCareerTitles": 103,
                "SglYtdTitles": 0,
                "SglYtdPrizeFormatted": "$0",
                "CareerPrizeFormatted": "$130,594,339",
                "DblCareerWon": 131,
                "DblCareerLost": 93,
                "DblYtdWon": 0,
                "DblYtdLost": 0,
                "DblCareerTitles": 8,
                "DblYtdTitles": 0,
                "DblYtdPrizeFormatted": "$0",
                "IsCarbonTrackerEnabled": False,
                "SocialLinks": [
                    {
                    "SocialId": "FB",
                    "SocialLink": "https://www.facebook.com/Federer"
                    },
                    {
                    "SocialId": "IG",
                    "SocialLink": "https://www.instagram.com/rogerfederer/"
                    },
                    {
                    "SocialId": "TW",
                    "SocialLink": "https://twitter.com/rogerfederer"
                    },
                    {
                    "SocialId": "Web",
                    "SocialLink": "http://www.rogerfederer.com"
                    }
                ],
                "CacheTags": None,
                "TopCourtLink": "",
                "SglHiRankDate": "2004-02-02T00:00:00",
                "DblHiRankDate": "2003-06-09T00:00:00"
            },
            status=200
        )

        rsps.add(
            rsps.GET,
            "https://www.atptour.com/en/-/www/site-search/federer/",
            json={
                "Players": [
                    {
                    "PlayerId": "F324",
                    "LastName": "Federer",
                    "FirstName": "Roger",
                    "NatlId": "SUI",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=F324&w=150&h=200",
                    "SubCategoryName": "roger-federer-f324"
                    }
                ],
                "Tournaments": []
            },
            status=200
        )

        rsps.add(
            rsps.GET,
            "https://www.atptour.com/en/-/www/site-search/herbert/",
            json={
                "Players": [
                    {
                    "PlayerId": "BS65",
                    "LastName": "Baddeley",
                    "FirstName": "Herbert",
                    "NatlId": None,
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=BS65&w=150&h=200",
                    "SubCategoryName": "herbert-baddeley-bs65"
                    },
                    {
                    "PlayerId": "BO78",
                    "LastName": "Behrens",
                    "FirstName": "Herbert",
                    "NatlId": "USA",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=BO78&w=150&h=200",
                    "SubCategoryName": "herbert-behrens-bo78"
                    },
                    {
                    "PlayerId": "B705",
                    "LastName": "Bende",
                    "FirstName": "Herbert",
                    "NatlId": "SVK",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=B705&w=150&h=200",
                    "SubCategoryName": "herbert-bende-b705"
                    },
                    {
                    "PlayerId": "BP00",
                    "LastName": "Bowman",
                    "FirstName": "Herbert",
                    "NatlId": "USA",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=BP00&w=150&h=200",
                    "SubCategoryName": "herbert-bowman-bp00"
                    },
                    {
                    "PlayerId": "BM64",
                    "LastName": "Browne",
                    "FirstName": "Herbert",
                    "NatlId": "USA",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=BM64&w=150&h=200",
                    "SubCategoryName": "herbert-browne-bm64"
                    },
                    {
                    "PlayerId": "CL93",
                    "LastName": "Chipp",
                    "FirstName": "Herbert",
                    "NatlId": "GBR",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=CL93&w=150&h=200",
                    "SubCategoryName": "herbert-chipp-cl93"
                    },
                    {
                    "PlayerId": "FA25",
                    "LastName": "Fischer",
                    "FirstName": "Herbert",
                    "NatlId": "USA",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=FA25&w=150&h=200",
                    "SubCategoryName": "herbert-fischer-fa25"
                    },
                    {
                    "PlayerId": "H893",
                    "LastName": "Herbert",
                    "FirstName": "Chris",
                    "NatlId": "GBR",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=H893&w=150&h=200",
                    "SubCategoryName": "chris-herbert-h893"
                    },
                    {
                    "PlayerId": "H966",
                    "LastName": "Herbert",
                    "FirstName": "Justus",
                    "NatlId": "GER",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=H966&w=150&h=200",
                    "SubCategoryName": "justus-herbert-h966"
                    },
                    {
                    "PlayerId": "H996",
                    "LastName": "Herbert",
                    "FirstName": "Pierre-Hugues",
                    "NatlId": "FRA",
                    "Active": "A",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=H996&w=150&h=200",
                    "SubCategoryName": "pierre-hugues-herbert-h996"
                    },
                    {
                    "PlayerId": "H430",
                    "LastName": "Herbert",
                    "FirstName": "William",
                    "NatlId": "GBR",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=H430&w=150&h=200",
                    "SubCategoryName": "william-herbert-h430"
                    },
                    {
                    "PlayerId": "J385",
                    "LastName": "Jerich",
                    "FirstName": "Herbert",
                    "NatlId": "AUT",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=J385&w=150&h=200",
                    "SubCategoryName": "herbert-jerich-j385"
                    },
                    {
                    "PlayerId": "KG69",
                    "LastName": "Kinzl",
                    "FirstName": "Herbert",
                    "NatlId": "AUT",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=KG69&w=150&h=200",
                    "SubCategoryName": "herbert-kinzl-kg69"
                    },
                    {
                    "PlayerId": "LG94",
                    "LastName": "Lawford",
                    "FirstName": "Herbert",
                    "NatlId": "GBR",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=LG94&w=150&h=200",
                    "SubCategoryName": "herbert-lawford-lg94"
                    },
                    {
                    "PlayerId": "L0E1",
                    "LastName": "Loerke",
                    "FirstName": "Herbert",
                    "NatlId": "GER",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=L0E1&w=150&h=200",
                    "SubCategoryName": None
                    },
                    {
                    "PlayerId": "M0M2",
                    "LastName": "Mann",
                    "FirstName": "Herbert",
                    "NatlId": "AUT",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=M0M2&w=150&h=200",
                    "SubCategoryName": None
                    },
                    {
                    "PlayerId": "R509",
                    "LastName": "Rapp",
                    "FirstName": "Herbert",
                    "NatlId": "USA",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=R509&w=150&h=200",
                    "SubCategoryName": "herbert-rapp-r509"
                    },
                    {
                    "PlayerId": "RF72",
                    "LastName": "Roper-Barrett",
                    "FirstName": "Herbert",
                    "NatlId": "GBR",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=RF72&w=150&h=200",
                    "SubCategoryName": "herbert-roper-barrett-rf72"
                    },
                    {
                    "PlayerId": "S264",
                    "LastName": "Sandberg",
                    "FirstName": "Herbert",
                    "NatlId": "GER",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=S264&w=150&h=200",
                    "SubCategoryName": "herbert-sandberg-s264"
                    },
                    {
                    "PlayerId": "TF94",
                    "LastName": "Taylor",
                    "FirstName": "Herbert",
                    "NatlId": None,
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=TF94&w=150&h=200",
                    "SubCategoryName": "herbert-taylor-tf94"
                    },
                    {
                    "PlayerId": "TF28",
                    "LastName": "Turner",
                    "FirstName": "Herbert",
                    "NatlId": "AUS",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=TF28&w=150&h=200",
                    "SubCategoryName": "herbert-turner-tf28"
                    },
                    {
                    "PlayerId": "W487",
                    "LastName": "Weirather",
                    "FirstName": "Herbert",
                    "NatlId": "AUT",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=W487&w=150&h=200",
                    "SubCategoryName": "herbert-weirather-w487"
                    },
                    {
                    "PlayerId": "W858",
                    "LastName": "Whitney",
                    "FirstName": "Herbert",
                    "NatlId": "GBR",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=W858&w=150&h=200",
                    "SubCategoryName": "herbert-whitney-w858"
                    },
                    {
                    "PlayerId": "WA15",
                    "LastName": "Wilberforce",
                    "FirstName": "Herbert W.W.",
                    "NatlId": None,
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=WA15&w=150&h=200",
                    "SubCategoryName": "herbert-ww-wilberforce-wa15"
                    },
                    {
                    "PlayerId": "W964",
                    "LastName": "Wilson-Fox",
                    "FirstName": "Herbert",
                    "NatlId": "GBR",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=W964&w=150&h=200",
                    "SubCategoryName": "herbert-wilson-fox-w964"
                    },
                    {
                    "PlayerId": "W200",
                    "LastName": "Wiltschnig",
                    "FirstName": "Herbert",
                    "NatlId": "AUT",
                    "Active": "I",
                    "PlayerHeadshotUrl": "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=W200&w=150&h=200",
                    "SubCategoryName": "herbert-wiltschnig-w200"
                    }
                ],
                "Tournaments": []
                },
            status=200
        )
        
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
