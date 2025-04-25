import os
import logging
import secrets
from typing import Generator, Optional, Annotated, List, Dict
from datetime import datetime
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    Query,
    Security,
    Depends
)
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security.api_key import APIKeyHeader
from starlette.status import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_503_SERVICE_UNAVAILABLE)
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

from src.entity.match import (
    Match,
    RawMatch,
    MatchApiBase,
    MatchApiDetail
)
from src.entity.player import (
    Player,
    PlayerApiDetail,
)
from src.repository.common import get_session
from src.service.match import insert_new_match

from contextlib import asynccontextmanager
import httpx

load_dotenv()

# ------------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

def provide_connection() -> Generator[Session, None, None]:
    with get_session() as conn:
        yield conn

# ------------------------------------------------------------------------------

TENNIS_ML_API = os.getenv("TENNIS_ML_API")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Other server that requests should be forwarded to
    async with httpx.AsyncClient(base_url=TENNIS_ML_API) as client:
        yield {'client': client}

# ------------------------------------------------------------------------------

FASTAPI_API_KEY = os.getenv("FASTAPI_API_KEY")
safe_clients = ['127.0.0.1']

api_key_header = APIKeyHeader(name='Authorization', auto_error=False)

async def validate_api_key(request: Request, key: str = Security(api_key_header)):
    '''
    Check if the API key is valid

    Args:
        key (str): The API key to check
    
    Raises:
        HTTPException: If the API key is invalid
    '''
    if request.client.host not in safe_clients and not secrets.compare_digest(str(key), str(FASTAPI_API_KEY)):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Unauthorized - API Key is wrong"
        )
    return None

app = FastAPI(dependencies=[Depends(validate_api_key)] if FASTAPI_API_KEY else None,
              lifespan=lifespan if TENNIS_ML_API else None,
              title="Tennis Insights API")

# ------------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def redirect_to_docs():
    '''
    Redirect to the API documentation.
    '''
    return RedirectResponse(url='/docs')

@app.get("/run_experiment", tags=["model"], description="Schedule a run of the ML experiment")
async def run_xp(request: Request):
    """
    Train the model
    """
    params = dict(request.query_params)

    async with httpx.AsyncClient() as client:
        response = await client.get(TENNIS_ML_API + "run_experiment", params=params)
        return response.json()

@app.get("/predict",
         tags=["model"],
         description="Predict the outcome of a tennis match",)
async def make_prediction(request: Request):
    """
    Predict the matches
    """
    params = dict(request.query_params)

    if not TENNIS_ML_API:
        return {"message": "TENNIS_ML_API environment variable not set."}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(TENNIS_ML_API + "predict", params=params)
        return response.json()

@app.get("/list_available_models", tags=["model"], description="List the available models")
async def list_available_models():
    """
    List the available models
    """
    if not TENNIS_ML_API:
        return {"message": "TENNIS_ML_API environment variable not set."}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(TENNIS_ML_API + "list_available_models")
        return response.json()

# List all the tournament names and years
@app.get("/tournament/names", tags=["tournament"], description="List all the tournament names and years", response_model=List[Dict])
async def list_tournament_names(
    session: Session = Depends(provide_connection)
):
    """
    List all the tournament names and first and last year of occurrence
    """
    tournaments = session.execute(text("SELECT t.name, t.first_year, t.last_year FROM data.tournaments_list_m_view AS t")).all()

    tournaments = [
        {
            "name": tournament[0],
            "first_year": tournament[1],
            "last_year": tournament[2]
        }
        for tournament in tournaments
    ]

    return tournaments

@app.get("/references/courts", tags=["reference"], description="List all the courts")
async def list_courts(
    session: Session = Depends(provide_connection)
):
    """
    List all the courts
    """
    courts = session.execute(text("SELECT name FROM data.ref_court_m_view")).all()

    courts = [court[0] for court in courts]

    return courts

@app.get("/references/surfaces", tags=["reference"], description="List all the surfaces")
async def list_surfaces(
    session: Session = Depends(provide_connection)
):
    """
    List all the surfaces
    """
    surfaces = session.execute(text("SELECT name FROM data.ref_surface_m_view")).all()

    surfaces = [surface[0] for surface in surfaces]

    return surfaces

@app.get("/references/series", tags=["reference"], description="List all the series")
async def list_series(
    session: Session = Depends(provide_connection)
):
    """
    List all the series
    """
    series = session.execute(text("SELECT name FROM data.ref_series_m_view")).all()

    series = [serie[0] for serie in series]

    return series

class ListPlayersInput(BaseModel):
    ids: List[int] = Field(
        description="List of player IDs",
    )

