"""
All Neo4j Cypher queries for the Research Intelligence System.
Implementations split into submodules; this file is the single public interface
so that routes always import from backend.graph.queries per CursorRules.
"""
from backend.graph._queries_nodes import (
    create_paper_node,
    update_paper_node_metadata,
    create_entity_node,
    create_mentions_relation,
    create_entity_relation,
    create_citation_edge,
    create_similarity_edge,
    upsert_node,
    upsert_edge,
)
from backend.graph._queries_search import (
    get_neighbors,
    find_path,
    get_subgraph,
    get_full_graph_for_visualization,
    find_bridges,
    get_community_papers,
)

__all__ = [
    "create_paper_node",
    "update_paper_node_metadata",
    "create_entity_node",
    "create_mentions_relation",
    "create_entity_relation",
    "create_citation_edge",
    "create_similarity_edge",
    "upsert_node",
    "upsert_edge",
    "get_neighbors",
    "find_path",
    "get_subgraph",
    "get_full_graph_for_visualization",
    "find_bridges",
    "get_community_papers",
]
