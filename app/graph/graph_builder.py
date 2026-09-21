from typing import Dict, Any, List
import networkx as nx
from app.data.models import FeederData, Asset, CableSegment


def build_electrical_graph(feeder_data: FeederData) -> nx.Graph:
    """Convert normalized FeederData into a NetworkX Graph.

    Adds every asset as a node with attributes: asset_id, label, asset_category,
    asset_type, condition_type, cable_spec, latitude, longitude.

    Creates edges ONLY from explicit feeder_data.cable_segments records.
    Does NOT invent edges if cable_segments is empty.
    """
    G = nx.Graph()

    # Add asset nodes
    for asset in feeder_data.assets:
        if asset.asset_id is not None:
            G.add_node(
                asset.asset_id,
                asset_id=asset.asset_id,
                label=asset.label,
                asset_category=asset.asset_category,
                asset_type=asset.asset_type,
                condition_type=asset.condition_type,
                cable_spec=asset.cable_spec,
                latitude=asset.latitude,
                longitude=asset.longitude,
            )

    # Add edges ONLY if explicit cable_segments exist
    for cs in feeder_data.cable_segments:
        if cs.from_asset and cs.to_asset:
            G.add_edge(
                cs.from_asset,
                cs.to_asset,
                cable_type=cs.cable_type,
                cable_size=cs.cable_size,
                length_m=cs.length_m,
            )

    return G


def get_graph_statistics(G: nx.Graph) -> Dict[str, Any]:
    """Return key topological statistics of the electrical graph."""
    node_count = G.number_of_nodes()
    edge_count = G.number_of_edges()
    connected_components = nx.number_connected_components(G) if node_count > 0 else 0
    isolated_nodes = list(nx.isolates(G))

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "connected_components": connected_components,
        "isolated_node_count": len(isolated_nodes),
        "isolated_nodes": isolated_nodes,
    }


def validate_electrical_graph(feeder_data: FeederData, G: nx.Graph) -> List[str]:
    """Validate graph structure against raw FeederData and return a list of warnings."""
    warnings = []

    # 1. Check duplicate asset IDs in feeder_data.assets
    asset_ids = [a.asset_id for a in feeder_data.assets if a.asset_id is not None]
    seen_ids = set()
    dup_ids = set()
    for aid in asset_ids:
        if aid in seen_ids:
            dup_ids.add(aid)
        seen_ids.add(aid)

    if dup_ids:
        warnings.append(f"Duplicate asset IDs found in FeederData: {sorted(list(dup_ids))}")

    # 2. Check cable segment references to unknown asset IDs & self-loops
    node_set = set(G.nodes)
    for idx, cs in enumerate(feeder_data.cable_segments, 1):
        if not cs.from_asset or not cs.to_asset:
            warnings.append(f"Cable segment #{idx} has missing from_asset or to_asset (from: {cs.from_asset}, to: {cs.to_asset})")
            continue

        if cs.from_asset not in node_set:
            warnings.append(f"Cable segment #{idx} references unknown from_asset ID '{cs.from_asset}'")

        if cs.to_asset not in node_set:
            warnings.append(f"Cable segment #{idx} references unknown to_asset ID '{cs.to_asset}'")

        if cs.from_asset == cs.to_asset:
            warnings.append(f"Cable segment #{idx} is a self-loop edge on asset ID '{cs.from_asset}'")

    # Add any graph-level validation warnings stored during build
    if "warnings" in G.graph and isinstance(G.graph["warnings"], list):
        warnings.extend(G.graph["warnings"])

    return warnings


def build_graph_from_ordered_topology(
    feeder_data: FeederData,
    ordered_asset_ids: List[str],
    source_node: Optional[Dict[str, Any]] = None,
    span_distances: Optional[List[float]] = None,
) -> nx.Graph:
    """Build an undirected electrical graph using an explicit ordered sequence of asset IDs.

    - Adds every feeder asset as a node.
    - Adds an optional source/substation node if provided.
    - Connects consecutive items in the ordered sequence with edges.
    - Stores span distances on edges as 'length_m' attribute when supplied.
    - Validates asset IDs and span distance counts, recording warnings in G.graph['warnings'].
    """
    warnings: List[str] = []
    G = nx.Graph()

    # 1. Add every feeder asset as a node
    asset_map = {}
    for asset in feeder_data.assets:
        if asset.asset_id is not None:
            asset_map[asset.asset_id] = asset
            G.add_node(
                asset.asset_id,
                asset_id=asset.asset_id,
                label=asset.label,
                asset_category=asset.asset_category,
                asset_type=asset.asset_type,
                condition_type=asset.condition_type,
                cable_spec=asset.cable_spec,
                latitude=asset.latitude,
                longitude=asset.longitude,
            )

    # 2. Add optional source node if provided
    source_id = None
    if source_node and isinstance(source_node, dict):
        source_id = source_node.get("node_id") or source_node.get("asset_id") or "SOURCE_SS"
        G.add_node(
            source_id,
            asset_id=source_id,
            label=source_node.get("label", "Substation"),
            asset_category=source_node.get("asset_category", "SUBSTATION"),
            asset_type=source_node.get("asset_type", "SUBSTATION"),
            condition_type=source_node.get("condition_type", "existing"),
            latitude=source_node.get("latitude"),
            longitude=source_node.get("longitude"),
        )

    # 3. Construct full ordered sequence
    sequence = []
    if source_id:
        sequence.append(source_id)

    for aid in ordered_asset_ids:
        if aid == source_id:
            continue
        if aid not in asset_map:
            warnings.append(f"Ordered asset ID '{aid}' not found in feeder_data.assets")
        sequence.append(aid)

    # 4. Validate span distances count
    num_spans = max(0, len(sequence) - 1)
    if span_distances is not None:
        if len(span_distances) != num_spans:
            warnings.append(
                f"Supplied span_distances count ({len(span_distances)}) does not match required span count ({num_spans})"
            )

    # 5. Create edges between consecutive items
    for i in range(num_spans):
        from_node = sequence[i]
        to_node = sequence[i + 1]

        edge_attrs = {}
        if span_distances is not None and i < len(span_distances):
            edge_attrs["length_m"] = span_distances[i]

        if G.has_edge(from_node, to_node):
            warnings.append(f"Duplicate edge creation attempt between '{from_node}' and '{to_node}'")
        else:
            G.add_edge(from_node, to_node, **edge_attrs)

    G.graph["warnings"] = warnings
    return G

