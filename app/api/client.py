import os
import logging
from typing import Optional, Dict, Any, List
import requests
from app.api.auth_client import ERPAuthClient

logger = logging.getLogger(__name__)


class ERPApiClient:
    """Authenticated API client for ERP API endpoints."""

    def __init__(
        self,
        auth_client: Optional[ERPAuthClient] = None,
        base_url: Optional[str] = None,
    ):
        self.auth_client = auth_client or ERPAuthClient(base_url=base_url)
        self.base_url = self.auth_client.base_url

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Perform an authenticated GET request to any given endpoint path.

        - Uses access token obtained from ERPAuthClient.
        - Sends Authorization: Bearer <accessToken> and Accept: application/json headers.
        - Accepts an endpoint path and optional query parameters.
        - Returns parsed JSON response.
        - Never logs or exposes the access token.
        """
        if not self.auth_client.is_authenticated:
            self.auth_client.login()

        headers = self.auth_client.get_auth_headers()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("API GET request failed for endpoint %s: %s", endpoint, str(e))
            raise

    def get_survey(
        self,
        survey_id: str,
        all_points: bool = True,
    ) -> Dict[str, Any]:
        """Fetch complete survey details for a given survey_id.

        Calls: GET /api/geo-survey/surveys/{survey_id}?all_points=true
        """
        params = {"all_points": "true" if all_points else "false"}
        return self.get(f"/api/geo-survey/surveys/{survey_id}", params=params)

    def get_assets(self, survey_id: str) -> Dict[str, Any]:
        """Fetch assets list for a given survey_id.

        Calls: GET /api/geo-survey/surveys/{survey_id}/assets
        """
        return self.get(f"/api/geo-survey/surveys/{survey_id}/assets")

    def get_cable_segments(self, survey_id: str) -> Dict[str, Any]:
        """Fetch cable segments list for a given survey_id.

        Calls: GET /api/geo-survey/surveys/{survey_id}/cable-segments
        """
        return self.get(f"/api/geo-survey/surveys/{survey_id}/cable-segments")

    def get_route_points(
        self,
        survey_id: str,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fetch route points list for a given survey_id.

        Calls: GET /api/geo-survey/surveys/{survey_id}/route-points
        Accepts optional page and limit query parameters.
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return self.get(
            f"/api/geo-survey/surveys/{survey_id}/route-points",
            params=params if params else None,
        )

    def get_all_route_points(self, survey_id: str) -> List[Dict[str, Any]]:
        """Fetch and combine all paginated route points for a given survey_id.

        Requests page 1, reads total_pages from pagination metadata, fetches
        remaining pages, and returns the combined list of route points in order.
        """
        first_page_res = self.get_route_points(survey_id, page=1)
        data = first_page_res.get("data", {}) if isinstance(first_page_res, dict) else {}

        all_points: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            points = data.get("points", [])
            if isinstance(points, list):
                all_points.extend(points)

            pagination = data.get("pagination", {})
            total_pages = pagination.get("total_pages", 1) if isinstance(pagination, dict) else 1

            for p in range(2, total_pages + 1):
                page_res = self.get_route_points(survey_id, page=p)
                page_data = page_res.get("data", {}) if isinstance(page_res, dict) else {}
                if isinstance(page_data, dict):
                    p_points = page_data.get("points", [])
                    if isinstance(p_points, list):
                        all_points.extend(p_points)
        elif isinstance(first_page_res, list):
            all_points.extend(first_page_res)

        return all_points

    def get_summary(self, survey_id: str) -> Dict[str, Any]:
        """Fetch summary for a given survey_id.

        Calls: GET /api/geo-survey/surveys/{survey_id}/summary
        """
        return self.get(f"/api/geo-survey/surveys/{survey_id}/summary")






