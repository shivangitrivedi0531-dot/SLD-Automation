import math
from typing import List, Dict, Any, Optional


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


def parse_float(val: Any) -> Optional[float]:
    """Safely parse float value."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if not math.isnan(f) else None
    except (ValueError, TypeError):
        return None


def map_assets_to_route(
    assets: List[Dict[str, Any]],
    route_points: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Find the nearest surveyed route point for each asset using geographic coordinates.

    Returns a list of mapping records containing asset details and matched route point info.
    """
    # Pre-parse route points with valid coordinates
    parsed_route_points = []
    for rp in route_points:
        if not isinstance(rp, dict):
            continue
        rp_lat = parse_float(rp.get("latitude"))
        rp_lon = parse_float(rp.get("longitude"))
        if rp_lat is not None and rp_lon is not None:
            parsed_route_points.append({
                "point_id": rp.get("point_id"),
                "sequence_no": rp.get("sequence_no"),
                "lat": rp_lat,
                "lon": rp_lon,
                "raw": rp,
            })

    mapped_records = []

    for asset in assets:
        if not isinstance(asset, dict):
            continue

        asset_id = asset.get("asset_id")
        label = asset.get("label")
        asset_category = asset.get("asset_category")
        asset_type = asset.get("asset_type")
        condition_type = asset.get("condition_type")
        asset_lat = parse_float(asset.get("latitude"))
        asset_lon = parse_float(asset.get("longitude"))

        matched_point_id = None
        matched_sequence_no = None
        min_distance = None

        if asset_lat is not None and asset_lon is not None and parsed_route_points:
            best_dist = float("inf")
            best_rp = None

            for rp in parsed_route_points:
                dist = haversine_distance(asset_lat, asset_lon, rp["lat"], rp["lon"])
                if dist < best_dist:
                    best_dist = dist
                    best_rp = rp

            if best_rp is not None:
                matched_point_id = best_rp["point_id"]
                matched_sequence_no = best_rp["sequence_no"]
                min_distance = round(best_dist, 3)

        mapped_records.append({
            "asset_id": asset_id,
            "label": label,
            "asset_category": asset_category,
            "asset_type": asset_type,
            "condition_type": condition_type,
            "latitude": asset_lat,
            "longitude": asset_lon,
            "matched_route_point_id": matched_point_id,
            "matched_route_sequence_no": matched_sequence_no,
            "distance_to_route_point_m": min_distance,
        })

    return mapped_records
