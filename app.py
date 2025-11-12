import streamlit as st
import pandas as pd
import re # Ini untuk filter jurusan yang canggih

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Filter Lowongan Magang",
    page_icon="🔎",
    layout="wide" # Layout "wide" agar tabelnya muat
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

# --- 3. Muat Data ---
with st.spinner('Memuat 37.000+ data lowongan...'):
    df, list_jurusan_unik, list_provinsi_unik, list_kota_unik = load_data()

# ===============================================
# --- 4. Tampilan Web / Interface (UI) ---
# ===============================================
st.title('🔎 Dashboard Filter Lowongan Magang KEMNAKER')
st.write(f"Total data lowongan di-crawl: {len(df)} baris")

# ===============================================
# --- 5. Sidebar untuk Filter ---
# ===============================================
st.sidebar.header('⚙️ Filter Pencarian')

# Filter 1: Posisi (Text Search)
posisi_search = st.sidebar.text_input(
    'Cari berdasarkan Nama Posisi (cth: admin, perawat):'
)

# --- FILTER DINAMIS ---
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
# --- AKHIR FILTER DINAMIS ---

# Filter 4: Jurusan (Multi-select)
jurusan_pilihan = st.sidebar.multiselect(
    'Pilih Jurusan (bisa lebih dari satu):',
    options=list_jurusan_unik,
    default=[]
)

# ===============================================
# --- 6. Logika Filtering Data ---
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
# --- 7. Tampilkan Hasil --- (MODIFIKASI)
# ===============================================

# --- FITUR KPI / METRIK (DISIMPAN) ---
st.header('Ringkasan Hasil Filter')
total_lowongan = len(df_hasil)
total_kuota = df_hasil['jumlah_kuota'].sum()
total_perusahaan = df_hasil['perusahaan.nama_perusahaan'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Lowongan Ditemukan", f"{total_lowongan:,}")
col2.metric("Total Kuota Magang", f"{total_kuota:,}")
col3.metric("Total Perusahaan Unik", f"{total_perusahaan:,}")

st.markdown("---") # Garis pemisah

# --- FITUR GRAFIK (DIEDIT) ---
st.header('Grafik Analisis')
if not df_hasil.empty:
    # --- Grafik Provinsi DIHAPUS ---
    
    # --- Grafik Jurusan DISIMPAN ---
    st.subheader("10 Jurusan Paling Dicari (dalam hasil filter)")
    jurusan_flat_list = [j for sublist in df_hasil['program_studi'].str.split(', ') if isinstance(sublist, list) for j in sublist]
    jurusan_count = pd.Series(jurusan_flat_list).value_counts().head(10)
    st.bar_chart(jurusan_count)
else:
    st.info("Tidak ada data terfilter untuk ditampilkan di grafik.")

st.markdown("---") # Garis pemisah

# --- FITUR TAMPILAN TABEL (DIKEMBALIKAN) ---
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

# Tampilkan dataframe (dari app.py versi 1)
# Ditambahkan hide_index=True agar kolom '0, 1, 2' hilang
st.dataframe(df_hasil[kolom_tampil], use_container_width=True, hide_index=True)

# (Opsional) Tampilkan data mentah jika ingin debug
with st.expander("Tampilkan Data Mentah Lengkap (Hasil Filter)"):
    st.dataframe(df_hasil, hide_index=True)
