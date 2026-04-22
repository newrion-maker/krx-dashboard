import os, json, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pykrx_openapi import KRXOpenAPI
import requests

# .env 파일에서 키 로드
_env_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
    os.path.join(os.getcwd(), '.env'),
]
for _p in _env_paths:
    if os.path.exists(_p):
        load_dotenv(dotenv_path=_p)
        break

KRX_API_KEY = os.getenv("KRX_API_KEY")
APP_KEY     = os.getenv("APP_KEY")
APP_SECRET  = os.getenv("APP_SECRET")

# --- 설정 (계좌 타입에 따라 변경하세요) ---
# 실전투자 사용 시 "REAL", 모의투자 사용 시 "VIRTUAL" 입력
ACCOUNT_TYPE = "REAL" 

if ACCOUNT_TYPE == "REAL":
    BASE_URL = "https://openapi.koreainvestment.com:9443"
else:
    BASE_URL = "https://openapivts.koreainvestment.com:29443"
# ---------------------------------------

TOP_N         = 60
MIN_THEME_CNT = 3

SECTOR_MAP = {
    "반도체": "반도체", "전기,전자": "전기전자", "디지털컨텐츠": "게임/콘텐츠",
    "소프트웨어": "게임/콘텐츠", "운수장비": "자동차", "운수창고": "해운/항공",
    "의약품": "바이오/제약", "의료정밀": "바이오/제약", "화학": "화학",
    "철강금속": "철강", "기계": "기계/방산", "건설업": "건설",
    "금융업": "금융", "은행": "금융", "증권": "금융", "보험업": "금융",
    "통신업": "통신", "서비스업": "서비스", "음식료업": "음식료",
    "유통업": "유통", "전기가스업": "전기가스", "해상 운송업": "해운",
    "항공 운송업": "항공", "무기 및 총포탄 제조업": "방산",
    "항공기, 우주선 및 부품 제조업": "방산", "선박 및 보트 건조업": "조선",
    "일차전지 및 축전지 제조업": "2차전지", "반도체 제조업": "반도체",
    "특수 목적용 기계 제조업": "반도체장비", "소프트웨어 개발 및 공급업": "게임/콘텐츠",
    "자동차 제조업": "자동차", "자동차 부품 제조업": "자동차",
    "통신 및 방송 장비 제조업": "전기전자", "전자 부품 제조업": "전기전자",
    "원자력 발전업": "원전", "기초 의약물질 및 생물학적 제제 제조업": "바이오/제약",
    "의약품 제조업": "바이오/제약",
}

SPAC_KEYWORDS = ["스팩", "SPAC", "spac"]

def is_spac(name):
    return any(k in name for k in SPAC_KEYWORDS)

def get_kst_now():
    """항상 한국 시간(KST) 반환"""
    return datetime.utcnow() + timedelta(hours=9)

def load_excel_themes():
    """엑셀 파일에서 테마 정보를 읽어 매핑 테이블 생성"""
    import openpyxl
    file_path = "한국_주식_테마_분류_섹터추가.xlsx"
    theme_map = {}
    
    if not os.path.exists(file_path):
        # 백업 파일명도 확인
        if os.path.exists("한국 주식 테마 분류.xlsx"):
            file_path = "한국 주식 테마 분류.xlsx"
        else:
            print(f"!!! 알림: 엑셀 파일을 찾을 수 없습니다. 기본 분류를 사용합니다.")
            return theme_map

    print(f"엑셀 테마 데이터 로드 중: {file_path}")
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        sheet = wb.active
        # 새 양식: B(1):섹터, C(2):테마, E(4):종목코드
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

