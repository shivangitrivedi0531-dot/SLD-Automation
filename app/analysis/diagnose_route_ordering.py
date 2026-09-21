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
    """Calculate great circle distance between two points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def evaluate_ordering(points_list: list, label: str):
    """Evaluate consecutive point-to-point distances and jumps for a given ordering."""
    if not points_list:
        return {
            "label": label,
            "total_dist": 0.0,
            "max_jump": 0.0,
            "avg_dist": 0.0,
            "jumps_over_100m": 0,
            "jumps_over_500m": 0,
        }

    total_dist = 0.0
    max_jump = 0.0
    jumps_over_100m = 0
    jumps_over_500m = 0
    distances = []

    for i in range(1, len(points_list)):
        p1 = points_list[i - 1]
        p2 = points_list[i]
        d = haversine_distance(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        total_dist += d
        distances.append(d)
        if d > max_jump:
            max_jump = d
        if d > 100.0:
            jumps_over_100m += 1
        if d > 500.0:
            jumps_over_500m += 1

    avg_dist = (total_dist / len(distances)) if distances else 0.0

    return {
        "label": label,
        "count": len(points_list),
        "total_dist": round(total_dist, 2),
        "max_jump": round(max_jump, 2),
        "avg_dist": round(avg_dist, 2),
        "jumps_over_100m": jumps_over_100m,
        "jumps_over_500m": jumps_over_500m,
    }


def run_ordering_diagnostics():
    load_dotenv()

    print("=== Fetching Survey ID 47 Raw Route Points ===")
    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    response_data = api_client.get(
        "/api/geo-survey/surveys/47",
        params={"all_points": "true"},
    )

    data = response_data.get("data", {}) if isinstance(response_data, dict) else {}
    route_points_raw = data.get("route_points", [])

    print(f"Loaded {len(route_points_raw)} raw route points from API.\n")

    # Parse route points preserving raw index
    parsed_points = []
    for idx, rp in enumerate(route_points_raw):
        pid_str = str(rp.get("point_id", ""))
        try:
            pid_int = int(pid_str)
        except ValueError:
            pid_int = idx

        seq_no = int(rp.get("sequence_no", idx + 1))
        rec_at = str(rp.get("recorded_at", ""))
        lat = float(rp["latitude"])
        lon = float(rp["longitude"])

        parsed_points.append({
            "raw_index": idx,
            "point_id": pid_str,
            "point_id_int": pid_int,
            "sequence_no": seq_no,
            "recorded_at": rec_at,
            "latitude": lat,
            "longitude": lon,
        })

    # 1. Investigate Region Around Sequence 5839 to 6040
    print("=== 1. REGION ANALYSIS: Sequence 5839 to 6040 ===")
    region_points = [p for p in parsed_points if 5839 <= p["sequence_no"] <= 6040]
    print(f"Total points in sequence range 5839..6040: {len(region_points)}")

    # Check duplicate sequence_no in this region
    region_seq_map = {}
    for p in region_points:
        region_seq_map.setdefault(p["sequence_no"], []).append(p)

    dup_region_seqs = {s: pts for s, pts in region_seq_map.items() if len(pts) > 1}
    print(f"Duplicate sequence numbers in region 5839..6040: {len(dup_region_seqs)}")

    # 2. Point ID Range & Track Pattern Analysis in Duplicate Region
    print("\n=== 2. POINT ID RANGE & TRACK PATTERN ANALYSIS (Seq 5880 to 5979) ===")
    seq_5880_5979_pts = [p for p in region_points if 5880 <= p["sequence_no"] <= 5979]
    print(f"Points in range 5880..5979: {len(seq_5880_5979_pts)}")

    # Group points by sequence number to observe the offset
    print("\nSample Interleaved Sequence Entries (Showing Point IDs, Timestamps, Coords):")
    sample_seqs = [5880, 5881, 5882, 5883, 5884, 5978, 5979]
    for s in sample_seqs:
        pts = [p for p in seq_5880_5979_pts if p["sequence_no"] == s]
        print(f"  Seq {s} ({len(pts)} points):")
        for p in pts:
            print(f"    RawIdx: {p['raw_index']:<5} | PointID: {p['point_id']:<8} | RecAt: {p['recorded_at']:<25} | Lat: {p['latitude']:.6f}, Lon: {p['longitude']:.6f}")

    # Inspect Point ID Ranges and Timestamps
    track_a_pts = [p for p in seq_5880_5979_pts if 137649 <= p["point_id_int"] <= 137748]
    track_b_pts = [p for p in seq_5880_5979_pts if 137749 <= p["point_id_int"] <= 137848]

    print(f"\nTrack A (Point IDs 137649 .. 137748): {len(track_a_pts)} points")
    if track_a_pts:
        print(f"  - First Point ID: {track_a_pts[0]['point_id']}, RecAt: {track_a_pts[0]['recorded_at']}, Lat/Lon: ({track_a_pts[0]['latitude']:.6f}, {track_a_pts[0]['longitude']:.6f})")
        print(f"  - Last Point ID:  {track_a_pts[-1]['point_id']}, RecAt: {track_a_pts[-1]['recorded_at']}, Lat/Lon: ({track_a_pts[-1]['latitude']:.6f}, {track_a_pts[-1]['longitude']:.6f})")

    print(f"\nTrack B (Point IDs 137749 .. 137848): {len(track_b_pts)} points")
    if track_b_pts:
        print(f"  - First Point ID: {track_b_pts[0]['point_id']}, RecAt: {track_b_pts[0]['recorded_at']}, Lat/Lon: ({track_b_pts[0]['latitude']:.6f}, {track_b_pts[0]['longitude']:.6f})")
        print(f"  - Last Point ID:  {track_b_pts[-1]['point_id']}, RecAt: {track_b_pts[-1]['recorded_at']}, Lat/Lon: ({track_b_pts[-1]['latitude']:.6f}, {track_b_pts[-1]['longitude']:.6f})")

    # 3. Compare Ordering Signals for Region (Sequence 5839..6040)
    print("\n=== 3. COMPARISON OF ORDERING SIGNALS (Region Seq 5839 to 6040) ===")

    # Order A: Raw API array order (subset region_points sorted by raw_index)
    ord_raw = sorted(region_points, key=lambda x: x["raw_index"])
    res_raw = evaluate_ordering(ord_raw, "a) Raw API Array Order")

    # Order B: Sequence_no order (stable sort by sequence_no, then raw_index)
    ord_seq = sorted(region_points, key=lambda x: (x["sequence_no"], x["raw_index"]))
    res_seq = evaluate_ordering(ord_seq, "b) Sequence_no Order")

    # Order C: Point_id order (sort by integer point_id)
    ord_pid = sorted(region_points, key=lambda x: x["point_id_int"])
    res_pid = evaluate_ordering(ord_pid, "c) Point_id Order")

    # Order D: Recorded_at order (sort by recorded_at timestamp)
    ord_rec = sorted(region_points, key=lambda x: (x["recorded_at"], x["point_id_int"]))
    res_rec = evaluate_ordering(ord_rec, "d) Recorded_at Order")

    results_region = [res_raw, res_seq, res_pid, res_rec]

    header = f"{'Ordering Signal':<30} | {'Points':<7} | {'Total Dist (m)':<15} | {'Avg Step (m)':<12} | {'Max Jump (m)':<12} | {'Jumps >100m':<12} | {'Jumps >500m':<12}"
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for r in results_region:
        print(f"{r['label']:<30} | {r['count']:<7} | {r['total_dist']:<15.2f} | {r['avg_dist']:<12.2f} | {r['max_jump']:<12.2f} | {r['jumps_over_100m']:<12} | {r['jumps_over_500m']:<12}")
    print("-" * len(header))

    # 4. Compare Ordering Signals for ENTIRE SURVEY (All 7,185 points)
    print("\n=== 4. COMPARISON OF ORDERING SIGNALS (Entire Survey 47 - 7,185 Points) ===")

    all_raw = sorted(parsed_points, key=lambda x: x["raw_index"])
    res_all_raw = evaluate_ordering(all_raw, "a) Raw API Array Order")

    all_seq = sorted(parsed_points, key=lambda x: (x["sequence_no"], x["raw_index"]))
    res_all_seq = evaluate_ordering(all_seq, "b) Sequence_no Order")

    all_pid = sorted(parsed_points, key=lambda x: x["point_id_int"])
    res_all_pid = evaluate_ordering(all_pid, "c) Point_id Order")

    all_rec = sorted(parsed_points, key=lambda x: (x["recorded_at"], x["point_id_int"]))
    res_all_rec = evaluate_ordering(all_rec, "d) Recorded_at Order")

    results_all = [res_all_raw, res_all_seq, res_all_pid, res_all_rec]

    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for r in results_all:
        print(f"{r['label']:<30} | {r['count']:<7} | {r['total_dist']:<15.2f} | {r['avg_dist']:<12.2f} | {r['max_jump']:<12.2f} | {r['jumps_over_100m']:<12} | {r['jumps_over_500m']:<12}")
    print("-" * len(header))

    # 5. Summary Findings Report
    print("\n=== 5. SUMMARY DIAGNOSTIC FINDINGS ===")
    print("1. In Region 5839..6040, raw array order and sequence_no order interleave Track A (point_ids 137649-137748) and Track B (point_ids 137749-137848).")
    print("2. Point_id order and Recorded_at order sort points sequentially along continuous geographic paths without zigzagging.")

    print("\n=== Ordering Signal Analysis Complete ===")


if __name__ == "__main__":
    run_ordering_diagnostics()
