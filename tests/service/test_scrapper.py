from typing import Dict
from src.service.scrapper import (
    search_player,
    get_personal_details,
)

def test_search_player_herbert(mock_responses):
    """
    Test the search_player function
    """
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

def test_search_player_federer():
    """
    Test the search_player function
    """
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

def test_get_personal_details():
    """
    Test the get_personal_details function
    """
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
    