import os
import sys
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def mask_sample_item(item: dict) -> dict:
    """Mask non-structure string values for safe printing (e.g. photos/urls/remarks/codes)."""
    if not isinstance(item, dict):
        return item
    masked = {}
    for k, v in item.items():
        if k in ["asset_id", "survey_id", "point_id", "sequence_no", "asset_category", "asset_type", "condition_type"]:
            masked[k] = v
        elif isinstance(v, (int, float, bool)):
            masked[k] = v
        elif v is None:
            masked[k] = None
        else:
            masked[k] = f"<{type(v).__name__}>"
    return masked


def run_survey_inspection():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()

    api_client = ERPApiClient(auth_client=auth_client)

    try:
        response_data = api_client.get(
            f"/api/geo-survey/surveys/{survey_id}",
            params={"all_points": "true"},
        )

        top_keys = list(response_data.keys()) if isinstance(response_data, dict) else []
        print("=== 1. Top-Level Keys ===")
        print(top_keys)

        data = response_data.get("data", {}) if isinstance(response_data, dict) else {}
        if not isinstance(data, dict):
            print("Data field is not a dictionary.")
            return

        data_keys = list(data.keys())
        print("\n=== 2. Keys Inside Data ===")
        print(data_keys)

        # 3. Metadata fields
        scalar_meta_fields = [k for k, v in data.items() if not isinstance(v, (dict, list))]
        print("\n=== 3. Survey Metadata Field Names ===")
        print(scalar_meta_fields)

        # 4. Assets
        assets = data.get("assets", [])
        print("\n=== 4. Assets ===")
        print(f"Asset Count: {len(assets) if isinstance(assets, list) else 0}")
        if isinstance(assets, list) and len(assets) > 0 and isinstance(assets[0], dict):
            print(f"Asset Field Names: {list(assets[0].keys())}")
            print(f"Sample Asset (Masked): {mask_sample_item(assets[0])}")

        # 5. Cable Segments
        cable_segments_exists = "cable_segments" in data
        cable_segments = data.get("cable_segments", [])
        print("\n=== 5. Cable Segments ===")
        print(f"Field Exists: {cable_segments_exists}")
        print(f"Cable Segments Count: {len(cable_segments) if isinstance(cable_segments, list) else 0}")
        if isinstance(cable_segments, list) and len(cable_segments) > 0 and isinstance(cable_segments[0], dict):
            print(f"Cable Segment Field Names: {list(cable_segments[0].keys())}")
        else:
            print("Cable Segment Field Names: None (empty list)")

        # 6. Route Points
        route_points = data.get("route_points", [])
        print("\n=== 6. Route Points ===")
        print(f"Route Points Count: {len(route_points) if isinstance(route_points, list) else 0}")
        if isinstance(route_points, list) and len(route_points) > 0 and isinstance(route_points[0], dict):
            print(f"Route Point Field Names: {list(route_points[0].keys())}")
            print(f"Sample Route Point: {mask_sample_item(route_points[0])}")

        # 7. Summary
        summary = data.get("summary", {})
        print("\n=== 7. Summary ===")
        if isinstance(summary, dict):
            print(f"Summary Field Names: {list(summary.keys())}")
            numeric_summary = {k: v for k, v in summary.items() if isinstance(v, (int, float, dict))}
            print(f"Summary Safe Numeric/Count Fields: {numeric_summary}")

        # 8. Specific Field Identification Mapping
        print("\n=== 8. Specific Field Identification ===")
        all_keys_flattened = set(data_keys)
        if isinstance(assets, list) and assets:
            all_keys_flattened.update(assets[0].keys())
        if isinstance(route_points, list) and route_points:
            all_keys_flattened.update(route_points[0].keys())

        print(f"- Asset ID: {'asset_id' in all_keys_flattened} (key: asset_id)")
        print(f"- Asset Name / Label: {'asset_category' in all_keys_flattened or 'label' in all_keys_flattened} (keys: asset_category, label)")
        print(f"- Asset Type/Category: {'asset_type' in all_keys_flattened} (keys: asset_category, asset_type)")
        print(f"- Latitude: {'latitude' in all_keys_flattened} (key: latitude in assets & route_points)")
        print(f"- Longitude: {'longitude' in all_keys_flattened} (key: longitude in assets & route_points)")
        print(f"- Sequence/Order: {'sequence_no' in all_keys_flattened} (key: sequence_no in route_points)")
        print(f"- From Asset / To Asset: {'from_ss_name' in all_keys_flattened or 'to_ss_name' in all_keys_flattened} (from_ss_name, to_ss_name in metadata)")
        print(f"- Cable Length/Distance: {'total_route_distance_meters' in all_keys_flattened} (key: total_route_distance_meters in metadata & summary)")
        print(f"- Cable Type/Size: {'cable_spec' in all_keys_flattened or 'cable_name' in all_keys_flattened} (keys: cable_spec in assets; cable_name/cable_lengths in summary)")
        print(f"- Route Point Sequence: {'sequence_no' in all_keys_flattened} (key: sequence_no in route_points)")

    except Exception as e:
        print(f"[ERROR] Inspection failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    run_survey_inspection()