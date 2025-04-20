import logging
from datetime import datetime
from rq_scheduler import Scheduler
from src.repository.common import get_session
from src.service import player
from src.jobs.scheduler import get_redis_connection

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

def fill_player_details(raw_player_name: str):
    try:
        with next(get_session()) as session:
            player.fill_player_details(session=session, player_raw_name=raw_player_name)
    except Exception as e:
        logger.error(f"Error: {e}")

def schedule_player_details(raw_player_name: str):
    """
    Schedule the job to fill player details
    """
    with next(get_redis_connection()) as r:
        scheduler = Scheduler(connection=r)
        # Check if the job is already scheduled
        for job in scheduler.get_jobs():
            if job.id == raw_player_name:
                logger.debug(f"Job for player {raw_player_name} already scheduled.")
                return

        # Schedule the job to run immediately
        logger.info(f"Scheduling job for player: {raw_player_name}")
        scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func=fill_player_details,
            kwargs={'raw_player_name': raw_player_name},
            id=raw_player_name, # Ensures deduplication of jobs
        )