# Get a list of players
@app.get("/players", tags=["player"], description="Get a list of players from the database", response_model=Dict[str|int, Optional[PlayerApiDetail]])
async def list_players(
    params: Annotated[ListPlayersInput, Query()],
    session: Session = Depends(provide_connection),
):
    """
    Get a list of players from the database
    """
    ids = sorted(params.ids)
    players = session.query(Player).filter(Player.id.in_(ids)).all()
    
    if not players:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Players {ids} not found"
        )
    
    players = {player.id: player for player in players}

    return {id: players.get(id) for id in ids}

@app.get("/player/{player_id}", tags=["player"], description="Get a player from the database", response_model=PlayerApiDetail)
async def get_player(
    player_id: int,
    session: Session = Depends(provide_connection)
):
    """
    Get a player from the database
    """
    player = session.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Player {player_id} not found"
        )

    return player

# Get all the matches from a tournament
@app.get("/tournament/matches", tags=["tournament"], description="Get all the matches from a tournament", response_model=List[MatchApiBase])
async def search_tournament_matches(
    name: str,
    year: int,
    session: Session = Depends(provide_connection)
):
    """
    Get all the matches from a tournament
    """
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    matches = session.query(Match).filter(
        Match.tournament_name == name,
        Match.date.between(start_date, end_date)
    ).all()

    return sorted(matches, key=lambda x: x.date, reverse=True)


# Get a match
@app.get("/match/{match_id}", tags=["match"], description="Get a match from the database", response_model=MatchApiDetail)
async def get_match(
    match_id: int,
    session: Session = Depends(provide_connection)
):
    """
    Get a match from the database
    """
    match = session.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Match {match_id} not found"
        )

    return match


@app.post("/match/insert", tags=["match"], description="Insert a match into the database")
async def insert_match(
    raw_match: RawMatch,
    session: Session = Depends(provide_connection)
):
    """
    Insert a match into the database
    """
    try:
        match = insert_new_match(
            db=session,
            raw_match=raw_match.model_dump(exclude_unset=True)
        )
    except IntegrityError as e:
        logger.error(f"Error inserting match: {e}")
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Entity already exists in the database"
        )

    output = {
        "status": "ok",
        "match_id": match.id,
    }

    return JSONResponse(content=output, status_code=HTTP_200_OK)


@app.post("/batch/match/insert", tags=["match"], description="Insert a batch of matches into the database")
async def insert_batch_match(
    raw_matches: list[RawMatch],
    session: Session = Depends(provide_connection)
):
    """
    Insert a batch of matches into the database
    """
    matches = []
    nb_errors = 0
    for raw_match in raw_matches:
        try:
            match = insert_new_match(
                db=session,
                raw_match=raw_match.model_dump(exclude_unset=True)
            )
            matches.append(match)
        except IntegrityError as e:
            nb_errors += 1
            logger.error(f"Error inserting match: {e}")

    logger.info(f"Number of matches inserted: {len(matches)}")
    if nb_errors > 0:
        logger.warning(f"Number of errors: {nb_errors}")
        return JSONResponse(
            content={"status": "ok", "message": f"{len(matches)} matches inserted, {nb_errors} errors"},
            status_code=HTTP_422_UNPROCESSABLE_ENTITY
        )
    else:
        output = {
            "status": "ok",
            "match_ids": [match.id for match in matches],
        }
        return JSONResponse(content=output, status_code=HTTP_200_OK)

# ------------------------------------------------------------------------------
@app.get("/check_health", tags=["general"], description="Check the health of the API")
async def check_health(session: Session = Depends(provide_connection)):
    """
    Check all the services in the infrastructure are working
    """
    # Check if the database is alive
    try:
        session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"DB check failed: {e}")
        return JSONResponse(content={"status": "unhealthy", "detail": "Database not reachable"},
                            status_code=HTTP_503_SERVICE_UNAVAILABLE)
    
    # Check if the scraper endpoint is reachable
    if FLARESOLVERR_API := os.getenv("FLARESOLVERR_API"):
        import requests

        try:
            # Ping the scraper endpoint
            response = requests.get(FLARESOLVERR_API + "health", timeout=5)
            if response.status_code != HTTP_200_OK:
                logger.error(f"Scraper check failed: {response.status_code}")
                return JSONResponse(content={"status": "unhealthy", "detail": "Flaresolverr not reachable"},
                                    status_code=HTTP_503_SERVICE_UNAVAILABLE)
        except requests.RequestException as e:
            logger.error(f"Scraper check failed: {e}")
            return JSONResponse(content={"status": "unhealthy", "detail": "Flaresolverr not reachable"},
                                status_code=HTTP_503_SERVICE_UNAVAILABLE)
    
    return JSONResponse(content={"status": "healthy"}, status_code=HTTP_200_OK)
