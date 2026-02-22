import pandas as pd
import numpy as np
import kagglehub
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
import glob

# Focus on key pressure and temperature sensors
FEATURES = ["P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP"]

def load_data(sample_frac: float = 1.0):
    """
    Downloads the 3W dataset using kagglehub, extracts relevant features, and loads ALL valid simulated records for training.
    """
    print("Downloading/Locating 3W dataset using kagglehub...")
    data_dir = kagglehub.dataset_download("afrniomelo/3w-dataset")
    print(f"Loading files from {data_dir}...")
    
    # Find all simulated parquet files in subdirectories
    files = glob.glob(os.path.join(data_dir, "**", "*.parquet"), recursive=True)
    
    dfs = []
    # Load all 50M+ rows across all files
    for file in files:
        try:
            df = pd.read_parquet(file)
            # We must keep the "class" column so we can use it to supervise the model
            if "class" in df.columns:
                df = df.dropna(subset=FEATURES + ["class"])
                # FIX: Remove infinity and clip extreme values so the ML model doesnt crash
                df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURES)
                df[FEATURES] = df[FEATURES].clip(lower=-1e30, upper=1e30)
                dfs.append(df)
        except Exception as e:
            pass
            
    if not dfs:
        raise ValueError("No data loaded. Check data path.")
        
    combined_df = pd.concat(dfs)
    
    # The user explicitly requested ALL data, no row cap
    sampled_df = combined_df.sample(frac=sample_frac, random_state=42)
        
    print(f"Total valid samples loaded: {len(sampled_df):,}")
    
    return sampled_df

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def train_model(df: pd.DataFrame, model_path: str):
    """
    Trains a robust Random Forest Classifier using a 70/30 train-test split.
    """
    print("Preparing 70:30 Train-Test split...")
    
    if "class" not in df.columns:
        raise ValueError("Cannot train Random Forest: missing ground truth ""class"" column.")
        
    # Create the binary target variable
    y = [1 if c > 0 else 0 for c in df["class"]]
    X = df[FEATURES]
    
    # 70:30 Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
    print(f"Training on {len(X_train):,} rows. Validating on {len(X_test):,} rows.")
    
    print("Training Supervised Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=50,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    
    model.fit(X_train, y_train)
    print("Training complete.")
    
    # Evaluate Accuracy
    print("\nEvaluating Model Accuracy on 30% Test Set:")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=["Normal (0)", "Anomaly (1)"]))
    
    # Save the model
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    print(f"\nModel saved successfully to {model_path}")


MODEL_PATH = "model.joblib"

# 1. Download/Load data via kagglehub
training_data = load_data()

# 2. Train and save model
train_model(training_data, MODEL_PATH)

print("\n--- Next Steps ---")
print("1. To deploy, the \"model.joblib\" file should be uploaded to the S3 raw-data bucket.")
print("2. The inference Lambda/ECS container will download it to make predictions.")

