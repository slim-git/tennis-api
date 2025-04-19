import os
from dotenv import load_dotenv
from typing import Generator
import redis

# Load environment variables from .env file
load_dotenv()

def get_redis_connection() -> Generator:
    # Set up Redis connection

    # Check if we are in a test environment
    if os.getenv("ENV") == "test":
        import fakeredis
        r = fakeredis.FakeStrictRedis()
    else:
        # Use the actual Redis connection
        REDIS_URL = os.getenv("REDIS_URL")
        if not REDIS_URL:
            raise ValueError("REDIS_URL environment variable is not set.")
        r = redis.from_url(REDIS_URL)
    
    try:
        yield r
    finally:
        r.close()
