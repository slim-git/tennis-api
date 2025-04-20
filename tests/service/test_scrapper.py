import os
from typing import Dict
from src.service.scrapper import (
    search_player,
    get_personal_details,
)

def test_search_player_herbert_without_flaresolverr(monkeypatch):
    """
    Test the search_player function
    """
    monkeypatch.delenv("FLARESOLVERR_API", raising=False)
    assert os.getenv("FLARESOLVERR_API") is None, "FLARESOLVERR_API is set"

    player_list = search_player(raw_name="Herbert P.H.")

    assert len(player_list) > 0, "No player found"
    player_data = None

    for player in player_list:
        assert isinstance(player, Dict), "player is not a dictionary"
        if player.get("name") == "Pierre-Hugues Herbert":
            player_data = player
            break
    
    assert player_data is not None, "Player data not found"
    assert isinstance(player_data, Dict), "Player data is not a dictionary"
    assert player_data.get("name") == "Pierre-Hugues Herbert", "Player name is not correct"
    assert player_data.get("first_name") == "Pierre-Hugues", "Player first name is not correct"
    assert player_data.get("last_name") == "Herbert", "Player last name is not correct"
    assert player_data.get("country") == "FRA", "Player country is not correct"
    assert player_data.get("active") == "A", "Player active status is not correct"
    assert player_data.get("headshot_url") == "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=H996&w=150&h=200", "Player headshot URL is not correct"
    assert player_data.get("sub_category_name") == "pierre-hugues-herbert-h996", "Player sub category name is not correct"
    assert player_data.get("player_id") == "H996", "Player ID is not correct"

def test_search_player_without_flaresolverr(monkeypatch):
    """
    Test the search_player function
    """
    monkeypatch.delenv("FLARESOLVERR_API", raising=False)
    assert os.getenv("FLARESOLVERR_API") is None, "FLARESOLVERR_API is set"

    player_list = search_player(raw_name="Federer R.")

    assert len(player_list) > 0, "No player found"
    player_data = player_list[0]

    assert isinstance(player_data, Dict), "Player data is not a dictionary"
    assert player_data.get("name") == "Roger Federer", "Player name is not correct"
    assert player_data.get("first_name") == "Roger", "Player first name is not correct"
    assert player_data.get("last_name") == "Federer", "Player last name is not correct"
    assert player_data.get("country") == "SUI", "Player country is not correct"
    assert player_data.get("active") == "I", "Player active status is not correct"
    assert player_data.get("headshot_url") == "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=F324&w=150&h=200", "Player headshot URL is not correct"
    assert player_data.get("sub_category_name") == "roger-federer-f324", "Player sub category name is not correct"
    assert player_data.get("player_id") == "F324", "Player ID is not correct"

def test_search_player_with_flaresolverr(monkeypatch):
    """
    Test the search_player function with FlareSolverr
    """
    monkeypatch.setenv("FLARESOLVERR_API", "http://localhost:8191/")
    assert os.getenv("FLARESOLVERR_API") is not None, "FLARESOLVERR_API is not set"

    player_list = search_player(raw_name="Gasquet R.")

    assert len(player_list) > 0, "No player found"
    player_data = player_list[0]

    assert isinstance(player_data, Dict), "Player data is not a dictionary"
    assert player_data.get("name") == "Richard Gasquet", "Player name is not correct"
    assert player_data.get("first_name") == "Richard", "Player first name is not correct"
    assert player_data.get("last_name") == "Gasquet", "Player last name is not correct"
    assert player_data.get("country") == "FRA", "Player country is not correct"
    assert player_data.get("active") == "A", "Player active status is not correct"
    assert player_data.get("headshot_url") == "https://www.atptour.com/en/-/ajax/PlayerSearch/HeadshotPhoto?playerId=G628&amp;w=150&amp;h=200", "Player headshot URL is not correct"
    assert player_data.get("sub_category_name") == "richard-gasquet-g628", "Player sub category name is not correct"
    assert player_data.get("player_id") == "G628", "Player ID is not correct"

def test_get_personal_details_without_flaresolverr(monkeypatch):
    """
    Test the get_personal_details function
    """
    monkeypatch.delenv("FLARESOLVERR_API", raising=False)
    assert os.getenv("FLARESOLVERR_API") is None, "FLARESOLVERR_API is set"

    personal_details = get_personal_details(playerId="F324")

    assert isinstance(personal_details, Dict), "Personal details is not a dictionary"
    assert personal_details.get("last_name") == "Federer", "Player last name is not correct"
    assert personal_details.get("first_name") == "Roger", "Player first name is not correct"
    assert personal_details.get("nationality") == "Switzerland", "Player nationality is not correct"
    assert personal_details.get("birth_date") == "1981-08-08T00:00:00", "Player birth date is not correct"
    assert personal_details.get("pro_year") == 1998, "Player pro year is not correct"
    assert personal_details.get("height_cm") == 185, "Player height is not correct"
    assert personal_details.get("weight_kg") == 85, "Player weight is not correct"
    assert personal_details.get("play_hand") == "R", "Player play hand is not correct"
    assert personal_details.get("back_hand") == "1", "Player back hand is not correct"

def test_get_personal_details_with_flaresolverr(monkeypatch):
    """
    Test the get_personal_details function with FlareSolverr
    """
    monkeypatch.setenv("FLARESOLVERR_API", "http://localhost:8191/")
    assert os.getenv("FLARESOLVERR_API") is not None, "FLARESOLVERR_API is not set"

    personal_details = get_personal_details(playerId="G628")

    assert isinstance(personal_details, Dict), "Personal details is not a dictionary"
    assert personal_details.get("last_name") == "Gasquet", "Player last name is not correct"
    assert personal_details.get("first_name") == "Richard", "Player first name is not correct"
    assert personal_details.get("nationality") == "France", "Player nationality is not correct"
    assert personal_details.get("birth_date") == "1986-06-18T00:00:00", "Player birth date is not correct"
    assert personal_details.get("pro_year") == 2002, "Player pro year is not correct"
    assert personal_details.get("height_cm") == 183, "Player height is not correct"
    assert personal_details.get("weight_kg") == 79, "Player weight is not correct"
    assert personal_details.get("play_hand") == "R", "Player play hand is not correct"
    assert personal_details.get("back_hand") == "1", "Player back hand is not correct"
