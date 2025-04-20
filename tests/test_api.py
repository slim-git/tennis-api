from src.entity.match import Match

def test_insert_match_success(client, db_session, raw_match):
    # Count the number of matches in the database before insertion
    match_count_before = db_session.query(Match).count()

    # Insert a valid match
    response = client.post("/match/insert", json=raw_match)
    
    assert response.status_code == 200
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
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "match_id": match_in_db.id,
    }
    

# # Test pour une erreur d'intégrité (match déjà existant)
# def test_insert_match_integrity_error(client):
#     # Insertion initiale d'un match
#     client.post("/match/insert", json=valid_match_data)

#     # Nouvelle tentative d'insertion du même match
#     response = client.post("/match/insert", json=valid_match_data)

#     assert response.status_code == 422
#     assert response.json() == {"detail": "Entity already exists in the database"}