import os
import sys
import networkx as nx

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.layout.sld_layout import generate_sld_layout
from app.dxf.sld_drawing import draw_sld_dxf


def test_dxf_drawing_engine():
    # 1. Define exact Survey 47 ordered topology sequence & labels
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

    # 2. Span distances in meters for all 43 edges
    span_distances = [
        215, 10, 30, 38, 36, 51, 41, 42, 39, 35,
        43, 60, 59, 44, 30, 30, 74, 107, 54, 43,
        57, 41, 44, 83, 73, 51, 80, 147, 56, 100,
        419, 221, 254, 100, 319, 124, 358, 950, 26, 61,
        930, 389, 257
    ]

    # 3. Build graph locally
    graph = nx.Graph()

    for nid, label in node_sequence:
        asset_cat = "SUBSTATION" if nid == "SOURCE_SS" else "POLE"
        graph.add_node(nid, label=label, asset_category=asset_cat)

    for i in range(len(node_sequence) - 1):
        u = node_sequence[i][0]
        v = node_sequence[i + 1][0]
        dist = span_distances[i] if i < len(span_distances) else 0
        graph.add_edge(u, v, length_m=dist)

    # 4. Generate multi-row schematic layout
    layout_positions = generate_sld_layout(graph)

    # Output DXF file path
    output_path = os.path.join(project_root, "output", "survey_47_test_sld.dxf")

    # Call draw_sld_dxf
    draw_sld_dxf(graph, layout_positions, output_path)

    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()
    dxf_exists = os.path.exists(output_path) and os.path.getsize(output_path) > 0

    print("=================================================================================")
    print("                             DXF DRAWING ENGINE TEST RESULTS")
    print("=================================================================================")
    if dxf_exists:
        print("DXF Generation: PASS")
    else:
        print("DXF Generation: FAIL")

    print(f"Output Path: {output_path}")
    print(f"Node Count:  {node_count}")
    print(f"Edge Count:  {edge_count}")
    if dxf_exists:
        print(f"DXF File Size: {os.path.getsize(output_path)} bytes")
    print("=================================================================================")


if __name__ == "__main__":
    test_dxf_drawing_engine()
