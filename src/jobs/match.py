import logging
from typing import Optional
from datetime import datetime
from rq_scheduler import Scheduler
from rq.job import Job

from src.jobs.scheduler import get_redis_connection, is_job_scheduled_queued_or_started
from src.repository.common import get_session
from src.service import match
from src.service.match import (
    fetch_raw_data,
    get_cleaned_data,
)

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

def ingestion_job(year: Optional[int] = None):
    """
    Ingest matches for a specific year
    """
    current_year = datetime.now().year
    
    if not year:
        year = current_year
    
    try:
        with get_session() as session:
            fetch_raw_data(year=year)
            
            # Get the cleaned data
            df = get_cleaned_data(year=year)
            
            # Send requests of 100 matches
            for start in range(0, len(df), 100):
                end = start + 99
                df_small = df.loc[start:end]
                
                match.insert_batch_matches(
                    raw_matches=df_small.to_dict(orient='records'),
                    on_conflict_do_nothing=True,
                    db=session,
                )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

def schedule_matches_ingestion(year: Optional[int] = None) -> Job:
    """
    Schedule the job to ingest matches for a specific year
    """
    job_id = f'matches_ingestion_{year if year else "current"}'

    if job := is_job_scheduled_queued_or_started(job_id=job_id):
        return job
    
    with get_redis_connection() as r:
        scheduler = Scheduler(connection=r)

        job_params = {
            'scheduled_time': datetime.now(),
            'kwargs': {'year': year},
            'id': job_id,  # Ensures deduplication of jobs
            'timeout': 7200,  # Timeout for the job
            'func': ingestion_job,
        }

        # For the current year data, we want to run the job every week
        if year is None:
            job_params['interval'] = 7 * 86400
            job_params['repeat'] = None

        # Schedule the job to run immediately
        logger.info(f"Scheduling job for year: {year if year else 'current'}")
        job = scheduler.schedule(**job_params)

        return job