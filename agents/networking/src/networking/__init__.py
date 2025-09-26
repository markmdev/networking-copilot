"""Networking crew package."""

from networking.api import app  # re-export FastAPI app for uvicorn entrypoint

__all__ = ["app"]
