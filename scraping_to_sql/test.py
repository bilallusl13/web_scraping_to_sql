from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# PostgreSQL bağlantısını güvenli hale getir
db_url = os.getenv("DB_URL")
if not db_url:
    raise ValueError("DB_URL çevresel değişkeni bulunamadı!")

engine = create_engine(db_url)

# CSV dosya yolunu güvenli hale getir
csv_path = os.getenv("CSV_PATH")
if not csv_path or not os.path.exists(csv_path):
    raise FileNotFoundError(f"CSV dosyası bulunamadı: {csv_path}")

# Chrome WebDriver başlat
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Verileri saklamak için listeler
ev_adlari, ev_fiyatlari, mahalleler, alan, daire_tipi, oda_sayisi = [], [], [], [], [], []

# 2'den 50'ye kadar sayfalardaki ilanları çek
for i in range(2, 50):  
    url = f"scraping yapılacak site"  
    driver.get(url)
    
    # İlan başlıklarını bul
    ev_adlar = driver.find_elements(By.CLASS_NAME, "styles_titleWrapper__HqJFc")
    for c in ev_adlar:
        ev_adlari.append(c.text)  # .text eklenmeli
    
    # Fiyatları bul
    ev_fiyatlar = driver.find_elements(By.CLASS_NAME, "styles_priceWrapper__TpQak")
    for t in ev_fiyatlar:
        ev_fiyatlari.append(t.text)  # .text eklenmeli

    # Mahalle bilgilerini al
    mahalle_bilgisi = driver.find_elements(By.CLASS_NAME, "styles_locationWrapper__Lym1J")
    for a in mahalle_bilgisi:
        mahalleler.append(a.text)

    # Özellikleri al
    özellikler = driver.find_elements(By.CLASS_NAME, "styles_quickinfoWrapper__F5BBD")
    for özellik in özellikler:
        metin = özellik.text
        oz = metin.split("|")
        
        if len(oz) >= 3:
            daire_tipi.append(oz[0])
            oda_sayisi.append(oz[1])
            alan.append(oz[2])
        else:
            daire_tipi.append("")
            oda_sayisi.append("")
            alan.append("")

    print(f"Şu an açılan sayfa: {url}")  # Bilgilendirme çıktısı

# Veriyi DataFrame'e aktar
data = {
    'Ev Adı': ev_adlari,
    'Ev Fiyatı': ev_fiyatlari,
    'Konum': mahalleler,
    'm^2': alan,
    'Daire Tipi': daire_tipi,
    'Oda Sayısı': oda_sayisi,
}

df = pd.DataFrame(data)

# Veriyi Excel'e kaydet
df.to_excel('emlak_verileri.xlsx', index=False)  # .xlsx uzantısını kullan

# CSV'yi PostgreSQL'e yüklemeden önce sütun isimlerini düzelt
df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace(r"[^\w]", "", regex=True)

# Veriyi PostgreSQL'e ekle
df.to_sql("emlak", engine, if_exists="append", index=False)

print("CSV başarıyla PostgreSQL'e yüklendi!")

# Tarayıcıyı kapat
driver.quit()
print("Veriler başarıyla kaydedildi!")