def get_today():
    """최근 거래일 자동 탐색 (KST 기준)"""
    from pykrx_openapi import KRXOpenAPI
    client = KRXOpenAPI(api_key=KRX_API_KEY)
    
    kst_now = get_kst_now()
    print(f"현재 한국 시간: {kst_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for i in range(7):
        check_date = (kst_now - timedelta(days=i)).strftime("%Y%m%d")
        print(f"[{i+1}/7] {check_date} 데이터 확인 중...", end=" ", flush=True)
        try:
            data = client.get_stock_daily_trade(bas_dd=check_date)
            if data.get("OutBlock_1"):
                print("성공! (데이터 발견)")
                return check_date
            else:
                print("데이터 없음")
        except Exception as e:
            print(f"오류: {e}")
            continue
    return kst_now.strftime("%Y%m%d")

def fmt_amount(val):
    ok = val / 100_000_000
    if ok >= 10000:
        return str(round(ok / 10000, 1)) + "조"
    return format(int(ok), ',') + "억"

def get_token():
    print(f"토큰 발급 시도 중... (접속주소: {BASE_URL})")
    res = requests.post(f"{BASE_URL}/oauth2/tokenP",
        json={"grant_type":"client_credentials","appkey":APP_KEY,"appsecret":APP_SECRET},
        timeout=10)
    
    if res.status_code != 200:
        print(f"!!! 토큰 발급 에러: {res.text}")
        raise Exception(f"토큰 발급 실패 ({res.status_code})")
        
    token = res.json().get("access_token")
    if not token: 
        raise Exception("토큰 발급 실패 (access_token 없음)")
    print("성공!")
    return token

def get_top60(today):
    print(f"{today} 기준 거래대금 상위 {TOP_N} 종목 수집 중...")
    client = KRXOpenAPI(api_key=KRX_API_KEY)
    data1 = client.get_stock_daily_trade(bas_dd=today)
    data2 = client.get_kosdaq_stock_daily_trade(bas_dd=today)
    all_stocks = data1.get("OutBlock_1", []) + data2.get("OutBlock_1", [])

    results = []
    for item in all_stocks:
        name   = item.get("ISU_NM", "")
        ticker = str(item.get("ISU_CD", "")).zfill(6)
        close  = float(item.get("TDD_CLSPRC") or 0)
        chg    = float(item.get("FLUC_RT") or 0)
        amount = float(item.get("ACC_TRDVAL") or 0)
        market = item.get("MKT_NM", "")
        if amount > 0 and not is_spac(name) and ticker:
            results.append({
                "ticker": ticker, "name": name, "close": close,
                "change": chg, "amount": int(amount),
                "amount_str": fmt_amount(amount), "market": market
            })
    return sorted(results, key=lambda x: -x["amount"])[:TOP_N]

def get_sector(token, ticker, excel_themes):
    # 1순위: 엑셀 테마
    if ticker in excel_themes:
        return excel_themes[ticker]
    
    # 2순위: 증권사 API 분류 (기본 섹터를 테마로 사용)
    res_data = {"sector": "미분류", "theme": "기타"}
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY, "appsecret": APP_SECRET,
        "tr_id": "CTPF1002R", "Content-Type": "application/json; charset=utf-8"
    }
    try:
        res = requests.get(
            f"{BASE_URL}/uapi/domestic-stock/v1/quotations/search-stock-info",
            headers=headers, params={"PRDT_TYPE_CD": "300", "PDNO": ticker}, timeout=10)
        out = res.json().get("output", {})
        scls = out.get("idx_bztp_scls_cd_name", "").strip()
        std  = out.get("std_idst_clsf_cd_name", "").strip()
        for key in [scls, std]:
            if key in SECTOR_MAP: 
                res_data["theme"] = SECTOR_MAP[key]
                return res_data
        res_data["theme"] = scls if scls else std if std else "기타"
        return res_data
    except: return res_data

def analyze(top60):
    # 1. 섹터별/테마별 그룹화
    # sector_data = { "반도체": { "amount": 0, "themes": { "HBM": [stocks...] } } }
    sector_data = {}
    
    for s in top60:
        info = s.get("sector") # 이제 info는 {"sector": "...", "theme": "..."} 형태
        if not info: continue
        
        sec_name = info.get("sector", "미분류")
        thm_name = info.get("theme", "기타")
        
        if sec_name not in sector_data:
            sector_data[sec_name] = {"amount": 0, "themes": {}}
        
        if thm_name not in sector_data[sec_name]["themes"]:
            sector_data[sec_name]["themes"][thm_name] = []
            
        sector_data[sec_name]["themes"][thm_name].append(s)
        # 종목 데이터에도 테마명 직접 주입 (UI 편의성)
        s["sector_name"] = sec_name
        s["theme_name"] = thm_name

    # 2. 분석 및 정렬
    final_sectors = []
    for sec_name, sec_info in sector_data.items():
        processed_themes = []
        sec_total_amount = 0
        
        for thm_name, stocks in sec_info["themes"].items():
            rising = [s for s in stocks if s["change"] > 0]
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

def save(today, top60, sector_results):
    total_amount = sum(s["amount"] for s in top60)
    
    # 테마에 속한 종목들의 총 거래대금
    theme_total_amount = 0
    all_themes = []
    for sec in sector_results:
        theme_total_amount += sec["total_amount"]
        all_themes.extend(sec["themes"])
    
    ratio = round(theme_total_amount / total_amount * 100, 1) if total_amount else 0
    d = datetime.strptime(today, "%Y%m%d")
    dm = {0:"월",1:"화",2:"수",3:"목",4:"금",5:"토",6:"일"}
    kst_now = get_kst_now()
    
    # 저장할 데이터 구성 (중복 themes 키 제거)
    data = {
        "date": f"{d.year}년 {d.month:02d}월 {d.day:02d}일 ({dm[d.weekday()]})",
        "generated_at": kst_now.strftime("%H:%M"),
        "summary": {
            "total_amount": total_amount, "total_str": fmt_amount(total_amount),
            "theme_amount": theme_total_amount, "theme_str": fmt_amount(theme_total_amount),
            "theme_ratio": ratio, 
            "sector_count": len(sector_results),
            "theme_count": len(all_themes), 
            "top60_count": len(top60)
        },
        "sectors": sector_results, 
        "top60": top60,
    }
    with open("market_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"market_data.json 저장 완료 (KST {kst_now.strftime('%H:%M')})")

if __name__ == "__main__":
    print("=== 주도 테마 수집 시작 ===")
    
    # 엑셀 테마 로드
    excel_themes = load_excel_themes()
    
    today  = get_today()
    token  = get_token()
    top60  = get_top60(today)
    
    print("종목별 섹터 정보 조회 중...")
    for i, s in enumerate(top60):
        # 엑셀 데이터를 우선적으로 활용하도록 전달
        s["sector"] = get_sector(token, s["ticker"], excel_themes)
        time.sleep(0.15)
        
    themes = analyze(top60)
    save(today, top60, themes)
    print(f"=== 완료! 주도업종 {len(themes)}개 발견 ===")


