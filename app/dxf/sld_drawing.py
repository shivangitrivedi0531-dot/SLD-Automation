import os
from typing import Dict, Any
import networkx as nx
import ezdxf


def draw_sld_dxf(
    graph: nx.Graph,
    layout_positions: Dict[str, Dict[str, float]],
    output_path: str,
) -> None:
    """Generate a valid DXF drawing for an electrical SLD graph and multi-row schematic layout.

    Args:
        graph: NetworkX electrical graph containing node attributes and edge distances.
        layout_positions: Dictionary mapping node_id to {"x": float, "y": float}.
        output_path: Target file path to save the generated DXF file.
    """
    # 1. Create new DXF document (AutoCAD 2010 format)
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # 2. Setup standard DXF layers
    doc.layers.new(name="SLD_LINE", dxfattribs={"color": 1})       # Red feeder lines
    doc.layers.new(name="SLD_NODE", dxfattribs={"color": 3})       # Green pole node symbols
    doc.layers.new(name="SLD_LABEL", dxfattribs={"color": 7})      # White/Black text labels
    doc.layers.new(name="SLD_DISTANCE", dxfattribs={"color": 2})   # Yellow distance text
    doc.layers.new(name="SLD_SOURCE", dxfattribs={"color": 5})     # Blue source/substation symbol

    # Calculate layout bounding box for title placement and drawing extents
    if layout_positions:
        x_vals = [pos["x"] for pos in layout_positions.values()]
        y_vals = [pos["y"] for pos in layout_positions.values()]
        min_x, max_x = min(x_vals), max(x_vals)
        min_y, max_y = min(y_vals), max(y_vals)
    else:
        min_x, max_x, min_y, max_y = 0.0, 900.0, -480.0, 0.0

    # 3. Add Drawing Title at top left of drawing bounding box
    title_text = "JOGNINATH FEEDER - SINGLE LINE DIAGRAM"
    title_entity = msp.add_text(
        title_text,
        height=6.0,
        dxfattribs={"layer": "SLD_LABEL"},
    )
    title_entity.set_placement((min_x, max_y + 30.0))

    # 4. Draw Edges (Feeder Line Segments & Distance Labels)
    for u, v, data in graph.edges(data=True):
        if u not in layout_positions or v not in layout_positions:
            continue

        p1 = layout_positions[u]
        p2 = layout_positions[v]
        x1, y1 = p1["x"], p1["y"]
        x2, y2 = p2["x"], p2["y"]

        # Draw feeder line connecting the two nodes (handles horizontal, vertical, and diagonal)
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "SLD_LINE"})

        # Display edge distance in meters if available
        length_m = data.get("length_m")
        if length_m is not None:
            mid_x = (x1 + x2) / 2.0
            mid_y = (y1 + y2) / 2.0
            dist_str = f"{length_m} m" if isinstance(length_m, (int, float)) else str(length_m)

            dx = x2 - x1
            dy = y2 - y1

            # Position distance text based on edge direction to avoid line overlap
            if abs(dx) >= abs(dy):
                # Predominantly horizontal edge -> offset text below line
                txt_x = mid_x - len(dist_str) * 0.9
                txt_y = mid_y - 8.0
            else:
                # Predominantly vertical edge -> offset text to the right of line
                txt_x = mid_x + 8.0
                txt_y = mid_y - 1.5

            txt = msp.add_text(
                dist_str,
                height=3.0,
                dxfattribs={"layer": "SLD_DISTANCE"},
            )
            txt.set_placement((txt_x, txt_y))

    # 5. Draw Nodes (Substation Source & Pole Symbols + Asset Labels)
    for nid, data in graph.nodes(data=True):
        if nid not in layout_positions:
            continue

        pos = layout_positions[nid]
        x, y = pos["x"], pos["y"]

        label = data.get("label") or str(nid)
        category = str(data.get("asset_category", "")).upper()

        is_source = category == "SUBSTATION" or "SOURCE" in str(nid).upper() or "S/S" in str(label).upper()

        if is_source:
            # Draw rectangular source/substation symbol
            box_size = 12.0
            half = box_size / 2.0
            points = [
                (x - half, y - half),
                (x + half, y - half),
                (x + half, y + half),
                (x - half, y + half),
            ]
            poly = msp.add_lwpolyline(points, dxfattribs={"layer": "SLD_SOURCE"})
            poly.close()

            # Add source label above box
            source_txt = label if label else "66 KV KATHWADA-2 S/S"
            txt = msp.add_text(
                source_txt,
                height=4.0,
                dxfattribs={"layer": "SLD_SOURCE"},
            )
            txt.set_placement((x - len(source_txt) * 1.0, y + 10.0))
        else:
            # Draw simple circular pole symbol
            msp.add_circle((x, y), radius=2.5, dxfattribs={"layer": "SLD_NODE"})

            # Display asset label above node
            txt = msp.add_text(
                label,
                height=3.5,
                dxfattribs={"layer": "SLD_LABEL"},
            )
            txt.set_placement((x - len(label) * 0.9, y + 6.0))

    # 6. Configure paper/view extents in document headers
    margin = 40.0
    doc.header["$EXTMIN"] = (min_x - margin, min_y - margin, 0.0)
    doc.header["$EXTMAX"] = (max_x + margin, max_y + margin + 40.0, 0.0)
    doc.header["$LIMMIN"] = (min_x - margin, min_y - margin)
    doc.header["$LIMMAX"] = (max_x + margin, max_y + margin + 40.0)

    # 7. Ensure target output directory exists and save DXF
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    doc.saveas(output_path)
