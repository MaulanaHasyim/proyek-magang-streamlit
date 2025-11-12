import streamlit as st
import pandas as pd
import re # Ini untuk filter jurusan yang canggih

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Dashboard Lowongan Magang",
    page_icon="📊",
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

# --- 3. Muat Data ---
with st.spinner('Memuat 37.000+ data lowongan...'):
    df, list_jurusan_unik, list_provinsi_unik, list_kota_unik = load_data()

# ===============================================
# --- 4. Tampilan Web / Interface (UI) ---
# ===============================================
st.title('📊 Dashboard Analitik Lowongan Magang KEMNAKER')
st.write(f"Total data lowongan di-crawl: {len(df)} baris")

# ===============================================
# --- 5. Sidebar untuk Filter ---
# ===============================================
st.sidebar.header('⚙️ Filter Pencarian')

# Filter 1: Posisi (Text Search)
posisi_search = st.sidebar.text_input(
    'Cari berdasarkan Nama Posisi (cth: admin, perawat):'
)

# --- FITUR BARU: FILTER DINAMIS ---
# Filter 2: Provinsi (Multi-select)
provinsi_pilihan = st.sidebar.multiselect(
    'Pilih Provinsi:',
    options=list_provinsi_unik,
    default=[]
)

# Filter 3: Kota/Kabupaten (Multi-select DINAMIS)
if provinsi_pilihan:
    # Jika provinsi dipilih, filter daftar kota
    kota_tersedia = sorted(df[df['perusahaan.nama_provinsi'].isin(provinsi_pilihan)]['perusahaan.nama_kabupaten'].dropna().unique())
else:
    # Jika tidak, tampilkan semua kota (atau bisa juga kita biarkan kosong)
    kota_tersedia = list_kota_unik 

kota_pilihan = st.sidebar.multiselect(
    'Pilih Kota/Kabupaten:',
    options=kota_tersedia,
    default=[]
)
# --- AKHIR FITUR BARU ---

# Filter 4: Jurusan (Multi-select)
jurusan_pilihan = st.sidebar.multiselect(
    'Pilih Jurusan (bisa lebih dari satu):',
    options=list_jurusan_unik,
    default=[]
)

# ===============================================
# --- 6. Logika Filtering Data (SAMA SEPERTI LAMA) ---
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
# --- 7. Tampilkan Hasil --- (BAGIAN INI DI-UPGRADE TOTAL)
# ===============================================

# --- FITUR BARU: KPI / METRIK ---
st.header('Ringkasan Hasil Filter')
total_lowongan = len(df_hasil)
total_kuota = df_hasil['jumlah_kuota'].sum()
total_perusahaan = df_hasil['perusahaan.nama_perusahaan'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Lowongan Ditemukan", f"{total_lowongan:,}")
col2.metric("Total Kuota Magang", f"{total_kuota:,}")
col3.metric("Total Perusahaan Unik", f"{total_perusahaan:,}")

st.markdown("---") # Garis pemisah

# --- FITUR BARU: GRAFIK INTERAKTIF ---
st.header('Grafik Analisis')
if not df_hasil.empty:
    col_grafik1, col_grafik2 = st.columns(2)
    
    with col_grafik1:
        st.subheader("10 Provinsi Lowongan Terbanyak")
        prov_count = df_hasil['perusahaan.nama_provinsi'].value_counts().head(10)
        st.bar_chart(prov_count)
        
    with col_grafik2:
        st.subheader("10 Jurusan Paling Dicari")
        # Ini mengambil data "Akuntansi, Manajemen" dan memisahnya
        jurusan_flat_list = [j for sublist in df_hasil['program_studi'].str.split(', ') if isinstance(sublist, list) for j in sublist]
        jurusan_count = pd.Series(jurusan_flat_list).value_counts().head(10)
        st.bar_chart(jurusan_count)
else:
    st.info("Tidak ada data terfilter untuk ditampilkan di grafik.")

st.markdown("---") # Garis pemisah

# --- FITUR BARU: TAMPILAN KARTU (CARD) ---
st.header(f'Hasil Lowongan ({total_lowongan} ditemukan)')

# Batasi tampilan agar tidak crash (misal: hanya 100 hasil pertama)
HASIL_LIMIT = 100 
for index, row in df_hasil.head(HASIL_LIMIT).iterrows():
    # st.container(border=True) membuat kotak border yang rapi
    with st.container(border=True):
        st.subheader(row['posisi'])
        st.write(f"**🏢 Perusahaan:** {row['perusahaan.nama_perusahaan']}")
        st.write(f"**📍 Lokasi:** {row['perusahaan.nama_kabupaten']}, {row['perusahaan.nama_provinsi']}")
        st.write(f"**🎓 Jurusan:** {row['program_studi']}")
        
        # Buat kolom untuk kuota
        col_info1, col_info2 = st.columns([3, 1]) # Kolom pertama 3x lebih besar
        with col_info1:
             st.write(f"**🎓 Jenjang:** {row['jenjang']}")
        with col_info2:
            # st.info() memberi kotak biru
            st.info(f"**Kuota: {row['jumlah_kuota']}**")

    st.write("") # Memberi spasi antar kartu

if total_lowongan > HASIL_LIMIT:
    st.warning(f"Hanya menampilkan {HASIL_LIMIT} hasil pertama. Gunakan filter untuk menyempurnakan pencarian Anda.")

# (Opsional) Tampilkan data mentah jika ingin debug
with st.expander("Tampilkan Data Mentah Lengkap (Hasil Filter)"):
    st.dataframe(df_hasil, hide_index=True)
