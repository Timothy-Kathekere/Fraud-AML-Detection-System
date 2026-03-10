"""
Training script for unsupervised anomaly detector.
"""
import logging
import pandas as pd
from argparse import ArgumentParser
from sklearn.metrics import confusion_matrix
from models.unsupervised.anomaly_detector import AnomalyDetector
from feature_engineering.feature_schema import FeatureSchema
from data_pipeline.batch_loader import HistoricalDataLoader
from database.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_unsupervised_model(data_path: str = None, contamination: float = 0.05):
    """Train unsupervised anomaly detector."""
    logger.info("Starting unsupervised model training...")
    
    # Load data
    if data_path:
        loader = HistoricalDataLoader()
        df = loader.load_from_csv(data_path)
    else:
        db_manager = DatabaseManager()
        query = "SELECT * FROM transactions LIMIT 100000"
        loader = HistoricalDataLoader(db_manager)
        df = loader.load_from_db(query)
    
    logger.info(f"Loaded {len(df)} transactions")
    
    # Prepare features
    feature_names = FeatureSchema.get_numerical_features()
    X = df[feature_names].fillna(0)
    
    # Train model
    model = AnomalyDetector(contamination=contamination)
    results = model.train(X)
    
    logger.info(f"Model trained: {results}")
    
    # Save model
    model.save("models/unsupervised/model_artifacts/anomaly_detector.pkl")
    
    logger.info("Unsupervised model training completed!")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data_path", type=str, help="Path to training data CSV")
    parser.add_argument("--contamination", type=float, default=0.05)
    
    args = parser.parse_args()
    train_unsupervised_model(args.data_path, args.contamination)