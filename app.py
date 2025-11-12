import streamlit as st
import pandas as pd
import re # Ini untuk filter jurusan yang canggih

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Filter Lowongan Magang",
    page_icon="🔎",
    layout="wide" # Layout "wide" agar tabelnya muat
)

# --- 2. Fungsi Load Data (Paling Penting) ---
# @st.cache_data: Ini adalah 'jurus sakti' Streamlit.
# Ini akan menyimpan data di cache, jadi 37.000 baris data itu
# hanya di-load SATU KALI, bukan setiap kali user memfilter.
@st.cache_data
def load_data():
    # Muat CSV Anda yang SUDAH BERSIH
    df = pd.read_csv("data_lowongan_BERSIH.csv")
    
    # --- Siapkan Filter Jurusan ---
    # Kolom 'program_studi' Anda isinya "Sastra Cina, Bahasa Mandarin"
    # Kita harus pisahkan, buat jadi unik, dan urutkan
    all_jurusan_set = set()
    for item_list in df['program_studi'].str.split(', '):
        # Cek jika item_list bukan list (misal: data kosong/NaN)
        if isinstance(item_list, list):
            all_jurusan_set.update(item_list) # update() untuk set
            
    list_jurusan_unik = sorted(list(all_jurusan_set))
    
    # --- Siapkan Filter Lokasi ---
    list_provinsi_unik = sorted(df['perusahaan.nama_provinsi'].dropna().unique())
    list_kota_unik = sorted(df['perusahaan.nama_kabupaten'].dropna().unique())
    
    return df, list_jurusan_unik, list_provinsi_unik, list_kota_unik

# --- 3. Muat Data (Tampilkan Spinner) ---
with st.spinner('Sedang memuat 37.000+ data lowongan...'):
    df, list_jurusan_unik, list_provinsi_unik, list_kota_unik = load_data()

# ===============================================
# --- 4. Tampilan Web / Interface (UI) ---
# ===============================================
st.title('🔎 Dashboard Filter Lowongan Magang KEMNAKER')
st.write(f"Total data lowongan di-crawl: {len(df)} baris")

# --- 5. Sidebar untuk Filter ---
st.sidebar.header('⚙️ Filter Pencarian')

# Filter 1: Posisi (Text Search)
posisi_search = st.sidebar.text_input(
    'Cari berdasarkan Nama Posisi (cth: admin, perawat):'
)

# Filter 2: Provinsi (Multi-select)
provinsi_pilihan = st.sidebar.multiselect(
    'Pilih Provinsi:',
    options=list_provinsi_unik,
    default=[] # Default-nya kosong
)

# Filter 3: Kota/Kabupaten (Multi-select)
kota_pilihan = st.sidebar.multiselect(
    'Pilih Kota/Kabupaten:',
    options=list_kota_unik,
    default=[]
)

# Filter 4: Jurusan (Multi-select)
jurusan_pilihan = st.sidebar.multiselect(
    'Pilih Jurusan (bisa lebih dari satu):',
    options=list_jurusan_unik,
    default=[]
)

# ===============================================
# --- 6. Logika Filtering Data ---
# ===============================================

# Mulai dengan data penuh, lalu kita "pangkas"
df_hasil = df

# Terapkan filter 1 (Posisi)
if posisi_search:
    df_hasil = df_hasil[df_hasil['posisi'].str.contains(posisi_search, case=False, na=False)]

# Terapkan filter 2 (Provinsi)
if provinsi_pilihan: # Jika list-nya tidak kosong
    df_hasil = df_hasil[df_hasil['perusahaan.nama_provinsi'].isin(provinsi_pilihan)]

# Terapkan filter 3 (Kota)
if kota_pilihan:
    df_hasil = df_hasil[df_hasil['perusahaan.nama_kabupaten'].isin(kota_pilihan)]

# Terapkan filter 4 (Jurusan) - Ini logikanya sedikit canggih
if jurusan_pilihan:
    # Buat pola regex: 'Akuntansi|Manajemen|Psikologi'
    # Ini akan mencari baris yang mengandung SALAH SATU dari jurusan yang dipilih
    pola_regex_jurusan = '|'.join([re.escape(j) for j in jurusan_pilihan])
    df_hasil = df_hasil[df_hasil['program_studi'].str.contains(pola_regex_jurusan, case=False, na=False)]


# ===============================================
# --- 7. Tampilkan Hasil ---
# ===============================================
st.header(f'Menampilkan {len(df_hasil)} Lowongan Terfilter')

# Pilih kolom mana saja yang mau ditampilkan
kolom_tampil = [
    'posisi', 
    'perusahaan.nama_perusahaan', 
    'program_studi', 
    'perusahaan.nama_kabupaten', 
    'perusahaan.nama_provinsi',
    'jumlah_kuota'
]

# Tampilkan dataframe
st.dataframe(df_hasil[kolom_tampil], use_container_width=True)

# (Opsional) Tampilkan data mentah jika ingin debug
with st.expander("Tampilkan Data Mentah Lengkap (Hasil Filter)"):
    st.dataframe(df_hasil)