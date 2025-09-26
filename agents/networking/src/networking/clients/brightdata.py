"""Bright Data dataset clients for retrieving LinkedIn information."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import httpx


class BrightDataError(RuntimeError):
    """Raised when a Bright Data API call fails."""


class BrightDataDatasetClient:
    """Generic helper for interacting with a Bright Data dataset."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        dataset_id: Optional[str] = None,
        base_url: str = "https://api.brightdata.com/datasets/v3",
        poll_interval: float = 2.0,
        timeout: float = 180.0,
    ) -> None:
        self.api_key = api_key or os.getenv("BRIGHTDATA_API_KEY")
        if not self.api_key:
            raise ValueError("BRIGHTDATA_API_KEY is required to call Bright Data API")

        self.dataset_id = dataset_id
        if not self.dataset_id:
            raise ValueError("Dataset ID is required to call Bright Data API")

        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self.timeout = timeout

    # ------------------------------------------------------------------
    def trigger_snapshot(
        self,
        payload: List[Dict[str, Any]],
        *,
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        endpoint = f"{self.base_url}/trigger"
        params: Dict[str, Any] = {
            "dataset_id": self.dataset_id,
        }
        if include_errors:
            params["include_errors"] = "true"
        if extra_params:
            params.update(extra_params)

        response = self._request("POST", endpoint, params=params, json=payload)
        snapshot_id = response.get("snapshot_id")
        if not snapshot_id:
            raise BrightDataError("Bright Data trigger response missing snapshot_id")
        return snapshot_id

    def wait_for_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/progress/{snapshot_id}"
        deadline = time.monotonic() + self.timeout

        while True:
            response = self._request("GET", endpoint)
            status = response.get("status")
            if status == "ready":
                return response
            if status in {"failed", "error"}:
                raise BrightDataError(
                    f"Snapshot {snapshot_id} failed with status {status}: {response}"
                )
            if time.monotonic() >= deadline:
                raise BrightDataError(
                    f"Timed out waiting for snapshot {snapshot_id} to become ready"
                )
            time.sleep(self.poll_interval)

    def download_snapshot(self, snapshot_id: str) -> List[Dict[str, Any]]:
        endpoint = f"{self.base_url}/snapshot/{snapshot_id}"
        params = {"format": "json"}
        response = self._request("GET", endpoint, params=params)
        if not isinstance(response, list):
            raise BrightDataError("Snapshot response is not a list of records")
        return response

    # ------------------------------------------------------------------
    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        headers = self._headers(kwargs.pop("headers", None))
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.request(method, url, headers=headers, **kwargs)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network failure
            raise BrightDataError(
                f"Bright Data API responded with status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            raise BrightDataError(f"Bright Data API request failed: {exc}") from exc

        try:
            return resp.json()
        except ValueError as exc:
            raise BrightDataError("Bright Data API returned non-JSON response") from exc

    def _headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers


class LinkedInFetcher(BrightDataDatasetClient):
    """Client that orchestrates LinkedIn profile retrieval via Bright Data datasets."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        dataset_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        dataset_id = dataset_id or os.getenv("BRIGHTDATA_DATASET_ID")
        super().__init__(api_key=api_key, dataset_id=dataset_id, **kwargs)

    def fetch_profile(self, url: str) -> Dict[str, Any]:
        """Fetch structured LinkedIn data for the provided profile URL."""

        snapshot_id = self.trigger_snapshot([{"url": url}])
        progress = self.wait_for_snapshot(snapshot_id)

        if progress.get("status") != "ready":
            raise BrightDataError(
                f"Snapshot {snapshot_id} did not reach ready state (status={progress.get('status')})"
            )

        records = self.download_snapshot(snapshot_id)
        return {
            "snapshot_id": snapshot_id,
            "dataset_id": self.dataset_id,
            "status": progress.get("status"),
            "errors": progress.get("errors", 0),
            "records": records,
        }


class LinkedInSearchClient(BrightDataDatasetClient):
    """Client that performs LinkedIn people search via Bright Data datasets."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        dataset_id: Optional[str] = None,
        default_search_url: str = "https://www.linkedin.com",
        **kwargs: Any,
    ) -> None:
        dataset_id = dataset_id or os.getenv("BRIGHTDATA_SEARCH_DATASET_ID")
        super().__init__(api_key=api_key, dataset_id=dataset_id, **kwargs)
        self.default_search_url = default_search_url

    def search_people(
        self,
        first_name: str,
        last_name: str,
        *,
        search_url: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "url": search_url or self.default_search_url,
            "first_name": first_name,
            "last_name": last_name,
        }
        if additional_fields:
            payload.update({k: v for k, v in additional_fields.items() if v})

        snapshot_id = self.trigger_snapshot([payload])

        try:
            progress = self.wait_for_snapshot(snapshot_id)
        except BrightDataError:
            # Some datasets may not expose a progress endpoint; fall back to polling snapshots.
            progress = {"status": "unknown"}

        records = self._download_snapshot_with_retry(snapshot_id)
        return {
            "snapshot_id": snapshot_id,
            "dataset_id": self.dataset_id,
            "status": progress.get("status"),
            "errors": progress.get("errors", 0),
            "records": records,
        }

    def _download_snapshot_with_retry(self, snapshot_id: str) -> List[Dict[str, Any]]:
        deadline = time.monotonic() + self.timeout
        last_error: Optional[BrightDataError] = None

        while True:
            try:
                return self.download_snapshot(snapshot_id)
            except BrightDataError as exc:  # pragma: no cover - network timing
                last_error = exc

            if time.monotonic() >= deadline:
                raise last_error or BrightDataError(
                    f"Timed out downloading snapshot {snapshot_id}"
                )

            time.sleep(self.poll_interval)
