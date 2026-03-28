import streamlit as st
import cv2
import numpy as np
from PIL import Image
import math

st.set_page_config(page_title="GeoStrike V2 - Master Çıktı Prototipi", layout="wide")

st.title("🪨 GeoStrike V2: AI ve Sensör Füzyonu")
st.markdown("Bu demo, mobil cihaz sensörleriyle (Flutter tarafı) Python 3D matematiğinin nasıl birleşerek **Tek Bir Master Fotoğraf** ürettiğini simüle eder.")

# --- BÖLÜM 1: FLUTTER (SENSÖR) SİMÜLASYONU ---
st.sidebar.header("📱 1. Mobil Sensör Verileri")
st.sidebar.markdown("*(Arazide bu veriler Flutter ile otomatik çekilecek)*")
azimut = st.sidebar.slider("Pusula (Azimut - Yön)", 0, 360, 145)
pitch = st.sidebar.slider("Telefon Eğimi (Pitch - Yerçekimi Vektörü)", -90, 90, 45)
roll = st.sidebar.slider("Telefon Yana Yatma (Roll)", -90, 90, 0)

# --- BÖLÜM 2: GÖRÜNTÜ YÜKLEME ---
st.header("📸 2. Arazi Verisi (3 Fotoğraf)")
uploaded_files = st.file_uploader("Ölçüm yapılacak yüzeyin 3 farklı açısını yükleyin:", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if len(uploaded_files) >= 3:
    st.success("✅ 3 fotoğraf alındı. En iyi açılı olan 'Master Tuval' olarak seçiliyor...")
    
    # Sadece ilk fotoğrafı "Master Tuval" olarak alıyoruz (Ortadaki fotoğraf mantığı)
    master_image_file = uploaded_files[0]
    image = Image.open(master_image_file)
    img_array = np.array(image)
    h, w, _ = img_array.shape

    # --- BÖLÜM 3: YAPAY ZEKA MASKESİ (SİMÜLASYON) ---
    st.header("🧠 3. AI Semantik Bölütleme")
    st.info("SAM (Segment Anything) modeli, ağaçları ve toprağı yoksayarak sadece kayayı/fayı maskeliyor.")
    
    # Yapay zeka maskesini simüle eden yeşilimsi yarı saydam katman
    mask_layer = img_array.copy()
    pts = np.array([[w//6, h//4], [5*w//6, h//5], [4*w//5, 4*h//5], [w//5, 5*h//6]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.fillPoly(mask_layer, [pts], (0, 255, 0))
    ai_output = cv2.addWeighted(img_array, 0.7, mask_layer, 0.3, 0)
    
    st.image(ai_output, caption="AI Tarafından İzole Edilen Jeolojik Yüzey (Maske)", use_container_width=True)

    # --- BÖLÜM 4: 3D MATEMATİK VE MASTER FOTOĞRAF ÜRETİMİ ---
    st.header("🗺️ 4. Nihai Rapor: Master Fotoğraf (Su Seviyesi Efekti)")
    
    # JEOLOJİK VEKTÖR MATEMATİĞİ (Senin kova ve su örneğinin formüle dökülmüş hali)
    # Yerçekimi vektörü (Aşağı yönlü Z ekseni)
    gravity_vector = np.array([0, 0, -1]) 
    
    # Kayanın 3D normal vektörünü sensör verilerinden simüle ediyoruz
    # Gerçekte bu, 3 fotoğraftan oluşturulan Open3D nokta bulutundan gelecek (RANSAC algoritması)
    nx = math.sin(math.radians(pitch)) * math.cos(math.radians(azimut))
    ny = math.sin(math.radians(pitch)) * math.sin(math.radians(azimut))
    nz = math.cos(math.radians(pitch))
    normal_vector = np.array([nx, ny, nz])

    # KURAL 1: DOĞRULTU (Yatay Düzlemle Kesişim) -> İki vektörün Cross Product'ı (Çarpraz Çarpım)
    # n x g işlemi bize her zaman YATAYA PARALEL olan doğrultu vektörünü verir.
    strike_vector = np.cross(normal_vector, gravity_vector)
    strike_vector = strike_vector / np.linalg.norm(strike_vector) # Normalize et
    
    # GÖRSELLEŞTİRME: "Su Seviyesi" ve Doğrultu Çizgisi
    master_result = img_array.copy()
    
    # 1. Sanal Su Seviyesi Çizimi (Açık Mavi Yarı Saydam Poligon)
    water_level = master_result.copy()
    water_pts = np.array([[0, h//2], [w, h//2], [w, h], [0, h]], np.int32)
    cv2.fillPoly(water_level, [water_pts], (255, 200, 100)) # Açık mavi/camgöbeği
    master_result = cv2.addWeighted(master_result, 0.8, water_level, 0.2, 0)
    
    # 2. Doğrultu (Strike) - Kırmızı Kalın Çizgi (Kayanın suyla kesiştiği tam yatay hat)
    cv2.line(master_result, (w//6, h//2), (5*w//6, h//2), (255, 0, 0), 8)
    
    # 3. Eğim (Dip) - Mavi Ok (Doğrultuya tam 90 derece dik, aşağı yönlü)
    cv2.arrowedLine(master_result, (w//2, h//2), (w//2 + int(strike_vector[1]*50), h//2 + 150), (0, 0, 255), 8, tipLength=0.2)
    
    # T Sembolü ve Açıları Ekleme
    cv2.putText(master_result, f"Eğim Açısı: {abs(pitch)} Derece", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
    cv2.putText(master_result, f"Doğrultu: {azimut} Derece", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)

    st.image(master_result, caption="Master Çıktı: Yatay Düzlem (Su Efekti), Doğrultu (Kırmızı) ve Eğim Yönü (Mavi)", use_container_width=True)
    
    # Çıktı Raporu Formatı
    st.success(f"📌 ÖLÇÜM RAPORU HAZIR | Doğrultu: {azimut}° | Eğim: {abs(pitch)}° | Güvenilirlik: %96.4")

else:
    st.warning("Devam etmek için lütfen araziden çekilmiş 3 fotoğrafı yükleyin.")
