from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from src.entity.match import Match
from src.entity.odds import Odds
from src.entity.player import Player
from src.repository import match_repo

def get_match(raw_match: Dict) -> Match:
    """
    Parse a raw match
    """
    match = Match()
    match.date = raw_match.get("Date")
    match.comment = raw_match.get("Comment")
    match.winner_rank = raw_match.get("WRank")
    match.winner_points = raw_match.get("WPts")
    match.loser_rank = raw_match.get("LRank")
    match.loser_points = raw_match.get("LPts")
    match.tournament_name = raw_match.get("Tournament")
    match.tournament_series = raw_match.get("Series")
    match.tournament_surface = raw_match.get("Surface")
    match.tournament_court = raw_match.get("Court")
    match.tournament_round = raw_match.get("Round")
    match.tournament_location = raw_match.get("Location")

    return match

def get_all_odds(raw_match: Dict) -> List[Odds]:
    """
    Parse the odds data from the raw match
    """
    all_odds = []

    odds_data = {k: v for k, v in raw_match.items() if k[-1] in ["W", "L"]}
    bookmakers = set(k[:-1] for k in odds_data.keys())
    
    for bookmaker in bookmakers:
        odds = Odds()
        odds.bookmaker = bookmaker
        odds.winner = odds_data[f"{bookmaker}W"]
        odds.loser = odds_data[f"{bookmaker}L"]

        all_odds.append(odds)
    
    return all_odds

def get_players(raw_match: Dict) -> Tuple[Player, Player]:
    """
    Parse the players data from the raw match
    """
    winner = Player(name = raw_match.get("Winner"))
    loser = Player(name = raw_match.get("Loser"))

    return winner, loser

def parse_raw_match(raw_match: Dict) -> Match:
    """
    Parse a raw match and odds
    """
    match = get_match(raw_match)
    all_odds = get_all_odds(raw_match)
    winner, loser = get_players(raw_match)

    match.odds = all_odds
    match.winner = winner
    match.loser = loser

    return match

def parse_raw_matches(raw_matches: Dict) -> List[Match]:
    """
    Parse a list of raw matches
    """
    matches = []
    for raw_match in raw_matches:
        match = parse_raw_match(raw_match)
        matches.append(match)

    return matches

def insert_new_match(db: Session, raw_match: Dict) -> Match:
    """
    Insert a new match into the database
    """
    match = parse_raw_match(raw_match)
    match_repo.insert_match(db, match)

    return match