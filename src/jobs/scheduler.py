import os
from dotenv import load_dotenv
from typing import Generator, TYPE_CHECKING, Union, Optional
from contextlib import contextmanager

from rq import Queue
from rq.job import JobStatus, Job
from rq_scheduler import Scheduler
import logging

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check if we are in a test environment
IS_TEST = os.getenv("ENV") == "test"

if IS_TEST:
    # If in test environment, use fakeredis
    import fakeredis
    RedisImpl = fakeredis
else:
    # Otherwise, use the actual Redis library
    import redis
    RedisImpl = redis

# For type checkers only
if TYPE_CHECKING:
    import redis
    import fakeredis
    RedisType = Union[redis.Redis, fakeredis.FakeStrictRedis]
else:
    RedisType = object  # Just a dummy placeholder to satisfy runtime

@contextmanager
def get_redis_connection() -> Generator[RedisType, None, None]:
    """
    Get a connection to the Redis database
    This function checks if the environment is set to "test". If it is, it uses a fake Redis connection.
    Otherwise, it uses the actual Redis connection.
    """
    # Check if we are in a test environment
    if IS_TEST:
        r = RedisImpl.FakeStrictRedis()
    else:
        # Use the actual Redis connection
        REDIS_URL = os.getenv("REDIS_URL")
        if not REDIS_URL:
            raise ValueError("REDIS_URL environment variable is not set.")
        r = RedisImpl.from_url(REDIS_URL)
    
    try:
        yield r
    finally:
        r.close()

def is_job_scheduled_queued_or_started(job_id: str) -> Optional[Job]:
    """
    Check if a job is scheduled, queued or started in Redis
    """
    with get_redis_connection() as r:
        q = Queue(connection=r)
        job = q.fetch_job(job_id)
        
        if job is None:
            return
        
        # Check if the job is scheduled, queued, or started
        if job.get_status() in [JobStatus.SCHEDULED, JobStatus.QUEUED, JobStatus.STARTED]:
            logger.debug(f"Job {job_id} already scheduled, queued or started.")
            return job
        
        # Check if the job is already in the scheduler
        scheduler = Scheduler(connection=r)
        for job in scheduler.get_jobs():
            if job.id == job_id:
                logger.debug(f"Job {job_id} already scheduled.")
                return job
        
    return