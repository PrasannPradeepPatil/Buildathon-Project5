
import networkx as nx
from typing import Dict, Any, List, Optional
from backend.neo4j_store import Neo4jStore

class GraphOperations:
    def __init__(self, neo4j_store: Neo4jStore):
        self.store = neo4j_store
    
    def compute_communities(self) -> bool:
        """Compute communities using NetworkX fallback (GDS integration can be added later)."""
        try:
            # Try Neo4j GDS first (if available)
            with self.store.driver.session() as session:
                try:
                    result = session.run("""
                        CALL gds.graph.exists('concept-graph') YIELD exists
                        RETURN exists
                    """)
                    # If GDS is available, use it
                    return self._compute_communities_gds()
                except Exception:
                    # Fall back to NetworkX
                    return self._compute_communities_networkx()
        except Exception:
            return self._compute_communities_networkx()
    
    def _compute_communities_gds(self) -> bool:
        """Use Neo4j GDS for community detection."""
        with self.store.driver.session() as session:
            try:
                # Create graph projection
                session.run("""
                    CALL gds.graph.project.cypher(
                        'concept-graph',
                        'MATCH (k:Concept) RETURN id(k) AS id',
                        'MATCH (k1:Concept)-[r:CO_OCCURS]-(k2:Concept) RETURN id(k1) AS source, id(k2) AS target, r.weight AS weight'
                    )
                """)
                
                # Run Louvain
                session.run("""
                    CALL gds.louvain.write('concept-graph', {
                        writeProperty: 'community'
                    })
                """)
                
                # Drop the graph
                session.run("CALL gds.graph.drop('concept-graph')")
                
                return True
            except Exception as e:
                print(f"GDS community detection failed: {e}")
                return False
    
    def _compute_communities_networkx(self) -> bool:
        """Fallback community detection using NetworkX."""
        try:
            # Get graph data
            graph_data = self.store.get_graph()
            nodes = graph_data['nodes']
            edges = graph_data['edges']
            
            if not nodes or not edges:
                return False
            
            # Create NetworkX graph
            G = nx.Graph()
            
            # Add nodes
            for node in nodes:
                G.add_node(node['id'], label=node['label'])
            
            # Add edges
            for edge in edges:
                if edge['source'] in G.nodes and edge['target'] in G.nodes:
                    weight = edge.get('weight', 1.0)
                    G.add_edge(edge['source'], edge['target'], weight=weight)
            
            # Compute communities using Louvain
            try:
                import community as community_louvain
                partition = community_louvain.best_partition(G)
            except ImportError:
                # Simple connected components if community detection library not available
                partition = {}
                for i, component in enumerate(nx.connected_components(G)):
                    for node in component:
                        partition[node] = i
            
            # Write communities back to Neo4j
            with self.store.driver.session() as session:
                for node_id, community_id in partition.items():
                    session.run("""
                        MATCH (k:Concept {id: $node_id})
                        SET k.community = $community_id
                    """, node_id=node_id, community_id=community_id)
            
            return True
            
        except Exception as e:
            print(f"NetworkX community detection failed: {e}")
            return False
