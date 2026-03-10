"""
Training script for supervised fraud classifier.
"""
import logging
import pandas as pd
from argparse import ArgumentParser
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from models.supervised.fraud_classifier import FraudClassifier
from feature_engineering.feature_schema import FeatureSchema
from data_pipeline.batch_loader import HistoricalDataLoader
from database.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_supervised_model(data_path: str = None, test_size: float = 0.2):
    """Train supervised fraud classifier."""
    logger.info("Starting supervised model training...")
    
    # Load data
    if data_path:
        loader = HistoricalDataLoader()
        df = loader.load_from_csv(data_path)
    else:
        # Load from database
        db_manager = DatabaseManager()
        query = "SELECT * FROM transactions WHERE label IS NOT NULL"
        loader = HistoricalDataLoader(db_manager)
        df = loader.load_from_db(query)
    
    logger.info(f"Loaded {len(df)} labeled transactions")
    
    # Prepare features
    feature_names = FeatureSchema.get_numerical_features()
    X = df[feature_names].fillna(0)
    y = df['label']
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    # Validation set
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    logger.info(f"Training set: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")
    
    # Train model
    model = FraudClassifier()
    model.train(X_train, y_train, X_val, y_val)
    
    # Evaluate
    y_pred_proba = [model.predict_proba(X_test.iloc[i].to_dict())[1] for i in range(len(X_test))]
    y_pred = [1 if p >= 0.5 else 0 for p in y_pred_proba]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'auc_roc': roc_auc_score(y_test, y_pred_proba)
    }
    
    logger.info(f"Model Metrics: {metrics}")
    
    # Save model
    model.save("models/supervised/model_artifacts/fraud_classifier.pkl")
    
    # Store in database
    db_manager = DatabaseManager()
    store_model_metrics(db_manager, "fraud_classifier", metrics, len(X_train))
    
    logger.info("Supervised model training completed!")


def store_model_metrics(db_manager, model_name, metrics, training_samples):
    """Store model metrics in database."""
    from database.models import ModelPerformance
    
    session = db_manager.get_session()
    
    performance = ModelPerformance(
        model_name=model_name,
        model_version="1.0",
        accuracy=metrics['accuracy'],
        precision=metrics['precision'],
        recall=metrics['recall'],
        f1_score=metrics['f1'],
        auc_roc=metrics['auc_roc'],
        validation_samples=training_samples
    )
    
    session.add(performance)
    session.commit()
    session.close()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data_path", type=str, help="Path to training data CSV")
    parser.add_argument("--test_size", type=float, default=0.2)
    
    args = parser.parse_args()
    train_supervised_model(args.data_path, args.test_size)