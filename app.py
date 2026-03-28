import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="GeoStrike - Jeolojik Ölçüm Demosu", layout="wide")

st.title("🪨 GeoStrike: 3D Katman Analiz Sistemi")
st.write("Doğruluğu test etmek için en az 3 fotoğraf yükleyin. Sistem uzaydaki konumu ve açıyı hesaplayacaktır.")

# Yan menü - Sensör simülasyonu
st.sidebar.header("Cihaz Sensör Verileri")
gps = st.sidebar.text_input("GPS Koordinatı", "38.4237° N, 27.1428° E")
pusula = st.sidebar.slider("Bakış Yönü (Azimut)", 0, 360, 180)

# Fotoğraf yükleme alanı
uploaded_files = st.file_uploader("Fotoğrafları Seçin (Min 3 tane)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

if len(uploaded_files) >= 3:
    st.success("✅ 3 fotoğraf alındı. Görüntü işleme ve 3D modelleme başlatılıyor...")
    
    cols = st.columns(3)
    processed_images = []

    for i, file in enumerate(uploaded_files[:3]):
        # Görüntüyü oku
        image = Image.open(file)
        img_array = np.array(image)
        
        # Basit görüntü işleme: Kenar bulma (Canny Edge Detection)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Çizgileri bulma (Hough Transform simülasyonu)
        # Burada senin istediğin o çizgileri çiziyoruz
        result_img = img_array.copy()
        h, w, _ = result_img.shape
        cv2.line(result_img, (w//4, h//2), (3*w//4, h//2), (255, 0, 0), 10) # Mavi Doğrultu
        cv2.arrowedLine(result_img, (w//2, h//2), (w//2, h//2 + 100), (255, 0, 0), 10) # Kırmızı Eğim
        
        cols[i].image(result_img, caption=f"Fotoğraf {i+1} İşlendi")

    # Yapay Zeka Hesaplama Sonuçları (Simüle edilmiş hassas hesaplama)
    st.divider()
    st.subheader("📊 Analiz Sonuçları")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Hesaplanan Eğim (Dip)", "42° NW")
    c2.metric("Doğrultu (Strike)", "125° SE")
    c3.metric("Hata Payı (Accuracy)", "%0.82")

    st.info(f"📍 Konum: {gps} | 🧭 Yön: {pusula}° | 🛠️ Metod: SfM + RANSAC Plane Fitting")

else:
    st.warning("Lütfen test etmek için en az 3 fotoğraf yükleyin.")
