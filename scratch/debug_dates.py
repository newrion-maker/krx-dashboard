import os, json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pykrx_openapi import KRXOpenAPI

# Try to find .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

KRX_API_KEY = os.getenv("KRX_API_KEY")

def debug_krx_dates():
    print(f"Loaded Key: {KRX_API_KEY[:5]}..." if KRX_API_KEY else "Key NOT loaded")
    client = KRXOpenAPI(api_key=KRX_API_KEY)
    today = datetime.today()
    for i in range(5):
        check = (today - timedelta(days=i)).strftime("%Y%m%d")
        try:
            # Try KOSPI
            data = client.get_stock_daily_trade(bas_dd=check)
            out = data.get("OutBlock_1", [])
            print(f"Date: {check}, KOSPI Count: {len(out)}")
            
            # Try KOSDAQ
            data2 = client.get_kosdaq_stock_daily_trade(bas_dd=check)
            out2 = data2.get("OutBlock_1", [])
            print(f"Date: {check}, KOSDAQ Count: {len(out2)}")
            
        except Exception as e:
            print(f"Date: {check}, Error: {e}")

if __name__ == "__main__":
    debug_krx_dates()
