import pandas as pd
import os

file_path = "한국 주식 테마 분류.xlsx"
if os.path.exists(file_path):
    try:
        # Load the first few rows to see the structure
        df = pd.read_excel(file_path, nrows=5)
        print("Columns:", df.columns.tolist())
        print("Data Preview:")
        print(df.head())
    except Exception as e:
        print("Error reading Excel:", e)
else:
    print("File not found.")
