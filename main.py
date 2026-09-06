import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import time
from datetime import datetime
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

def get_tum_hisseler():
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = uc.Chrome(options=options)
        
        # KAP sitesine bağlan
        driver.get("https://www.kap.org.tr/tr/bist-sirketler")
        time.sleep(5) # Tablonun JS ile yüklenmesi için bekleme
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        hisseler = set()
        
        # Sitedeki hücrelerden 4 veya 5 karakterli büyük harfli hisse kodlarını ayıkla
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if text.isupper() and text.isalpha() and 4 <= len(text) <= 5:
                hisseler.add(text)
                
        return list(hisseler)
    except Exception as e:
        print(f"Hisse listesi çekilemedi: {e}")
        return []

def get_takas_data(hisse_kodu):
    # DİKKAT: Buraya asıl veriyi çeken (scraping/API) kodunuzu entegre etmelisiniz.
    bugun = datetime.now().strftime('%Y-%m-%d')
    data = {
        "Tarih": [bugun, bugun],
        "Hisse": [hisse_kodu, hisse_kodu],
        "Kurum": ["Citi", "Doçe"], 
        "Net_Lot": [15000, -5000]
    } 
    return pd.DataFrame(data)

def guncelle_ve_eskiyisil(df):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_json = json.loads(os.environ["GCP_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key("1NrL6Q7eJRgN6YBQNjdev_1wVCAsh8Zz-zR-I9eMeGgo").sheet1 
    
    # 6 ay (yaklaşık 180 gün) filtresi uygula
    df['Tarih'] = pd.to_datetime(df['Tarih'])
    alti_ay_once = pd.to_datetime('today') - pd.DateOffset(months=6)
    
    df_guncel = df[df['Tarih'] >= alti_ay_once].copy()
    df_guncel['Tarih'] = df_guncel['Tarih'].dt.strftime('%Y-%m-%d')
    
    # E-Tablo'yu temizle ve sadece güncel 6 aylık veriyi ekle
    sheet.clear()
    sheet.update([df_guncel.columns.values.tolist()] + df_guncel.values.tolist())

if __name__ == "__main__":
    hisse_listesi = get_tum_hisseler()
    print(f"Toplam {len(hisse_listesi)} hisse senedi bulundu.")
    
    tum_takaslar = []
    
    # Bütün hisseleri dön ve verileri topla
    for hisse in hisse_listesi:
        print(f"{hisse} verisi çekiliyor...")
        try:
            df_hisse = get_takas_data(hisse)
            tum_takaslar.append(df_hisse)
        except Exception as e:
            print(f"{hisse} çekilirken hata: {e}")
            
        time.sleep(5) # IP engeline takılmamak için aralara bekleme koyulur
        
    if tum_takaslar:
        ana_tablo = pd.concat(tum_takaslar, ignore_index=True)
        guncelle_ve_eskiyisil(ana_tablo)
        print("Tüm veriler başarıyla filtrelendi ve E-Tabloya yazıldı!")
