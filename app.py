import streamlit as st
import pandas as pd
import re # Untuk filter jurusan
import ast # Untuk membersihkan data 'jenjang' (disimpan untuk jaga-jaga)
import plotly.express as px # <-- DIBUTUHKAN UNTUK TREEMAP

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Filter Lowongan Magang",
    page_icon="🔎",
    layout="wide"
)

# --- 2. Fungsi Load Data (Cache) ---
@st.cache_data
def load_data():
    df = pd.read_csv("data_lowongan_BERSIH.csv")
    
    # --- Siapkan Filter Jurusan ---
    all_jurusan_set = set()
    for item_list in df['program_studi'].str.split(', '):
        if isinstance(item_list, list):
            all_jurusan_set.update(item_list)
    list_jurusan_unik = sorted(list(all_jurusan_set))
    
    # --- Siapkan Filter Lokasi ---
    list_provinsi_unik = sorted(df['perusahaan.nama_provinsi'].dropna().unique())
    list_kota_unik = sorted(df['perusahaan.nama_kabupaten'].dropna().unique())
    
    return df, list_jurusan_unik, list_provinsi_unik, list_kota_unik

# --- Fungsi BANTUAN untuk membersihkan kolom 'jenjang' (DISIMPAN, tapi tidak dipakai di grafik) ---
def parse_jenjang(jenjang_str):
    try:
        return ast.literal_eval(jenjang_str)
    except (ValueError, SyntaxError):
        return []

# --- 3. Muat Data ---
with st.spinner('Memuat 37.000+ data lowongan...'):
    df, list_jurusan_unik, list_provinsi_unik, list_kota_unik = load_data()

# ===============================================
# --- 4. Tampilan Web / Interface (UI) ---
# ===============================================
st.title('🔎 Dashboard Filter Lowongan Magang KEMNAKER')
st.write(f"Total data lowongan di-crawl: {len(df)} baris")

# ===============================================
# --- 5. Sidebar untuk Filter (HANYA LOKASI) ---
# ===============================================
st.sidebar.header('⚙️ Filter Lokasi (Instan)')

# Filter 2: Provinsi (Multi-select)
provinsi_pilihan = st.sidebar.multiselect(
    'Pilih Provinsi:',
    options=list_provinsi_unik,
    default=[]
)

# Filter 3: Kota/Kabupaten (Multi-select DINAMIS)
if provinsi_pilihan:
    kota_tersedia = sorted(df[df['perusahaan.nama_provinsi'].isin(provinsi_pilihan)]['perusahaan.nama_kabupaten'].dropna().unique())
else:
    kota_tersedia = list_kota_unik 

kota_pilihan = st.sidebar.multiselect(
    'Pilih Kota/Kabupaten:',
    options=kota_tersedia,
    default=[]
)

# ===============================================
# --- 6. FORM FILTER UTAMA (DI ATAS TABEL) ---
# ===============================================
st.markdown("---") # Garis pemisah

with st.form(key='form_filter_utama'):
    st.write("Pilih filter Posisi/Jurusan di bawah, lalu tekan 'Terapkan':")
    
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        # Filter 1: Posisi
        posisi_search = st.text_input(
            'Cari berdasarkan Nama Posisi (cth: admin, perawat):'
        )
    
    with col_filter2:
        # Filter 4: Jurusan
        jurusan_pilihan = st.multiselect(
            'Pilih Jurusan (bisa lebih dari satu):',
            options=list_jurusan_unik,
            default=[]
        )
    
    submitted = st.form_submit_button('Terapkan Filter')

# ===============================================
# --- 7. Logika Filtering Data ---
# ===============================================
df_hasil = df

if posisi_search:
    df_hasil = df_hasil[df_hasil['posisi'].str.contains(posisi_search, case=False, na=False)]
if provinsi_pilihan:
    df_hasil = df_hasil[df_hasil['perusahaan.nama_provinsi'].isin(provinsi_pilihan)]
if kota_pilihan:
    df_hasil = df_hasil[df_hasil['perusahaan.nama_kabupaten'].isin(kota_pilihan)]
if jurusan_pilihan:
    pola_regex_jurusan = '|'.join([re.escape(j) for j in jurusan_pilihan])
    df_hasil = df_hasil[df_hasil['program_studi'].str.contains(pola_regex_jurusan, case=False, na=False)]

# ===============================================
# --- 8. Tampilkan
