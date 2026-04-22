import openpyxl
import os

file_path = "한국 주식 테마 분류.xlsx"
if os.path.exists(file_path):
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True)
        sheet = wb.active
        print(f"Sheet Name: {sheet.title}")
        
        # Get first two rows
        rows = list(sheet.iter_rows(min_row=1, max_row=5, values_only=True))
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {row}")
            
    except Exception as e:
        print("Error reading Excel with openpyxl:", e)
else:
    print("File not found.")
