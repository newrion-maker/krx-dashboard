import os
import requests
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import openpyxl

load_dotenv()
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
BASE_URL = "https://openapi.koreainvestment.com:9443"

TOP_N = 60
MIN_THEME_CNT = 2

def fmt_amount(val):
    ok = val / 100_000_000
    if ok >= 10000: return str(round(ok / 10000, 1)) + "조"
    return str(int(ok)) + "억"

def load_excel_themes(file_path):
    if not os.path.exists(file_path): return {}
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        theme_map = {}
        # 검증된 열 번호: C열(2번 인덱스) = 테마명, E열(4번 인덱스) = 종목코드
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 5: continue
            code = str(row[4]).zfill(6) # 5번째 칸(E열)
            theme = str(row[2]).strip() if row[2] else "" # 3번째 칸(C열)
            if theme and theme not in ['None', 'nan', '']:
                theme_map[code] = theme
        print(f"엑셀 로드 완료: {len(theme_map)}개 종목 매핑 (고정 위치 사용)")
        return theme_map
    except Exception as e:
        print(f"엑셀 로드 오류: {e}")
        return {}

def get_top60(token):
    try:
        headers = {"authorization": f"Bearer {token}", "appkey": APP_KEY, "appsecret": APP_SECRET, "tr_id": "FHPST01710000", "Content-Type": "application/json"}
        params = {"fid_cond_mrkt_div_code": "J", "fid_cond_scr_div_code": "20174", "fid_input_iscd": "0000", "fid_div_cls_code": "0", "fid_blng_cls_code": "0", "fid_trgt_cls_code": "000000000", "fid_trgt_exls_cls_code": "0000000000", "fid_vol_cnt": "100", "fid_input_date_1": ""}
        res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/ranking/quote-balance", headers=headers, params=params, timeout=15)
        
        all_results = []
        if res.status_code == 200:
            for item in res.json().get("output", []):
                ticker = item.get("mksc_shrn_iscd", "").strip()
                name = item.get("hts_kor_isnm", "").strip()
                amt = float(item.get("acml_tr_pbmn", "0").replace(",", ""))
                if amt > 0 and ticker:
                    all_results.append({
                        "ticker": ticker, "name": name,
                        "close": int(float(item.get("stck_prpr") or 0)),
                        "change": float(item.get("prdy_ctrt") or 0),
                        "amount": amt, "amount_str": fmt_amount(amt),
                        "market": "KOSPI" if ticker.startswith('0') else "KOSDAQ"
                    })
        return sorted(all_results, key=lambda x: -x["amount"])[:TOP_N]
    except: return []

def analyze_for_frontend(stocks, theme_map):
    theme_data = {}
    total_market_amt = sum(s["amount"] for s in stocks)
    for s in stocks:
        t_name = theme_map.get(s["ticker"], "기타/미분류")
        if t_name not in theme_data:
            theme_data[t_name] = {"total_amount": 0, "stocks": []}
        theme_data[t_name]["total_amount"] += s["amount"]
        theme_data[t_name]["stocks"].append(s)

    sorted_themes = []
    for name, info in theme_data.items():
        if name == "기타/미분류": continue
        if len(info["stocks"]) >= MIN_THEME_CNT:
            sorted_themes.append({
                "theme": name, "total_amount": info["total_amount"], "total_str": fmt_amount(info["total_amount"]),
                "count": len(info["stocks"]),
                "champion": sorted(info["stocks"], key=lambda x: -x["amount"])[0],
                "stocks": sorted(info["stocks"], key=lambda x: -x["amount"])[1:6]
            })
    
    sorted_themes = sorted(sorted_themes, key=lambda x: -x["total_amount"])
    theme_total_amt = sum(t["total_amount"] for t in sorted_themes)
    
    return {
        "summary": {
            "total_amount": total_market_amt, "total_str": fmt_amount(total_market_amt),
            "theme_amount": theme_total_amt, "theme_str": fmt_amount(theme_total_amt),
            "theme_ratio": round((theme_total_amt / total_market_amt * 100), 1) if total_market_amt > 0 else 0,
            "sector_count": 1, "theme_count": len(sorted_themes), "top60_count": len(stocks)
        },
        "sectors": [
            {"sector": "실시간 주도 테마군", "total_amount": theme_total_amt, "total_str": fmt_amount(theme_total_amt), "themes": sorted_themes}
        ]
    }

def main():
    excel_path = "한국_주식_테마_분류_섹터추가.xlsx"
    theme_map = load_excel_themes(excel_path)
    now = datetime.utcnow() + timedelta(hours=9)
    
    res = requests.post(f"{BASE_URL}/oauth2/tokenP", json={"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET})
    token = res.json().get("access_token") if res.status_code == 200 else None
    if not token: return
    
    stocks = get_top60(token)
    if not stocks: return
    
    final_output = analyze_for_frontend(stocks, theme_map)
    final_output["date"] = now.strftime("%Y년 %m월 %d일")
    final_output["generated_at"] = now.strftime("%H:%M")
    final_output["top60"] = stocks
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print(f"data.json 저장 완료 (테마 {final_output['summary']['theme_count']}개)")

if __name__ == "__main__":
    main()
