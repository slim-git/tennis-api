import pytest
from src.entity.match import Match
from src.repository.match_repo import insert_match

def test_insert_new_match(db_session, roland_garros_final):
    """
    Test inserting a new match into the database
    """
    match = insert_match(db=db_session, match=roland_garros_final)

    assert match.id is not None
    assert match.winner.name == roland_garros_final.winner.name
    assert match.loser.name == roland_garros_final.loser.name
    assert len(match.odds) > 0
    for odds in match.odds:
        assert odds.id is not None

def test_insert_existing_match(db_session, wimbledon_final):
    """
    Test inserting an already existing match into the database
    """
    duplicate = Match(
        date=wimbledon_final.date,
        winner=wimbledon_final.winner,
        loser=wimbledon_final.loser,
    )
    # Attempt to insert the same match again
    with pytest.raises(Exception):
        insert_match(db=db_session, match=duplicate)  # Assuming this raises an IntegrityError
