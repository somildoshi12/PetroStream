import json
import os
import boto3
import urllib.parse
import pandas as pd
import joblib

s3_client = boto3.client('s3')

# We load the model outside the handler so it stays cached in memory for subsequent invocations
# of the same Lambda execution environment.
MODEL_FILE = '/tmp/model.joblib'
FEATURES = ['P-PDG', 'P-TPT', 'T-TPT', 'P-MON-CKP', 'T-JUS-CKP']
CURATED_BUCKET = os.environ.get('CURATED_BUCKET_NAME')
RAW_BUCKET = os.environ.get('RAW_BUCKET_NAME')
MODEL_KEY = 'model.joblib'

model_loaded = False
global_model = None

def load_model():
    global model_loaded, global_model
    if not model_loaded:
        print(f"Downloading model from s3://{RAW_BUCKET}/{MODEL_KEY}")
        s3_client.download_file(RAW_BUCKET, MODEL_KEY, MODEL_FILE)
        global_model = joblib.load(MODEL_FILE)
        model_loaded = True
        print("Model loaded successfully.")
    return global_model

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))
    
    # 1. Load the ML model
    model = load_model()
    
    # 2. Process SQS messages
    for record in event['Records']:
        body = json.loads(record['body'])
        
        # SQS could contain multiple S3 events (or test events)
        if 'Records' not in body:
            print("No S3 records found in SQS body. Skipping.")
            continue
            
        for s3_event in body['Records']:
            source_bucket = s3_event['s3']['bucket']['name']
            source_key = urllib.parse.unquote_plus(s3_event['s3']['object']['key'])
            
            # Prevent accidental infinite loops if the model runs directly on the curated bucket,
            # or if it's the model file itself
            if source_bucket == CURATED_BUCKET:
                print(f"Skipping key {source_key} - it is already in the curated bucket.")
                continue
            if 'model.joblib' in source_key:
                print("Skipping the model file.")
                continue
            if not source_key.endswith('.parquet'):
                print(f"Skipping non-parquet file: {source_key}")
                continue
                
            print(f"Processing object: s3://{source_bucket}/{source_key}")
            
            # 3. Download the data file
            local_input_path = f"/tmp/input_{os.path.basename(source_key)}"
            s3_client.download_file(source_bucket, source_key, local_input_path)
            
            # 4. Run Inference
            try:
                df = pd.read_parquet(local_input_path)
                
                # Filter down to the exact rows we can predict on (no NaNs)
                inference_df = df.dropna(subset=FEATURES).copy()
                
                if inference_df.empty:
                    print("No valid data available for inference after dropping NaNs.")
                    continue
                    
                # The model returns 1 for inliers (normal) and -1 for outliers (anomalies)
                predictions = model.predict(inference_df[FEATURES])
                
                # Clean it up for the database: 0 = Normal, 1 = Anomaly
                inference_df['anomaly_flag'] = [0 if p == 1 else 1 for p in predictions]
                
                # Merge back to the main DataFrame (or just save the inference_df)
                # To keep it simple and clean, let's just save the rows we predicted on.
                local_output_path = f"/tmp/output_{os.path.basename(source_key)}"
                
                # 5. Save and Upload to Curated Bucket
                inference_df.to_parquet(local_output_path, engine='pyarrow')
                
                # Using the exact same key structure means it organizes nicely
                # For example: data/9/SIMULATED_00002.parquet -> curved_bucket/data/9/SIMULATED_00002.parquet
                s3_client.upload_file(local_output_path, CURATED_BUCKET, source_key)
                print(f"Successfully uploaded predictions to s3://{CURATED_BUCKET}/{source_key}")
                
            except Exception as e:
                print(f"Error processing {source_key}: {e}")
                raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Inference processing complete.')
    }
