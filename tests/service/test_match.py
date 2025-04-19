from typing import Dict, List
from src.service.match import (
    parse_raw_match,
    parse_raw_matches,
    get_players,
    get_all_odds,
    get_match,
    insert_new_match,
)

def test_get_players(raw_match: Dict):
    """
    Test the get_players function
    
    Get the players from the raw match and return a tuple of Player objects
    The players are created from the raw match data and the names are set
    to the names of the players in the raw match data
    """
    winner, loser = get_players(raw_match)

    assert winner.name == raw_match.get("Winner")
    assert loser.name == raw_match.get("Loser")
    assert winner.name == "Federer R."
    assert loser.name == "Djokovic N."

def test_get_all_odds(raw_match: Dict):
    """
    Test the get_all_odds function

    Get all odds from the raw match and return a list of Odds objects
    """
    odds = get_all_odds(raw_match)

    assert len(odds) == 3, "Number of odds is not correct"

    # Get the odds object for bookmaker == "B365"
    assert "B365" in [odds.bookmaker for odds in odds], "B365 odds not found"
    B365_odds = next(odds for odds in odds if odds.bookmaker == "B365")
    assert B365_odds.winner == raw_match.get("B365W")
    assert B365_odds.loser == raw_match.get("B365L")
    assert B365_odds.winner == 1.2
    assert B365_odds.loser == 4.5

    # Get the odds object for bookmaker == "Max"
    assert "Max" in [odds.bookmaker for odds in odds], "Max odds not found"
    max_odds = next(odds for odds in odds if odds.bookmaker == "Max")
    assert max_odds.winner == raw_match.get("MaxW")
    assert max_odds.loser == raw_match.get("MaxL")
    assert max_odds.winner == 1.5
    assert max_odds.loser == 1.8

    # Get the odds object for bookmaker == "Avg"
    assert "Avg" in [odds.bookmaker for odds in odds], "Avg odds not found"
    avg_odds = next(odds for odds in odds if odds.bookmaker == "Avg")
    assert avg_odds.winner == raw_match.get("AvgW")
    assert avg_odds.loser == raw_match.get("AvgL")
    assert avg_odds.winner == 1.3
    assert avg_odds.loser == 2.3

def test_get_match(raw_match: Dict):
    """
    Test the get_match function
    """
    match = get_match(raw_match)

    assert match.comment == raw_match.get("Comment")
    assert match.winner_rank == raw_match.get("WRank")
    assert match.winner_points == raw_match.get("WPts")
    assert match.loser_rank == raw_match.get("LRank")
    assert match.loser_points == raw_match.get("LPts")
    assert match.tournament_name == raw_match.get("Tournament")
    assert match.tournament_series == raw_match.get("Series")
    assert match.tournament_surface == raw_match.get("Surface")
    assert match.tournament_court == raw_match.get("Court")
    assert match.tournament_round == raw_match.get("Round")
    assert match.tournament_location == raw_match.get("Location")
    assert match.date == raw_match.get("Date")

    assert match.date == "2019-06-15"
    assert match.tournament_name == "Wimbledon"
    assert match.tournament_series == "Grand Slam"
    assert match.tournament_surface == "Grass"
    assert match.tournament_court == "Outdoor"
    assert match.tournament_round == "The Final"
    assert match.tournament_location == "London"
    assert match.winner_rank == 1
    assert match.winner_points == 4000
    assert match.loser_rank == 2
    assert match.loser_points == 3000

