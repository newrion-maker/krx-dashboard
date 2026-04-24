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

def fmt_amount(val):
    ok = val / 100_000_000
    if ok >= 10000: return str(round(ok / 10000, 1)) + "조"
    return str(int(ok)) + "억"

def load_excel_mapping(file_path):
    if not os.path.exists(file_path): 
        print(f"!!! 엑셀 파일을 찾을 수 없습니다: {file_path}")
        return {}
    try:
        # 속도를 위해 read_only=True 사용
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        ws = wb.active
        mapping = {}
        # B열(1): 분류(섹터), C열(2): 테마명, E열(4): 종목코드
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 5: continue
            code = str(row[4]).zfill(6) if row[4] else ""
            if not code or code == "None": continue
            
            mapping[code] = {
                "theme": str(row[2]).strip() if row[2] else "기타",
                "sector": str(row[1]).strip() if row[1] else "기타"
            }
        print(f"엑셀 로드 완료: {len(mapping)}개 종목 매핑 (소스: {file_path})")
        return mapping
    except Exception as e:
        print(f"!!! 엑셀 로드 중 오류 발생: {e}")
        return {}

def get_top60(token):
    try:
        headers = {"authorization": f"Bearer {token}", "appkey": APP_KEY, "appsecret": APP_SECRET, "tr_id": "FHPST01710000", "Content-Type": "application/json"}
        params = {"fid_cond_mrkt_div_code": "J", "fid_cond_scr_div_code": "20174", "fid_input_iscd": "0000", "fid_div_cls_code": "0", "fid_blng_cls_code": "0", "fid_trgt_cls_code": "000000000", "fid_trgt_exls_cls_code": "0000000000", "fid_vol_cnt": "100", "fid_input_date_1": ""}
        res = requests.get(f"{BASE_URL}/uapi/domestic-stock/v1/ranking/quote-balance", headers=headers, params=params, timeout=15)
        
        all_results = []
        if res.status_code == 200:
            output = res.json().get("output", [])
            for item in output:
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
    except Exception as e:
        print(f"!!! 데이터 수집 중 오류 발생: {e}")
        return []

def analyze_hierarchical(stocks, mapping):
    total_market_amt = sum(s["amount"] for s in stocks)
    sector_data = {}

    for i, s in enumerate(stocks):
        m = mapping.get(s["ticker"], {"theme": "기타", "sector": "기타"})
        s["theme_name"] = m["theme"]
        s["sector_name"] = m["sector"]
        s["sector"] = m # 호환성 유지
        
        sec_name = m["sector"]
        if sec_name not in sector_data:
            sector_data[sec_name] = {"total_amount": 0, "themes": {}}
        
        theme_name = m["theme"]
        if theme_name not in sector_data[sec_name]["themes"]:
            sector_data[sec_name]["themes"][theme_name] = {"total_amount": 0, "stocks": []}
            
        sector_data[sec_name]["total_amount"] += s["amount"]
        sector_data[sec_name]["themes"][theme_name]["total_amount"] += s["amount"]
        sector_data[sec_name]["themes"][theme_name]["stocks"].append(s)

    final_sectors = []
    for s_name, s_info in sector_data.items():
        if s_name == "기타": continue
        
        final_themes = []
        for t_name, t_info in s_info["themes"].items():
            if t_name == "기타": continue
            
            # 필터: 종목 2개 이상 OR 상위 10위권 대장주 포함
            has_big_stock = any(stocks.index(stk) < 10 for stk in t_info["stocks"])
            if len(t_info["stocks"]) >= 2 or has_big_stock:
                sorted_stks = sorted(t_info["stocks"], key=lambda x: -x["amount"])
                final_themes.append({
                    "theme": t_name,
                    "total_amount": t_info["total_amount"],
                    "total_str": fmt_amount(t_info["total_amount"]),
                    "count": len(t_info["stocks"]),
                    "champion": sorted_stks[0],
                    "stocks": sorted_stks[1:6]
                })
        
        if final_themes:
            final_sectors.append({
                "sector": s_name,
                "total_amount": s_info["total_amount"],
                "total_str": fmt_amount(s_info["total_amount"]),
                "themes": sorted(final_themes, key=lambda x: -x["total_amount"])
            })

    final_sectors = sorted(final_sectors, key=lambda x: -x["total_amount"])
    theme_total_amt = sum(sec["total_amount"] for sec in final_sectors)

    return {
        "summary": {
            "total_amount": total_market_amt, "total_str": fmt_amount(total_market_amt),
            "theme_amount": theme_total_amt, "theme_str": fmt_amount(theme_total_amt),
            "theme_ratio": round((theme_total_amt / total_market_amt * 100), 1) if total_market_amt > 0 else 0,
            "sector_count": len(final_sectors), "theme_count": sum(len(s["themes"]) for s in final_sectors),
            "top60_count": len(stocks)
        },
        "sectors": final_sectors
    }

def get_token():
    token_file = "token_cache.json"
    
    # 1. 캐시된 토큰 확인
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                cache = json.load(f)
                # 만료 시간 확인 (24시간 유효하지만 안전하게 12시간으로 잡음)
                if time.time() - cache.get("timestamp", 0) < 3600 * 12:
                    print("캐시된 토큰을 사용합니다.")
                    return cache.get("token")
        except: pass

    # 2. 새로운 토큰 발급
    print(f"새로운 API 토큰 발급 중...")
    res = requests.post(f"{BASE_URL}/oauth2/tokenP", json={"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET})
    
    if res.status_code == 200:
        token = res.json().get("access_token")
        # 캐시 저장
        with open(token_file, "w") as f:
            json.dump({"token": token, "timestamp": time.time()}, f)
        return token
    else:
        print(f"!!! 토큰 발급 실패 (Status: {res.status_code})")
        print(f"!!! 에러 메시지: {res.text}")
        return None

def main():
    excel_file = "한국_주식_테마_분류_섹터추가.xlsx"
    if not os.path.exists(excel_file):
        excel_file = "한국 주식 테마 분류.xlsx"
        
    mapping = load_excel_mapping(excel_file)
    now = datetime.utcnow() + timedelta(hours=9)
    
    token = get_token()
    if not token: return
        
    print(f"실시간 거래대금 상위 종목 수집 중...")
    stocks = get_top60(token)
    if not stocks: 
        print("!!! 종목 수집 실패")
        return
        
    print(f"데이터 분석 및 계층화 중...")
    final_output = analyze_hierarchical(stocks, mapping)
    final_output.update({
        "date": now.strftime("%Y년 %m월 %d일"), 
        "generated_at": now.strftime("%H:%M"), 
        "top60": stocks
    })
    
    # data.json과 market_data.json 모두 저장하거나 하나로 통일
    # 여기서는 대시보드가 사용하는 market_data.json으로 통일
    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    print(f"market_data.json 저장 완료 (섹터 {len(final_output['sectors'])}개, KST {final_output['generated_at']})")

if __name__ == "__main__":
    main()
