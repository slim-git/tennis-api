import pytest
import pandas as pd

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
