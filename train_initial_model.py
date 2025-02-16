from utils.data_processor import load_training_data, prepare_features
from utils.model_handler import ProductRecommender
import pandas as pd
import os
from datetime import datetime

def log_model_version(num_samples, accuracy, version):
    """Log model version information to a file"""
    log_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'model_versions.txt')
    version_file = os.path.join(log_dir, 'model_version.txt')
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Model retrained with {num_samples} samples. Training accuracy: {accuracy:.2%}\n"
    version_entry = f"{version}\n"
    
    with open(log_file, 'a') as f:
        f.write(log_entry)
    with open(version_file, 'w') as f:
        f.write(version_entry)
    
    print(f"✓ Logged model version to: {log_file}")
    print(f"✓ Saved model version to: {version_file}")

def train_initial_model():
    print("\n=== Starting Model Training ===")
    
    # Load the training data
    print("\n1. Loading training data...")
    try:
        # Try to load user data first
        from utils.data_processor import load_user_data
        user_df = load_user_data()
        if len(user_df) > 0:
            print(f"Found {len(user_df)} user data records")
            training_df = user_df
        else:
            print("No user data found, using initial training data")
            training_df = pd.read_csv('insurance_training_data.csv')
    except Exception as e:
        print(f"Error loading user data: {str(e)}")
        print("Falling back to initial training data")
        training_df = pd.read_csv('insurance_training_data.csv')
    
    X = prepare_features(training_df)
    y = training_df['recommended_product']
    print(f"✓ Loaded {len(X)} training samples")
    
    # Initialize and train the model
    print("\n2. Training model...")
    recommender = ProductRecommender()
    print(f"Model will be saved to: {recommender.model_path}")
    
    success, accuracy = recommender.train_model(X, y)
    if not success:
        print("✗ Error: Failed to train or save model")
        return
        
    # Log the model version
    log_model_version(len(X), accuracy, recommender.version)
    print("✓ Model training completed!")
    
    # Verify the model exists
    if os.path.exists(recommender.model_path):
        print(f"✓ Model file exists at: {recommender.model_path}")
        print(f"✓ File size: {os.path.getsize(recommender.model_path)} bytes")
    else:
        print("✗ Error: Model file not found after training")
        return
    
    # Try to load the model
    print("\n3. Verifying model can be loaded...")
    new_recommender = ProductRecommender()
    if new_recommender.load_model():
        print("✓ Successfully loaded the trained model")
        
        # Test prediction
        print("\n4. Testing prediction...")
        test_features = X.iloc[0:1]
        try:
            prediction, probabilities = new_recommender.predict(test_features)
            print(f"✓ Test prediction successful: {prediction}")
        except Exception as e:
            print(f"✗ Error during prediction: {str(e)}")
    else:
        print("✗ Error: Could not load the trained model")

if __name__ == "__main__":
    train_initial_model()
