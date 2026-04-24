import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 로드 및 키 확인 로직
env_path = ".env"
load_dotenv(env_path)

APP_KEY = os.getenv("APP_KEY", "").strip()
APP_SECRET = os.getenv("APP_SECRET", "").strip()
BASE_URL = "https://openapi.koreainvestment.com:9443"

if not APP_KEY or not APP_SECRET:
    print("\n" + "!"*50)
    print(" 처음 한 번은 API 키 설정이 필요합니다.")
    print("!"*50)
    APP_KEY = input("1. APP_KEY를 입력하세요: ").strip()
    APP_SECRET = input("2. APP_SECRET을 입력하세요: ").strip()
    with open(env_path, "w") as f:
        f.write(f"APP_KEY={APP_KEY}\n")
        f.write(f"APP_SECRET={APP_SECRET}\n")
        f.write(f"ACCOUNT_TYPE=REAL\n")
    print("\n✅ 키 정보가 저장되었습니다.\n")

def get_token():
    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        return res.json().get("access_token")
    print(f"❌ 토큰 발급 실패: {res.text}")
    return None

def test_config(token, scr_code, div_code):
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY, "appsecret": APP_SECRET,
        "tr_id": "FHPST01710000",
        "Content-Type": "application/json; charset=utf-8"
    }
    url = f"{BASE_URL}/uapi/domestic-stock/v1/ranking/quote-balance"
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_cond_scr_div_code": scr_code,
        "fid_input_iscd": "0000",
        "fid_div_cls_code": div_code,
        "fid_blng_cls_code": "0",
        "fid_trgt_cls_code": "000000000",
        "fid_trgt_exls_cls_code": "0000000000",
        "fid_vol_cnt": "30",
        "fid_input_date_1": ""
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            output = res.json().get("output", [])
            if output:
                print(f"✅ [성공] 화면:{scr_code}, 구분:{div_code} -> {len(output)}개 종목 발견")
                for i, item in enumerate(output[:3]):
                    print(f"  {i+1}위: {item.get('hts_kor_isnm')} ({item.get('acml_tr_pbmn')}원)")
                return True
    except: pass
    return False

if __name__ == "__main__":
    token = get_token()
    if token:
        print("🔍 실시간 데이터 수집 조합 테스트를 시작합니다...")
        configs = [
            ("20171", "0"), ("20171", "1"),
            ("20173", "0"), ("20173", "1"),
            ("20174", "0"), ("20174", "1")
        ]
        for scr, div in configs:
            test_config(token, scr, div)
            
    print("\n테스트 종료.")
    input("Press Enter...")
