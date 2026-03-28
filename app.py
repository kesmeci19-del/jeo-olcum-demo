import streamlit as st
import cv2
import numpy as np
from PIL import Image
import math

st.set_page_config(page_title="GeoStrike V3 - Profesyonel Çıktı", layout="wide")

st.title("🪨 GeoStrike V3: Jeolojik Notasyon ve Perspektif")
st.markdown("Bu sürümde çizgiler sadece maske içinde kalır ve Türkçe (K/G/D/B) jeolojik format kusursuz hesaplanır.")

# --- BÖLÜM 1: DİNAMİK SENSÖR VERİLERİ ---
st.sidebar.header("📱 Sensör Verileri")
st.sidebar.markdown("*(Doğrultu ve eğim yönü arasındaki 90° kuralı otomatik korunur)*")

# Kullanıcı eğim yönünü ve açısını girer, doğrultu otomatik 90 derece farkla hesaplanır.
dip_direction = st.sidebar.slider("Eğim Yönü (Azimut)", 0, 360, 45) # Örnek: 45 = KD
dip_angle = st.sidebar.slider("Eğim Açısı (Derece)", 0, 90, 65)

# Doğrultu Azimutu her zaman Eğim Yönünden 90 derece geridedir (Sol el / Sağ el esnekliği)
strike_azimuth = (dip_direction - 90) % 360

# --- JEOLOJİK ÇEVİRMEN (Azimut -> Türkçe Kadran) ---
def get_quadrant_strike(azimuth):
    """0-360 derecelik azimutu K..D veya K..B formatına çevirir"""
    azimuth = azimuth % 180 # Doğrultu çift yönlüdür, Kuzey yarımküreye sabitliyoruz
    if 0 <= azimuth <= 90:
        return f"K{int(azimuth)}D"
    else:
        return f"K{int(180 - azimuth)}B"

def get_quadrant_dip_dir(azimuth):
    """Eğim yönünü pusula yönlerine (KD, GD, GB, KB) çevirir"""
    if 0 <= azimuth < 90: return "KD"
    elif 90 <= azimuth < 180: return "GD"
    elif 180 <= azimuth < 270: return "GB"
    else: return "KB"

# Nihai Jeolojik String (Örn: K45B / 65KD)
formatli_dogrultu = get_quadrant_strike(strike_azimuth)
formatli_egim_yonu = get_quadrant_dip_dir(dip_direction)
sonuc_metni = f"{formatli_dogrultu} / {dip_angle}{formatli_egim_yonu}"

# --- BÖLÜM 2: GÖRÜNTÜ VE MASKELEME ---
uploaded_files = st.file_uploader("Test fotoğrafını yükleyin:", type=['png', 'jpg', 'jpeg'])

if uploaded_files:
    image = Image.open(uploaded_files)
    img_array = np.array(image)
    h, w, _ = img_array.shape

    # 1. AI Maskesi Oluşturma (Sadece kayanın olduğu bölge)
    mask = np.zeros((h, w), dtype=np.uint8)
    # Maske koordinatları (Kayanın sınırlarını simüle eder)
    pts = np.array([[w//5, h//3], [4*w//5, h//4], [7*w//8, 3*h//4], [w//4, 4*h//5]], np.int32)
    cv2.fillPoly(mask, [pts], 255) # Sadece bu çokgenin içi beyaz (255) olur
    
    # Görsel Çıktı Tuvali
    master_result = img_array.copy()

    # 2. Çizgileri Çizeceğimiz Boş Bir Şeffaf Katman
    line_layer = np.zeros_like(img_array)

    # PERSPEKTİF SİMÜLASYONU (Çizgilerin laptop fotoğrafındaki gibi eğik görünmesi için)
    # Merkezi nokta maskenin ortası olsun
    M = cv2.moments(pts)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # Doğrultu Çizgisi (Kırmızı) - Maskenin dışına taşmayacak uzunlukta çiziyoruz
    # Eğimi perspektife göre (örneğin -15 derece yatık) simüle ediyoruz
    length = w
    angle_rad = math.radians(-15) # Perspektif açısı (Kameranın yatay ufka göre konumu)
    x1 = int(cX - length * math.cos(angle_rad))
    y1 = int(cY - length * math.sin(angle_rad))
    x2 = int(cX + length * math.cos(angle_rad))
    y2 = int(cY + length * math.sin(angle_rad))
    cv2.line(line_layer, (x1, y1), (x2, y2), (255, 0, 0), 10) # Kırmızı çizgi

    # Eğim Oku (Mavi) - Doğrultuya görsel olarak dik ve aşağı yönlü
    dip_angle_rad = math.radians(-15 + 90) 
    dx = int(150 * math.cos(dip_angle_rad))
    dy = int(150 * math.sin(dip_angle_rad))
    cv2.arrowedLine(line_layer, (cX, cY), (cX + dx, cY + dy), (0, 0, 255), 8, tipLength=0.3)

    # 3. KESİŞİM İŞLEMİ (Sihirli Kısım: Çizgileri maskenin içine hapsetmek)
    # Sadece 'mask'in beyaz olduğu yerlerdeki çizgileri al
    lines_masked = cv2.bitwise_and(line_layer, line_layer, mask=mask)
    
    # Maskelenmiş çizgileri orijinal fotoğrafa ekle
    master_result = cv2.addWeighted(master_result, 1, lines_masked, 1, 0)
    
    # Maskenin dış hatlarını hafifçe belli et (Profesyonel AR hissi)
    cv2.polylines(master_result, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

    st.image(master_result, caption="V3 Master Çıktı: Maskelenmiş Çizgiler ve Perspektif Uyumu", use_container_width=True)
    
    # Jeolojik Formatlı Rapor
    st.success(f"📌 JEOLOJİK ÖLÇÜM SONUCU: **{sonuc_metni}**")

else:
    st.info("Lütfen bir fotoğraf yükleyin.")
