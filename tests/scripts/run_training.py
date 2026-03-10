"""
Run all model training.
"""
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting model training pipeline...")
    
    # Generate training data
    logger.info("Generating sample training data...")
    subprocess.run([
        sys.executable, "scripts/generate_sample_data.py",
        "--num_transactions", "50000"
    ])
    
    # Train supervised model
    logger.info("Training supervised model...")
    subprocess.run([sys.executable, "training/train_supervised.py"])
    
    # Train unsupervised model
    logger.info("Training unsupervised model...")
    subprocess.run([sys.executable, "training/train_unsupervised.py"])
    
    logger.info("Model training pipeline completed!")

if __name__ == "__main__":
    main()