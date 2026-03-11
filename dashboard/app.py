import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Streamlit dashboard for fraud detection monitoring.
"""
import streamlit as st # type: ignore
import pandas as pd
import plotly.graph_objects as go # type: ignore
from datetime import datetime, timedelta
import requests # type: ignore
from database.db_manager import DatabaseManager

# Page config
st.set_page_config(page_title="Fraud Detection Dashboard", layout="wide")

# Initialize
db_manager = DatabaseManager()
api_url = "http://localhost:8000/api"


def main():
    st.title("🚨 Fraud Detection & AML System Dashboard")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Alerts", "Transactions", "Network Analysis", "Model Performance"]
    )
    
    if page == "Overview":
        show_overview()
    elif page == "Alerts":
        show_alerts()
    elif page == "Transactions":
        show_transactions()
    elif page == "Network Analysis":
        show_network_analysis()
    elif page == "Model Performance":
        show_model_performance()


def show_overview():
    """Overview page."""
    st.header("System Overview")
    
    try:
        # Get metrics
        response = requests.get(f"{api_url}/dashboard/metrics")
        metrics = response.json()
        
        # Metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Transactions (24h)",
                f"{metrics.get('total_transactions_24h', 0):,}"
            )
        
        with col2:
            st.metric(
                "Fraud Detections",
                f"{metrics.get('fraud_detections_24h', 0):,}"
            )
        
        with col3:
            st.metric(
                "AML Alerts",
                f"{metrics.get('aml_alerts_24h', 0):,}"
            )
        
        with col4:
            st.metric(
                "Avg Fraud Score",
                f"{metrics.get('avg_fraud_score', 0):.2%}"
            )
        
        # Timeline
        st.subheader("Alert Timeline (24h)")
        response = requests.get(f"{api_url}/dashboard/alerts-timeline?hours=24")
        timeline = response.json()
        
        if timeline.get('timeline'):
            times = list(timeline['timeline'].keys())
            counts = list(timeline['timeline'].values())
            
            fig = go.Figure(data=[go.Scatter(x=times, y=counts, mode='lines+markers')])
            fig.update_layout(title="Alerts Over Time", xaxis_title="Time", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading overview: {str(e)}")


def show_alerts():
    """Alerts page."""
    st.header("Active Alerts")
    
    try:
        response = requests.get(f"{api_url}/alerts/open?limit=100")
        alerts = response.json().get('alerts', [])
        
        if alerts:
            df = pd.DataFrame(alerts)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No active alerts")
    
    except Exception as e:
        st.error(f"Error loading alerts: {str(e)}")


def show_transactions():
    """Transactions page."""
    st.header("Recent Transactions")
    
    try:
        from database.models import Transaction
        
        session = db_manager.get_session()
        transactions = session.query(Transaction).order_by(
            Transaction.timestamp.desc()
        ).limit(100).all()
        
        data = []
        for txn in transactions:
            data.append({
                'Transaction ID': txn.transaction_id,
                'From': txn.from_account,
                'To': txn.to_account,
                'Amount': f"${txn.amount:,.2f}",
                'Fraud Score': f"{txn.fraud_score:.2%}",
                'Time': txn.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        session.close()
    
    except Exception as e:
        st.error(f"Error loading transactions: {str(e)}")


def show_network_analysis():
    """Network analysis page."""
    st.header("Network Analysis")
    
    st.info("Network analysis and graph visualization coming soon...")


def show_model_performance():
    """Model performance page."""
    st.header("Model Performance")
    
    try:
        from database.models import ModelPerformance
        
        session = db_manager.get_session()
        performances = session.query(ModelPerformance).order_by(
            ModelPerformance.recorded_at.desc()
        ).limit(10).all()
        
        data = []
        for perf in performances:
            data.append({
                'Model': perf.model_name,
                'Version': perf.model_version,
                'Accuracy': f"{perf.accuracy:.2%}",
                'Precision': f"{perf.precision:.2%}",
                'Recall': f"{perf.recall:.2%}",
                'F1 Score': f"{perf.f1_score:.2%}",
                'AUC-ROC': f"{perf.auc_roc:.2%}",
                'Recorded': perf.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        session.close()
    
    except Exception as e:
        st.error(f"Error loading model performance: {str(e)}")


if __name__ == "__main__":
    main()