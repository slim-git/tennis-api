import pytest
import pandas as pd
from typing import Dict

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
        "Round": "Final",
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
            "Round": "Final",
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