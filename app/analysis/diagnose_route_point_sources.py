import os
import sys
import math
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient
from app.analysis.asset_route_mapping import haversine_distance, parse_float


def run_route_point_source_comparison():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    print("=== 1. Fetching Data from Both Endpoints ===")
    survey_response = api_client.get_survey(survey_id, all_points=True)
    survey_data = survey_response.get("data", {}) if isinstance(survey_response, dict) else {}
    survey_rp_list = survey_data.get("route_points", []) if isinstance(survey_data, dict) else []

    total_route_points_count_meta = survey_data.get("total_route_points_count")
    is_downsampled_meta = survey_data.get("is_downsampled")

    dedicated_rp_list = api_client.get_all_route_points(survey_id)

    print(f"1. Route point count from GET /surveys/47 (all_points=true): {len(survey_rp_list)}")
    print(f"2. total_route_points_count from survey metadata: {total_route_points_count_meta}")
    print(f"3. is_downsampled from survey metadata: {is_downsampled_meta}")
    print(f"4. Total points returned by GET /surveys/47/route-points: {len(dedicated_rp_list)}")

    print("\n=== 2. Checking Existence of Point IDs 137649 and 137749 ===")
    survey_rp_dict = {p.get("point_id"): p for p in survey_rp_list if isinstance(p, dict)}
    dedicated_rp_dict = {p.get("point_id"): p for p in dedicated_rp_list if isinstance(p, dict)}

    print(f"5. point_id 137649 in survey endpoint route_points: {137649 in survey_rp_dict}")
    print(f"   point_id 137649 in dedicated route-points endpoint: {137649 in dedicated_rp_dict}")

    print(f"6. point_id 137749 in survey endpoint route_points: {137749 in survey_rp_dict}")
    print(f"   point_id 137749 in dedicated route-points endpoint: {137749 in dedicated_rp_dict}")

    # Details of point 137649 if present
    if 137649 in survey_rp_dict:
        pt = survey_rp_dict[137649]
        print(f"   Details of 137649 (Survey endpoint): point_id={pt.get('point_id')}, sequence_no={pt.get('sequence_no')}, lat={pt.get('latitude')}, lon={pt.get('longitude')}")

    if 137749 in dedicated_rp_dict:
        pt = dedicated_rp_dict[137749]
        print(f"   Details of 137749 (Dedicated endpoint): point_id={pt.get('point_id')}, sequence_no={pt.get('sequence_no')}, lat={pt.get('latitude')}, lon={pt.get('longitude')}")

    print("\n=== 3. Nearest Point Calculation for Asset 183 (POLE-42) ===")
    asset_183_lat = 22.9996033
    asset_183_lon = 70.1056317
    print(f"Asset 183 Coordinates: ({asset_183_lat}, {asset_183_lon})")

    # Nearest in survey endpoint
    best_survey_pt = None
    best_survey_dist = float("inf")
    for pt in survey_rp_list:
        lat = parse_float(pt.get("latitude"))
        lon = parse_float(pt.get("longitude"))
        if lat is not None and lon is not None:
            dist = haversine_distance(asset_183_lat, asset_183_lon, lat, lon)
            if dist < best_survey_dist:
                best_survey_dist = dist
                best_survey_pt = pt

    print(f"7. Nearest in GET /surveys/47 (all_points=true):")
    if best_survey_pt:
        print(f"   point_id: {best_survey_pt.get('point_id')}")
        print(f"   sequence_no: {best_survey_pt.get('sequence_no')}")
        print(f"   lat: {best_survey_pt.get('latitude')}, lon: {best_survey_pt.get('longitude')}")
        print(f"   distance: {best_survey_dist:.3f} meters")

    # Nearest in dedicated endpoint
    best_dedicated_pt = None
    best_dedicated_dist = float("inf")
    for pt in dedicated_rp_list:
        lat = parse_float(pt.get("latitude"))
        lon = parse_float(pt.get("longitude"))
        if lat is not None and lon is not None:
            dist = haversine_distance(asset_183_lat, asset_183_lon, lat, lon)
            if dist < best_dedicated_dist:
                best_dedicated_dist = dist
                best_dedicated_pt = pt

    print(f"8. Nearest in GET /surveys/47/route-points:")
    if best_dedicated_pt:
        print(f"   point_id: {best_dedicated_pt.get('point_id')}")
        print(f"   sequence_no: {best_dedicated_pt.get('sequence_no')}")
        print(f"   lat: {best_dedicated_pt.get('latitude')}, lon: {best_dedicated_pt.get('longitude')}")
        print(f"   distance: {best_dedicated_dist:.3f} meters")

    print("\n=== 4. Sequence Numbers Around Asset 183 ===")
    if best_survey_pt:
        s_seq = best_survey_pt.get("sequence_no")
        print(f"Survey endpoint nearest sequence_no: {s_seq}")
    if best_dedicated_pt:
        d_seq = best_dedicated_pt.get("sequence_no")
        print(f"Dedicated endpoint nearest sequence_no: {d_seq}")

    # Print points around sequence_no from both sources if possible
    print("\n   [Points near 137649 in Survey Endpoint]:")
    if best_survey_pt:
        s_target_seq = best_survey_pt.get("sequence_no")
        nearby_survey = [p for p in survey_rp_list if isinstance(p, dict) and abs(p.get("sequence_no", 0) - s_target_seq) <= 2]
        for p in nearby_survey:
            d = haversine_distance(asset_183_lat, asset_183_lon, parse_float(p.get("latitude")), parse_float(p.get("longitude")))
            print(f"   - point_id={p.get('point_id')}, sequence_no={p.get('sequence_no')}, lat={p.get('latitude')}, lon={p.get('longitude')}, dist_to_asset183={d:.3f}m")

    print("\n   [Points near 137749 in Dedicated Endpoint]:")
    if best_dedicated_pt:
        d_target_seq = best_dedicated_pt.get("sequence_no")
        nearby_dedicated = [p for p in dedicated_rp_list if isinstance(p, dict) and abs(p.get("sequence_no", 0) - d_target_seq) <= 2]
        for p in nearby_dedicated:
            d = haversine_distance(asset_183_lat, asset_183_lon, parse_float(p.get("latitude")), parse_float(p.get("longitude")))
            print(f"   - point_id={p.get('point_id')}, sequence_no={p.get('sequence_no')}, lat={p.get('latitude')}, lon={p.get('longitude')}, dist_to_asset183={d:.3f}m")

    print("\n=== 5. Downsampling / Subset Evaluation ===")
    survey_point_ids = set(survey_rp_dict.keys())
    dedicated_point_ids = set(dedicated_rp_dict.keys())

    is_subset = survey_point_ids.issubset(dedicated_point_ids)
    intersection_count = len(survey_point_ids.intersection(dedicated_point_ids))
    only_in_survey = len(survey_point_ids - dedicated_point_ids)
    only_in_dedicated = len(dedicated_point_ids - survey_point_ids)

    print(f"10. Are survey endpoint route_points a subset of dedicated endpoint route_points? {is_subset}")
    print(f"    - Points in both endpoints: {intersection_count}")
    print(f"    - Points ONLY in survey endpoint (GET /surveys/47): {only_in_survey}")
    print(f"    - Points ONLY in dedicated endpoint (GET /surveys/47/route-points): {only_in_dedicated}")


if __name__ == "__main__":
    run_route_point_source_comparison()
