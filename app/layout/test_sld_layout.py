import os
import sys
import networkx as nx

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.layout.sld_layout import generate_sld_layout


def test_sld_layout_verification():
    """Verify SLD layout engine deterministically using a local in-memory topology graph."""
    # 1. Define exact ordered topology sequence & labels for Survey 47
    node_sequence = [
        ("SOURCE_SS", "66 KV KATHWADA-2 S/S"),
        ("142", "POLE-01"),
        ("143", "POLE-02"),
        ("144", "POLE-03"),
        ("145", "POLE-04"),
        ("146", "POLE-05"),
        ("147", "POLE-06"),
        ("148", "POLE-07"),
        ("149", "POLE-08"),
        ("150", "POLE-09"),
        ("151", "POLE-10"),
        ("152", "POLE-11"),
        ("153", "POLE-12"),
        ("154", "POLE-13"),
        ("155", "POLE-14"),
        ("156", "POLE-15"),
        ("157", "POLE-16"),
        ("158", "POLE-17"),
        ("159", "POLE-18"),
        ("160", "POLE-19"),
        ("161", "POLE-20"),
        ("162", "POLE-21"),
        ("163", "POLE-22"),
        ("164", "POLE-23"),
        ("165", "POLE-24"),
        ("166", "POLE-25"),
        ("167", "POLE-26"),
        ("168", "POLE-27"),
        ("169", "POLE-28"),
        ("170", "POLE-29"),
        ("171", "POLE-30"),
        ("172", "POLE-31"),
        ("173", "POLE-32"),
        ("174", "POLE-33"),
        ("175", "POLE-34"),
        ("176", "POLE-35"),
        ("177", "POLE-36"),
        ("178", "POLE-37"),
        ("179", "POLE-38"),
        ("180", "POLE-39"),
        ("181", "POLE-40"),
        ("183", "POLE-42"),
        ("184", "POLE-42"),
        ("182", "POLE-41"),
    ]

    # 2. Build local in-memory NetworkX graph
    graph = nx.Graph()

    for nid, label in node_sequence:
        asset_cat = "SUBSTATION" if nid == "SOURCE_SS" else "POLE"
        graph.add_node(nid, label=label, asset_category=asset_cat)

    for i in range(len(node_sequence) - 1):
        u = node_sequence[i][0]
        v = node_sequence[i + 1][0]
        graph.add_edge(u, v)

    # 3. Call generate_sld_layout(graph)
    layout = generate_sld_layout(graph)

    total_nodes = len(layout)
    graph_node_count = graph.number_of_nodes()

    ordered_keys = list(layout.keys())

    x_vals = [pos["x"] for pos in layout.values()]
    y_vals = [pos["y"] for pos in layout.values()]

    min_x, max_x = min(x_vals), max(x_vals)
    min_y, max_y = min(y_vals), max(y_vals)
    unique_y_levels = len(set(y_vals))

    print("====================================================================================================")
    print("                               SLD LAYOUT ENGINE VERIFICATION")
    print("====================================================================================================")
    print(f"Total Positioned Nodes: {total_nodes}")

    print("\nFirst 5 Nodes:")
    for nid in ordered_keys[:5]:
        label = graph.nodes[nid].get("label", nid)
        pos = layout[nid]
        print(f"  - node_id: '{nid:<10}' | label: '{label:<23}' | x: {pos['x']:>7.2f} | y: {pos['y']:>7.2f}")

    print("\nLast 5 Nodes:")
    for nid in ordered_keys[-5:]:
        label = graph.nodes[nid].get("label", nid)
        pos = layout[nid]
        print(f"  - node_id: '{nid:<10}' | label: '{label:<23}' | x: {pos['x']:>7.2f} | y: {pos['y']:>7.2f}")

    print(f"\nMinimum X: {min_x:.2f} | Maximum X: {max_x:.2f}")
    print(f"Minimum Y: {min_y:.2f} | Maximum Y: {max_y:.2f}")

    # 4. Validation checks
    exactly_44_nodes = (total_nodes == 44) and (graph_node_count == 44)
    all_nodes_positioned = all(n in layout for n in graph.nodes())
    no_missing_pos = all(isinstance(pos, dict) and "x" in pos and "y" in pos for pos in layout.values())
    multiple_y_rows = unique_y_levels > 1
    order_preserved = (ordered_keys == [nid for nid, _ in node_sequence])

    is_valid = (
        exactly_44_nodes
        and all_nodes_positioned
        and no_missing_pos
        and multiple_y_rows
        and order_preserved
    )

    print("\n====================================================================================================")
    if is_valid:
        print("Layout Validation: PASS")
    else:
        print("Layout Validation: FAIL")
    print("====================================================================================================")


if __name__ == "__main__":
    test_sld_layout_verification()
