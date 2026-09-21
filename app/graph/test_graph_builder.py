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
    build_electrical_graph,
    get_graph_statistics,
    validate_electrical_graph,
)


def test_builder():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    feeder_data = load_feeder_data(survey_id, api_client=api_client)

    # Build NetworkX graph
    G = build_electrical_graph(feeder_data)

    # Calculate statistics
    stats = get_graph_statistics(G)

    # Validate graph
    warnings = validate_electrical_graph(feeder_data, G)

    print("=== Electrical Graph Builder Test Results ===")
    print(f"Node Count:                 {stats['node_count']}")
    print(f"Edge Count:                 {stats['edge_count']}")
    print(f"Connected Component Count:  {stats['connected_components']}")
    print(f"Isolated Node Count:        {stats['isolated_node_count']}")
    print(f"Validation Warnings:        {warnings if warnings else 'None'}")


if __name__ == "__main__":
    test_builder()
