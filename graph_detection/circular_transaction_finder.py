"""
Specialized detection of circular transaction patterns and cycles.
"""
import logging
from typing import List, Dict, Set, Tuple
import networkx as nx # type: ignore
from datetime import datetime

logger = logging.getLogger(__name__)


class CircularTransactionFinder:
    """Finds and analyzes circular transaction patterns."""
    
    def __init__(self, graph_builder):
        """
        Initialize finder.
        
        Args:
            graph_builder: TransactionGraphBuilder instance
        """
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph
    
    def find_all_cycles(self, max_length: int = 10) -> List[List[str]]:
        """
        Find all cycles in the network up to max length.
        
        Args:
            max_length: Maximum cycle length
            
        Returns:
            List of cycles
        """
        try:
            all_cycles = list(nx.simple_cycles(self.graph))
            
            # Filter by length
            filtered_cycles = [
                cycle for cycle in all_cycles
                if len(cycle) <= max_length
            ]
            
            logger.info(f"Found {len(filtered_cycles)} cycles")
            return filtered_cycles
        
        except Exception as e:
            logger.error(f"Error finding cycles: {str(e)}")
            return []
    
    def find_self_loops(self) -> List[Tuple[str, float, int]]:
        """
        Find self-loops (account sending money to itself).
        
        Returns:
            List of (account, amount, count) tuples
        """
        self_loops = []
        
        for account in self.graph.nodes():
            if self.graph.has_edge(account, account):
                edge_data = self.graph[account][account]
                self_loops.append((
                    account,
                    edge_data['weight'],
                    edge_data['count']
                ))
        
        logger.info(f"Found {len(self_loops)} self-loops")
        return self_loops
    
    def find_two_node_cycles(self) -> List[Tuple[str, str, float, float]]:
        """
        Find two-node cycles (A->B->A).
        
        Returns:
            List of (account_a, account_b, amount_a_to_b, amount_b_to_a) tuples
        """
        two_node_cycles = []
        
        for node_a in self.graph.nodes():
            for node_b in self.graph.successors(node_a):
                if self.graph.has_edge(node_b, node_a):
                    amount_a_to_b = self.graph[node_a][node_b]['weight']
                    amount_b_to_a = self.graph[node_b][node_a]['weight']
                    
                    two_node_cycles.append((
                        node_a,
                        node_b,
                        amount_a_to_b,
                        amount_b_to_a
                    ))
        
        logger.info(f"Found {len(two_node_cycles)} two-node cycles")
        return two_node_cycles
    
    def analyze_cycle_characteristics(self, cycle: List[str]) -> Dict:
        """
        Analyze characteristics of a specific cycle.
        
        Args:
            cycle: List of accounts in cycle
            
        Returns:
            Dictionary of cycle characteristics
        """
        characteristics = {
            'cycle': cycle,
            'length': len(cycle),
            'total_amount': 0.0,
            'transactions': [],
            'average_amount': 0.0,
            'is_balanced': False,
        }
        
        # Calculate cycle metrics
        for i in range(len(cycle)):
            from_acc = cycle[i]
            to_acc = cycle[(i + 1) % len(cycle)]
            
            if self.graph.has_edge(from_acc, to_acc):
                edge_data = self.graph[from_acc][to_acc]
                amount = edge_data['weight']
                
                characteristics['total_amount'] += amount
                characteristics['transactions'].append({
                    'from': from_acc,
                    'to': to_acc,
                    'amount': amount,
                    'count': edge_data['count']
                })
        
        if len(cycle) > 0:
            characteristics['average_amount'] = characteristics['total_amount'] / len(cycle)
        
        # Check if cycle is balanced (each account roughly sends and receives same amount)
        flow_in = {}
        flow_out = {}
        
        for txn in characteristics['transactions']:
            flow_out[txn['from']] = flow_out.get(txn['from'], 0) + txn['amount']
            flow_in[txn['to']] = flow_in.get(txn['to'], 0) + txn['amount']
        
        # Check if balanced
        total_in = sum(flow_in.values())
        total_out = sum(flow_out.values())
        
        if total_in > 0 and total_out > 0:
            balance_ratio = min(total_in, total_out) / max(total_in, total_out)
            characteristics['is_balanced'] = balance_ratio > 0.9
        
        return characteristics
    
    def find_suspicious_cycles(self, min_amount: float = 50000,
                              max_length: int = 6) -> List[Dict]:
        """
        Find cycles that match suspicious characteristics.
        
        Args:
            min_amount: Minimum cycle amount to flag
            max_length: Maximum cycle length
            
        Returns:
            List of suspicious cycle analysis
        """
        suspicious = []
        
        cycles = self.find_all_cycles(max_length=max_length)
        
        for cycle in cycles:
            if len(cycle) >= 3:  # At least 3 nodes for meaningful cycle
                analysis = self.analyze_cycle_characteristics(cycle)
                
                if analysis['total_amount'] >= min_amount:
                    # Calculate suspicion score
                    suspicion_score = 0.0
                    
                    # Score based on cycle length (shorter is more suspicious)
                    if len(cycle) <= 3:
                        suspicion_score += 0.3
                    elif len(cycle) <= 5:
                        suspicion_score += 0.2
                    
                    # Score based on balance (balanced cycles more suspicious)
                    if analysis['is_balanced']:
                        suspicion_score += 0.4
                    
                    # Score based on amount
                    suspicion_score += min(0.3, analysis['total_amount'] / 1000000.0)
                    
                    analysis['suspicion_score'] = min(1.0, suspicion_score)
                    suspicious.append(analysis)
        
        logger.info(f"Found {len(suspicious)} suspicious cycles")
        return suspicious
    
    def detect_cycle_clusters(self) -> List[Dict]:
        """
        Detect clusters of related cycles (indicating larger laundering networks).
        
        Returns:
            List of cycle clusters
        """
        clusters = []
        
        cycles = self.find_all_cycles(max_length=8)
        cycle_nodes = [set(cycle) for cycle in cycles]
        
        # Find overlapping cycles
        processed = set()
        
        for i, nodes_i in enumerate(cycle_nodes):
            if i in processed:
                continue
            
            cluster = [cycles[i]]
            cluster_nodes = nodes_i.copy()
            
            for j in range(i + 1, len(cycle_nodes)):
                if j in processed:
                    continue
                
                nodes_j = cycle_nodes[j]
                
                # Check for overlap
                if len(nodes_i & nodes_j) >= 2:  # At least 2 common nodes
                    cluster.append(cycles[j])
                    cluster_nodes.update(nodes_j)
            
            if len(cluster) > 1:
                clusters.append({
                    'cluster_cycles': cluster,
                    'total_nodes': len(cluster_nodes),
                    'nodes': list(cluster_nodes),
                    'cluster_size': len(cluster)
                })
            
            processed.update(range(i, len(cycle_nodes)))
        
        logger.info(f"Found {len(clusters)} cycle clusters")
        return clusters