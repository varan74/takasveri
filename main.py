import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import json

def get_takas_data(hisse_kodu):
    # Çekilen veriyi DataFrame'e çevirdiğiniz bölüm
    data = {"Kurum": ["Citi", "Doçe"], "Net_Lot": [15000, -5000]} 
    return pd.DataFrame(data)

def update_sheet(df):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_json = json.loads(os.environ["GCP_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)

    # DÜZELTİLEN KISIM: Tabloyu doğrudan ID'si ile açıyoruz
    sheet = client.open_by_key("1NrL6Q7eJRgN6YBQNjdev_1wVCAsh8Zz-zR-I9eMeGgo").sheet1 
    
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

if __name__ == "__main__":
    hisse = "THYAO" 
    df_takas = get_takas_data(hisse)
    update_sheet(df_takas)
