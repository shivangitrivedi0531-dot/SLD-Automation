import os
import sys
import math
from dotenv import load_dotenv

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def parse_float(val):
    if val is None:
        return None
    try:
        f = float(val)
        return f if not math.isnan(f) else None
    except (ValueError, TypeError):
        return None


def find_nearest_point(target_lat: float, target_lon: float, points: list):
    best_point = None
    min_dist = float("inf")
    for pt in points:
        if not isinstance(pt, dict):
            continue
        lat = parse_float(pt.get("latitude"))
        lon = parse_float(pt.get("longitude"))
        if lat is not None and lon is not None:
            dist = haversine_distance(target_lat, target_lon, lat, lon)
            if dist < min_dist:
                min_dist = dist
                best_point = pt
    return best_point, min_dist


def main():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    # Endpoint A: GET /api/geo-survey/surveys/47?all_points=true
    response_a = api_client.get_survey(survey_id, all_points=True)
    data_a = response_a.get("data", {}) if isinstance(response_a, dict) else {}
    points_a = data_a.get("route_points", []) if isinstance(data_a, dict) else []
    total_route_points_count_a = data_a.get("total_route_points_count") if isinstance(data_a, dict) else None
    is_downsampled_a = data_a.get("is_downsampled") if isinstance(data_a, dict) else None

    # Endpoint B: GET /api/geo-survey/surveys/47/route-points (all paginated pages)
    points_b = api_client.get_all_route_points(survey_id)

    # Check point_id existence (normalize to string keys for robust lookup)
    dict_a = {str(p.get("point_id")): p for p in points_a if isinstance(p, dict) and p.get("point_id") is not None}
    dict_b = {str(p.get("point_id")): p for p in points_b if isinstance(p, dict) and p.get("point_id") is not None}

    p137649_in_a = "137649" in dict_a
    p137649_in_b = "137649" in dict_b
    p137749_in_a = "137749" in dict_a
    p137749_in_b = "137749" in dict_b


    # Asset 183 coordinates (POLE-42)
    assets = data_a.get("assets", []) if isinstance(data_a, dict) else []
    asset_183 = next((a for a in assets if isinstance(a, dict) and str(a.get("asset_id")) == "183"), None)

    if asset_183:
        asset_lat = parse_float(asset_183.get("latitude"))
        asset_lon = parse_float(asset_183.get("longitude"))
    else:
        # Fallback to known Asset 183 coordinates if not found
        asset_lat = 22.9996033
        asset_lon = 70.1056317

    nearest_a, dist_a = find_nearest_point(asset_lat, asset_lon, points_a) if asset_lat and asset_lon else (None, None)
    nearest_b, dist_b = find_nearest_point(asset_lat, asset_lon, points_b) if asset_lat and asset_lon else (None, None)

    # Print required output
    print(f"1. Route-point count from Endpoint A (GET /surveys/47?all_points=true): {len(points_a)}")
    print(f"2. total_route_points_count from Endpoint A: {total_route_points_count_a}")
    print(f"3. is_downsampled from Endpoint A: {is_downsampled_a}")
    print(f"4. Total route-point count from Endpoint B (GET /surveys/47/route-points): {len(points_b)}")
    print(f"5. point_id 137649 exists in Endpoint A: {p137649_in_a}, in Endpoint B: {p137649_in_b}")
    print(f"6. point_id 137749 exists in Endpoint A: {p137749_in_a}, in Endpoint B: {p137749_in_b}")
    print("\n7 & 8. Nearest Route Point for Asset ID 183 (POLE-42):")
    if nearest_a:
        print(f"   - Endpoint A: nearest_point_id={nearest_a.get('point_id')}, sequence_no={nearest_a.get('sequence_no')}, distance_m={dist_a:.3f}")
    else:
        print("   - Endpoint A: None")

    if nearest_b:
        print(f"   - Endpoint B: nearest_point_id={nearest_b.get('point_id')}, sequence_no={nearest_b.get('sequence_no')}, distance_m={dist_b:.3f}")
    else:
        print("   - Endpoint B: None")

    print("\n9. Coordinates of route points 137649 and 137749:")
    if p137649_in_a or p137649_in_b:
        pt = dict_a.get("137649") or dict_b.get("137649")
        print(f"   - point_id 137649: latitude={pt.get('latitude')}, longitude={pt.get('longitude')}")
    else:
        print("   - point_id 137649: Does not exist in responses from either endpoint")

    if p137749_in_a or p137749_in_b:
        pt = dict_a.get("137749") or dict_b.get("137749")
        print(f"   - point_id 137749: latitude={pt.get('latitude')}, longitude={pt.get('longitude')}")
    else:
        print("   - point_id 137749: Does not exist in responses from either endpoint")



if __name__ == "__main__":
    main()
