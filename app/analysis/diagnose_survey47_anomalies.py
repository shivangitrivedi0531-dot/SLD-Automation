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

    print(f"Total raw assets: {len(assets_raw)}")
    print(f"Total raw route points: {len(route_points_raw)}\n")

    # 1. Parse raw route points preserving original array order
    raw_rp_list = []
    seq_map = {}  # seq_no -> list of route points

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

    # 2. Check duplicate sequence numbers: identical vs different coordinates
    print("=== 1. DUPLICATE SEQUENCE NUMBERS ANALYSIS ===")
    duplicate_seq_counts = {seq: pts for seq, pts in seq_map.items() if len(pts) > 1}
    print(f"Total unique sequence_no values with duplicates: {len(duplicate_seq_counts)}")

    identical_coords_count = 0
    different_coords_count = 0
    diff_coord_examples = []

    for seq, pts in duplicate_seq_counts.items():
        first_coords = (pts[0]["latitude"], pts[0]["longitude"])
        all_identical = all((p["latitude"], p["longitude"]) == first_coords for p in pts)
        if all_identical:
            identical_coords_count += 1
        else:
            different_coords_count += 1
            if len(diff_coord_examples) < 5:
                diff_coord_examples.append((seq, pts))

    print(f"- Duplicate sequence_no with EXACT IDENTICAL coordinates: {identical_coords_count}")
    print(f"- Duplicate sequence_no with DIFFERENT coordinates: {different_coords_count}")

    if diff_coord_examples:
        print("\nExamples of duplicate sequence_no with DIFFERENT coordinates:")
        for seq, pts in diff_coord_examples:
            print(f"  Sequence {seq} ({len(pts)} points):")
            for p in pts:
                print(f"    Raw Index {p['raw_index']}, Point ID {p['point_id']}, Lat: {p['latitude']}, Lon: {p['longitude']}")

    # 3. Target Assets Focus: POLE-40, POLE-41, POLE-42
    target_labels = ["POLE-40", "POLE-41", "POLE-42"]
    target_assets = [a for a in assets_raw if str(a.get("label")) in target_labels or str(a.get("asset_id")) in ["181", "182", "183", "184"]]

    print("\n=== 2. TARGET ASSET INFORMATION & ROUTE MATCHING ===")
    matched_target_info = []

    for a in target_assets:
        aid = a.get("asset_id")
        label = a.get("label")
        a_lat = float(a["latitude"])
        a_lon = float(a["longitude"])

        # Find nearest point in raw route points list
        min_dist_raw = float("inf")
        best_raw_pt = None

        for rp in raw_rp_list:
            d = haversine_distance(a_lat, a_lon, rp["latitude"], rp["longitude"])
            if d < min_dist_raw:
                min_dist_raw = d
                best_raw_pt = rp

        info = {
            "asset_id": aid,
            "label": label,
            "latitude": a_lat,
            "longitude": a_lon,
            "matched_point_id": best_raw_pt["point_id"],
            "matched_sequence_no": best_raw_pt["sequence_no"],
            "matched_raw_index": best_raw_pt["raw_index"],
            "dist_to_route_m": round(min_dist_raw, 2),
            "matched_rp_lat": best_raw_pt["latitude"],
            "matched_rp_lon": best_raw_pt["longitude"],
        }
        matched_target_info.append(info)

        print(f"Asset ID: {aid:<6} | Label: {str(label):<10} | Lat: {a_lat:.6f}, Lon: {a_lon:.6f} | "
              f"Matched Point ID: {best_raw_pt['point_id']} | Matched Seq: {best_raw_pt['sequence_no']} | "
              f"Raw Index: {best_raw_pt['raw_index']} | Dist to Route: {min_dist_raw:.2f}m")

    # 4. Direct Geographic (Geodesic/Haversine) Distances Between Target Assets
    print("\n=== 3. DIRECT GEOGRAPHIC DISTANCE COMPARISON ===")
    for i in range(len(matched_target_info)):
        for j in range(i + 1, len(matched_target_info)):
            a1 = matched_target_info[i]
            a2 = matched_target_info[j]
            direct_d = haversine_distance(a1["latitude"], a1["longitude"], a2["latitude"], a2["longitude"])
            rp_d = haversine_distance(a1["matched_rp_lat"], a1["matched_rp_lon"], a2["matched_rp_lat"], a2["matched_rp_lon"])
            print(f"Direct Distance ({a1['label']} ID:{a1['asset_id']} <-> {a2['label']} ID:{a2['asset_id']}):")
            print(f"  - Asset-to-Asset Direct: {direct_d:.2f} m")
            print(f"  - Matched Route Point to Route Point Direct: {rp_d:.2f} m")

    # 5. Surrounding Route Points Analysis in Raw Order vs Sorted Sequence Order
    print("\n=== 4. SURROUNDING ROUTE POINTS & GPS JUMP ANALYSIS ===")
    
    # Sort route points by sequence_no (same as previous script)
    sorted_rp_list = sorted(raw_rp_list, key=lambda x: x["sequence_no"])

    for info in matched_target_info:
        raw_idx = info["matched_raw_index"]
        seq_no = info["matched_sequence_no"]
        print(f"\n--------------------------------------------------------------------------------")
        print(f"Surrounding Points for {info['label']} (Asset ID {info['asset_id']}, Matched Seq {seq_no}, Raw Index {raw_idx})")
        print(f"--------------------------------------------------------------------------------")

        # A. In RAW Array Order (indices raw_idx - 3 to raw_idx + 3)
        print("\n--- A. In RAW Array Order ---")
        start_raw = max(0, raw_idx - 3)
        end_raw = min(len(raw_rp_list), raw_idx + 4)
        
        for k in range(start_raw, end_raw):
            pt = raw_rp_list[k]
            prev_pt = raw_rp_list[k - 1] if k > 0 else pt
            step_d = haversine_distance(prev_pt["latitude"], prev_pt["longitude"], pt["latitude"], pt["longitude"])
            jump_flag = " *** [LARGE JUMP > 500m] ***" if step_d > 500.0 else ""
            marker = "  <-- MATCHED ASSET POINT" if k == raw_idx else ""
            print(f"  RawIdx: {pt['raw_index']:<5} | PointID: {pt['point_id']:<8} | Seq: {pt['sequence_no']:<5} | "
                  f"Lat: {pt['latitude']:.6f}, Lon: {pt['longitude']:.6f} | StepDist: {step_d:8.2f}m{jump_flag}{marker}")

        # B. In SORTED Sequence_No Order
        print("\n--- B. In SORTED Sequence_No Order ---")
        # Find index in sorted_rp_list
        sorted_idx = next(i for i, pt in enumerate(sorted_rp_list) if pt["raw_index"] == raw_idx)
        start_sorted = max(0, sorted_idx - 3)
        end_sorted = min(len(sorted_rp_list), sorted_idx + 4)

        for k in range(start_sorted, end_sorted):
            pt = sorted_rp_list[k]
            prev_pt = sorted_rp_list[k - 1] if k > 0 else pt
            step_d = haversine_distance(prev_pt["latitude"], prev_pt["longitude"], pt["latitude"], pt["longitude"])
            jump_flag = " *** [LARGE JUMP > 500m] ***" if step_d > 500.0 else ""
            marker = "  <-- MATCHED ASSET POINT" if k == sorted_idx else ""
            print(f"  SortedIdx: {k:<5} | PointID: {pt['point_id']:<8} | Seq: {pt['sequence_no']:<5} | "
                  f"Lat: {pt['latitude']:.6f}, Lon: {pt['longitude']:.6f} | StepDist: {step_d:8.2f}m{jump_flag}{marker}")

    # 6. Global GPS Jump Inspection across sorted array vs raw array
    print("\n=== 5. GLOBAL GPS JUMP INSPECTION (> 500m) ===")
    
    # In RAW array
    raw_jumps = []
    for i in range(1, len(raw_rp_list)):
        p1 = raw_rp_list[i - 1]
        p2 = raw_rp_list[i]
        d = haversine_distance(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        if d > 500.0:
            raw_jumps.append((i - 1, i, p1, p2, d))

    print(f"Jumps > 500m in RAW array order: {len(raw_jumps)}")
    for j in raw_jumps[:10]:
        print(f"  - Raw Index {j[0]} -> {j[1]}: Seq {j[2]['sequence_no']} -> Seq {j[3]['sequence_no']}, Distance = {j[4]:.2f} m")

    # In SORTED array
    sorted_jumps = []
    for i in range(1, len(sorted_rp_list)):
        p1 = sorted_rp_list[i - 1]
        p2 = sorted_rp_list[i]
        d = haversine_distance(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        if d > 500.0:
            sorted_jumps.append((i - 1, i, p1, p2, d))

    print(f"\nJumps > 500m in SORTED sequence_no order: {len(sorted_jumps)}")
    for j in sorted_jumps[:10]:
        print(f"  - Sorted Index {j[0]} -> {j[1]}: RawIdx {j[2]['raw_index']} (Seq {j[2]['sequence_no']}) -> RawIdx {j[3]['raw_index']} (Seq {j[3]['sequence_no']}), Distance = {j[4]:.2f} m")

    # Total accumulated route distance in RAW vs SORTED order
    total_raw_dist = sum(
        haversine_distance(raw_rp_list[i - 1]["latitude"], raw_rp_list[i - 1]["longitude"],
                           raw_rp_list[i]["latitude"], raw_rp_list[i]["longitude"])
        for i in range(1, len(raw_rp_list))
    )
    total_sorted_dist = sum(
        haversine_distance(sorted_rp_list[i - 1]["latitude"], sorted_rp_list[i - 1]["longitude"],
                           sorted_rp_list[i]["latitude"], sorted_rp_list[i]["longitude"])
        for i in range(1, len(sorted_rp_list))
    )

    print(f"\n=== 6. ROUTE TOTAL DISTANCE SUMMARY ===")
    print(f"Total route distance traversing RAW array order: {total_raw_dist:.2f} m ({total_raw_dist / 1000.0:.2f} km)")
    print(f"Total route distance traversing SORTED sequence_no order: {total_sorted_dist:.2f} m ({total_sorted_dist / 1000.0:.2f} km)")

    print("\n=== Diagnostics Complete ===")


if __name__ == "__main__":
    run_diagnostics()
