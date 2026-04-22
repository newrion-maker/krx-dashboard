import openpyxl

def peek():
    file_path = "한국 주식 테마 분류.xlsx"
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    sheet = wb.active
    
    print(f"Sheet: {sheet.title}")
    for i, row in enumerate(sheet.iter_rows(min_row=1, max_row=10, values_only=True)):
        # 각 셀의 내용을 안전하게 출력 (문자열 변환)
        row_str = [str(cell) if cell is not None else "" for cell in row]
        print(f"Row {i+1}: {row_str}")

if __name__ == "__main__":
    peek()
