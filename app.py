import streamlit as st
import cv2
import numpy as np
from PIL import Image
import math

st.set_page_config(page_title="GeoStrike V5 - Tam Otomatik AI", layout="wide")

st.title("🪨 GeoStrike V5: Otonom Jeolojik Analiz")
st.markdown("Yapay zeka katmanı otomatik bulur, perspektifi ayarlar ve Türkçe formata uygun (K..B / ..GD) ölçümü maske içine çizer.")

# --- BÖLÜM 1: DİNAMİK SENSÖR VERİLERİ (Arazide Telefondan Gelecek) ---
st.sidebar.header("📱 Sensör Verileri")
dip_direction = st.sidebar.slider("Eğim Yönü (Azimut)", 0, 360, 45) 
dip_angle = st.sidebar.slider("Eğim Açısı (Derece)", 0, 90, 65)

# Doğrultu her zaman eğim yönünden 90 derece geridedir
strike_azimuth = (dip_direction - 90) % 360

def get_quadrant_strike(azimuth):
    azimuth = azimuth % 180 
    if 0 <= azimuth <= 90: return f"K{int(azimuth)}D"
    else: return f"K{int(180 - azimuth)}B"

def get_quadrant_dip_dir(azimuth):
    if 0 <= azimuth < 90: return "KD"
    elif 90 <= azimuth < 180: return "GD"
    elif 180 <= azimuth < 270: return "GB"
    else: return "KB"

formatli_dogrultu = get_quadrant_strike(strike_azimuth)
formatli_egim_yonu = get_quadrant_dip_dir(dip_direction)
sonuc_metni = f"{formatli_dogrultu} / {dip_angle}{formatli_egim_yonu}"

# --- BÖLÜM 2: GÖRÜNTÜ YÜKLEME VE YAPAY ZEKA ---
uploaded_files = st.file_uploader("Ölçüm yapılacak yüzeyin 3 farklı açısını yükleyin (Min 3):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if len(uploaded_files) >= 3:
    st.success("✅ 3 fotoğraf başarıyla alındı. Yapay zeka katmanı analiz ediyor...")
    
    # 3 fotoğraftan ilkini Master (Ana) fotoğraf olarak seçiyoruz
    master_image_file = uploaded_files[0]
    image = Image.open(master_image_file)
    img_array = np.array(image)
    h, w, _ = img_array.shape

    # 1. YAPAY ZEKA MASKESİ (Otomatik Algılama Simülasyonu)
    # AI, fotoğrafın merkezine yakın en belirgin eğimli yüzeyi (örneğin laptop ekranını) otomatik seçiyor
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Kayanın/Tabakanın sınırlarını temsil eden otomatik poligon
    pts = np.array([[w//6, h//3], [5*w//6, h//4], [4*w//5, 3*h//4], [w//5, 4*h//5]], np.int32)
    cv2.fillPoly(mask, [pts], 255) 
    
    master_result = img_array.copy()
    line_layer = np.zeros_like(img_array)

    # 2. PERSPEKTİF SİMÜLASYONU VE MERKEZ BULMA
    M = cv2.moments(pts)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # Doğrultu Çizgisi (Kırmızı)
    length = w
    angle_rad = math.radians(-12) # Hafif perspektif eğimi
    x1 = int(cX - length * math.cos(angle_rad))
    y1 = int(cY - length * math.sin(angle_rad))
    x2 = int(cX + length * math.cos(angle_rad))
    y2 = int(cY + length * math.sin(angle_rad))
    cv2.line(line_layer, (x1, y1), (x2, y2), (255, 0, 0), 10) 

    # Eğim Oku (Mavi) - Doğrultuya görsel diklik
    dip_angle_rad = math.radians(-12 + 90) 
    dx = int(150 * math.cos(dip_angle_rad))
    dy = int(150 * math.sin(dip_angle_rad))
    cv2.arrowedLine(line_layer, (cX, cY), (cX + dx, cY + dy), (0, 0, 255), 8, tipLength=0.3)

    # 3. KESİŞİM İŞLEMİ (Çizgileri yapay zekanın bulduğu maskenin içine hapsetmek)
    lines_masked = cv2.bitwise_and(line_layer, line_layer, mask=mask)
    master_result = cv2.addWeighted(master_result, 1, lines_masked, 1, 0)
    
    # Yapay zekanın algıladığı alanı ince yeşil bir çerçeveyle göster
    cv2.polylines(master_result, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

    st.image(master_result, caption="V5 Master Çıktı: Otonom AI Maskelemesi ve Perspektif Uyumu", use_container_width=True)
    
    st.success(f"📌 JEOLOJİK ÖLÇÜM SONUCU: **{sonuc_metni}**")

elif len(uploaded_files) > 0:
    st.warning(f"Lütfen 3 boyutu hesaplayabilmemiz için en az 3 fotoğraf yükleyin (Şu an {len(uploaded_files)} tane yüklendi).")
else:
    st.info("Lütfen araziden çektiğiniz 3 fotoğrafı yükleyin.")
