import pandas as pd
import os
import numpy as np
from sklearn.preprocessing import StandardScaler

# Constants
FEATURES = [
    'savings_amount',
    'salary_above_3k',
    'monthly_card_spend',
    'num_giro_payments',
    'has_insurance',
    'has_investments',
    'increased_balance',
    'high_balance'
]

PRODUCT_MAPPING = {
    0: 'Term Insurance',
    1: 'Whole Life Insurance',
    2: 'ILP'
}

def load_training_data(file_path='insurance_training_data.csv'):
    """Load and preprocess initial training data"""
    df = pd.read_csv(file_path)
    return df[FEATURES], df['recommended_product']

def prepare_features(data):
    """Prepare features for model input"""
    if isinstance(data, dict):
        # Convert single data point to DataFrame
        data = pd.DataFrame([data])
    elif isinstance(data, pd.Series):
        data = pd.DataFrame([data])
    
    # Ensure all required features are present
    for feature in FEATURES:
        if feature not in data.columns:
            raise ValueError(f"Missing required feature: {feature}")
    
    # Convert boolean columns to int
    bool_columns = ['salary_above_3k', 'has_insurance', 'has_investments', 'increased_balance', 'high_balance']
    for col in bool_columns:
        data[col] = data[col].astype(int)
    
    # Ensure numeric columns are float
    numeric_columns = ['savings_amount', 'monthly_card_spend', 'num_giro_payments']
    for col in numeric_columns:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    
    # For prediction, we don't need to scale the features as the model was trained on unscaled data
    return data[FEATURES]

def load_user_data():
    """Load accumulated user data and recommendations"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    data_file = os.path.join(data_dir, 'user_recommendations.csv')
    
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Create or load the file
    if not os.path.exists(data_file):
        # Create empty DataFrame with correct columns
        columns = FEATURES + ['recommended_product', 'timestamp']
        df = pd.DataFrame(columns=columns)
        df.to_csv(data_file, index=False)
        return df
    
    return pd.read_csv(data_file)

def save_user_data(user_data, recommended_product):
    """Save user data and recommendation"""
    try:
        print("Starting save_user_data...")  # Debug
        
        # Load existing data
        df = load_user_data()
        print(f"Loaded existing data with {len(df)} rows")  # Debug
        
        # Print the incoming data for debugging
        print("User data to save:", user_data)
        print("Recommended product:", recommended_product)
        
        # Create a new row with the user data
        # Access the first row of the DataFrame since prepare_features returns a DataFrame
        new_data = {
            'savings_amount': float(user_data['savings_amount'].iloc[0]),
            'salary_above_3k': bool(user_data['salary_above_3k'].iloc[0]),
            'monthly_card_spend': float(user_data['monthly_card_spend'].iloc[0]),
            'num_giro_payments': int(user_data['num_giro_payments'].iloc[0]),
            'has_insurance': bool(user_data['has_insurance'].iloc[0]),
            'has_investments': bool(user_data['has_investments'].iloc[0]),
            'increased_balance': bool(user_data['increased_balance'].iloc[0]),
            'high_balance': bool(user_data['high_balance'].iloc[0]),
            'recommended_product': int(recommended_product),
            'timestamp': pd.Timestamp.now()
        }
        
        print("New data row:", new_data)  # Debug
        
        # Append new data
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        print(f"After concat, dataframe has {len(df)} rows")  # Debug
        
        # Save updated data
        data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'user_recommendations.csv')
        print(f"Saving to file: {data_file}")  # Debug
        df.to_csv(data_file, index=False)
        print("Save completed successfully")  # Debug
        
        return len(df)
    except Exception as e:
        print(f"Error in save_user_data: {str(e)}")  # Debug
        raise  # Re-raise the exception after logging
