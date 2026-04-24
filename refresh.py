import json, os
from datetime import datetime, timedelta
from collect import analyze_hierarchical, fmt_amount, load_excel_mapping

def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

def refresh():
    print("=== 테마 정보 즉시 새로고침 시작 ===")

    if not os.path.exists("market_data.json"):
        print("!!! 오류: market_data.json 파일이 없습니다. 먼저 collect.py를 실행해주세요.")
        return

    with open("market_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    top60 = data.get("top60", [])
    if not top60:
        print("!!! 오류: market_data.json에 종목 정보(top60)가 없습니다.")
        return

    excel_file = "한국_주식_테마_분류_섹터추가.xlsx"
    if not os.path.exists(excel_file):
        excel_file = "한국 주식 테마 분류.xlsx"
    mapping = load_excel_mapping(excel_file)

    print("기존 데이터에 새로운 테마 분류 적용 중...")
    final_output = analyze_hierarchical(top60, mapping)

    kst_now = get_kst_now()
    final_output.update({
        "date": data.get("date", "-"),
        "generated_at": kst_now.strftime("%H:%M") + " (업데이트)",
        "top60": top60
    })

    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"=== 완료! (KST {final_output['generated_at']}) ===")
    print("대시보드를 새로고침(F5) 하세요!")

if __name__ == "__main__":
    refresh()
