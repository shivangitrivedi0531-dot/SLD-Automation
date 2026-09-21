import os
import sys
from collections import Counter
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient
from app.analysis.asset_route_mapping import map_assets_to_route


def test_mapping():
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

    # 3. Map assets to route points
    mapped_records = map_assets_to_route(assets, route_points)

    print("=========================================================================================================================================")
    print(f"                                      SURVEY {survey_id} ASSET-TO-ROUTE MAPPING RESULTS")
    print("=========================================================================================================================================")
    header = f"{'#':<3} | {'asset_id':<9} | {'label':<9} | {'asset_category':<15} | {'asset_type':<18} | {'matched_rp_id':<14} | {'matched_seq_no':<15} | {'dist_to_rp (m)':<13}"
    print(header)
    print("-" * len(header))

    rp_id_counts = Counter()
    seq_no_counts = Counter()
    max_dist = 0.0
    matched_count = 0
    unmatched_count = 0

    for idx, rec in enumerate(mapped_records, 1):
        aid = str(rec["asset_id"] or "")
        label = str(rec["label"] or "")
        cat = str(rec["asset_category"] or "")
        atype = str(rec["asset_type"] or "")
        rp_id = str(rec["matched_route_point_id"]) if rec["matched_route_point_id"] is not None else "None"
        seq_no = str(rec["matched_route_sequence_no"]) if rec["matched_route_sequence_no"] is not None else "None"
        dist = rec["distance_to_route_point_m"]

        if rec["matched_route_point_id"] is not None:
            matched_count += 1
            rp_id_counts[rec["matched_route_point_id"]] += 1
            if dist is not None and dist > max_dist:
                max_dist = dist
        else:
            unmatched_count += 1

        if rec["matched_route_sequence_no"] is not None:
            seq_no_counts[rec["matched_route_sequence_no"]] += 1

        dist_str = f"{dist:.3f}" if dist is not None else "N/A"
        row = f"{idx:<3} | {aid:<9} | {label:<9} | {cat:<15} | {atype:<18} | {rp_id:<14} | {seq_no:<15} | {dist_str:<13}"
        print(row)

    print("=" * len(header))

    # Calculate duplicates
    duplicate_rp_ids = {k: v for k, v in rp_id_counts.items() if v > 1}
    duplicate_seq_nos = {k: v for k, v in seq_no_counts.items() if v > 1}

    print("\n=========================================================================================================================================")
    print("                                                          SUMMARY")
    print("=========================================================================================================================================")
    print(f"Total Assets: {len(mapped_records)}")
    print(f"Matched Assets: {matched_count}")
    print(f"Unmatched Assets: {unmatched_count}")
    print(f"Maximum Distance from Asset to Matched Route Point: {max_dist:.3f} meters")
    print(f"Duplicate Matched Route-Point IDs: {duplicate_rp_ids if duplicate_rp_ids else 'None'}")
    print(f"Duplicate Matched Sequence Numbers: {duplicate_seq_nos if duplicate_seq_nos else 'None'}")
    print("=========================================================================================================================================")


if __name__ == "__main__":
    test_mapping()
