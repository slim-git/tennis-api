import pandas as pd
from src.model import create_pairwise_data

def test_create_pairwise_data(simple_match: pd.DataFrame, simple_match_pairwise_data: pd.DataFrame):
    result = create_pairwise_data(simple_match)

    assert set(result.columns) == set(simple_match_pairwise_data.columns), "Columns are different"
    assert simple_match_pairwise_data.equals(result), "Dataframes are different"
