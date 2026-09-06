import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import time
from datetime import datetime
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

def get_tum_hisseler(driver):
    try:
        driver.get("https://www.kap.org.tr/tr/bist-sirketler")
        time.sleep(4) # KAP sayfasındaki tablonun JS ile yüklenmesini bekle
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        hisseler = set()
        
        # Sitedeki div'lerden büyük harfli ve 4-5 karakterli BİST kodlarını ayıkla
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if text.isupper() and text.isalpha() and 4 <= len(text) <= 5:
                hisseler.add(text)
                
        return list(hisseler)
    except Exception as e:
        print(f"Hisse listesi çekilemedi: {e}")
        return []

def get_takas_data(hisse_kodu, driver):
    # İş Yatırım veya benzeri bir finans sitesinin şirket detay sayfasına gidilir
    url = f"https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={hisse_kodu}"
    driver.get(url)
    time.sleep(3) # Tabloların ekrana yansıması için bekle
    
    try:
        # Sayfadaki tüm tabloları tespit et
        tablolar = pd.read_html(driver.page_source)
    except ValueError:
        return pd.DataFrame() 
        
    df_takas = pd.DataFrame()
    
    # İçinde "kurum", "takas", "yabancı" veya "pay" geçen doğru tabloyu bul
    for tablo in tablolar:
        cols = [str(c).lower() for c in tablo.columns]
        if any("kurum" in c or "takas" in c or "yabancı" in c or "pay" in c for c in cols):
            df_takas = tablo.copy()
            break
            
    if df_takas.empty:
        return pd.DataFrame()
        
    # Google E-Tablo'da sorun çıkmaması için sütun isimlerini ve NaN (boş) değerleri temizle
    df_takas.columns = [str(c).strip() for c in df_takas.columns]
    
    # Tarih ve Hisse Kodu sütunlarını en başa ekle
    bugun = datetime.now().strftime('%Y-%m-%d')
    df_takas.insert(0, "Hisse", hisse_kodu)
    df_takas.insert(0, "Tarih", bugun)
    
    return df_takas

def guncelle_ve_eskiyisil(df):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_json = json.loads(os.environ["GCP_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key("1NrL6Q7eJRgN6YBQNjdev_1wVCAsh8Zz-zR-I9eMeGgo").sheet1 
    
    # Veri tiplerinden kaynaklı hataları önlemek için boş hücreleri string yap
    df = df.fillna("")
    
    # 6 ay (yaklaşık 180 gün) filtresi
    df['Tarih'] = pd.to_datetime(df['Tarih'])
    alti_ay_once = pd.to_datetime('today') - pd.DateOffset(months=6)
    
    df_guncel = df[df['Tarih'] >= alti_ay_once].copy()
    df_guncel['Tarih'] = df_guncel['Tarih'].dt.strftime('%Y-%m-%d')
    
    # Eski kayıtları uçur ve yenisini kaydet
    sheet.clear()
    sheet.update([df_guncel.columns.values.tolist()] + df_guncel.values.tolist())

if __name__ == "__main__":
    # Tarayıcı (Driver) bir kere başlatılır. Yüzlerce hisse aynı pencerede açılır.
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(options=options)
    
    hisse_listesi = get_tum_hisseler(driver)
    print(f"Toplam {len(hisse_listesi)} hisse senedi KAP'tan bulundu.")
    
    tum_takaslar = []
    
    for hisse in hisse_listesi:
        print(f"{hisse} takas verisi taranıyor...")
        try:
            df_hisse = get_takas_data(hisse, driver)
            if not df_hisse.empty:
                tum_takaslar.append(df_hisse)
            else:
                print(f"{hisse} sayfasında geçerli takas tablosu bulunamadı.")
        except Exception as e:
            print(f"{hisse} okuma hatası: {e}")
            
        time.sleep(3) # Sunucu IP bloklaması yapmasın diye 3 saniye bekle
        
    driver.quit() # Tüm işlemler bitince belleği temizlemek için tarayıcıyı kapat
    
    if tum_takaslar:
        ana_tablo = pd.concat(tum_takaslar, ignore_index=True)
        guncelle_ve_eskiyisil(ana_tablo)
        print("Tüm hisse verileri Google E-Tablo'ya başarıyla aktarıldı!")
    else:
        print("İşlem iptal edildi: Hiçbir veri bulunamadı.")
