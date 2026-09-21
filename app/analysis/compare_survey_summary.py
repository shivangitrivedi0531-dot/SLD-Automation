import os
import sys
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def compare_summary():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    survey_response = api_client.get_survey(survey_id, all_points=True)
    summary_response = api_client.get_summary(survey_id)

    survey_data = survey_response.get("data", {}) if isinstance(survey_response, dict) else {}
    summary_data = summary_response.get("data", {}) if isinstance(summary_response, dict) else {}

    # Extract fields from get_survey()
    survey_summary_field = survey_data.get("summary", {}) if isinstance(survey_data, dict) else {}

    survey_total_dist = survey_data.get("total_route_distance_meters")
    survey_total_assets = survey_data.get("total_assets_count") or len(survey_data.get("assets", []))
    survey_cable_name = survey_data.get("cable_name")
    survey_cable_lengths = survey_summary_field.get("cable_lengths") if isinstance(survey_summary_field, dict) else None
    survey_total_points_count = survey_data.get("total_route_points_count") or len(survey_data.get("route_points", []))
    survey_status = survey_data.get("status")
    survey_updated_at = survey_data.get("updated_at")

    # Additional related route-distance fields in survey_data
    survey_distance_related = {
        k: v for k, v in survey_data.items()
        if ("distance" in k or "length" in k or "dist" in k) and not isinstance(v, (dict, list))
    }
    if isinstance(survey_summary_field, dict):
        for k, v in survey_summary_field.items():
            if ("distance" in k or "length" in k or "dist" in k) and not isinstance(v, (dict, list)):
                survey_distance_related[f"summary.{k}"] = v

    # Extract fields from get_summary()
    summary_total_dist = summary_data.get("total_route_distance_meters") if isinstance(summary_data, dict) else None
    summary_total_assets = summary_data.get("total_assets") if isinstance(summary_data, dict) else None
    summary_cable_name = summary_data.get("cable_name") if isinstance(summary_data, dict) else None
    summary_cable_lengths = summary_data.get("cable_lengths") if isinstance(summary_data, dict) else None
    summary_total_points_count = summary_data.get("total_route_points_count") if isinstance(summary_data, dict) else None
    summary_status = summary_data.get("status") if isinstance(summary_data, dict) else None
    summary_updated_at = summary_data.get("updated_at") if isinstance(summary_data, dict) else None

    summary_distance_related = {}
    if isinstance(summary_data, dict):
        summary_distance_related = {
            k: v for k, v in summary_data.items()
            if ("distance" in k or "length" in k or "dist" in k) and not isinstance(v, (dict, list))
        }

    print("=================================================================")
    print("      SURVEY 47 ENDPOINT COMPARISON: GET /surveys/47 vs GET /surveys/47/summary")
    print("=================================================================")

    print("\n--- 1. Route Distance ---")
    print(f"  GET /surveys/47 (all_points=true):  {survey_total_dist} meters")
    print(f"  GET /surveys/47/summary:            {summary_total_dist} meters")
    print(f"  Related Distance Fields (Survey):  {survey_distance_related}")
    print(f"  Related Distance Fields (Summary): {summary_distance_related}")

    print("\n--- 2. Total Assets ---")
    print(f"  GET /surveys/47 (all_points=true):  {survey_total_assets}")
    print(f"  GET /surveys/47/summary:            {summary_total_assets}")

    print("\n--- 3. Cable Name ---")
    print(f"  GET /surveys/47 (all_points=true):  {survey_cable_name}")
    print(f"  GET /surveys/47/summary:            {summary_cable_name}")

    print("\n--- 4. Cable Lengths Break-down ---")
    print(f"  GET /surveys/47 (all_points=true):  {survey_cable_lengths}")
    print(f"  GET /surveys/47/summary:            {summary_cable_lengths}")

    print("\n--- 5. Total Route Points Count ---")
    print(f"  GET /surveys/47 (all_points=true):  {survey_total_points_count}")
    print(f"  GET /surveys/47/summary:            {summary_total_points_count}")

    print("\n--- 6. Status & Updated At ---")
    print(f"  GET /surveys/47 Status:             {survey_status}")
    print(f"  GET /surveys/47 Updated At:         {survey_updated_at}")
    print(f"  GET /surveys/47/summary Status:     {summary_status}")
    print(f"  GET /surveys/47/summary Updated At: {summary_updated_at}")

    print("=================================================================")


if __name__ == "__main__":
    compare_summary()
