import json, os, time
from datetime import datetime
import openpyxl

# --- 기존 collect.py에서 필요한 로직만 가져오기 ---

def get_kst_now():
    from datetime import timedelta
    return datetime.utcnow() + timedelta(hours=9)

def load_excel_themes():
    """엑셀 파일에서 테마 정보를 읽어 매핑 테이블 생성"""
    file_path = "한국_주식_테마_분류_섹터추가.xlsx"
    theme_map = {}
    
    if not os.path.exists(file_path):
        if os.path.exists("한국 주식 테마 분류.xlsx"):
            file_path = "한국 주식 테마 분류.xlsx"
        else:
            print(f"!!! 알림: 엑셀 파일을 찾을 수 없습니다.")
            return theme_map

    print(f"엑셀 테마 데이터 로드 중...")
    try:
        # 속도를 위해 read_only=True 사용
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 5: continue
            sector = str(row[1]).strip() if row[1] else ""
            theme  = str(row[2]).strip() if row[2] else ""
            ticker = str(row[4]).strip().zfill(6) if row[4] else ""
            if ticker and theme and theme != "None":
                theme_map[ticker] = {"sector": sector if sector else "기타", "theme": theme}
        print(f"총 {len(theme_map)}개 종목의 테마 매핑 완료.")
    except Exception as e:
        print(f"!!! 엑셀 로드 중 오류 발생: {e}")
    return theme_map

def fmt_amount(val):
    ok = val / 100_000_000
    if ok >= 10000:
        return str(round(ok / 10000, 1)) + "조"
    return format(int(ok), ',') + "억"

def analyze(top60):
    """종목 리스트를 받아 섹터/테마별로 그룹화 및 주도 테마 추출"""
    MIN_THEME_CNT = 2
    sector_data = {}
    
    for s in top60:
        info = s.get("sector")
        if not info: continue
        
        # 이전 버전 data.json 호환성 처리
        if isinstance(info, str):
            sec_name = "미분류"
            thm_name = info
        else:
            sec_name = info.get("sector", "미분류")
            thm_name = info.get("theme", "기타")
        
        if sec_name not in sector_data:
            sector_data[sec_name] = {"amount": 0, "themes": {}}
        if thm_name not in sector_data[sec_name]["themes"]:
            sector_data[sec_name]["themes"][thm_name] = []
        
        sector_data[sec_name]["themes"][thm_name].append(s)
        s["sector_name"] = sec_name
        s["theme_name"] = thm_name

    final_sectors = []
    for sec_name, sec_info in sector_data.items():
        processed_themes = []
        sec_total_amount = 0
        
        for thm_name, stocks in sec_info["themes"].items():
            rising = [s for s in stocks if s["change"] >= 0]
            if len(rising) < MIN_THEME_CNT: continue
            
            thm_amount = sum(s["amount"] for s in rising)
            sec_total_amount += thm_amount
            for s in rising:
                s["score"] = s["change"] * (s["amount"] / 1_000_000_000)
            
            champ = max(rising, key=lambda x: x["score"])
            others = sorted([s for s in rising if s["ticker"] != champ["ticker"]], key=lambda x: -x["amount"])
            processed_themes.append({
                "theme": thm_name, "total_amount": thm_amount, "total_str": fmt_amount(thm_amount),
                "count": len(rising), "champion": champ, "stocks": others
            })
        
        if processed_themes:
            final_sectors.append({
                "sector": sec_name,
                "total_amount": sec_total_amount,
                "total_str": fmt_amount(sec_total_amount),
                "themes": sorted(processed_themes, key=lambda x: -x["total_amount"])
            })

    return sorted(final_sectors, key=lambda x: -x["total_amount"])

def refresh():
    print("=== 테마 정보 즉시 새로고침 시작 ===")
    
    # 1. 기존 market_data.json 읽기
    if not os.path.exists("market_data.json"):
        if os.path.exists("data.json"):
            print("이전 data.json을 market_data.json으로 변환합니다.")
            os.rename("data.json", "market_data.json")
        else:
            print("!!! 오류: market_data.json 파일이 없습니다. 먼저 collect.py를 실행해주세요.")
            return

    with open("market_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    top60 = data.get("top60", [])
    if not top60:
        print("!!! 오류: data.json에 종목 정보(top60)가 없습니다.")
        return

    # 2. 최신 엑셀 테마 로드
    excel_themes = load_excel_themes()

    # 3. 테마 재분류 (API 호출 없음!)
    print("기존 데이터에 새로운 테마 분류 적용 중...")
    for s in top60:
        ticker = s.get("ticker")
        if ticker in excel_themes:
            s["sector"] = excel_themes[ticker]

    # 4. 재분석
    sector_results = analyze(top60)

    # 5. data.json 업데이트 (구조 최적화)
    total_amount = sum(s["amount"] for s in top60)
    theme_total_amount = 0
    all_themes = []
    for sec in sector_results:
        theme_total_amount += sec["total_amount"]
        all_themes.extend(sec["themes"])
    
    ratio = round(theme_total_amount / total_amount * 100, 1) if total_amount else 0
    kst_now = get_kst_now()
    
    # 새로운 데이터 객체를 생성하여 기존 themes 키 등 불필요한 정보 제거
    final_data = {
        "date": data.get("date", "-"),
        "generated_at": kst_now.strftime("%H:%M") + " (업데이트)",
        "summary": {
            "total_amount": total_amount, "total_str": fmt_amount(total_amount),
            "theme_amount": theme_total_amount, "theme_str": fmt_amount(theme_total_amount),
            "theme_ratio": ratio, 
            "sector_count": len(sector_results),
            "theme_count": len(all_themes),
            "top60_count": len(top60)
        },
        "sectors": sector_results,
        "top60": top60
    }

    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"=== 완료! market_data.json이 갱신되었습니다. (KST {final_data['generated_at']}) ===")
    print("이제 대시보드를 새로고침(F5) 하세요!")

if __name__ == "__main__":
    refresh()
