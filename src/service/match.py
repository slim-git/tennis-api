import os
import logging
import requests
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.entity.match import Match, RawMatch
from src.entity.odds import Odds
from src.entity.player import Player
from src.repository import match_repo
from src.jobs.player import schedule_player_details

# Set up logging
logger = logging.getLogger(__name__)

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

def insert_new_match(db: Session, raw_match: Dict, on_conflict_do_nothing: bool = False) -> Match:
    """
    Insert a new match into the database
    """
    match = parse_raw_match(raw_match)

    try:
        match_repo.insert_match(db, match)
    except IntegrityError as e:
        if on_conflict_do_nothing:
            logging.debug(f"Match already exists: {match.date}")
            db.rollback()
            return match
        else:
            # Log the error and re-raise
            logging.error(f"Error inserting match: {e}")
            db.rollback()
            raise
    except Exception as e:
        # Log the error and re-raise
        logging.error(f"Error inserting match: {e}")
        db.rollback()
        raise

    # Schedule tasks to fetch player details
    if _should_fetch_details(match.winner):
        schedule_player_details(match.winner.name)

    if _should_fetch_details(match.loser):
        schedule_player_details(match.loser.name)

    return match

def insert_batch_matches(db: Session, raw_matches: List[Dict], on_conflict_do_nothing: bool = False) -> Dict:
    matches = []
    nb_errors = 0
    for raw_match in raw_matches:
        try:
            match = insert_new_match(
                db=db,
                raw_match=raw_match.model_dump(exclude_unset=True) if isinstance(raw_match, RawMatch) else raw_match,
                on_conflict_do_nothing=on_conflict_do_nothing,
            )

            if match.id is not None:
                matches.append(match)
        except IntegrityError as e:
            nb_errors += 1
            logger.error(f"Error inserting match: {e}")

    logger.info(f"Number of matches inserted: {len(matches)}")

    if nb_errors > 0:
        logger.warning(f"Number of errors: {nb_errors}")
    
    return {'matches': matches, 'nb_errors': nb_errors}

def _should_fetch_details(player: Player) -> bool:
    """
    Check if player details should be fetched
    """
    return player.tennis_id is None or player.caracteristics is None

def fetch_raw_data(year: Optional[int] = None) -> None:
    """
    Fetch data from tennis-data.co.uk for a given year and circuit (ATP or WTA) and save it to a file

    Args:
        year (int, optional): Year to retrieve. If None, fetch current year data.
    """
    current_year = datetime.now().year
    
    if not year:
        year = current_year
    
    filename = f"{year}.xlsx"
    file_path = f"./data/atp/{filename}"

    # Check if the file already exists
    if os.path.exists(file_path) and year != current_year:
        logging.info(f"File {file_path} already exists. Skipping download.")
        return

    logging.info(f"Fetching data from tennis-data.co.uk for year {year}")

    url = f"http://www.tennis-data.co.uk/{year}/{filename}"
    
    response = requests.get(url, stream=True)

    # Check response status code
    response.raise_for_status()

    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
        file.flush()

    logging.info(f"Data fetched from {url} 👍 and saved to {file_path}")

def get_cleaned_data(year: Optional[int]) -> pd.DataFrame:
    if not year:
        year = datetime.now().year
    
    df = pd.read_excel(f'./data/atp/{year}.xlsx')

    # Remove rows where LRank or WRank is NaN
    df = df.dropna(subset=['LRank', 'WRank'])
    df['Lsets'] = df['Lsets'].fillna(0)
    df['Wsets'] = df['Wsets'].fillna(0)

    # Strip whitespace from 'winner' and 'loser' columns
    df['Winner'] = df['Winner'].str.strip()
    df['Loser'] = df['Loser'].str.strip()

    # Replace NaN values with None
    df = df.replace({np.nan: None})
    df = df.where(pd.notnull(df), None)

    return df
