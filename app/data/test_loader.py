import os
import sys
from collections import Counter
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient
from app.data.loader import load_feeder_data
from app.data.models import FeederData


def test_feeder_loader():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    try:
        feeder_data = load_feeder_data(survey_id, api_client=api_client)

        success = isinstance(feeder_data, FeederData)

        meta = feeder_data.metadata
        summary = feeder_data.summary

        # Calculate asset category counts
        cat_counts = Counter(a.asset_category or "Unknown" for a in feeder_data.assets)

        print("=== FeederData Loader Test Results ===")
        print(f"1. Survey ID: {meta.survey_id}")
        print(f"2. Feeder Name: {meta.feeder_name}")
        print(f"3. Project Name: {meta.project_name}")
        print(f"4. Total Assets: {len(feeder_data.assets)}")
        print(f"5. Total Route Points: {len(feeder_data.route_points)}")
        print(f"6. Total Cable Segments: {len(feeder_data.cable_segments)}")
        print(f"7. Survey Route Distance: {meta.total_route_distance_meters} meters")
        print(f"8. Summary Route Distance: {summary.get('total_route_distance_meters')} meters")
        print(f"9. Asset Categories/Counts: {dict(cat_counts)}")
        print(f"10. FeederData Created Successfully: {success}")

    except Exception as e:
        print(f"[ERROR] Loader test failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_feeder_loader()
