import os
import requests
import json
from dotenv import load_dotenv, set_key

# .env 로드 시도
env_path = ".env"
load_dotenv(env_path)

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
BASE_URL = "https://openapi.koreainvestment.com:9443"

# 키가 없으면 직접 물어보기
if not APP_KEY or not APP_SECRET:
    print("\n" + "!"*50)
    print(" 처음 한 번은 API 키 설정이 필요합니다.")
    print("!"*50)
    APP_KEY = input("1. APP_KEY를 입력하세요: ").strip()
    APP_SECRET = input("2. APP_SECRET을 입력하세요: ").strip()
    
    # .env 파일에 저장하여 다음부터는 안 물어보게 함
    with open(env_path, "a") as f: pass # 파일 없으면 생성
    set_key(env_path, "APP_KEY", APP_KEY)
    set_key(env_path, "APP_SECRET", APP_SECRET)
    set_key(env_path, "ACCOUNT_TYPE", "REAL")
    print("\n✅ 키 정보가 .env 파일에 저장되었습니다. 테스트를 계속합니다...\n")

def get_access_token():
    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        return res.json().get("access_token")
    print(f"❌ 토큰 발급 실패: {res.text}")
    return None

def test_endpoints(token):
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY, "appsecret": APP_SECRET,
        "tr_id": "FHPST01710000",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 3가지 주소 후보군 테스트
    endpoints = [
        "/uapi/domestic-stock/v1/ranking/quote-balance",
        "/uapi/domestic-stock/v1/quotation/ranking/quote-balance",
        "/uapi/domestic-stock/v1/ranking/top-item"
    ]
    
    for ep in endpoints:
        print(f"\n[시도] 주소: {ep}")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20171",
            "fid_input_iscd": "0001",
            "fid_div_cls_code": "1", # 거래대금
            "fid_blng_cls_code": "0",
            "fid_trgt_cls_code": "000000000",
            "fid_trgt_exls_cls_code": "0000000000",
            "fid_vol_cnt": "30",
            "fid_input_date_1": ""
        }
        try:
            res = requests.get(f"{BASE_URL}{ep}", headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                print(f"✅ 성공! 데이터를 정상적으로 가져왔습니다.")
                output = res.json().get("output", [])
                
                # 상위 종목 출력
                print("\n--- 현재 거래대금 상위 종목 ---")
                for i, item in enumerate(output[:5]):
                    print(f"{i+1}위: {item.get('hts_kor_isnm')} ({item.get('acml_tr_pbmn')}원)")
                
                return # 성공 시 종료
            else:
                print(f"⚠️ {res.status_code} 에러 발생")
        except Exception as e:
            print(f"💥 에러: {e}")

if __name__ == "__main__":
    token = get_access_token()
    if token:
        test_endpoints(token)
    print("\n" + "="*50)
    print("테스트가 종료되었습니다.")
    print("="*50)
