import requests
import os
from dotenv import load_dotenv

load_dotenv()
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
BASE_URL = "https://openapi.koreainvestment.com:9443"

res = requests.post(f"{BASE_URL}/oauth2/tokenP",
    json={"grant_type":"client_credentials","appkey":APP_KEY,"appsecret":APP_SECRET})
token = res.json().get("access_token")
print("토큰 완료")

headers = {
    "authorization": f"Bearer {token}",
    "appkey": APP_KEY,
    "appsecret": APP_SECRET,
    "tr_id": "FHPST01710000",
    "Content-Type": "application/json; charset=utf-8"
}

# 코스피 거래대금 순위
print("\n=== 코스피 거래대금 TOP10 ===")
params = {
    "fid_cond_mrkt_div_code": "J",
    "fid_cond_scr_div_code": "20171",
    "fid_input_iscd": "0001",
    "fid_div_cls_code": "0",
    "fid_blng_cls_code": "0",
    "fid_trgt_cls_code": "111111111",
    "fid_trgt_exls_cls_code": "0000000000",
    "fid_input_price_1": "",
    "fid_input_price_2": "",
    "fid_vol_cnt": "",
    "fid_input_date_1": ""
}
res = requests.get(
    f"{BASE_URL}/uapi/domestic-stock/v1/ranking/quote-balance",
    headers=headers, params=params, timeout=15
)
for i, item in enumerate(res.json().get("output",[])[:10]):
    print(f"{i+1}. {item.get('hts_kor_isnm','')} {int(item.get('acml_tr_pbmn','0').replace(',','')):,}원 {item.get('prdy_ctrt','')}%")

# 코스닥 거래대금 순위
print("\n=== 코스닥 거래대금 TOP10 ===")
params["fid_input_iscd"] = "1001"
params["fid_blng_cls_code"] = "1"
res2 = requests.get(
    f"{BASE_URL}/uapi/domestic-stock/v1/ranking/quote-balance",
    headers=headers, params=params, timeout=15
)
for i, item in enumerate(res2.json().get("output",[])[:10]):
    print(f"{i+1}. {item.get('hts_kor_isnm','')} {int(item.get('acml_tr_pbmn','0').replace(',','')):,}원 {item.get('prdy_ctrt','')}%")
