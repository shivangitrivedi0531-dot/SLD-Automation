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


def run_diagnostics():
    load_dotenv()

    print("=== Fetching Survey ID 47 Diagnostic Data ===")
    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    response_data = api_client.get(
        "/api/geo-survey/surveys/47",
        params={"all_points": "true"},
    )

    data = response_data.get("data", {}) if isinstance(response_data, dict) else {}
    assets_raw = data.get("assets", [])
    route_points_raw = data.get("route_points", [])

    print(f"Total Assets: {len(assets_raw)}")
    print(f"Total Route Points: {len(route_points_raw)}\n")

    # Parse route points
    raw_rp_list = []
    seq_map = {}

    for idx, rp in enumerate(route_points_raw):
        lat = float(rp["latitude"])
        lon = float(rp["longitude"])
        seq = int(rp.get("sequence_no", idx + 1))
        pid = str(rp.get("point_id", f"idx_{idx}"))

        pt_obj = {
            "raw_index": idx,
            "point_id": pid,
            "sequence_no": seq,
            "latitude": lat,
            "longitude": lon,
        }
        raw_rp_list.append(pt_obj)
        seq_map.setdefault(seq, []).append(pt_obj)

    # 1. Target Assets: POLE-40, POLE-42, POLE-41
    target_labels = ["POLE-40", "POLE-41", "POLE-42"]
    target_assets = [
        a for a in assets_raw
        if str(a.get("label")) in target_labels or str(a.get("asset_id")) in ["181", "182", "183", "184"]
    ]

    print("=== 1. TARGET ASSETS MATCHED ROUTE POINTS ===")
    matched_target_info = []

    for a in target_assets:
        aid = str(a.get("asset_id"))
        label = str(a.get("label"))
        a_lat = float(a["latitude"])
        a_lon = float(a["longitude"])

        # Find nearest route point in raw list
        min_dist = float("inf")
        best_rp = None

        for rp in raw_rp_list:
            d = haversine_distance(a_lat, a_lon, rp["latitude"], rp["longitude"])
            if d < min_dist:
                min_dist = d
                best_rp = rp

        info = {
            "asset_id": aid,
            "label": label,
            "latitude": a_lat,
            "longitude": a_lon,
            "matched_point_id": best_rp["point_id"],
            "matched_sequence_no": best_rp["sequence_no"],
            "matched_raw_index": best_rp["raw_index"],
            "dist_to_route_m": round(min_dist, 2),
            "matched_rp_lat": best_rp["latitude"],
            "matched_rp_lon": best_rp["longitude"],
        }
        matched_target_info.append(info)

        print(f"Asset ID: {aid:<6} | Label: {label:<10} | Lat: {a_lat:.6f}, Lon: {a_lon:.6f} | "
              f"Matched Point ID: {best_rp['point_id']} | Matched Route Seq: {best_rp['sequence_no']}")

    # 2. Nearby Route Points & Step Distances
    print("\n=== 2. NEARBY ROUTE POINTS & CONSECUTIVE DISTANCES ===")
    for info in matched_target_info:
        raw_idx = info["matched_raw_index"]
        seq_no = info["matched_sequence_no"]
        print(f"\n--- Nearby Points for {info['label']} (Asset ID {info['asset_id']}, Matched Seq {seq_no}) ---")

        start_idx = max(0, raw_idx - 3)
        end_idx = min(len(raw_rp_list), raw_idx + 4)

        for k in range(start_idx, end_idx):
            pt = raw_rp_list[k]
            prev_pt = raw_rp_list[k - 1] if k > 0 else pt
            step_d = haversine_distance(prev_pt["latitude"], prev_pt["longitude"], pt["latitude"], pt["longitude"])
            jump_flag = " *** [GPS JUMP > 500m] ***" if step_d > 500.0 else ""
            marker = " <-- MATCHED ASSET POINT" if k == raw_idx else ""

            print(f"  PointID: {pt['point_id']:<8} | Seq: {pt['sequence_no']:<5} | "
                  f"Lat: {pt['latitude']:.6f}, Lon: {pt['longitude']:.6f} | StepDist: {step_d:7.2f}m{jump_flag}{marker}")

    # 3. GPS Jumps (> 500m)
    print("\n=== 3. GPS JUMPS LARGER THAN 500 METERS ===")
    gps_jumps = []
    for i in range(1, len(raw_rp_list)):
        p1 = raw_rp_list[i - 1]
        p2 = raw_rp_list[i]
        d = haversine_distance(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        if d > 500.0:
            gps_jumps.append((i - 1, i, p1, p2, d))

    if gps_jumps:
        print(f"Found {len(gps_jumps)} GPS jump(s) > 500m:")
        for j in gps_jumps:
            print(f"  - Point ID {j[2]['point_id']} (Seq {j[2]['sequence_no']}) -> Point ID {j[3]['point_id']} (Seq {j[3]['sequence_no']}): Distance = {j[4]:.2f} m")
    else:
        print("No GPS jumps > 500m found in consecutive raw route points.")

    # 4. Duplicate Sequence Numbers Check
    print("\n=== 4. DUPLICATE SEQUENCE NUMBERS CHECK ===")
    duplicate_seqs = {seq: pts for seq, pts in seq_map.items() if len(pts) > 1}
    print(f"Total unique sequence numbers with duplicates: {len(duplicate_seqs)}")

    identical_count = 0
    different_count = 0
    different_examples = []

    for seq, pts in duplicate_seqs.items():
        first_coords = (pts[0]["latitude"], pts[0]["longitude"])
        if all((p["latitude"], p["longitude"]) == first_coords for p in pts):
            identical_count += 1
        else:
            different_count += 1
            if len(different_examples) < 3:
                different_examples.append((seq, pts))

    print(f"- Duplicate sequence_no with IDENTICAL coordinates: {identical_count}")
    print(f"- Duplicate sequence_no with DIFFERENT coordinates: {different_count}")

    if different_examples:
        print("\nExamples of duplicate sequence_no with DIFFERENT coordinates:")
        for seq, pts in different_examples:
            print(f"  Sequence {seq} ({len(pts)} points):")
            for p in pts:
                print(f"    Point ID: {p['point_id']}, Lat: {p['latitude']:.6f}, Lon: {p['longitude']:.6f}")

    # 5. Direct Geodesic Distances Comparison
    print("\n=== 5. DIRECT GEODESIC DISTANCE COMPARISON ===")
    for i in range(len(matched_target_info)):
        for j in range(i + 1, len(matched_target_info)):
            a1 = matched_target_info[i]
            a2 = matched_target_info[j]
            direct_d = haversine_distance(a1["latitude"], a1["longitude"], a2["latitude"], a2["longitude"])
            print(f"Direct Geodesic Distance ({a1['label']} ID:{a1['asset_id']} <-> {a2['label']} ID:{a2['asset_id']}): {direct_d:.2f} m")

    print("\n=== Diagnosis Complete ===")


if __name__ == "__main__":
    run_diagnostics()
