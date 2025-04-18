import os
from dotenv import load_dotenv
from typing import Generator
import redis

# Load environment variables from .env file
load_dotenv()

# Set up Redis connection
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable is not set.")

def get_redis_connection() -> Generator:
    # Connect to Redis and create a scheduler
    r = redis.from_url(REDIS_URL)

    try:
        yield r
    finally:
        r.close()
