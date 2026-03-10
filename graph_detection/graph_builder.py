"""
Build and maintain transaction network graphs.
"""
import logging
from typing import Dict, List, Tuple, Optional, Set
import networkx as nx # type: ignore
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)


class TransactionGraphBuilder:
    """Builds directed graphs of transactions for network analysis."""
    
    def __init__(self):
        """Initialize graph builder."""
        self.graph = nx.DiGraph()
        self.transaction_counts = defaultdict(int)
        self.transaction_amounts = defaultdict(float)
        self.transaction_times = defaultdict(list)
    
    def add_transaction(self, from_account: str, to_account: str, 
                       amount: float, timestamp: str = None, 
                       transaction_id: str = None) -> None:
        """
        Add a transaction to the graph.
        
        Args:
            from_account: Source account
            to_account: Destination account
            amount: Transaction amount
            timestamp: Transaction timestamp
            transaction_id: Unique transaction ID
        """
        # Add nodes
        self.graph.add_node(from_account)
        self.graph.add_node(to_account)
        
        # Create edge key
        edge_key = (from_account, to_account)
        
        # Add edge with attributes
        if self.graph.has_edge(from_account, to_account):
            # Update existing edge
            edge_data = self.graph[from_account][to_account]
            edge_data['weight'] += amount
            edge_data['count'] += 1
            edge_data['transactions'].append({
                'id': transaction_id,
                'amount': amount,
                'timestamp': timestamp
            })
        else:
            # Create new edge
            self.graph.add_edge(
                from_account,
                to_account,
                weight=amount,
                count=1,
                transactions=[{
                    'id': transaction_id,
                    'amount': amount,
                    'timestamp': timestamp
                }],
                last_transaction=timestamp
            )
        
        # Update global tracking
        self.transaction_counts[edge_key] += 1
        self.transaction_amounts[edge_key] += amount
        if timestamp:
            self.transaction_times[edge_key].append(timestamp)
    
    def add_transactions_batch(self, transactions: List[Dict]) -> None:
        """
        Add batch of transactions to graph.
        
        Args:
            transactions: List of transaction dictionaries
        """
        for txn in transactions:
            self.add_transaction(
                from_account=txn['from_account'],
                to_account=txn['to_account'],
                amount=txn['amount'],
                timestamp=txn.get('timestamp'),
                transaction_id=txn.get('transaction_id')
            )
        
        logger.info(f"Added {len(transactions)} transactions to graph")
    
    def get_account_statistics(self, account: str) -> Dict[str, any]:
        """
        Get network statistics for an account.
        
        Args:
            account: Account ID
            
        Returns:
            Dictionary of statistics
        """
        if account not in self.graph:
            return {}
        
        stats = {
            'in_degree': self.graph.in_degree(account),
            'out_degree': self.graph.out_degree(account),
            'total_degree': self.graph.degree(account),
            'in_amount': sum(self.graph[pred][account]['weight'] 
                           for pred in self.graph.predecessors(account)),
            'out_amount': sum(self.graph[account][succ]['weight'] 
                            for succ in self.graph.successors(account)),
        }
        
        return stats
    
    def get_subgraph(self, accounts: Set[str]) -> nx.DiGraph:
        """
        Get subgraph for specific accounts.
        
        Args:
            accounts: Set of account IDs
            
        Returns:
            Subgraph
        """
        return self.graph.subgraph(accounts).copy()
    
    def get_temporal_subgraph(self, days: int = 7) -> nx.DiGraph:
        """
        Get subgraph for transactions in last N days.
        
        Args:
            days: Number of days to include
            
        Returns:
            Temporal subgraph
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Create new graph with filtered edges
        temporal_graph = nx.DiGraph()
        
        for from_acc, to_acc, data in self.graph.edges(data=True):
            # Check if any transaction is within timeframe
            recent_txns = [
                t for t in data['transactions']
                if t['timestamp'] and t['timestamp'] >= cutoff_date
            ]
            
            if recent_txns:
                temporal_graph.add_edge(
                    from_acc,
                    to_acc,
                    weight=sum(t['amount'] for t in recent_txns),
                    count=len(recent_txns),
                    transactions=recent_txns
                )
        
        return temporal_graph
    
    def get_graph_metrics(self) -> Dict[str, any]:
        """Get overall graph metrics."""
        if len(self.graph) == 0:
            return {}
        
        return {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_strongly_connected': nx.is_strongly_connected(self.graph),
            'num_strongly_connected_components': nx.number_strongly_connected_components(self.graph),
            'num_weakly_connected_components': nx.number_weakly_connected_components(self.graph),
        }
    
    def reset(self) -> None:
        """Clear the graph."""
        self.graph.clear()
        self.transaction_counts.clear()
        self.transaction_amounts.clear()
        self.transaction_times.clear()