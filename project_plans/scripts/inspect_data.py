
import pandas as pd
import os

def inspect_parquet(file_path):
    print(f"\n{'='*50}")
    print(f"Inspecting file: {os.path.basename(file_path)}")
    print(f"{'='*50}")
    
    try:
        # Load the parquet file
        df = pd.read_parquet(file_path)
        
        # Basic Info
        print(f"Shape: {df.shape}")
        print("\nColumns & Types:")
        print(df.dtypes)
        
        # Sample Data
        print("\nFirst 5 Rows:")
        print(df.head())
        
        # Check for specific columns if they exist (common in O&G data)
        interesting_cols = [col for col in df.columns if any(x in col.lower() for x in ['press', 'temp', 'flow', 'class', 'label'])]
        if interesting_cols:
            print(f"\nPotential Sensor/Label Columns found: {interesting_cols}")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    # Path to the files based on previous ls output
    base_dir = "/Users/somildoshi/Somil Doshi/UH - Coding/Personal Projects/AWS/Petrobras Data/1"
    
    real_file = os.path.join(base_dir, "DRAWN_00001.parquet")
    simulated_file = os.path.join(base_dir, "SIMULATED_00001.parquet")
    
    inspect_parquet(real_file)
    inspect_parquet(simulated_file)
