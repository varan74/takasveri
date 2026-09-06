import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import json

# 1. Takas Verisini Çekme
def get_takas_data(hisse_kodu):
    # KAP botunda yaptığın gibi scraping (undetected_chromedriver) veya HTTP istekleri ile 
    # İş Yatırım / Matriks web üzerinden 6 aylık veriyi çeken kod buraya gelecek.
    # Çekilen veriyi Pandas DataFrame'e çevir.
    
    # Örnek veri formatı
    data = {"Kurum": ["Citi", "Doçe"], "Net_Lot": [15000, -5000]} 
    return pd.DataFrame(data)

# 2. Google E-Tablo'ya Aktarma
def update_sheet(df):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    # GitHub Secrets üzerinden JSON anahtarını alıyoruz
    creds_json = json.loads(os.environ["GCP_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)

    # Tablo adını kendine göre düzenle
    sheet = client.open("BIST_Takas").sheet1 
    
    # Eski veriyi temizle ve yenisini yaz
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

if __name__ == "__main__":
    hisse = "THYAO" # Örnek hisse
    df_takas = get_takas_data(hisse)
    update_sheet(df_takas)
