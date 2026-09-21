import os
import sys
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient
from app.data.loader import load_feeder_data
from app.graph.graph_builder import (
    build_graph_from_ordered_topology,
    get_graph_statistics,
    validate_electrical_graph,
)


def test_ordered_topology():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    feeder_data = load_feeder_data(survey_id, api_client=api_client)

    # 1. Source node definition
    source_node = {
        "node_id": "SOURCE_SS",
        "label": "66 KV KATHWADA-2 S/S",
        "asset_category": "SUBSTATION",
        "asset_type": "SUBSTATION",
        "condition_type": "existing",
    }

    # 2. Confirmed Survey 47 reference asset ID sequence (43 asset IDs)
    # POLE-01 (142) through POLE-40 (181), POLE-42 existing (183), POLE-42 proposed (184), POLE-41 (182)
    ordered_asset_ids = [
        "142", "143", "144", "145", "146", "147", "148", "149", "150", "151",
        "152", "153", "154", "155", "156", "157", "158", "159", "160", "161",
        "162", "163", "164", "165", "166", "167", "168", "169", "170", "171",
        "172", "173", "174", "175", "176", "177", "178", "179", "180", "181",
        "183", "184", "182"
    ]

    # 3. Confirmed reference span distances (43 span values in meters)
    span_distances = [
        215, 10, 30, 38, 36, 51, 41, 42, 39, 35,
        43, 60, 59, 44, 30, 30, 74, 107, 54, 43,
        57, 41, 44, 83, 73, 51, 80, 147, 56, 100,
        419, 221, 254, 100, 319, 124, 358, 950, 26, 61,
        930, 389, 257
    ]

    # Build electrical graph
    G = build_graph_from_ordered_topology(
        feeder_data,
        ordered_asset_ids,
        source_node=source_node,
        span_distances=span_distances,
    )

    # Statistics & Validation
    stats = get_graph_statistics(G)
    warnings = validate_electrical_graph(feeder_data, G)

    # Extract edge details
    edges_list = list(G.edges(data=True))

    total_edge_distance = sum(
        d.get("length_m", 0.0) for u, v, d in edges_list if isinstance(d.get("length_m"), (int, float))
    )

    print("=== Ordered Electrical Graph Test Results ===")
    print(f"Node Count:                 {stats['node_count']}")
    print(f"Edge Count:                 {stats['edge_count']}")
    print(f"Connected Component Count:  {stats['connected_components']}")
    print(f"Isolated Node Count:        {stats['isolated_node_count']}")
    print(f"Total Edge Distance:        {total_edge_distance} meters")
    print(f"Validation Warnings:        {warnings if warnings else 'None'}")

    print("\nFirst 5 Edges:")
    for idx, (u, v, d) in enumerate(edges_list[:5], 1):
        u_label = G.nodes[u].get("label", u)
        v_label = G.nodes[v].get("label", v)
        length = d.get("length_m", "N/A")
        print(f"  {idx}. ({u} [{u_label}]) <---> ({v} [{v_label}]): {length} m")

    print("\nLast 5 Edges:")
    for idx, (u, v, d) in enumerate(edges_list[-5:], 1):
        u_label = G.nodes[u].get("label", u)
        v_label = G.nodes[v].get("label", v)
        length = d.get("length_m", "N/A")
        print(f"  {idx}. ({u} [{u_label}]) <---> ({v} [{v_label}]): {length} m")


if __name__ == "__main__":
    test_ordered_topology()
