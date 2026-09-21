from typing import Dict, Any, Optional, List
import networkx as nx


def find_source_node(graph: nx.Graph) -> Optional[str]:
    """Auto-detect the start/source node in an electrical graph.

    Checks node attributes for category 'SUBSTATION', node ID keywords ('SOURCE', 'SS'),
    or falls back to a degree-1 leaf node.
    """
    if not graph or graph.number_of_nodes() == 0:
        return None

    # 1. Search by asset_category == 'SUBSTATION'
    for node_id, data in graph.nodes(data=True):
        category = str(data.get("asset_category", "")).upper()
        if category == "SUBSTATION":
            return node_id

    # 2. Search by node ID keywords
    for node_id in graph.nodes():
        node_str = str(node_id).upper()
        if "SOURCE" in node_str or "SUBSTATION" in node_str or "_SS" in node_str:
            return node_id

    # 3. Search for degree-1 leaf node
    degree_ones = [n for n, d in graph.degree() if d == 1]
    if degree_ones:
        return degree_ones[0]

    # 4. Fallback to first node
    return next(iter(graph.nodes()))


def generate_sld_layout(
    graph: nx.Graph,
    source_node_id: Optional[str] = None,
    x_spacing: float = 100.0,
    y_spacing: float = 120.0,
    max_row_width: float = 1000.0,
    max_nodes_per_row: Optional[int] = 10,
    label_offset: float = 15.0,
    distance_offset: float = 8.0,
    base_y: float = 0.0,
    start_x: float = 0.0,
    snake_pattern: bool = True,
    **kwargs: Any,
) -> Dict[str, Dict[str, float]]:
    """Generate a deterministic multi-row schematic (x, y) layout for an electrical graph.

    Traverses the electrical graph starting from the source/substation node following
    topological connectivity and arranges nodes into a compact, serpentine/page-friendly
    multi-row grid layout.

    Args:
        graph: NetworkX electrical graph.
        source_node_id: Optional explicit ID of the source node. Auto-detected if None.
        x_spacing: Configurable horizontal distance between consecutive nodes (default: 100.0).
        y_spacing: Configurable vertical distance between consecutive rows (default: 120.0).
        max_row_width: Maximum horizontal width allowed per row (default: 1000.0).
        max_nodes_per_row: Maximum number of nodes per row (default: 10).
        label_offset: Configurable offset for node labels (default: 15.0).
        distance_offset: Configurable offset for edge distance labels (default: 8.0).
        base_y: Base vertical Y coordinate for the first row (default: 0.0).
        start_x: Starting horizontal X coordinate for the source node (default: 0.0).
        snake_pattern: If True, alternates row direction (L->R then R->L) for a continuous
            serpentine feeder layout (default: True).
        **kwargs: Additional alias arguments:
            - horizontal_node_spacing: Alias for x_spacing
            - vertical_row_spacing: Alias for y_spacing
            - distance_label_offset: Alias for distance_offset

    Returns:
        A dictionary mapping node_id to {"x": float, "y": float}.
    """
    layout: Dict[str, Dict[str, float]] = {}

    if not graph or graph.number_of_nodes() == 0:
        return layout

    # Handle alias kwargs if passed
    if "horizontal_node_spacing" in kwargs:
        x_spacing = float(kwargs["horizontal_node_spacing"])
    if "vertical_row_spacing" in kwargs:
        y_spacing = float(kwargs["vertical_row_spacing"])
    if "distance_label_offset" in kwargs:
        distance_offset = float(kwargs["distance_label_offset"])

    # Identify source node
    start_node = source_node_id or find_source_node(graph)

    # Determine ordered nodes list via topological traversal (DFS)
    visited = set()
    ordered_nodes: List[str] = []

    if start_node in graph:
        ordered_nodes = list(nx.dfs_preorder_nodes(graph, source=start_node))
        visited.update(ordered_nodes)

    # Append any remaining disconnected components
    remaining_nodes = [n for n in graph.nodes() if n not in visited]
    while remaining_nodes:
        comp_start = remaining_nodes[0]
        comp_nodes = list(nx.dfs_preorder_nodes(graph, source=comp_start))
        ordered_nodes.extend(comp_nodes)
        visited.update(comp_nodes)
        remaining_nodes = [n for n in graph.nodes() if n not in visited]

    # Calculate effective nodes per row
    if max_nodes_per_row and max_nodes_per_row > 0:
        eff_nodes_per_row = max_nodes_per_row
    else:
        eff_nodes_per_row = max(1, int(max_row_width // x_spacing) + 1)

    # Split into rows and assign (x, y) coordinates
    for i, node_id in enumerate(ordered_nodes):
        row_idx = i // eff_nodes_per_row
        col_idx = i % eff_nodes_per_row

        row_y = base_y - row_idx * y_spacing

        if snake_pattern and (row_idx % 2 == 1):
            # Odd rows: Right-to-Left (serpentine continuous flow)
            x = start_x + (eff_nodes_per_row - 1 - col_idx) * x_spacing
        else:
            # Even rows: Left-to-Right
            x = start_x + col_idx * x_spacing

        layout[node_id] = {
            "x": round(x, 2),
            "y": round(row_y, 2),
        }

    return layout
