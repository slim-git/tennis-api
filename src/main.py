import os
import joblib
import logging
import secrets
from typing import Literal, Optional, Annotated
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
from pydantic import BaseModel, Field, ConfigDict
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
from src.repository.common import get_session
from src.repository.sql import list_tournaments as _list_tournaments
from src.service.match import insert_new_match

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
    round: Literal['1st Round', '2nd Round', '3nd Round', '4th Round', 'Quarterfinals', 'Semifinals', 'The Final', 'Round Robin'] = '1st Round'
    series: Literal['Grand Slam', 'Masters 1000', 'Masters', 'Masters Cup', 'ATP500', 'ATP250', 'International Gold', 'International'] = 'Grand Slam'
    model: Optional[str] = 'LogisticRegression'
    version: Optional[str] = 'latest'

class ModelOutput(BaseModel):
    result: int = Field(description="The prediction result. 1 if player 1 is expected to win, 0 otherwise.", example=1)
    prob: list[float] = Field(description="Probability of [defeat, victory] of player 1.", example=[0.15, 0.85])

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


class Tournament(BaseModel):
    name: str = Field(description="The tournament's name.", example='Wimbledon')
    series: Literal['ATP250', 'ATP500', 'Grand Slam', 'Masters 1000', 'Masters', 'Masters Cup', 'International Gold', 'International'] = 'Grand Slam'
    court: Literal['Outdoor', 'Indoor'] = 'Outdoor'
    surface: Literal['Grass', 'Carpet', 'Clay', 'Hard'] = 'Grass'

@app.get("/{circuit}/tournaments", tags=["reference"], description="List the tournaments of the circuit", response_model=list[Tournament])
async def list_tournaments(circuit: Literal["atp", "wta"]):
    """
    List the tournaments of the circuit
    """
    return _list_tournaments(circuit)

class RawMatch(BaseModel):
    Comment: Literal['Completed', 'Retired', 'Walkover'] = 'Completed'
    Loser: str = Field(description="The name of the loser.", example='Djokovic N.')
    Winner: str = Field(description="The name of the winner.", example='Federer R.')
    Round: Literal['1st Round', '2nd Round', '3nd Round', '4th Round', 'Quarterfinals', 'Semifinals', 'The Final', 'Round Robin'] = '1st Round'
    Court: Literal['Outdoor', 'Indoor'] = 'Outdoor'
    Surface: Literal['Grass', 'Carpet', 'Clay', 'Hard'] = 'Grass'
    Wsets: int = Field(description="The number of sets won by the winner.", example=3)
    Lsets: int = Field(description="The number of sets won by the loser.", example=0)
    Date: str = Field(description="The date of the match.", example='2019-06-15')
    WRank: int = Field(description="The rank of the winner.", example=1)
    WPts: int = Field(description="The number of points of the winner.", example=4000)
    LPts: int = Field(description="The number of points of the loser.", example=3000)
    LRank: int = Field(description="The rank of the loser.", example=2)
    Location: str = Field(description="The location of the tournament.", example='London')
    Series: Literal['ATP250', 'ATP500', 'Grand Slam', 'Masters 1000', 'Masters', 'Masters Cup', 'International Gold', 'International'] = 'Grand Slam'
    W1: Optional[int] = Field(description="The score of the winner in the first set.", example=6)
    W2: Optional[int] = Field(description="The score of the winner in the second set.", example=6)
    W3: Optional[int] = Field(description="The score of the winner in the third set.", example=6)
    W4: Optional[int] = Field(description="The score of the winner in the fourth set.", example=None)
    W5: Optional[int] = Field(description="The score of the winner in the fifth set.", example=None)
    L1: Optional[int] = Field(description="The score of the loser in the first set.", example=3)
    L2: Optional[int] = Field(description="The score of the loser in the second set.", example=2)
    L3: Optional[int] = Field(description="The score of the loser in the third set.", example=0)
    L4: Optional[int] = Field(description="The score of the loser in the fourth set.", example=None)
    L5: Optional[int] = Field(description="The score of the loser in the fifth set.", example=None)
    Tournament: str = Field(description="The name of the tournament.", example='Wimbledon')
    Location: str = Field(description="The location of the tournament.", example='London')
    # Best_of: str = Field(description="The number of sets to win the match.", example=3)
    
    Config = ConfigDict(extra="allow")

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
    for raw_match in raw_matches:
        try:
            match = insert_new_match(
                db=session,
                raw_match=raw_match.model_dump(exclude_unset=True)
            )
            matches.append(match)
        except IntegrityError as e:
            logger.error(f"Error inserting match: {e}")
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Entity already exists in the database"
            )

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
        return JSONResponse(content={"status": "unhealthy"}, status_code=HTTP_503_SERVICE_UNAVAILABLE)
    
    return JSONResponse(content={"status": "healthy"}, status_code=HTTP_200_OK)
