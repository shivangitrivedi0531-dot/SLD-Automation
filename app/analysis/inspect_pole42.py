import os
import sys
import math
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance between two lat/lon points in meters."""
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


def run_pole42_inspection():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    # 1. Fetch assets
    assets_res = api_client.get_assets(survey_id)
    if isinstance(assets_res, dict):
        assets = assets_res.get("data", [])
        if isinstance(assets, dict):
            assets = assets.get("assets", [])
    elif isinstance(assets_res, list):
        assets = assets_res
    else:
        assets = []

    # 2. Fetch all route points
    route_points = api_client.get_all_route_points(survey_id)

    pole42_assets = [a for a in assets if isinstance(a, dict) and str(a.get("label", "")).strip().upper() == "POLE-42"]

    print("====================================================================================================")
    print("                               SURVEY 47: POLE-42 ASSET DIAGNOSTIC")
    print("====================================================================================================")

    # Pre-parse valid route points
    parsed_rps = []
    for rp in route_points:
        if isinstance(rp, dict):
            lat = parse_float(rp.get("latitude"))
            lon = parse_float(rp.get("longitude"))
            if lat is not None and lon is not None:
                parsed_rps.append({
                    "point_id": rp.get("point_id"),
                    "sequence_no": rp.get("sequence_no"),
                    "latitude": lat,
                    "longitude": lon,
                })

    for asset in pole42_assets:
        aid = asset.get("asset_id")
        label = asset.get("label")
        cond = asset.get("condition_type")
        alat = parse_float(asset.get("latitude"))
        alon = parse_float(asset.get("longitude"))

        print(f"\n--- ASSET {aid} ({label} - {cond}) ---")
        print(f"Coordinates: ({alat}, {alon})")

        # Sort route points by distance to this asset
        distances = []
        for rp in parsed_rps:
            d = haversine_distance(alat, alon, rp["latitude"], rp["longitude"])
            distances.append((d, rp))

        distances.sort(key=lambda x: x[0])

        if distances:
            nearest_dist, nearest_rp = distances[0]
            print(f"Nearest Route Point:")
            print(f"  - point_id:    {nearest_rp['point_id']}")
            print(f"  - sequence_no: {nearest_rp['sequence_no']}")
            print(f"  - distance:    {nearest_dist:.3f} meters")

            print("\n5 Nearest Route Points:")
            for rank, (dist, rp) in enumerate(distances[:5], 1):
                print(f"  {rank}. point_id: {rp['point_id']:<8} | sequence_no: {rp['sequence_no']:<6} | lat: {rp['latitude']:.7f} | lon: {rp['longitude']:.7f} | dist: {dist:.3f} m")

            # Check if asset lies between nearby route points or clearly outside
            top5_dists = [round(d[0], 3) for d in distances[:5]]
            if nearest_dist < 10.0:
                location_evaluation = "Within/Adjacent to surveyed route segment (< 10 meters)"
            else:
                location_evaluation = f"Clearly OUTSIDE the returned surveyed route (Nearest point is {nearest_dist:.3f} m away)"

            print(f"\nLocation Assessment: {location_evaluation}")
        else:
            print("No valid route points found.")

    # 7. Direct geodesic distance between the two POLE-42 assets
    if len(pole42_assets) >= 2:
        a1 = pole42_assets[0]
        a2 = pole42_assets[1]
        lat1, lon1 = parse_float(a1.get("latitude")), parse_float(a1.get("longitude"))
        lat2, lon2 = parse_float(a2.get("latitude")), parse_float(a2.get("longitude"))

        if lat1 and lon1 and lat2 and lon2:
            dist_between = haversine_distance(lat1, lon1, lat2, lon2)
            print("\n====================================================================================================")
            print(f"Direct Geodesic Distance between Asset {a1.get('asset_id')} ({a1.get('condition_type')}) and Asset {a2.get('asset_id')} ({a2.get('condition_type')}):")
            print(f"  -> {dist_between:.3f} meters ({dist_between / 1000.0:.3f} km)")
            print("====================================================================================================")


if __name__ == "__main__":
    run_pole42_inspection()
