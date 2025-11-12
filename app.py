import streamlit as st
import pandas as pd
import re # Untuk filter jurusan
import ast # Untuk membersihkan data 'jenjang'

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="DashboardLowongan Magang",
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

# --- Fungsi BANTUAN untuk membersihkan kolom 'jenjang' ---
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


# ===============================================
# --- 5. Sidebar untuk Filter (HANYA LOKASI) ---
# ===============================================
st.sidebar.header('⚙️ Filter Lokasi (Instan)')

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

# ===============================================
# --- 6. FORM FILTER UTAMA (DI ATAS TABEL) ---
# ===============================================
st.markdown("---") # Garis pemisah

# 'with st.form(...)' akan menampung filter dan tombol
with st.form(key='form_filter_utama'):
    st.write("Pilih filter Posisi/Jurusan di bawah, lalu tekan 'Terapkan':")
    
    # Kita pindahkan filter Posisi dan Jurusan ke sini
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
    
    # --- INI TOMBOL YANG ANDA MINTA ---
    # Saat tombol ini ditekan, nilai 'posisi_search' dan 'jurusan_pilihan'
    # akan dikirim untuk memfilter data.
    submitted = st.form_submit_button('Terapkan Filter')

# ===============================================
# --- 7. Logika Filtering Data ---
# ===============================================

# Logika filter ini sekarang menggabungkan nilai dari
# sidebar (instan) dan form (setelah ditekan)
df_hasil = df

# Filter 1 (dari form)
if posisi_search:
    df_hasil = df_hasil[df_hasil['posisi'].str.contains(posisi_search, case=False, na=False)]
# Filter 2 (dari sidebar)
if provinsi_pilihan:
    df_hasil = df_hasil[df_hasil['perusahaan.nama_provinsi'].isin(provinsi_pilihan)]
# Filter 3 (dari sidebar)
if kota_pilihan:
    df_hasil = df_hasil[df_hasil['perusahaan.nama_kabupaten'].isin(kota_pilihan)]
# Filter 4 (dari form)
if jurusan_pilihan:
    pola_regex_jurusan = '|'.join([re.escape(j) for j in jurusan_pilihan])
    df_hasil = df_hasil[df_hasil['program_studi'].str.contains(pola_regex_jurusan, case=False, na=False)]

# ===============================================
# --- 8. Tampilkan Hasil ---
# ===============================================

# --- FITUR KPI / METRIK ---
st.header('Ringkasan Hasil Filter')
total_lowongan = len(df_hasil)
total_kuota = df_hasil['jumlah_kuota'].sum()
total_perusahaan = df_hasil['perusahaan.nama_perusahaan'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Lowongan Ditemukan", f"{total_lowongan:,}")
col2.metric("Total Kuota Magang", f"{total_kuota:,}")
col3.metric("Total Perusahaan", f"{total_perusahaan:,}")

st.markdown("---") # Garis pemisah

# --- TAMPILAN TABEL ---
st.header(f'Menampilkan {len(df_hasil)} Lowongan')

kolom_tampil = [
    'posisi', 
    'perusahaan.nama_perusahaan', 
    'program_studi', 
    'perusahaan.nama_kabupaten', 
    'perusahaan.nama_provinsi',
    'jumlah_kuota'
]
st.dataframe(df_hasil[kolom_tampil], use_container_width=True, hide_index=True)


st.markdown("---") # Garis pemisah

# --- FITUR GRAFIK ---
st.header('Grafik Analisis')
if not df_hasil.empty:
    col_grafik1, col_grafik2 = st.columns(2)
    with col_grafik1:
        st.subheader("10 Jurusan Paling Dicari")
        jurusan_flat_list = [j for sublist in df_hasil['program_studi'].str.split(', ') if isinstance(sublist, list) for j in sublist]
        jurusan_count = pd.Series(jurusan_flat_list).value_counts().head(10)
        st.bar_chart(jurusan_count)
else:
    st.info("Tidak ada data terfilter untuk ditampilkan di grafik.")

