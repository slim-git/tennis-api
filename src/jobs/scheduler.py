import os
from dotenv import load_dotenv
from typing import Generator, TYPE_CHECKING, Union
from contextlib import contextmanager

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
