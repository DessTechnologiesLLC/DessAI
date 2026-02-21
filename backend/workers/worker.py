# backend/workers/worker.py
"""
Simple RQ worker entrypoint.

When we start background processing, we'll run this worker
and push ingestion/search tasks onto Redis queues.
"""
import os

import rq
from redis import Redis

from backend.core.config import settings

redis_conn = Redis.from_url(settings.redis_url)
queue = rq.Queue("default", connection=redis_conn)


def main():
    worker = rq.Worker([queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
