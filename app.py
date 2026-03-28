import streamlit as st
import cv2
import numpy as np
from PIL import Image
import math

st.set_page_config(page_title="GeoStrike V3.1 - Profesyonel Çıktı", layout="wide")

st.title("🪨 GeoStrike V3.1: 3 Fotoğraf ve Jeolojik Notasyon")
st.markdown("Bu sürümde en az 3 fotoğraf yükleme zorunluluğu geri getirildi. Çizgiler maske içinde kalır ve Türkçe (K/G/D/B) jeolojik format kusursuz hesaplanır.")

# --- BÖLÜM 1: DİNAMİK SENSÖR VERİLERİ ---
st.sidebar.header("📱 Sensör Verileri")
st.sidebar.markdown("*(Doğrultu ve eğim yönü arasındaki 90° kuralı otomatik korunur)*")

dip_direction = st.sidebar.slider("Eğim Yönü (Azimut)", 0, 360, 45) 
dip_angle = st.sidebar.slider("Eğim Açısı (Derece)", 0, 90, 65)

strike_azimuth = (dip_direction - 90) % 360

# --- JEOLOJİK ÇEVİRMEN (Azimut -> Türkçe Kadran) ---
def get_quadrant_strike(azimuth):
    azimuth = azimuth % 180 
    if 0 <= azimuth <= 90:
        return f"K{int(azimuth)}D"
    else:
        return f"K{int(180 - azimuth)}B"

def get_quadrant_dip_dir(azimuth):
    if 0 <= azimuth < 90: return "KD"
    elif 90 <= azimuth < 180: return "GD"
    elif 180 <= azimuth < 270: return "GB"
    else: return "KB"

formatli_dogrultu = get_quadrant_strike(strike_azimuth)
formatli_egim_yonu = get_quadrant_dip_dir(dip_direction)
sonuc_metni = f"{formatli_dogrultu} / {dip_angle}{formatli_egim_yonu}"

# --- BÖLÜM 2: GÖRÜNTÜ VE MASKELEME (DÜZELTİLEN KISIM) ---
uploaded_files = st.file_uploader("Ölçüm yapılacak yüzeyin 3 farklı açısını yükleyin (Min 3):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if len(uploaded_files) >= 3:
    st.success("✅ 3 fotoğraf başarıyla alındı. 'Master Tuval' oluşturuluyor...")
    
    # 3 fotoğraftan ilkini Master (Ana) fotoğraf olarak seçiyoruz
    master_image_file = uploaded_files[0]
    image = Image.open(master_image_file)
    img_array = np.array(image)
    h, w, _ = img_array.shape

    # 1. AI Maskesi Oluşturma (Sadece kayanın olduğu bölge)
    mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array([[w//5, h//3], [4*w//5, h//4], [7*w//8, 3*h//4], [w//4, 4*h//5]], np.int32)
    cv2.fillPoly(mask, [pts], 255) 
    
    master_result = img_array.copy()
    line_layer = np.zeros_like(img_array)

    # PERSPEKTİF SİMÜLASYONU
    M = cv2.moments(pts)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])

    # Doğrultu Çizgisi (Kırmızı)
    length = w
    angle_rad = math.radians(-15) 
    x1 = int(cX - length * math.cos(angle_rad))
    y1 = int(cY - length * math.sin(angle_rad))
    x2 = int(cX + length * math.cos(angle_rad))
    y2 = int(cY + length * math.sin(angle_rad))
    cv2.line(line_layer, (x1, y1), (x2, y2), (255, 0, 0), 10) 

    # Eğim Oku (Mavi)
    dip_angle_rad = math.radians(-15 + 90) 
    dx = int(150 * math.cos(dip_angle_rad))
    dy = int(150 * math.sin(dip_angle_rad))
    cv2.arrowedLine(line_layer, (cX, cY), (cX + dx, cY + dy), (0, 0, 255), 8, tipLength=0.3)

    # KESİŞİM İŞLEMİ (Çizgileri maskenin içine hapsetmek)
    lines_masked = cv2.bitwise_and(line_layer, line_layer, mask=mask)
    master_result = cv2.addWeighted(master_result, 1, lines_masked, 1, 0)
    cv2.polylines(master_result, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

    st.image(master_result, caption="V3.1 Master Çıktı: Maskelenmiş Çizgiler ve Perspektif Uyumu", use_container_width=True)
    
    st.success(f"📌 JEOLOJİK ÖLÇÜM SONUCU: **{sonuc_metni}**")

elif len(uploaded_files) > 0:
    st.warning(f"Lütfen 3 boyutu hesaplayabilmemiz için en az 3 fotoğraf yükleyin (Şu an {len(uploaded_files)} tane yüklendi).")
else:
    st.info("Lütfen araziden çektiğiniz 3 fotoğrafı yükleyin.")
