from src.entity.match import Match
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY

def test_insert_match_success(client, db_session, raw_match):
    # Count the number of matches in the database before insertion
    match_count_before = db_session.query(Match).count()

    # Insert a valid match
    response = client.post("/match/insert", json=raw_match)
    
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json.get("status") == "ok", "Status should be 'ok'"
    
    match_id = response_json.get("match_id")
    assert match_id is not None, "Match ID should not be None"

    # Count the number of matches in the database after insertion
    match_count_after = db_session.query(Match).count()
    assert match_count_after == match_count_before + 1

    # Check the match details
    match_in_db = db_session.query(Match).filter(Match.id == match_id).first()
    assert match_in_db is not None
    assert match_in_db.winner is not None
    assert match_in_db.loser is not None
    assert match_in_db.winner.name == raw_match.get("Winner")
    assert match_in_db.loser.name == raw_match.get("Loser")

    # Check the response
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "status": "ok",
        "match_id": match_in_db.id,
    }
    
# Test for inserting an already existing match
def test_insert_match_integrity_error(client, db_session, wimbledon_final_raw):
    """
    Test inserting an already existing match into the database
    """
    # Attempt to insert the same match again
    response = client.post("/match/insert", json=wimbledon_final_raw)

    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY, f"Status code should be {HTTP_422_UNPROCESSABLE_ENTITY} for duplicate match"

def test_list_surfaces(client, with_materialized_views):
    """
    Test the list of surfaces
    """
    response = client.get("/references/surfaces")
    
    assert response.status_code == HTTP_200_OK
    assert set(response.json()) == set([
        "Carpet",
        "Clay",
        "Grass",
        "Hard",
    ])

def test_list_courts(client, with_materialized_views):
    """
    Test the list of courts
    """
    response = client.get("/references/courts")
    
    assert response.status_code == HTTP_200_OK
    assert set(response.json()) == set([
        "Indoor",
        "Outdoor",
    ])

def test_list_series(client, with_materialized_views):
    """
    Test the list of surfaces
    """
    response = client.get("/references/series")

    assert response.status_code == HTTP_200_OK
    assert set(response.json()) == set([
        "ATP250",
        "ATP500",
        "Grand Slam",
        "International",
        "International Gold",
        "Masters",
        "Masters 1000",
        "Masters Cup"
    ])
