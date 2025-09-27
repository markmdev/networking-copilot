"""RQ queue helpers for capture/extraction jobs."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

import redis
from rq import Queue, get_current_job
from rq.exceptions import NoSuchJobError
from rq.job import Job

from networking.services import process_capture

_QUEUE_NAME = os.getenv("CAPTURE_QUEUE_NAME", "capture")
_JOB_TIMEOUT = int(os.getenv("CAPTURE_JOB_TIMEOUT", "900"))
_RESULT_TTL = int(os.getenv("CAPTURE_JOB_RESULT_TTL", str(60 * 60 * 24)))

_connection: Optional[redis.Redis] = None
_queue: Optional[Queue] = None


def _get_connection() -> redis.Redis:
    global _connection

    if _connection is not None:
        return _connection

    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        conn = redis.Redis.from_url(url)
        conn.ping()
    except redis.exceptions.RedisError as exc:  # pragma: no cover - connection error surface
        raise RuntimeError(f"Unable to connect to Redis at {url}: {exc}") from exc

    _connection = conn
    return conn


def _get_queue() -> Queue:
    global _queue

    if _queue is not None:
        return _queue

    conn = _get_connection()
    _queue = Queue(_QUEUE_NAME, connection=conn, default_timeout=_JOB_TIMEOUT)
    return _queue


def enqueue_capture_job(image_bytes: bytes, filename: str) -> str:
    """Enqueue a capture processing job and return the job id."""

    queue = _get_queue()
    try:
        job = queue.enqueue(
            run_capture_pipeline,
            image_bytes,
            filename,
            job_timeout=_JOB_TIMEOUT,
            result_ttl=_RESULT_TTL,
        )
    except redis.exceptions.RedisError as exc:  # pragma: no cover - surface redis errors
        raise RuntimeError(f"Failed to enqueue capture job: {exc}") from exc

    job.meta.update({"progress": 0, "message": "Queued"})
    job.save_meta()
    return job.id


def get_capture_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Return the serialized job state for the given id, if it exists."""

    queue = _get_queue()
    try:
        job = queue.fetch_job(job_id)
    except (redis.exceptions.RedisError, NoSuchJobError):
        job = None

    if job is None:
        return None

    job.refresh()

    data: Dict[str, Any] = {
        "job_id": job.id,
        "status": job.get_status(),
        "progress": int(job.meta.get("progress", 0) or 0),
        "message": job.meta.get("message"),
        "enqueued_at": _iso(job.enqueued_at),
        "started_at": _iso(job.started_at),
        "ended_at": _iso(job.ended_at),
    }

    if job.is_failed:
        data["error"] = job.meta.get("error") or job.exc_info

    if job.result is not None and job.get_status() == "finished":
        data["result"] = job.result

    return data


def run_capture_pipeline(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Worker entrypoint: process an image capture with progress updates."""

    job = get_current_job()

    def _progress(progress: int, message: str) -> None:
        if job is None:
            return
        job.meta["progress"] = int(progress)
        job.meta["message"] = message
        job.save_meta()

    try:
        result = process_capture(image_bytes, filename, progress_cb=_progress)
    except Exception as exc:
        if job is not None:
            job.meta["progress"] = 100
            job.meta["message"] = "Failed"
            job.meta["error"] = str(exc)
            job.save_meta()
        raise

    if job is not None:
        job.meta["progress"] = 100
        job.meta["message"] = "Completed"
        job.save_meta()

    return result


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.isoformat()


__all__ = [
    "enqueue_capture_job",
    "get_capture_job",
    "run_capture_pipeline",
]
