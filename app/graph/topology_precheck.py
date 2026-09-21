import os
import sys
import math
from collections import Counter
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient
from app.data.loader import load_feeder_data
from app.data.models import FeederData, Asset, RoutePoint


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


def run_topology_precheck(survey_id: str = "47", feeder_data: FeederData = None) -> Dict[str, Any]:
    if feeder_data is None:
        load_dotenv()
        auth_client = ERPAuthClient()
        
        # Retry loop for transient remote server errors
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                auth_client.login()
                break
            except Exception as e:
                if attempt == max_retries:
                    raise
                import time
                time.sleep(2)

        api_client = ERPApiClient(auth_client=auth_client)
        feeder_data = load_feeder_data(survey_id, api_client=api_client)


    assets = feeder_data.assets
    route_points = feeder_data.route_points
    cable_segments = feeder_data.cable_segments

    # 1. Counts
    asset_count = len(assets)
    rp_count = len(route_points)
    cs_count = len(cable_segments)

    # 2. Asset IDs & Labels check
    asset_ids = [a.asset_id for a in assets if a.asset_id is not None]
    id_counts = Counter(asset_ids)
    duplicate_ids = {k: v for k, v in id_counts.items() if v > 1}

    asset_labels = [a.label for a in assets if a.label is not None]
    label_counts = Counter(asset_labels)
    duplicate_labels = {k: v for k, v in label_counts.items() if v > 1}

    missing_coords = [a.asset_id for a in assets if a.latitude is None or a.longitude is None]

    # 3. Route-point sequence check
    seq_numbers = [rp.sequence_no for rp in route_points if rp.sequence_no is not None]
    min_seq = min(seq_numbers) if seq_numbers else None
    max_seq = max(seq_numbers) if seq_numbers else None

    seq_counts = Counter(seq_numbers)
    duplicate_seqs = {k: v for k, v in seq_counts.items() if v > 1}

    # Sequence numbers with different coordinates
    seq_coords_map: Dict[int, List[Tuple[float, float]]] = {}
    for rp in route_points:
        if rp.sequence_no is not None and rp.latitude is not None and rp.longitude is not None:
            seq_coords_map.setdefault(rp.sequence_no, []).append((rp.latitude, rp.longitude))

    seq_diff_coords = {}
    for seq, coords_list in seq_coords_map.items():
        if len(coords_list) > 1:
            # Check if any coords differ significantly
            first_c = coords_list[0]
            if any(haversine_distance(first_c[0], first_c[1], c[0], c[1]) > 0.1 for c in coords_list[1:]):
                seq_diff_coords[seq] = coords_list

    # 4. Consecutive route-point jumps
    valid_rps = [rp for rp in route_points if rp.sequence_no is not None and rp.latitude is not None and rp.longitude is not None]
    valid_rps.sort(key=lambda rp: rp.sequence_no)

    jumps_gt_100 = []
    jumps_gt_500 = []

    for i in range(len(valid_rps) - 1):
        rp1 = valid_rps[i]
        rp2 = valid_rps[i + 1]
        dist = haversine_distance(rp1.latitude, rp1.longitude, rp2.latitude, rp2.longitude)
        seq_gap = rp2.sequence_no - rp1.sequence_no
        if dist > 100.0:
            jumps_gt_100.append((rp1.sequence_no, rp2.sequence_no, dist, seq_gap))
        if dist > 500.0:
            jumps_gt_500.append((rp1.sequence_no, rp2.sequence_no, dist, seq_gap))

    # 5. Asset-to-route matching
    asset_matches = []
    rp_match_counts = Counter()

    for asset in assets:
        best_rp = None
        min_d = float("inf")
        if asset.latitude is not None and asset.longitude is not None:
            for rp in valid_rps:
                d = haversine_distance(asset.latitude, asset.longitude, rp.latitude, rp.longitude)
                if d < min_d:
                    min_d = d
                    best_rp = rp

        matched_id = best_rp.point_id if best_rp else None
        matched_seq = best_rp.sequence_no if best_rp else None
        if matched_id is not None:
            rp_match_counts[matched_id] += 1

        asset_matches.append({
            "asset_id": asset.asset_id,
            "label": asset.label,
            "matched_point_id": matched_id,
            "matched_sequence_no": matched_seq,
            "distance_m": min_d if min_d != float("inf") else None,
        })

    max_asset_dist = max((m["distance_m"] for m in asset_matches if m["distance_m"] is not None), default=0.0)
    assets_gt_30m = [m for m in asset_matches if m["distance_m"] is not None and m["distance_m"] > 30.0]

    duplicate_matched_rps = {k: v for k, v in rp_match_counts.items() if v > 1}

    # 6. Check sequence monotonicity
    # Are matched sequence numbers strictly increasing in order of asset listing?
    matched_seq_list = [m["matched_sequence_no"] for m in asset_matches if m["matched_sequence_no"] is not None]
    is_strictly_increasing = all(matched_seq_list[i] < matched_seq_list[i + 1] for i in range(len(matched_seq_list) - 1))

    # 7. Problematic assets
    problematic_assets = assets_gt_30m

    # 8. Readiness assessment
    reasons_not_ready = []
    if cs_count == 0:
        reasons_not_ready.append("Zero explicit cable segments returned by API endpoint")
    if duplicate_labels:
        reasons_not_ready.append(f"Duplicate asset labels present ({list(duplicate_labels.keys())})")
    if assets_gt_30m:
        reasons_not_ready.append(f"Asset(s) located > 30m from route: {[a['label'] + ' (id=' + str(a['asset_id']) + ', dist=' + str(round(a['distance_m'], 1)) + 'm)' for a in assets_gt_30m]}")
    if not is_strictly_increasing:
        reasons_not_ready.append("Matched route sequence numbers are NOT strictly increasing relative to asset listing order")
    if jumps_gt_500:
        reasons_not_ready.append(f"Consecutive route point gaps > 500m present ({len(jumps_gt_500)} gaps)")

    status = "NOT READY" if reasons_not_ready else "READY"

    results = {
        "status": status,
        "reasons": reasons_not_ready,
        "asset_count": asset_count,
        "rp_count": rp_count,
        "cs_count": cs_count,
        "duplicate_ids": duplicate_ids,
        "duplicate_labels": duplicate_labels,
        "missing_coords": missing_coords,
        "min_seq": min_seq,
        "max_seq": max_seq,
        "duplicate_seqs": duplicate_seqs,
        "seq_diff_coords": seq_diff_coords,
        "jumps_gt_100_count": len(jumps_gt_100),
        "jumps_gt_500_count": len(jumps_gt_500),
        "jumps_gt_500": jumps_gt_500,
        "max_asset_dist": max_asset_dist,
        "assets_gt_30m": assets_gt_30m,
        "duplicate_matched_rps": duplicate_matched_rps,
        "is_strictly_increasing": is_strictly_increasing,
        "asset_matches": asset_matches,
    }

    return results


