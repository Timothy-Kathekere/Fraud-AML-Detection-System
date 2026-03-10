"""
Detect suspicious patterns in transaction networks.
"""
import logging
from typing import List, Dict, Tuple, Set
import networkx as nx # type: ignore
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SuspiciousPatternDetector:
    """Detects money laundering patterns in transaction networks."""
    
    def __init__(self, graph_builder):
        """
        Initialize pattern detector.
        
        Args:
            graph_builder: TransactionGraphBuilder instance
        """
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph
    
    def detect_circular_transactions(self, max_cycle_length: int = 6) -> List[List[str]]:
        """
        Detect circular money flows (potential layering).
        
        Args:
            max_cycle_length: Maximum cycle length to detect
            
        Returns:
            List of cycles (each cycle is a list of accounts)
        """
        try:
            # Find all simple cycles
            cycles = list(nx.simple_cycles(self.graph))
            
            # Filter by length and remove trivial cycles
            suspicious_cycles = [
                cycle for cycle in cycles
                if 2 < len(cycle) <= max_cycle_length
            ]
            
            logger.info(f"Detected {len(suspicious_cycles)} suspicious cycles")
            return suspicious_cycles
        
        except Exception as e:
            logger.error(f"Error detecting cycles: {str(e)}")
            return []
    
    def detect_structuring_patterns(self, threshold_amount: float = 10000,
                                   max_days: int = 7) -> List[Dict]:
        """
        Detect structuring (smurfing) - multiple small transactions to avoid reporting.
        
        Args:
            threshold_amount: Amount threshold for individual transactions
            max_days: Time window for analysis
            
        Returns:
            List of structuring patterns
        """
        patterns = []
        
        # Group transactions by sender
        sender_groups = defaultdict(list)
        
        for from_acc, to_acc, data in self.graph.edges(data=True):
            for txn in data.get('transactions', []):
                if txn['amount'] < threshold_amount:
                    sender_groups[from_acc].append({
                        'to_account': to_acc,
                        'amount': txn['amount'],
                        'timestamp': txn['timestamp']
                    })
        
        # Detect patterns where account sends many small transactions
        for sender, transactions in sender_groups.items():
            if len(transactions) >= 5:  # Suspicious pattern threshold
                total_amount = sum(t['amount'] for t in transactions)
                
                if total_amount > threshold_amount * 2:
                    patterns.append({
                        'type': 'structuring',
                        'sender': sender,
                        'num_transactions': len(transactions),
                        'total_amount': total_amount,
                        'recipients': list(set(t['to_account'] for t in transactions)),
                        'severity': min(1.0, len(transactions) / 20.0)
                    })
        
        logger.info(f"Detected {len(patterns)} structuring patterns")
        return patterns
    
    def detect_rapid_movement(self, time_window_minutes: int = 60,
                             min_hops: int = 3) -> List[Dict]:
        """
        Detect rapid movement of funds through multiple accounts (potential layering).
        
        Args:
            time_window_minutes: Time window for tracking fund movement
            min_hops: Minimum number of hops to consider suspicious
            
        Returns:
            List of rapid movement patterns
        """
        patterns = []
        
        cutoff_time = (datetime.utcnow() - timedelta(minutes=time_window_minutes)).isoformat()
        
        for from_acc, to_acc, data in self.graph.edges(data=True):
            recent_transactions = [
                t for t in data['transactions']
                if t['timestamp'] and t['timestamp'] >= cutoff_time
            ]
            
            if recent_transactions:
                # Try to find paths from this starting account
                try:
                    paths = list(nx.all_simple_paths(
                        self.graph,
                        from_acc,
                        max_length=min_hops + 1
                    ))
                    
                    for path in paths:
                        if len(path) > min_hops:
                            total_amount = sum(
                                self.graph[path[i]][path[i+1]]['weight']
                                for i in range(len(path) - 1)
                            )
                            
                            patterns.append({
                                'type': 'rapid_movement',
                                'path': path,
                                'path_length': len(path),
                                'total_amount': total_amount,
                                'severity': min(1.0, len(path) / 10.0)
                            })
                
                except nx.NetworkXNoPath:
                    pass
        
        logger.info(f"Detected {len(patterns)} rapid movement patterns")
        return patterns
    
    def detect_layering_networks(self, min_density: float = 0.3,
                                min_size: int = 4) -> List[Dict]:
        """
        Detect layering networks - densely connected subgraphs.
        
        Args:
            min_density: Minimum density threshold
            min_size: Minimum subgraph size
            
        Returns:
            List of layering networks
        """
        patterns = []
        
        # Find strongly connected components
        sccs = nx.strongly_connected_components(self.graph)
        
        for component in sccs:
            if len(component) >= min_size:
                subgraph = self.graph_builder.get_subgraph(component)
                density = nx.density(subgraph)
                
                if density >= min_density:
                    # Calculate total volume
                    total_volume = sum(
                        data['weight']
                        for _, _, data in subgraph.edges(data=True)
                    )
                    
                    patterns.append({
                        'type': 'layering_network',
                        'accounts': list(component),
                        'network_size': len(component),
                        'density': density,
                        'total_volume': total_volume,
                        'severity': min(1.0, density)
                    })
        
        logger.info(f"Detected {len(patterns)} layering networks")
        return patterns
    
    def detect_hub_accounts(self, degree_threshold: float = 0.3,
                           amount_threshold: float = 1000000) -> List[Dict]:
        """
        Detect hub accounts - accounts with high in/out degree and volume.
        
        Args:
            degree_threshold: Degree centrality threshold
            amount_threshold: Amount volume threshold
            
        Returns:
            List of hub accounts
        """
        patterns = []
        
        if len(self.graph) == 0:
            return patterns
        
        # Calculate centrality
        degree_centrality = nx.degree_centrality(self.graph)
        
        for account, centrality in degree_centrality.items():
            if centrality >= degree_threshold:
                stats = self.graph_builder.get_account_statistics(account)
                
                if stats.get('in_amount', 0) + stats.get('out_amount', 0) > amount_threshold:
                    patterns.append({
                        'type': 'hub_account',
                        'account': account,
                        'degree_centrality': centrality,
                        'in_degree': stats['in_degree'],
                        'out_degree': stats['out_degree'],
                        'in_amount': stats['in_amount'],
                        'out_amount': stats['out_amount'],
                        'severity': min(1.0, centrality * 1.5)
                    })
        
        logger.info(f"Detected {len(patterns)} hub accounts")
        return patterns
    
    def extract_graph_features(self, from_account: str, to_account: str) -> Dict[str, float]:
        """
        Extract graph-based features for a transaction.
        
        Args:
            from_account: Source account
            to_account: Destination account
            
        Returns:
            Dictionary of graph features
        """
        features = {
            'graph_clustering_coefficient': 0.0,
            'graph_degree_centrality': 0.0,
            'graph_betweenness_centrality': 0.0,
            'is_in_suspicious_network': 0.0,
            'network_risk_propagation_score': 0.0,
            'circular_flow_likelihood': 0.0,
            'layering_pattern_score': 0.0,
        }
        
        if len(self.graph) == 0:
            return features
        
        try:
            # Clustering coefficient
            if from_account in self.graph:
                features['graph_clustering_coefficient'] = nx.clustering(
                    self.graph.to_undirected(), from_account
                )
            
            # Degree centrality
            degree_cent = nx.degree_centrality(self.graph)
            features['graph_degree_centrality'] = degree_cent.get(from_account, 0.0)
            
            # Betweenness centrality (expensive for large graphs)
            if len(self.graph) < 1000:
                betweenness_cent = nx.betweenness_centrality(self.graph)
                features['graph_betweenness_centrality'] = betweenness_cent.get(from_account, 0.0)
            
            # Check if accounts are in suspicious network
            suspicious_cycles = self.detect_circular_transactions()
            suspicious_accounts = set()
            for cycle in suspicious_cycles:
                suspicious_accounts.update(cycle)
            
            if from_account in suspicious_accounts or to_account in suspicious_accounts:
                features['is_in_suspicious_network'] = 1.0
            
            # Network risk propagation
            if from_account in self.graph and to_account in self.graph:
                try:
                    # Check if there's a path back (indicating potential circular flow)
                    if nx.has_path(self.graph, to_account, from_account):
                        features['circular_flow_likelihood'] = 0.8
                        features['layering_pattern_score'] = 0.7
                except:
                    pass
            
            # Network risk score
            num_neighbors = len(list(self.graph.neighbors(from_account)))
            features['network_risk_propagation_score'] = min(1.0, num_neighbors / 100.0)
        
        except Exception as e:
            logger.error(f"Error extracting graph features: {str(e)}")
        
        return features