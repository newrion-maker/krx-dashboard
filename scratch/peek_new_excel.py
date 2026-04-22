import openpyxl

def peek():
    file_path = "한국_주식_테마_분류_섹터추가.xlsx"
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    sheet = wb.active
    
    print(f"Sheet: {sheet.title}")
    for i, row in enumerate(sheet.iter_rows(min_row=1, max_row=10, values_only=True)):
        row_str = [str(cell) if cell is not None else "" for cell in row]
        print(f"Row {i+1}: {row_str}")

if __name__ == "__main__":
    peek()
