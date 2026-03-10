"""
Analyze money flow patterns and detect anomalies.
"""
import logging
from typing import Dict, List, Tuple, Set
import networkx as nx # type: ignore
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MoneyFlowAnalyzer:
    """Analyzes money flow patterns across the network."""
    
    def __init__(self, graph_builder):
        """
        Initialize money flow analyzer.
        
        Args:
            graph_builder: TransactionGraphBuilder instance
        """
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph
    
    def analyze_account_flow(self, account: str, depth: int = 3) -> Dict:
        """
        Analyze money flow in/out of an account.
        
        Args:
            account: Account ID
            depth: Depth of flow to analyze
            
        Returns:
            Flow analysis dictionary
        """
        analysis = {
            'account': account,
            'inflows': [],
            'outflows': [],
            'net_flow': 0.0,
            'flow_velocity': 0.0,
        }
        
        if account not in self.graph:
            return analysis
        
        # Analyze inflows
        for predecessor in self.graph.predecessors(account):
            edge_data = self.graph[predecessor][account]
            analysis['inflows'].append({
                'from': predecessor,
                'amount': edge_data['weight'],
                'transaction_count': edge_data['count']
            })
        
        # Analyze outflows
        for successor in self.graph.successors(account):
            edge_data = self.graph[account][successor]
            analysis['outflows'].append({
                'to': successor,
                'amount': edge_data['weight'],
                'transaction_count': edge_data['count']
            })
        
        # Calculate net flow
        total_inflow = sum(f['amount'] for f in analysis['inflows'])
        total_outflow = sum(f['amount'] for f in analysis['outflows'])
        analysis['net_flow'] = total_inflow - total_outflow
        
        # Flow velocity (how quickly money moves through)
        total_transactions = sum(f['transaction_count'] for f in analysis['inflows'])
        analysis['flow_velocity'] = total_transactions / max(1, total_inflow)
        
        return analysis
    
    def detect_round_tripping(self, min_similarity: float = 0.8) -> List[Dict]:
        """
        Detect round-tripping - money that comes and goes from same source.
        
        Args:
            min_similarity: Minimum similarity threshold for amounts
            
        Returns:
            List of round-trip patterns
        """
        patterns = []
        
        for account in self.graph.nodes():
            flow = self.analyze_account_flow(account)
            
            # Check if money comes in and goes back out in similar amounts
            for inflow in flow['inflows']:
                inflow_source = inflow['from']
                inflow_amount = inflow['amount']
                
                # Check if there's a return flow
                for outflow in flow['outflows']:
                    outflow_dest = outflow['to']
                    outflow_amount = outflow['amount']
                    
                    if inflow_source == outflow_dest:
                        similarity = min(inflow_amount, outflow_amount) / max(inflow_amount, outflow_amount)
                        
                        if similarity >= min_similarity:
                            patterns.append({
                                'type': 'round_tripping',
                                'intermediary': account,
                                'source': inflow_source,
                                'inflow_amount': inflow_amount,
                                'outflow_amount': outflow_amount,
                                'similarity': similarity,
                                'severity': similarity
                            })
        
        logger.info(f"Detected {len(patterns)} round-tripping patterns")
        return patterns
    
    def detect_conversion_chains(self, max_chain_length: int = 5) -> List[Dict]:
        """
        Detect conversion chains - sequences of currency conversions or wire transfers.
        
        Args:
            max_chain_length: Maximum chain length to detect
            
        Returns:
            List of conversion chain patterns
        """
        patterns = []
        
        # Find all paths in the graph
        for start_node in self.graph.nodes():
            try:
                for path_length in range(2, min(max_chain_length + 1, len(self.graph))):
                    for path in nx.all_simple_paths(
                        self.graph,
                        start_node,
                        max_length=path_length
                    ):
                        if len(path) >= 3:  # At least 2 conversions
                            total_amount = sum(
                                self.graph[path[i]][path[i+1]]['weight']
                                for i in range(len(path) - 1)
                            )
                            
                            patterns.append({
                                'type': 'conversion_chain',
                                'path': path,
                                'chain_length': len(path),
                                'total_amount': total_amount,
                                'severity': min(1.0, len(path) / 10.0)
                            })
            except nx.NetworkXNoPath:
                pass
        
        logger.info(f"Detected {len(patterns)} conversion chain patterns")
        return patterns
    
    def detect_time_based_anomalies(self, window_minutes: int = 60) -> List[Dict]:
        """
        Detect anomalies based on transaction timing.
        
        Args:
            window_minutes: Time window for analysis
            
        Returns:
            List of timing anomalies
        """
        anomalies = []
        
        cutoff_time = (datetime.utcnow() - timedelta(minutes=window_minutes)).isoformat()
        
        # Analyze transaction density in time windows
        time_buckets = defaultdict(list)
        
        for from_acc, to_acc, data in self.graph.edges(data=True):
            for txn in data['transactions']:
                if txn['timestamp'] and txn['timestamp'] >= cutoff_time:
                    time_bucket = txn['timestamp'][:13]  # Hour bucket
                    time_buckets[time_bucket].append({
                        'from': from_acc,
                        'to': to_acc,
                        'amount': txn['amount']
                    })
        
        # Detect unusual activity patterns
        for time_bucket, transactions in time_buckets.items():
            if len(transactions) > 100:  # Unusual spike
                total_amount = sum(t['amount'] for t in transactions)
                
                anomalies.append({
                    'type': 'timing_anomaly',
                    'time_bucket': time_bucket,
                    'transaction_count': len(transactions),
                    'total_amount': total_amount,
                    'severity': min(1.0, len(transactions) / 500.0)
                })
        
        logger.info(f"Detected {len(anomalies)} timing anomalies")
        return anomalies
    
    def calculate_flow_statistics(self) -> Dict:
        """
        Calculate overall network flow statistics.
        
        Returns:
            Dictionary of flow statistics
        """
        if len(self.graph) == 0:
            return {}
        
        total_volume = sum(
            data['weight']
            for _, _, data in self.graph.edges(data=True)
        )
        
        transaction_counts = [
            data['count']
            for _, _, data in self.graph.edges(data=True)
        ]
        
        return {
            'total_volume': total_volume,
            'total_transactions': sum(transaction_counts),
            'avg_transaction_amount': total_volume / max(1, sum(transaction_counts)),
            'avg_transactions_per_edge': sum(transaction_counts) / max(1, self.graph.number_of_edges()),
            'avg_out_degree': sum(dict(self.graph.out_degree()).values()) / max(1, len(self.graph)),
            'avg_in_degree': sum(dict(self.graph.in_degree()).values()) / max(1, len(self.graph)),
        }