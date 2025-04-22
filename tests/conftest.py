import pytest
import pandas as pd
import pkgutil
import importlib
import responses
import fakeredis
from typing import Dict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from responses.matchers import json_params_matcher
from fastapi.testclient import TestClient
from src.main import app
from src.repository.common import get_session

from src.entity import Base

# ----------------------------------------------------------------
# Load all classes from src.entity
module = importlib.import_module('src.entity')

# Loop over all modules in the 'src.entity' package
package = importlib.import_module('src.entity')

for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
    module = importlib.import_module(module_name)

@pytest.fixture
def client(db_session):
    """
    Create a test client for the FastAPI app.
    """
    # Override the get_session dependency to use the test database session
    def override_get_session():
        yield db_session
    
    # Override the dependency in the FastAPI app
    app.dependency_overrides[get_session] = override_get_session

    return TestClient(app)

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
    connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    try:
        yield session
    except Exception:
        session.rollback()  # In case of an error, rollback the session
        raise
    finally:
        session.close()
        connection.close()

@pytest.fixture()
def with_materialized_views(db_session):
    """
    Create materialized views for testing.
    """
    # Create the ref_surface_m_view materialized view
    db_session.execute(text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS data.ref_surface_m_view AS
        SELECT *
        FROM (
            VALUES  ('Carpet'),
                    ('Clay'),
                    ('Grass'),
                    ('Hard')
            ) AS t(name);
    """))

    # Create the ref_court_m_view materialized view
    db_session.execute(text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS data.ref_court_m_view AS
        SELECT *
        FROM (
            VALUES  ('Indoor'),
                    ('Outdoor')
            ) AS t(name);
    """))
    
    # Create the ref_series_m_view materialized view
    db_session.execute(text("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS data.ref_series_m_view AS
        SELECT *
        FROM (
            VALUES  ('ATP250'),
                    ('ATP500'),
                    ('Grand Slam'),
                    ('International'),
                    ('International Gold'),
                    ('Masters'),
                    ('Masters 1000'),
                    ('Masters Cup')
            ) AS t(name);
    """))
    
    yield

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
            "https://www.atptour.com/en/-/www/players/hero/F324/",
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
        
        rsps.add(
            rsps.POST,
            "http://localhost:8191/v1",
            match=[json_params_matcher({
                "cmd": "request.get",
                "url": "https://www.atptour.com/en/-/www/site-search/gasquet/",
                "maxTimeout": 60000,
            })],
            json={
                "status": "ok",
                "message": "Challenge not detected!",
                "solution": {
                    "url": "https://www.atptour.com/en/-/www/site-search/gasquet/",
                    "status": 200,
                    "cookies": [
                        {
                            "version": 0,
                            "name": "__cf_bm",
                            "value": "WDSm4XHIA8j37G9XV8CUfLKlUVTBysgyT23FkRppgtM-1745136598-1.0.1.1-m4nLAUUG.jeVm2QXn_9moCv_FQJ0x7tdVvrInb5kdJkN_v.larvZupdSl7yBs8WK3q32axMEUdZF5iIMAzjYp3ymMmJOy1TTa6BPvPuxSJQ",
                            "port": None,
                            "port_specified": False,
                            "domain": ".atptour.com",
                            "domain_specified": True,
                            "domain_initial_dot": True,
                            "path": "/",
                            "path_specified": True,
                            "secure": True,
                            "expires": 1745138398,
                            "discard": True,
                            "comment": None,
                            "comment_url": None,
                            "rfc2109": False,
                            "_rest": {
                                "HttpOnly": None
                            }
                        },
                        {
                            "version": 0,
                            "name": "__Secure-ENID",
                            "value": "27.SE=GdzvtamVZTVdmqlnUQ4oTV7-4n9LEA4-QFnIHHTH3wQDVKkV20g6PCFev_Sr17kvtHzSyb7Zl8c41QMOsYZecJRykBL-Yq7GM9JCc0YkS8LyXG-qrlyTXP2-_ifZn-KeYjIIrfv_QmptCwCQlkSGdstAQD3eKOwVbeVeUpytdY-i_Kai8uSkNp4LmmE0PXAIq4_DYqCf-b5HqFUOtELS89CBnSn6kaju82Ilk-PARJzxLOam",
                            "port": None,
                            "port_specified": False,
                            "domain": ".google.com",
                            "domain_specified": True,
                            "domain_initial_dot": True,
                            "path": "/",
                            "path_specified": True,
                            "secure": True,
                            "expires": 1779323296,
                            "discard": True,
                            "comment": None,
                            "comment_url": None,
                            "rfc2109": False,
                            "_rest": {
                                "HttpOnly": None
                            }
                        }
                    ],
                    "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    "headers": {},
                    "response": "<html><head><meta name=\"color-scheme\" content=\"light dark\"><meta charset=\"utf-8\"></head><body><pre>{\"Players\":[{\"PlayerId\":\"G628\",\"LastName\":\"Gasquet\",\"FirstName\":\"Richard\",\"NatlId\":\"FRA\",\"Active\":\"A\",\"PlayerHeadshotUrl\":\"https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=G628&amp;w=150&amp;h=200\",\"SubCategoryName\":\"richard-gasquet-g628\"}],\"Tournaments\":[]}</pre><div class=\"json-formatter-container\"></div></body></html>"
                },
                "startTimestamp": 1745136597163,
                "endTimestamp": 1745136600038,
                "version": "3.4.0"
            },
        )

        rsps.add(
            rsps.POST,
            "http://localhost:8191/v1",
            match=[json_params_matcher({
                "cmd": "request.get",
                "url": "https://www.atptour.com/en/-/www/players/hero/G628/",
                "maxTimeout": 60000,
            })],
            json={
                "status": "ok",
                "message": "Challenge not detected!",
                "solution": {
                    "url": "https://www.atptour.com/en/-/www/players/hero/G628/",
                    "status": 200,
                    "cookies": [
                        {
                            "version": 0,
                            "name": "__cf_bm",
                            "value": "GY6qsK8u3tOIPnVIMAm9GRdevol.fIfKCIiSh2lm0N0-1745144497-1.0.1.1-ll6tTf2iuAjap4V5dMY5a86bSCnkc.X3wLm51ynROa9uMDBWJiMbuPVFoYpAEjB6_x1JT.H3O3R4KA0kjyEwgWjH9lx.uAeArf6vOpl_ebc",
                            "port": None,
                            "port_specified": True,
                            "domain": ".atptour.com",
                            "domain_specified": True,
                            "domain_initial_dot": True,
                            "path": "/",
                            "path_specified": True,
                            "secure": True,
                            "expires": 1745146297,
                            "discard": True,
                            "comment": None,
                            "comment_url": None,
                            "rfc2109": True,
                            "_rest": {
                                "HttpOnly": None
                            }
                        }
                    ],
                    "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    "headers": {},
                    "response": "<html><head><meta name=\"color-scheme\" content=\"light dark\"><meta charset=\"utf-8\"></head><body><pre>{\"LastName\":\"Gasquet\",\"FirstName\":\"Richard\",\"MidInitial\":null,\"BirthCity\":\"Beziers, France\",\"Residence\":null,\"Coach\":\"Julien Cassaigne\",\"Pronunciation\":\"gas-KAY\",\"BirthDate\":\"1986-06-18T00:00:00\",\"Age\":38,\"NatlId\":\"FRA\",\"Nationality\":\"France\",\"HeightIn\":72,\"HeightFt\":\"6'0\\\"\",\"HeightCm\":183,\"WeightLb\":174,\"WeightKg\":79,\"PlayHand\":{\"Id\":\"R\",\"Description\":\"Right-Handed\"},\"BackHand\":{\"Id\":\"1\",\"Description\":\"One-Handed\"},\"ProYear\":2002,\"Active\":{\"Id\":\"A\",\"Description\":\"Active\"},\"DblSpecialist\":false,\"SglRank\":142,\"SglHiRank\":7,\"SglRankMove\":22,\"SglRankTie\":false,\"DblRank\":null,\"DblHiRank\":45,\"DblRankMove\":0,\"DblRankTie\":false,\"ScRelativeUrlPlayerProfile\":\"/en/players/richard-gasquet/g628/overview\",\"ScRelativeUrlPlayerCountryFlag\":\"/en/~/media/images/flags/fra.svg\",\"GladiatorImageUrl\":null,\"SglCareerWon\":609,\"SglCareerLost\":407,\"SglYtdWon\":3,\"SglYtdLost\":4,\"SglCareerTitles\":16,\"SglYtdTitles\":0,\"SglYtdPrizeFormatted\":\"$107,399\",\"CareerPrizeFormatted\":\"$21,338,168\",\"DblCareerWon\":72,\"DblCareerLost\":63,\"DblYtdWon\":0,\"DblYtdLost\":1,\"DblCareerTitles\":2,\"DblYtdTitles\":0,\"DblYtdPrizeFormatted\":\"$1,699\",\"IsCarbonTrackerEnabled\":false,\"SocialLinks\":[{\"SocialId\":\"IG\",\"SocialLink\":\"https://www.instagram.com/richardgasquet34/\"},{\"SocialId\":\"TW\",\"SocialLink\":\"https://twitter.com/richardgasquet1\"}],\"CacheTags\":null,\"TopCourtLink\":\"\",\"SglHiRankDate\":\"2007-07-09T00:00:00\",\"DblHiRankDate\":\"2008-04-07T00:00:00\"}</pre><div class=\"json-formatter-container\"></div></body></html>"
                },
                "startTimestamp": 1745144495599,
                "endTimestamp": 1745144498574,
                "version": "3.4.0"
            }
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
def wimbledon_final(db_session):
    """
    Create a Wimbledon final match with odds and new players
    """
    from src.entity.match import Match
    from src.entity.odds import Odds
    from src.entity.player import Player
    
    match = Match(
        date="2019-06-15",
        comment="Completed",
        winner=Player(name="Federer R."),
        loser=Player(name="Djokovic N."),
        tournament_name="Wimbledon",
        tournament_series="Grand Slam",
        tournament_surface="Grass",
        tournament_court="Outdoor",
        tournament_round="The Final",
        tournament_location="London",
        winner_rank=1,
        winner_points=4000,
        loser_rank=2,
        loser_points=3000,
    )
    match.odds = [
        Odds(
            bookmaker="B365",
            winner=1.2,
            loser=4.5,
            match=match
        ),
        Odds(
            bookmaker="PS",
            winner=1.22,
            loser=4.52,
            match=match
        ),
        Odds(
            bookmaker="Max",
            winner=1.24,
            loser=4.55,
            match=match
        ),
        Odds(
            bookmaker="Avg",
            winner=1.21,
            loser=4.7,
            match=match
        ),
    ]

    # Add the match to the database
    db_session.add(match)
    db_session.commit()

    return match

@pytest.fixture
def wimbledon_final_raw(wimbledon_final):
    """
    Create a Wimbledon final match with odds and new players
    """
    raw_match = {
        "Comment": wimbledon_final.comment,
        "Loser": wimbledon_final.loser.name,
        "Round": wimbledon_final.tournament_round,
        "Winner": wimbledon_final.winner.name,
        "Court": wimbledon_final.tournament_court,
        "Surface": wimbledon_final.tournament_surface,
        "Date": wimbledon_final.date.strftime("%Y-%m-%d"),
        "Tournament": wimbledon_final.tournament_name,
        "Location": wimbledon_final.tournament_location,
        "Series": wimbledon_final.tournament_series,
        "WRank": wimbledon_final.winner_rank,
        "WPts": wimbledon_final.winner_points,
        "LPts": wimbledon_final.loser_points,
        "LRank": wimbledon_final.loser_rank,
        "Best of": 3,
        "Wsets": 3,
        "Lsets": 0,
        'W1': 6,
        'W2': 6,
        'W3': 6,
        'W4': None,
        'W5': None,
        'L1': 3,
        'L2': 2,
        'L3': 0,
        'L4': None,
        'L5': None,
    }

    for i, odds in enumerate(wimbledon_final.odds):
        raw_match[f'{odds.bookmaker}W'] = odds.winner
        raw_match[f'{odds.bookmaker}L'] = odds.loser

    return raw_match

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
