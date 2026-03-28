import streamlit as st
import cv2
import numpy as np
from PIL import Image
import math
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="GeoStrike V4.1 - Canlı Tıklama", layout="wide")

st.title("🪨 GeoStrike V4.1: Canlı Yüzey Seçimi")
st.markdown("Dokunmatik ekran sorunu çözüldü! Artık tıkladığınız noktalar anında fotoğraf üzerinde belirecek.")

# --- BÖLÜM 1: DİNAMİK SENSÖR VERİLERİ ---
st.sidebar.header("📱 Sensör Verileri")
dip_direction = st.sidebar.slider("Eğim Yönü (Azimut)", 0, 360, 45) 
dip_angle = st.sidebar.slider("Eğim Açısı (Derece)", 0, 90, 65)

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

# --- BÖLÜM 2: GÖRÜNTÜ YÜKLEME VE TIKLAMA ---
uploaded_files = st.file_uploader("Test fotoğrafını yükleyin (Min 3):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if len(uploaded_files) >= 3:
    st.success("✅ 3 fotoğraf başarıyla alındı.")
    
    master_image_file = uploaded_files[0]
    image = Image.open(master_image_file)
    img_array = np.array(image)
    h, w, _ = img_array.shape

    # Tıklama hafızası
    if "clicked_points" not in st.session_state:
        st.session_state["clicked_points"] = []

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("🔄 Noktaları Temizle"):
            st.session_state["clicked_points"] = []
            st.rerun()

    # CANLI ÇİZİM ALANI
    master_marked = img_array.copy()
    
    # Hafızadaki noktaları resme kalın yeşil ile çiz
    for pt in st.session_state["clicked_points"]:
        cv2.circle(master_marked, pt, 25, (0, 255, 0), -1) 
    
    # 2'den fazla nokta varsa aralarını birleştirip çerçeve yap
    if len(st.session_state["clicked_points"]) >= 2:
        pts_poly = np.array(st.session_state["clicked_points"], np.int32)
        cv2.polylines(master_marked, [pts_poly], isClosed=True, color=(0, 255, 0), thickness=6)

    # Çizilmiş resmi PIL formatına çevirip tıklanabilir araca veriyoruz
    marked_pil = Image.fromarray(master_marked)
    
    st.subheader("Aşağıdaki fotoğrafın üzerinde ölçülecek yüzeyin köşelerine tıklayın:")
    coords = streamlit_image_coordinates(marked_pil, key="geo_coords")

    # Tıklama anında çalışacak kod (Saniyesinde yeniler)
    if coords is not None:
        pt = (coords["x"], coords["y"])
        # Aynı noktaya üst üste tıklamayı engelle
        if len(st.session_state["clicked_points"]) == 0 or st.session_state["clicked_points"][-1] != pt:
            st.session_state["clicked_points"].append(pt)
            st.rerun() # SAYFAYI ANINDA YENİLE

    # ÖLÇÜMÜ TAMAMLA BUTONU
    if st.button("✅ Ölçümü Tamamla ve Raporu Al"):
        if len(st.session_state["clicked_points"]) >= 3:
            
            # KULLANICI MASKESİ
            mask = np.zeros((h, w), dtype=np.uint8)
            pts = np.array(st.session_state["clicked_points"], np.int32)
            cv2.fillPoly(mask, [pts], 255) 
            
            master_result = img_array.copy()
            line_layer = np.zeros_like(img_array)

            # PERSPEKTİF SİMÜLASYONU VE MERKEZ
            M = cv2.moments(pts)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

                # Doğrultu (Kırmızı)
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

                # KESİŞİM İŞLEMİ (Sadece tıklanan çerçevenin içinde kalır)
                lines_masked = cv2.bitwise_and(line_layer, line_layer, mask=mask)
                master_result = cv2.addWeighted(master_result, 1, lines_masked, 1, 0)
                cv2.polylines(master_result, [pts], isClosed=True, color=(0, 255, 0), thickness=3)

                st.divider()
                st.subheader("Nihai Master Çıktı Raporu")
                st.image(master_result, caption="Senin Belirlediğin Maske İçinde Kalan Çizgiler ve Perspektif", use_container_width=True)
                
                st.success(f"📌 JEOLOJİK ÖLÇÜM SONUCU: **{sonuc_metni}**")
            else:
                st.error("Tıklanan noktalar geçerli bir alan oluşturmadı.")
        else:
            st.warning("Raporu almak için lütfen fotoğrafta en az 3 nokta işaretleyin.")

elif len(uploaded_files) > 0:
    st.warning("Devam etmek için 3 fotoğraf yüklemeniz gerekiyor.")
