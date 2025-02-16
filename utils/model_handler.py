import os
import joblib
from datetime import datetime
import xgboost as xgb
import shap
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from .data_processor import PRODUCT_MAPPING, FEATURES, prepare_features
import streamlit as st
import traceback

class ProductRecommender:
    def __init__(self):
        self.model = None
        self.explainer = None
        self.scaler = None
        self.model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, 'product_recommender.joblib')
        self.scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
        self.version_path = os.path.join(self.model_dir, 'version.txt')
        self.log_path = os.path.join(self.model_dir, 'model_versions.log')
        self.version = self._get_current_version()
        self.data_count = 0
        
    def _get_current_version(self):
        try:
            if os.path.exists(self.version_path):
                with open(self.version_path, 'r') as f:
                    return int(f.read().strip())
            return 0
        except Exception:
            return 0
    
    def train_model(self, X, y):
        """Train the model and create SHAP explainer"""
        print("Starting model training...")
        
        # Initialize XGBoost classifier
        self.model = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=len(PRODUCT_MAPPING),
            max_depth=3,
            learning_rate=0.1,
            n_estimators=100
        )
        
        # Fit the model
        self.model.fit(X, y)
        print("Model training completed")
        
        # Create SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)
        
        # Calculate training accuracy
        y_pred = self.model.predict(X)
        accuracy = accuracy_score(y, y_pred)
        print(f"Training accuracy: {accuracy:.4f}")
        
        try:
            # Save model and explainer
            print(f"Saving model to: {self.model_path}")
            model_data = {
                'model': self.model,
                'explainer': self.explainer
            }
            joblib.dump(model_data, self.model_path)
            
            # Update version
            self.version += 1
            with open(self.version_path, 'w') as f:
                f.write(str(self.version))
            
            # Log version
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] Version {self.version}: {len(X)} samples, accuracy: {accuracy:.2%}\n"
            with open(self.log_path, 'a') as f:
                f.write(log_entry)
            
            return True, accuracy
        except Exception as e:
            print(f"Error saving model: {str(e)}")
            return False, 0.0
    
    def load_model(self):
        """Load the trained model"""
        try:
            # Debug current directory
            st.write("Debug - Current directory:", os.getcwd())
            st.write("Debug - Model directory:", self.model_dir)
            st.write("Debug - Model path:", self.model_path)
            
            # Check if directory exists
            st.write("Debug - Model directory exists:", os.path.exists(self.model_dir))
            
            # List files in model directory
            if os.path.exists(self.model_dir):
                st.write("Debug - Files in model directory:", os.listdir(self.model_dir))
            
            # Check if model file exists
            st.write("Debug - Model file exists:", os.path.exists(self.model_path))
            
            if not os.path.exists(self.model_path):
                st.error(f"Model file not found at: {self.model_path}")
                return False
            
            st.write("Debug - Attempting to load model file...")
            model_data = joblib.load(self.model_path)
            
            st.write("Debug - Model data keys:", model_data.keys())
            
            self.model = model_data['model']
            self.explainer = model_data['explainer']
            
            st.write("Debug - Model loaded successfully")
            return True
        
        except Exception as e:
            st.error(f"Error loading model: {str(e)}")
            st.write("Debug - Model load error details:", traceback.format_exc())
            return False
    
    def predict(self, features):
        """Get product recommendation with SHAP explanations"""
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Ensure features are in correct format
        if isinstance(features, dict):
            features = pd.DataFrame([features])
        elif isinstance(features, pd.Series):
            features = pd.DataFrame([features])
            
        # Prepare features using data_processor
        features = prepare_features(features)
        
        # Debug: Print input features
        print("\nInput features:")
        print(features)
        
        # Make prediction
        probabilities = self.model.predict_proba(features)
        prediction = int(self.model.predict(features)[0])  # Convert to Python int
        
        # Debug: Print prediction info
        print("\nPrediction:", prediction)
        print("Probabilities:", probabilities[0])
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(features)
        
        # Debug information
        print("\nSHAP values type:", type(shap_values))
        print("Shape of SHAP values:", shap_values.shape)
        
        # Get actual feature names from the model
        model_features = self.model.get_booster().feature_names
        print("Model features:", model_features)
        
        # Create explanation dictionary
        feature_importance = {}
        for idx, feature in enumerate(model_features):
            try:
                # Get SHAP value for the predicted class
                shap_value = shap_values[0, idx, prediction]  # Access the correct class's SHAP value
                print(f"SHAP value for feature {feature}:", shap_value)
                importance = float(np.abs(shap_value))
                feature_importance[feature] = importance
            except Exception as e:
                print(f"Error processing feature {feature} at index {idx}: {str(e)}")
        
        # Sort features by importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        explanations = []
        for feature, importance in sorted_features:
            if importance > 0:
                value = features[feature].iloc[0]
                if feature in ['has_insurance', 'has_investments', 'increased_balance', 'high_balance', 'salary_above_3k']:
                    value = bool(int(value))
                elif feature in ['savings_amount', 'monthly_card_spend']:
                    value = f"${float(value):,.2f}"
                elif feature == 'num_giro_payments':
                    value = int(value)
                
                explanations.append({
                    'feature': feature,
                    'value': value,
                    'importance': float(importance)
                })
        
        return prediction, [float(p) for p in probabilities[0]], explanations
    
    def should_retrain(self):
        """Check if retraining is needed"""
        self.data_count += 1
        if self.data_count >= 50:
            self.data_count = 0
            return True
        return False
        
    def _save_model(self):
        """Save model and update version tracking"""
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Save model and scaler
        model_data = {
            'model': self.model,
            'explainer': self.explainer
        }
        joblib.dump(model_data, self.model_path)
        if self.scaler:
            joblib.dump(self.scaler, self.scaler_path)
            
        # Update version number
        self.version += 1
        with open(self.version_path, 'w') as f:
            f.write(str(self.version))
        
        # Append to log file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Version {self.version}\n"
        with open(self.log_path, 'a') as f:
            f.write(log_entry)
