import os
import sys
from dotenv import load_dotenv

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def test_get_cable_segments():
    load_dotenv()

    survey_id = "47"
    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    try:
        response_data = api_client.get_cable_segments(survey_id)
        http_status = 200
        success = True

        if isinstance(response_data, dict):
            top_level_keys = list(response_data.keys())
            if "cable_segments" in response_data:
                segments = response_data["cable_segments"]
            elif "data" in response_data:
                data = response_data["data"]
                if isinstance(data, list):
                    segments = data
                elif isinstance(data, dict):
                    segments = data.get("cable_segments", [])
                else:
                    segments = []
            else:
                segments = []
        elif isinstance(response_data, list):
            top_level_keys = []
            segments = response_data
        else:
            top_level_keys = []
            segments = []

        cable_segment_count = len(segments) if isinstance(segments, list) else 0

        print(f"HTTP Status: {http_status}")
        print(f"Success/Failure: Success")
        print(f"Top-Level Response Keys: {top_level_keys}")
        print(f"Cable Segment Count: {cable_segment_count}")

    except Exception as e:
        http_status = getattr(getattr(e, "response", None), "status_code", "Error")
        print(f"HTTP Status: {http_status}")
        print("Success/Failure: Failure")
        print("Top-Level Response Keys: None")
        print("Cable Segment Count: 0")


if __name__ == "__main__":
    test_get_cable_segments()
