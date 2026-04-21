import requests, os
from dotenv import load_dotenv
load_dotenv()

APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')
BASE_URL = 'https://openapi.koreainvestment.com:9443'

res = requests.post(f'{BASE_URL}/oauth2/tokenP',
    json={'grant_type':'client_credentials','appkey':APP_KEY,'appsecret':APP_SECRET})
token = res.json().get('access_token')
print('토큰 발급 완료')

headers = {
    'authorization': f'Bearer {token}',
    'appkey': APP_KEY,
    'appsecret': APP_SECRET,
    'tr_id': 'CTPF1002R',
    'Content-Type': 'application/json; charset=utf-8'
}

stocks = [
    ('삼성전자', '005930'),
    ('SK하이닉스', '000660'),
    ('한화에어로', '012450'),
    ('HD한국조선해양', '009540'),
    ('셀트리온', '068270')
]

for name, ticker in stocks:
    res = requests.get(
        f'{BASE_URL}/uapi/domestic-stock/v1/quotations/search-stock-info',
        headers=headers,
        params={'PRDT_TYPE_CD': '300', 'PDNO': ticker}
    )
    out = res.json().get('output', {})
    scls = out.get('idx_bztp_scls_cd_name', '')
    mcls = out.get('idx_bztp_mcls_cd_name', '')
    std = out.get('std_idst_clsf_cd_name', '')
    print(f'{name}: [{scls}] [{mcls}] [{std}]')