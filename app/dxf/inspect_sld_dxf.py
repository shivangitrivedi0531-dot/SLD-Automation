import os
import sys
import ezdxf


def inspect_dxf(dxf_path: str):
    """Inspect DXF entities, layers, text labels, and distance labels."""
    if not os.path.exists(dxf_path):
        print(f"Error: DXF file not found at {dxf_path}")
        print("DXF Inspection: FAIL")
        return

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    lines = list(msp.query("LINE"))
    circles = list(msp.query("CIRCLE"))
    texts = list(msp.query("TEXT"))
    mtexts = list(msp.query("MTEXT"))
    polylines = list(msp.query("LWPOLYLINE"))

    layer_names = [layer.dxf.name for layer in doc.layers]

    # Categorize text entities
    label_texts = []
    distance_texts = []

    for text in texts:
        content = text.dxf.text
        layer = text.dxf.layer
        if layer == "SLD_DISTANCE" or content.endswith(" m"):
            distance_texts.append(content)
        elif layer in ("SLD_LABEL", "SLD_SOURCE"):
            label_texts.append(content)

    print("=================================================================================")
    print("                             DXF INSPECTION REPORT")
    print("=================================================================================")
    print(f"number of LINE entities:   {len(lines)}")
    print(f"number of CIRCLE entities: {len(circles)}")
    print(f"number of TEXT entities:   {len(texts)}")
    print(f"number of MTEXT entities:  {len(mtexts)}")
    print(f"number of layers:          {len(layer_names)}")
    print("---------------------------------------------------------------------------------")
    print("Layer Names:")
    for l_name in layer_names:
        print(f"  - {l_name}")
    print("---------------------------------------------------------------------------------")

    print("First 10 Text Labels:")
    for idx, txt in enumerate(label_texts[:10], 1):
        print(f"  {idx}. {txt}")

    print("---------------------------------------------------------------------------------")
    print("First 10 Distance Labels:")
    for idx, dist in enumerate(distance_texts[:10], 1):
        print(f"  {idx}. {dist}")

    print("=================================================================================")

    # Checks
    feeder_lines_exist = len(lines) == 43
    node_symbols_exist = len(circles) == 43
    source_symbol_exists = len(polylines) >= 1 or any(t.dxf.layer == "SLD_SOURCE" for t in texts)
    node_labels_exist = len(label_texts) >= 44
    distance_labels_exist = len(distance_texts) == 43
    title_exists = any("JOGNINATH FEEDER" in t.dxf.text for t in texts)
    node_count_ok = (len(circles) + 1) == 44
    edge_count_ok = len(lines) == 43

    all_passed = (
        feeder_lines_exist
        and node_symbols_exist
        and source_symbol_exists
        and node_labels_exist
        and distance_labels_exist
        and title_exists
        and node_count_ok
        and edge_count_ok
    )

    if all_passed:
        print("DXF Inspection: PASS")
    else:
        print("DXF Inspection: FAIL")


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    dxf_path = os.path.join(project_root, "output", "survey_47_test_sld.dxf")
    inspect_dxf(dxf_path)
