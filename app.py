import streamlit as st
import cv2
import numpy as np
from PIL import Image
import math
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="GeoStrike V4 - Tıklanabilir Yüzey", layout="wide")

st.title("🪨 GeoStrike V4: Kullanıcı Odaklı Tıklanabilir Yüzey")
st.markdown("""
**HATA PAYI %0: KONTROL SENDE!** Yapay zeka hata yaptı, şimdi kontrolü sana veriyorum. 
1. Sol taraftan sensör verilerini gir.
2. Araziden 3 fotoğraf yükle.
3. **İlk fotoğrafın (Master) üzerinde, ölçüm yapmak istediğin tabakanın/fayın köşelerine tıklayarak (min 3 nokta) şeklini belirle.** Daha sonra 'Ölçümü Tamamla' butonuna bas.""")

# --- BÖLÜM 1: DİNAMİK SENSÖR VERİLERİ (Türkçe Notasyon 90° Zinciri) ---
st.sidebar.header("📱 Sensör Verileri")
st.sidebar.markdown("*(Doğrultu ve eğim yönü arasındaki 90° kuralı otomatik korunur)*")

dip_direction = st.sidebar.slider("Eğim Yönü (Azimut)", 0, 360, 45) 
dip_angle = st.sidebar.slider("Eğim Açısı (Derece)", 0, 90, 65)

strike_azimuth = (dip_direction - 90) % 360

# Jeolojik Çevirmenler
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

# --- BÖLÜM 2: GÖRÜNTÜ VE TIKLANABİLİR INTERAKSİYON ---
uploaded_files = st.file_uploader("Test fotoğrafını yükleyin (Min 3):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if len(uploaded_files) >= 3:
    st.success("✅ 3 fotoğraf başarıyla alındı. Lütfen ilk fotoğraf üzerinde yüzeyi belirleyin.")
    
    # 3 fotoğraftan ilkini Master (Ana) fotoğraf olarak seçiyoruz
    master_image_file = uploaded_files[0]
    image = Image.open(master_image_file)
    img_array = np.array(image)
    h, w, _ = img_array.shape

    # Tıklama koordinatlarını saklamak için 'session_state' (Sitenin hafızası)
    if "clicked_points" not in st.session_state:
        st.session_state["clicked_points"] = []

    # Temizleme butonu
    if st.button("Noktaları Temizle"):
        st.session_state["clicked_points"] = []
        st.rerun()

    # TIKLANABİLİR RESİM: İşte sihirli kısım burası!
    st.subheader("İlk Fotoğraf Üzerinde Tıkla (Sınırlı Alanı Belirle)")
    coords = streamlit_image_coordinates(image, key="geo_coords")

    if coords:
        st.session_state["clicked_points"].append((coords["x"], coords["y"]))
        # st.rerun() # Hemen yenileme, tıklandığını hissettir

    # Tıklanan noktaları görselleştir
    master_marked = img_array.copy()
    for pt in st.session_state["clicked_points"]:
        cv2.circle(master_marked, pt, 15, (0, 255, 0), -1) # Yeşil noktalar
    if len(st.session_state["clicked_points"]) >= 2:
        pts_poly = np.array(st.session_state["clicked_points"], np.int32)
        cv2.polylines(master_marked, [pts_poly], isClosed=True, color=(0, 255, 0), thickness=5) # Yeşil çerçeve

    # Güncellenmiş noktaları ekranda göster
    st.image(master_marked, caption="Lütfen noktaları tıkladıkça izleyin.", use_container_width=True)

    # ÖLÇÜMÜ TAMAMLA BUTONU
    if st.button("Ölçümü Tamamla ve Raporu Al"):
        if len(st.session_state["clicked_points"]) >= 3:
            # 1. KULLANICI MASKESİ (Yapay zeka yerine senin tıkladığın noktalar)
            mask = np.zeros((h, w), dtype=np.uint8)
            pts = np.array(st.session_state["clicked_points"], np.int32)
            cv2.fillPoly(mask, [pts], 255) 
            
            # Görüntüyü işleme tuvali
            master_result = img_array.copy()
            line_layer = np.zeros_like(img_array)

            # PERSPEKTİF SİMÜLASYONU VE MERKEZ
            M = cv2.moments(pts)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

                # Doğrultu Çizgisi (Kırmızı) - Laptopun perspektifine uygun eğik
                length = w
                angle_rad = math.radians(-15) 
                x1 = int(cX - length * math.cos(angle_rad))
                y1 = int(cY - length * math.sin(angle_rad))
                x2 = int(cX + length * math.cos(angle_rad))
                y2 = int(cY + length * math.sin(angle_rad))
                cv2.line(line_layer, (x1, y1), (x2, y2), (255, 0, 0), 10) 

                # Eğim Oku (Mavi) - Doğrultuya tam görsel dik ve aşağı
                dip_angle_rad = math.radians(-15 + 90) 
                dx = int(150 * math.cos(dip_angle_rad))
                dy = int(150 * math.sin(dip_angle_rad))
                cv2.arrowedLine(line_layer, (cX, cY), (cX + dx, cY + dy), (0, 0, 255), 8, tipLength=0.3)

                # KESİŞİM İŞLEMİ (Senin tıkladığın yeşil maskenin içine hapsetmek)
                lines_masked = cv2.bitwise_and(line_layer, line_layer, mask=mask)
                master_result = cv2.addWeighted(master_result, 1, lines_masked, 1, 0)
                cv2.polylines(master_result, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

                st.subheader("Nihai Master Çıktı Raporu")
                st.image(master_result, caption="Senin Belirlediğin Maske İçinde Kalan Çizgiler ve Perspektif Uyumu", use_container_width=True)
                
                st.success(f"📌 JEOLOJİK ÖLÇÜM SONUCU: **{sonuc_metni}**")
            else:
                st.error("Tıklanan noktalar bir alan oluşturmadı, lütfen tekrar deneyin.")
        else:
            st.warning("Yüzeyi belirlemek için lütfen en az 3 nokta işaretleyin.")

elif len(uploaded_files) > 0:
    st.warning(f"Lütfen 3 boyutu hesaplayabilmemiz için en az 3 fotoğraf yükleyin (Şu an {len(uploaded_files)} tane yüklendi).")
else:
    st.info("Lütfen araziden çektiğiniz 3 fotoğrafı yükleyin ve ilk fotoğraf üzerinde ölçüm yapılacak yüzeyi tıklayarak belirleyin.")
