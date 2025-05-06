import logging
from datetime import datetime
from rq_scheduler import Scheduler
from rq.job import Job

from src.jobs.scheduler import get_redis_connection, is_job_scheduled_queued_or_started
from src.repository.common import get_session
from src.service import player

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

def fill_player_details(raw_player_name: str):
    try:
        with get_session() as session:
            player.fill_player_details(session=session, player_raw_name=raw_player_name)
    except Exception as e:
        logger.error(f"Error: {e}")

def schedule_player_details(raw_player_name: str) -> Job:
    """
    Schedule the job to fill player details
    """
    job_id = f'player_details_{raw_player_name}'

    if job := is_job_scheduled_queued_or_started(job_id=job_id):
        return job
    
    with get_redis_connection() as r:
        scheduler = Scheduler(connection=r)

        # Schedule the job to run immediately
        logger.info(f"Scheduling job for player: {raw_player_name}")
        job = scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func=fill_player_details,
            kwargs={'raw_player_name': raw_player_name},
            id=job_id, # Ensures deduplication of jobs
        )

        return job