def print_topology_report(results: Dict[str, Any]):
    print("====================================================================================================")
    print("                               SURVEY 47 TOPOLOGY PRE-CHECK REPORT")
    print("====================================================================================================")
    print(f"1. Asset Count:              {results['asset_count']}")
    print(f"2. Route-Point Count:        {results['rp_count']}")
    print(f"3. Cable-Segment Count:      {results['cs_count']}")
    print(f"4. Duplicate Asset IDs:      {results['duplicate_ids'] if results['duplicate_ids'] else 'None'}")
    print(f"5. Duplicate Asset Labels:   {results['duplicate_labels'] if results['duplicate_labels'] else 'None'}")
    print(f"6. Missing Coordinates:      {len(results['missing_coords'])} assets")

    print("\n--- Route-Point Sequence Metrics ---")
    print(f"7. Sequence Range:           min={results['min_seq']}, max={results['max_seq']}")
    print(f"   Duplicate Sequence Nos:   {results['duplicate_seqs'] if results['duplicate_seqs'] else 'None'}")
    print(f"   Seq Nos Diff Coords:      {len(results['seq_diff_coords'])}")

    print("\n--- Route-Point Geographic Jumps ---")
    print(f"8. Jumps > 100 meters:       {results['jumps_gt_100_count']}")
    print(f"   Jumps > 500 meters:       {results['jumps_gt_500_count']}")
    if results["jumps_gt_500"]:
        for j in results["jumps_gt_500"][:5]:
            print(f"     * Gap seq {j[0]} -> {j[1]}: {j[2]:.1f} meters (seq delta: {j[3]})")

    print("\n--- Asset-to-Route Matching ---")
    print(f"9. Max Asset-to-Route Dist:  {results['max_asset_dist']:.3f} meters")
    print(f"   Assets > 30m from route:  {len(results['assets_gt_30m'])}")
    for a in results["assets_gt_30m"]:
        print(f"     * Asset ID {a['asset_id']} ({a['label']}): {a['distance_m']:.3f} meters away (matched point {a['matched_point_id']}, seq {a['matched_sequence_no']})")

    print(f"10. Multiple Assets Same RP:  {results['duplicate_matched_rps'] if results['duplicate_matched_rps'] else 'None'}")
    print(f"11. Strictly Increasing Seq:  {results['is_strictly_increasing']}")

    print("\n====================================================================================================")
    print(f"READINESS VERDICT FOR AUTOMATIC ELECTRICAL GRAPH CONSTRUCTION:")
    print(f"STATUS: {results['status']}")
    print("====================================================================================================")
    if results["status"] == "NOT READY":
        print("EXPLANATION OF WHY NOT READY:")
        for idx, reason in enumerate(results["reasons"], 1):
            print(f"  {idx}. {reason}")
    else:
        print("Survey 47 topology data passes all pre-checks and is ready for graph construction.")
    print("====================================================================================================")


if __name__ == "__main__":
    res = run_topology_precheck("47")
    print_topology_report(res)
