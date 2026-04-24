import os
import requests
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import openpyxl

# .env 파일 로드
load_dotenv()

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
BASE_URL = "https://openapi.koreainvestment.com:9443"

# 분석 설정
TOP_N = 60
MIN_THEME_CNT = 2
SPAC_KEYWORDS = ["스팩", "SPAC", "spac"]

def is_spac(name):
    return any(k in name for k in SPAC_KEYWORDS)

def get_access_token():
    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        return res.json().get("access_token")
    return None

def fmt_amount(val):
    ok = val / 100_000_000
    if ok >= 10000:
        return str(round(ok / 10000, 1)) + "조"
    return str(int(ok)) + "억"

def load_excel_themes(file_path):
    if not os.path.exists(file_path): return {}
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        theme_map = {}
        # 엑셀의 컬럼 위치를 찾기 위해 첫 줄 확인
        header = [str(cell.value) for cell in ws[1]]
        code_idx = 0
        theme_idx = 2 # 기본값: 3번째 열
        
        for i, h in enumerate(header):
            if '종목코드' in h: code_idx = i
            if '테마명' in h: theme_idx = i
            
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) <= max(code_idx, theme_idx): continue
            code = str(row[code_idx]).zfill(6)
            theme = str(row[theme_idx]).strip() if row[theme_idx] else ""
            if theme and theme != 'None' and theme != 'nan':
                theme_map[code] = theme
        print(f"엑셀 로드 완료: {len(theme_map)}개 종목 매핑 (코드열:{code_idx}, 테마열:{theme_idx})")
        return theme_map
    except Exception as e:
        print(f"!!! 엑셀 로드 오류: {e}")
        return {}

def get_top60(token):
    print(f"한국투자증권 API(20174)를 통한 실시간 거래대금 상위 {TOP_N} 종목 수집 중...")
    try:
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": APP_KEY, "appsecret": APP_SECRET,
            "tr_id": "FHPST01710000",
            "Content-Type": "application/json; charset=utf-8"
        }
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20174",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_blng_cls_code": "0",
            "fid_trgt_cls_code": "000000000",
            "fid_trgt_exls_cls_code": "0000000000",
            "fid_vol_cnt": "100",
            "fid_input_date_1": ""
        }
        res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/ranking/quote-balance",
                         headers=headers, params=params, timeout=15)
        all_results = []
        if res.status_code == 200:
            output = res.json().get("output", [])
            for item in output:
                name = item.get("hts_kor_isnm", "").strip()
                ticker = item.get("mksc_shrn_iscd", "").strip()
                amt_str = item.get("acml_tr_pbmn", "0").replace(",", "")
                amount = float(amt_str) if amt_str else 0
                if amount > 0 and not is_spac(name) and ticker:
                    all_results.append({
                        "ticker": ticker, "name": name,
                        "close": float(item.get("stck_prpr") or 0),
                        "chg": float(item.get("prdy_ctrt") or 0),
                        "amount": amount, "amount_str": fmt_amount(amount)
                    })
        return sorted(all_results, key=lambda x: -x["amount"])[:TOP_N]
    except: return []

def analyze(stocks, theme_map):
    theme_data = {}
    print("\n--- 상위 종목 테마 매핑 결과 (디버깅) ---")
    for s in stocks[:20]: # 상위 20개만 로그 출력
        theme = theme_map.get(s["ticker"], "기타/미분류")
        print(f"[{s['ticker']}] {s['name']} -> {theme}")
        
    for s in stocks:
        theme = theme_map.get(s["ticker"], "기타/미분류")
        if theme not in theme_data:
            theme_data[theme] = {"count": 0, "total_amt": 0, "stocks": []}
        theme_data[theme]["count"] += 1
        theme_data[theme]["total_amt"] += s["amount"]
        theme_data[theme]["stocks"].append(s)

    final_themes = []
    for t_name, info in theme_data.items():
        if t_name == "기타/미분류": continue
        # 조건 완화: 테마 내 종목이 1개라도 있으면 일단 표시 (디버깅용)
        avg_chg = sum(s["chg"] for s in info["stocks"]) / len(info["stocks"])
        final_themes.append({
            "name": t_name, "count": info["count"], "total_amt": info["total_amt"],
            "total_amt_str": fmt_amount(info["total_amt"]), "avg_chg": round(avg_chg, 2),
            "stocks": sorted(info["stocks"], key=lambda x: -x["amount"])
        })
    return sorted(final_themes, key=lambda x: -x["total_amt"])

def main():
    print(f"=== 주도 테마 수집 시작 (디버깅 모드) ===")
    excel_path = "한국_주식_테마_분류_섹터추가.xlsx"
    theme_map = load_excel_themes(excel_path)
    now_kst = datetime.utcnow() + timedelta(hours=9)
    token = get_access_token()
    if not token: return
    stocks = get_top60(token)
    if not stocks: return
    sectors = analyze(stocks, theme_map)
    result = {
        "date": now_kst.strftime("%Y년 %m월 %d일"),
        "generated_at": now_kst.strftime("%H:%M"),
        "sectors": sectors, "top60": stocks
    }
    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료 (KST {now_kst.strftime('%H:%M')}) - {len(sectors)}개 테마 발견")

if __name__ == "__main__":
    main()
