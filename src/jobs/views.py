import logging
from rq_scheduler import Scheduler

from src.jobs.scheduler import get_redis_connection, is_job_scheduled_queued_or_started
from src.repository.common import get_session
from src.repository import views

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

def refresh_all_materialized_views():
    try:
        with get_session() as session:
            views.refresh_all_materialized_views(db=session)
    except Exception as e:
        logger.error(f"Error: {e}")

def schedule_refresh():
    """
    Schedule the job to refresh the materialized view
    """
    job_id = 'refresh_materialized_views'

    if job := is_job_scheduled_queued_or_started(job_id=job_id):
        return job
    
    with get_redis_connection() as r:
        scheduler = Scheduler(connection=r)
        
        # Schedule the job to run immediately
        logger.info("Scheduling job for refreshing views")
        job = scheduler.cron(
            cron_string="0 3 * * *",  # Every day at 3AM
            func=refresh_all_materialized_views,
            repeat=None,
            id=job_id,
        )

        return job
