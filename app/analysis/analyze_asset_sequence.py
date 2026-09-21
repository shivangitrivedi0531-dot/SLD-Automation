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
    """Calculate the great circle distance between two points on Earth in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def run_asset_sequence_analysis(survey_id: str = "47"):
    load_dotenv()

    print(f"=== Fetching Survey ID {survey_id} ===")
    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    response_data = api_client.get(
        f"/api/geo-survey/surveys/{survey_id}",
        params={"all_points": "true"},
    )

    data = response_data.get("data", {}) if isinstance(response_data, dict) else {}
    assets_raw = data.get("assets", [])
    route_points_raw = data.get("route_points", [])

    print(f"Loaded {len(assets_raw)} assets and {len(route_points_raw)} route points.\n")

    # 1. Inspect Route Points & Check Duplicate Sequence Numbers
    route_points = []
    seq_counts = {}
    duplicate_seqs = []

    for idx, rp in enumerate(route_points_raw):
        try:
            lat = float(rp["latitude"])
            lon = float(rp["longitude"])
            seq = int(rp.get("sequence_no", idx + 1))
            route_points.append({
                "point_id": rp.get("point_id"),
                "sequence_no": seq,
                "latitude": lat,
                "longitude": lon,
                "original_idx": idx
            })
            seq_counts[seq] = seq_counts.get(seq, 0) + 1
            if seq_counts[seq] == 2:
                duplicate_seqs.append(seq)
        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Invalid route point at index {idx}: {rp}")

    # Sort route points strictly by sequence_no
    route_points.sort(key=lambda x: x["sequence_no"])

    # 2. Pre-calculate Cumulative Route Distance along Route Points
    cum_distances = [0.0] * len(route_points)
    for i in range(1, len(route_points)):
        p1 = route_points[i - 1]
        p2 = route_points[i]
        d = haversine_distance(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        cum_distances[i] = cum_distances[i - 1] + d

    # 3. Match Assets to Nearest Route Point
    matched_assets = []
    unmatched_assets = []
    far_assets = []  # distance > 30m threshold

    for a_idx, asset in enumerate(assets_raw):
        asset_id = asset.get("asset_id", f"unknown_{a_idx}")
        category = asset.get("asset_category", "")
        asset_type = asset.get("asset_type", "")
        label = asset.get("label") or ""

        try:
            a_lat = float(asset["latitude"])
            a_lon = float(asset["longitude"])
        except (ValueError, TypeError, KeyError):
            unmatched_assets.append({
                "asset_id": asset_id,
                "reason": "Missing or invalid lat/lon"
            })
            continue

        # Find nearest route point
        min_dist = float("inf")
        best_rp_idx = -1

        for r_idx, rp in enumerate(route_points):
            dist = haversine_distance(a_lat, a_lon, rp["latitude"], rp["longitude"])
            if dist < min_dist:
                min_dist = dist
                best_rp_idx = r_idx

        if best_rp_idx != -1:
            best_rp = route_points[best_rp_idx]
            cum_dist = cum_distances[best_rp_idx]

            matched = {
                "asset_id": asset_id,
                "asset_category": category,
                "asset_type": asset_type,
                "label": str(label) if label else "<str>",
                "matched_route_idx": best_rp_idx,
                "matched_route_sequence": best_rp["sequence_no"],
                "dist_to_route_m": round(min_dist, 2),
                "cum_dist_m": cum_dist,
                "lat": a_lat,
                "lon": a_lon,
            }
            matched_assets.append(matched)

            if min_dist > 30.0:  # Threshold for "very far from route"
                far_assets.append(matched)
        else:
            unmatched_assets.append({
                "asset_id": asset_id,
                "reason": "No route points available"
            })

    # 4. Sort Matched Assets by Position Along Route (cum_dist_m / matched_route_sequence)
    matched_assets.sort(key=lambda x: (x["matched_route_idx"], x["dist_to_route_m"]))

    # 5. Check Duplicate Asset Positions (multiple assets matched to same route point sequence)
    route_seq_to_assets = {}
    for m in matched_assets:
        seq = m["matched_route_sequence"]
        route_seq_to_assets.setdefault(seq, []).append(m["asset_id"])

    duplicate_asset_positions = {seq: aids for seq, aids in route_seq_to_assets.items() if len(aids) > 1}

    # 6. Calculate distance_from_previous_m
    for i, asset in enumerate(matched_assets):
        if i == 0:
            asset["distance_from_previous_m"] = 0.0
        else:
            prev_asset = matched_assets[i - 1]
            route_dist = asset["cum_dist_m"] - prev_asset["cum_dist_m"]
            asset["distance_from_previous_m"] = round(route_dist, 2)

    # 7. Print Table of Sorted Assets
    print("=== ASSET SEQUENCE TABLE (Sorted by Route Position) ===")
    header = f"{'Seq':<5} | {'Asset ID':<10} | {'Category':<12} | {'Asset Type':<22} | {'Label':<15} | {'Route Seq':<10} | {'Dist to Rp(m)':<13} | {'Dist Prev(m)':<12}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    for idx, m in enumerate(matched_assets, start=1):
        row = f"{idx:<5} | {str(m['asset_id']):<10} | {str(m['asset_category']):<12} | {str(m['asset_type'])[:22]:<22} | {str(m['label'])[:15]:<15} | {m['matched_route_sequence']:<10} | {m['dist_to_route_m']:<13.2f} | {m['distance_from_previous_m']:<12.2f}"
        print(row)

    print("-" * len(header))

    # 8. Report Problems / Anomaly Summary
    print("\n=== ANOMALY & PROBLEM REPORT ===")
    
    print(f"\n1. Duplicate Route Sequence Numbers in Route Points:")
    if duplicate_seqs:
        print(f"   [FOUND] {len(duplicate_seqs)} duplicate sequence numbers: {duplicate_seqs[:10]}")
    else:
        print("   [NONE] Route sequence numbers are unique and monotonic.")

    print(f"\n2. Unmatched Assets (Missing/Invalid Coordinates):")
    if unmatched_assets:
        print(f"   [FOUND] {len(unmatched_assets)} unmatched assets:")
        for u in unmatched_assets:
            print(f"     - Asset ID {u['asset_id']}: {u['reason']}")
    else:
        print("   [NONE] All assets successfully matched to route points.")

    print(f"\n3. Duplicate Asset Positions (Multiple assets matching the same route sequence):")
    if duplicate_asset_positions:
        print(f"   [FOUND] {len(duplicate_asset_positions)} route sequence points matched by multiple assets:")
        for seq, aids in duplicate_asset_positions.items():
            print(f"     - Route Seq {seq}: Asset IDs {aids}")
    else:
        print("   [NONE] Each asset mapped to a unique route sequence point.")

    print(f"\n4. Assets Far From Surveyed Route (> 30m distance to nearest route point):")
    if far_assets:
        print(f"   [FOUND] {len(far_assets)} assets > 30m away from route:")
        for f in far_assets:
            print(f"     - Asset ID {f['asset_id']} ({f['asset_category']} - {f['asset_type']}): {f['dist_to_route_m']}m away at Route Seq {f['matched_route_sequence']}")
    else:
        print("   [NONE] All assets are within 30m of the surveyed route points.")

    print("\n=== Analysis Complete ===")


if __name__ == "__main__":
    run_asset_sequence_analysis("47")
