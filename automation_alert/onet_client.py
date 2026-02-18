"""O*NET Web Services API client.

Fetches all scorable attribute categories for a given SOC code.
Requires an O*NET API username/password (free at https://services.onetcenter.org/).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from .models import OnetCategory, SCORABLE_CATEGORIES


ONET_BASE_URL = "https://services.onetcenter.org/ws"

# Mapping from our category enum to O*NET API endpoint paths
_CATEGORY_ENDPOINTS: dict[OnetCategory, str] = {
    OnetCategory.TASKS: "tasks",
    OnetCategory.SKILLS: "skills",
    OnetCategory.KNOWLEDGE: "knowledge",
    OnetCategory.ABILITIES: "abilities",
    OnetCategory.WORK_ACTIVITIES: "work_activities",
    OnetCategory.DETAILED_WORK_ACTIVITIES: "detailed_work_activities",
    OnetCategory.TECHNOLOGY_SKILLS: "technology_skills",
    OnetCategory.WORK_CONTEXT: "work_context",
    OnetCategory.WORK_STYLES: "work_styles",
    OnetCategory.WORK_VALUES: "work_values",
    OnetCategory.INTERESTS: "interests",
    OnetCategory.JOB_ZONES: "job_zone",
    OnetCategory.EDUCATION: "education",
}


class OnetApiError(Exception):
    """Raised when the O*NET API returns an error."""


class OnetClient:
    """Async client for the O*NET Web Services REST API."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        base_url: str = ONET_BASE_URL,
    ):
        self.username = username or os.environ.get("ONET_USERNAME", "")
        self.password = password or os.environ.get("ONET_PASSWORD", "")
        self.base_url = base_url.rstrip("/")

    def _auth(self) -> tuple[str, str]:
        return (self.username, self.password)

    async def _get(self, path: str) -> dict[str, Any]:
        """Make an authenticated GET request to the O*NET API."""
        url = f"{self.base_url}/{path}"
        headers = {"Accept": "application/json"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                auth=self._auth(),
                headers=headers,
                timeout=30.0,
            )
            if resp.status_code != 200:
                raise OnetApiError(
                    f"O*NET API error {resp.status_code} for {url}: {resp.text}"
                )
            return resp.json()

    async def get_occupation_summary(self, soc_code: str) -> dict[str, Any]:
        """Fetch basic occupation info (title, description)."""
        return await self._get(f"online/occupations/{soc_code}")

    async def get_category(
        self, soc_code: str, category: OnetCategory
    ) -> list[dict[str, Any]]:
        """Fetch all items for a single attribute category."""
        endpoint = _CATEGORY_ENDPOINTS.get(category)
        if not endpoint:
            return []
        data = await self._get(f"online/occupations/{soc_code}/{endpoint}")
        # O*NET API wraps results in varying keys; normalize.
        for key in ("task", "skill", "knowledge", "ability",
                     "work_activity", "detailed_work_activity",
                     "technology_skill", "work_context", "work_style",
                     "work_value", "interest", "job_zone", "education",
                     "element", "category"):
            if key in data:
                items = data[key]
                return items if isinstance(items, list) else [items]
        # Fallback: return items under any list-valued key
        for v in data.values():
            if isinstance(v, list):
                return v
        return []

    async def get_all_categories(
        self, soc_code: str
    ) -> dict[OnetCategory, list[dict[str, Any]]]:
        """Fetch all scorable attribute categories for an occupation."""
        results: dict[OnetCategory, list[dict[str, Any]]] = {}
        for cat in SCORABLE_CATEGORIES:
            try:
                items = await self.get_category(soc_code, cat)
                results[cat] = items
            except OnetApiError:
                results[cat] = []
        return results

    def get_category_sync(
        self, soc_code: str, category: OnetCategory
    ) -> list[dict[str, Any]]:
        """Synchronous version of get_category."""
        endpoint = _CATEGORY_ENDPOINTS.get(category)
        if not endpoint:
            return []
        url = f"{self.base_url}/online/occupations/{soc_code}/{endpoint}"
        headers = {"Accept": "application/json"}
        resp = httpx.get(
            url, auth=self._auth(), headers=headers, timeout=30.0
        )
        if resp.status_code != 200:
            raise OnetApiError(
                f"O*NET API error {resp.status_code} for {url}: {resp.text}"
            )
        data = resp.json()
        for key in ("task", "skill", "knowledge", "ability",
                     "work_activity", "detailed_work_activity",
                     "technology_skill", "work_context", "work_style",
                     "work_value", "interest", "job_zone", "education",
                     "element", "category"):
            if key in data:
                items = data[key]
                return items if isinstance(items, list) else [items]
        for v in data.values():
            if isinstance(v, list):
                return v
        return []

    def get_all_categories_sync(
        self, soc_code: str
    ) -> dict[OnetCategory, list[dict[str, Any]]]:
        """Synchronous version of get_all_categories."""
        results: dict[OnetCategory, list[dict[str, Any]]] = {}
        for cat in SCORABLE_CATEGORIES:
            try:
                items = self.get_category_sync(soc_code, cat)
                results[cat] = items
            except OnetApiError:
                results[cat] = []
        return results
