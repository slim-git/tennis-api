import os
import joblib
import logging
import secrets
from typing import Literal, Optional, Annotated, List, Dict
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
from fastapi.background import BackgroundTasks
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
from mlflow.exceptions import RestException
from sqlalchemy.exc import IntegrityError

from src.model import (
    run_experiment,
    train_model_from_scratch,
    predict,
    list_registered_models,
    load_model
)
from src.entity.match import (
    Match,
    RawMatch,
    MatchApiBase,
    MatchApiDetail
)
from src.entity.player import (
    Player,
    PlayerApiDetail,
    PlayerApiBase
)
from src.entity.tournament import Tournament
from src.repository.common import get_session
from src.repository.sql import list_tournaments as _list_tournaments
from src.service.match import insert_new_match

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

load_dotenv()
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
              title="Tennis Insights API")


# ------------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def redirect_to_docs():
    '''
    Redirect to the API documentation.
    '''
    return RedirectResponse(url='/docs')

@app.get("/train_model", tags=["model"], deprecated=True)
async def train_model(
    background_tasks: BackgroundTasks,
    circuit: Literal["atp", "wta"] = 'atp',
    from_date: str = "2024-01-01",
    to_date: str = "2024-12-31"):
    """
    Train the model
    """
    # Check dates format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return {"message": "Invalid date format. Please use the format 'YYYY-MM-DD'"}
    
    background_tasks.add_task(
        func=train_model_from_scratch,
        circuit=circuit,
        from_date=from_date,
        to_date=to_date)
    
    return {"message": "Model training in progress"}

@app.get("/run_experiment", tags=["model"], description="Schedule a run of the ML experiment")
async def run_xp(
    background_tasks: BackgroundTasks,
    circuit: Literal["atp", "wta"] = 'atp',
    from_date: str = "2024-01-01",
    to_date: str = "2024-12-31"):
    """
    Train the model
    """
    # Check dates format
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        return {"message": "Invalid date format. Please use the format 'YYYY-MM-DD'"}
    
    background_tasks.add_task(
        func=run_experiment,
        circuit=circuit,
        from_date=from_date,
        to_date=to_date)
    
    return {"message": "Experiment scheduled"}

class ModelInput(BaseModel):
    rank_player_1: int = Field(gt=0, default=1, description="The rank of the 1st player")
    rank_player_2: int = Field(gt=0, default=100, description="The rank of the 2nd player")
    points_player_1: int = Field(gt=0, default=4000, description="The number of points of the 1st player")
    points_player_2: int = Field(gt=0, default=500, description="The number of points of the 2nd player")
    court: Literal['Outdoor', 'Indoor'] = 'Outdoor'
    surface: Literal['Grass', 'Carpet', 'Clay', 'Hard'] = 'Clay'
    round: Literal['1st Round', '2nd Round', '3rd Round', '4th Round', 'Quarterfinals', 'Semifinals', 'The Final', 'Round Robin'] = '1st Round'
    series: Literal['Grand Slam', 'Masters 1000', 'Masters', 'Masters Cup', 'ATP500', 'ATP250', 'International Gold', 'International'] = 'Grand Slam'
    model: Optional[str] = 'LogisticRegression'
    version: Optional[str] = 'latest'

class ModelOutput(BaseModel):
    result: int = Field(description="The prediction result. 1 if player 1 is expected to win, 0 otherwise.", json_schema_extra={"example": "1"})
    prob: list[float] = Field(description="Probability of [defeat, victory] of player 1.", json_schema_extra={"example": "[0.15, 0.85]"})

@app.get("/predict",
         tags=["model"],
         description="Predict the outcome of a tennis match",
         response_model=ModelOutput)
async def make_prediction(params: Annotated[ModelInput, Query()]):
    """
    Predict the matches
    """
    if not params.model:
        # check the presence of 'model.pkl' file in data/
        if not os.path.exists("/data/model.pkl"):
            return {"message": "Model not trained. Please train the model first."}
    
        # Load the model
        pipeline = joblib.load("/data/model.pkl")
    else:
        # Get the model info
        try:
            pipeline = load_model(params.model, params.version)
        except RestException as e:
            logger.error(e)

            # Return HTTP error 404
            return HTTPException(
                status=HTTP_404_NOT_FOUND,
                detail=f"Model {params.model} not found"
            )

    # Make the prediction
    prediction = predict(
        pipeline=pipeline,
        rank_player_1=params.rank_player_1,
        rank_player_2=params.rank_player_2,
        points_player_1=params.points_player_1,
        points_player_2=params.points_player_2,
        court=params.court,
        surface=params.surface,
        round_stage=params.round,
        series=params.series
    )

    logger.info(prediction)

    return prediction

@app.get("/list_available_models", tags=["model"], description="List the available models")
async def list_available_models():
    """
    List the available models
    """
    return list_registered_models()


@app.get("/{circuit}/tournaments", tags=["tournament"], description="List the tournaments of the circuit", response_model=List[Tournament])
async def list_tournaments(circuit: Literal["atp", "wta"]):
    """
    List the tournaments of the circuit
    """
    return _list_tournaments(circuit)

# List all the tournament names and years
@app.get("/tournament/names", tags=["tournament"], description="List all the tournament names and years", response_model=List[Dict])
async def list_tournament_names(
    session: Annotated[Session, Depends(get_session)]
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
    session: Annotated[Session, Depends(get_session)]
):
    """
    List all the courts
    """
    courts = session.execute(text("SELECT name FROM data.ref_court_m_view")).all()

    courts = [court[0] for court in courts]

    return courts

@app.get("/references/surfaces", tags=["reference"], description="List all the surfaces")
async def list_surfaces(
    session: Annotated[Session, Depends(get_session)]
):
    """
    List all the surfaces
    """
    surfaces = session.execute(text("SELECT name FROM data.ref_surface_m_view")).all()

    surfaces = [surface[0] for surface in surfaces]

    return surfaces

@app.get("/references/series", tags=["reference"], description="List all the series")
async def list_series(
    session: Annotated[Session, Depends(get_session)]
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
    session: Annotated[Session, Depends(get_session)],
    params: Annotated[ListPlayersInput, Query()],
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
    session: Annotated[Session, Depends(get_session)]
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
    session: Annotated[Session, Depends(get_session)]
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
    session: Annotated[Session, Depends(get_session)]
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
    session: Annotated[Session, Depends(get_session)]
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
    session: Annotated[Session, Depends(get_session)]
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
async def check_health(session: Annotated[Session, Depends(get_session)]):
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
