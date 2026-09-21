import os
import sys
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def test_paginated_route_points():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    # 1. Fetch initial page to inspect pagination metadata & per-page counts
    first_res = api_client.get_route_points(survey_id, page=1)
    data = first_res.get("data", {}) if isinstance(first_res, dict) else {}
    pagination = data.get("pagination", {}) if isinstance(data, dict) else {}

    total_pages = pagination.get("total_pages", 1)
    total_points = pagination.get("total_points", 0)

    points_per_page = []
    for p in range(1, total_pages + 1):
        res = api_client.get_route_points(survey_id, page=p)
        p_data = res.get("data", {}) if isinstance(res, dict) else {}
        pts = p_data.get("points", []) if isinstance(p_data, dict) else []
        points_per_page.append(len(pts))

    # 2. Fetch all combined route points using get_all_route_points()
    combined_points = api_client.get_all_route_points(survey_id)
    combined_count = len(combined_points)

    first_seq = combined_points[0].get("sequence_no") if combined_count > 0 and isinstance(combined_points[0], dict) else None
    last_seq = combined_points[-1].get("sequence_no") if combined_count > 0 and isinstance(combined_points[-1], dict) else None
    count_matches = (combined_count == total_points)

    print(f"Total Pages: {total_pages}")
    print(f"Points Returned Per Page: {points_per_page}")
    print(f"Combined Point Count: {combined_count}")
    print(f"First Point sequence_no: {first_seq}")
    print(f"Last Point sequence_no: {last_seq}")
    print(f"Combined Count Matches total_points: {count_matches}")


if __name__ == "__main__":
    test_paginated_route_points()
