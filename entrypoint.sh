#!/bin/bash

# Launch rqscheduler --url $REDIS_URL and rq worker in the background
# if REDIS_URL is set and ENV is not test
if [[ -n "$REDIS_URL" && "$ENV" != "test" ]]; then
    echo "Starting rq scheduler and worker..."
    rq worker --url $REDIS_URL &
    rqscheduler --url $REDIS_URL &
else
    echo "Skipping rq scheduler and worker startup."
fi

# Run the API
uvicorn src.main:app --host 0.0.0.0 --port 7860