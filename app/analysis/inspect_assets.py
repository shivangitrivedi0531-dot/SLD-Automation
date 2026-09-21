import os
import sys
from collections import Counter
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def inspect_assets():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    response = api_client.get_assets(survey_id)
    
    # Extract asset list
    if isinstance(response, dict):
        assets = response.get("data", [])
        if isinstance(assets, dict):
            assets = assets.get("assets", [])
    elif isinstance(response, list):
        assets = response
    else:
        assets = []

    print(f"=========================================================================================================================")
    print(f"                                          SURVEY {survey_id} ASSET INSPECTION TABLE")
    print(f"=========================================================================================================================")
    header = f"{'#':<4} | {'asset_id':<10} | {'label':<15} | {'asset_category':<20} | {'asset_type':<25} | {'cable_spec':<15} | {'latitude':<12} | {'longitude':<12} | {'condition_type':<15}"
    print(header)
    print("-" * len(header))

    category_counts = Counter()
    type_counts = Counter()
    with_cable_spec = 0
    without_cable_spec = 0
    valid_coords_count = 0

    for idx, asset in enumerate(assets, 1):
        if not isinstance(asset, dict):
            continue

        asset_id = str(asset.get("asset_id", ""))
        label = str(asset.get("label", ""))
        asset_category = str(asset.get("asset_category", ""))
        asset_type = str(asset.get("asset_type", ""))
        cable_spec = str(asset.get("cable_spec") or "")
        lat = asset.get("latitude")
        lon = asset.get("longitude")
        condition_type = str(asset.get("condition_type", ""))

        category_counts[asset_category or "Unknown"] += 1
        type_counts[asset_type or "Unknown"] += 1

        if cable_spec.strip():
            with_cable_spec += 1
        else:
            without_cable_spec += 1

        # Check valid coordinates
        try:
            float_lat = float(lat) if lat is not None else None
            float_lon = float(lon) if lon is not None else None
            is_valid_lat = float_lat is not None and -90 <= float_lat <= 90 and float_lat != 0
            is_valid_lon = float_lon is not None and -180 <= float_lon <= 180 and float_lon != 0
            if is_valid_lat and is_valid_lon:
                valid_coords_count += 1
        except (ValueError, TypeError):
            pass

        lat_str = f"{float(lat):.6f}" if lat is not None and isinstance(lat, (int, float)) else str(lat or "")
        lon_str = f"{float(lon):.6f}" if lon is not None and isinstance(lon, (int, float)) else str(lon or "")


        row = f"{idx:<4} | {asset_id:<10} | {label:<15} | {asset_category:<20} | {asset_type:<25} | {cable_spec:<15} | {lat_str:<12} | {lon_str:<12} | {condition_type:<15}"
        print(row)

    print("=" * len(header))
    print("\n=========================================================================================================================")
    print("                                                  SUMMARY")
    print("=========================================================================================================================")
    print(f"Total Assets: {len(assets)}")
    print("\n- Count by asset_category:")
    for cat, count in category_counts.items():
        print(f"  * {cat}: {count}")

    print("\n- Count by asset_type:")
    for atype, count in type_counts.items():
        print(f"  * {atype}: {count}")

    print(f"\n- Number with cable_spec: {with_cable_spec}")
    print(f"- Number without cable_spec: {without_cable_spec}")
    print(f"- Number with valid coordinates: {valid_coords_count}")
    print("=========================================================================================================================")


if __name__ == "__main__":
    inspect_assets()