def test_parse_raw_match(raw_match: Dict):
    """
    Test the parse_raw_match function
    """
    match = parse_raw_match(raw_match)

    assert match.comment == raw_match.get("Comment")
    assert match.winner_rank == raw_match.get("WRank")
    assert match.winner_points == raw_match.get("WPts")
    assert match.loser_rank == raw_match.get("LRank")
    assert match.loser_points == raw_match.get("LPts")
    assert match.tournament_name == raw_match.get("Tournament")
    assert match.tournament_series == raw_match.get("Series")
    assert match.tournament_surface == raw_match.get("Surface")
    assert match.tournament_court == raw_match.get("Court")
    assert match.tournament_round == raw_match.get("Round")
    assert match.tournament_location == raw_match.get("Location")
    assert match.winner.name == raw_match.get("Winner")
    assert match.loser.name == raw_match.get("Loser")
    assert len(match.odds) == 3, "Number of odds is not correct"

    # Get the odds object for bookmaker == "B365"
    assert "B365" in [odds.bookmaker for odds in match.odds], "B365 odds not found"
    B365_odds = next(odds for odds in match.odds if odds.bookmaker == "B365")
    assert B365_odds.winner == raw_match.get("B365W")
    assert B365_odds.loser == raw_match.get("B365L")
    assert B365_odds.winner == 1.2
    assert B365_odds.loser == 4.5

    # Get the odds object for bookmaker == "Max"
    assert "Max" in [odds.bookmaker for odds in match.odds], "Max odds not found"
    max_odds = next(odds for odds in match.odds if odds.bookmaker == "Max")
    assert max_odds.winner == raw_match.get("MaxW")
    assert max_odds.loser == raw_match.get("MaxL")
    assert max_odds.winner == 1.5
    assert max_odds.loser == 1.8

    # Get the odds object for bookmaker == "Avg"
    assert "Avg" in [odds.bookmaker for odds in match.odds], "Avg odds not found"
    avg_odds = next(odds for odds in match.odds if odds.bookmaker == "Avg")
    assert avg_odds.winner == raw_match.get("AvgW")
    assert avg_odds.loser == raw_match.get("AvgL")
    assert avg_odds.winner == 1.3
    assert avg_odds.loser == 2.3

    # Check the winner and loser
    assert match.winner.name == raw_match.get("Winner")
    assert match.loser.name == raw_match.get("Loser")
    assert match.winner.name == "Federer R."
    assert match.loser.name == "Djokovic N."

def test_parse_raw_matches_batch(raw_matches_batch: List[Dict]):
    """
    Test the parse_raw_matches_batch function

    Parse a batch of raw matches and return a list of Match objects
    The matches are created from the raw match data and the names are set
    to the names of the players in the raw match data
    """
    matches = parse_raw_matches(raw_matches_batch)

    assert len(matches) == len(raw_matches_batch), "Number of matches is not correct"

    for match, raw_match in zip(matches, raw_matches_batch):
        assert match.comment == raw_match.get("Comment")
        assert match.winner_rank == raw_match.get("WRank")
        assert match.winner_points == raw_match.get("WPts")
        assert match.loser_rank == raw_match.get("LRank")
        assert match.loser_points == raw_match.get("LPts")
        assert match.tournament_name == raw_match.get("Tournament")
        assert match.tournament_series == raw_match.get("Series")
        assert match.tournament_surface == raw_match.get("Surface")
        assert match.tournament_court == raw_match.get("Court")
        assert match.tournament_round == raw_match.get("Round")
        assert match.tournament_location == raw_match.get("Location")

def test_insert_new_match(db_session, super_joueur):
    """
    Test inserting a new match into the database
    """
    raw_match = {
        "Date": "2023-04-01",
        "Comment": "Walkover",
        "WRank": 1,
        "WPts": 3000,
        "LRank": 2000,
        "LPts": 2900,
        "Tournament": "Wimbledon",
        "Series": "Grand Slam",
        "Surface": "Grass",
        "Court": "Outdoor",
        "Round": "Semifinals",
        "Location": "London",
        "Winner": super_joueur.name,
        "Loser": "Unknown A.",
        "B365W": 1.5,
        "B365L": 2.6
    }

    match = insert_new_match(db=db_session, raw_match=raw_match)

    assert match.id is not None
    assert match.winner.name == super_joueur.name
    assert match.winner.caracteristics is not None
    assert match.loser.name == "Unknown A."
    assert match.loser.caracteristics is None
    assert len(match.odds) > 0
