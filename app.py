import streamlit as st
import pandas as pd
import re # Untuk filter jurusan
import ast # Untuk membersihkan data 'jenjang'

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
    
    # --- Siapkan Filter List ---
    all_jurusan_set = set()
    for item_list in df['program_studi'].str.split(', '):
        if isinstance(item_list, list):
            all_jurusan_set.update(item_list)
    list_jurusan_unik = sorted(list(all_jurusan_set))
    
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
st.write(f"Total data lowongan di-crawl: {len(df)} baris")

# --- 5. Sidebar Pengaturan Baru ---
st.sidebar.header('⚙️ Pengaturan Aplikasi')

# Pengaturan 1: Tampilkan Data Mentah
tampil_data_mentah = st.sidebar.checkbox('Tampilkan Data Mentah Lengkap', value=False)

# Pengaturan 2: Tombol Reset
if st.sidebar.button("Reset Semua Filter"):
    # Ini akan memaksa aplikasi me-refresh ke kondisi awal
    st.experimental_rerun()
st.sidebar.markdown("---")


# ===============================================
# --- 6. FORM FILTER UTAMA (4 FILTERS DIGABUNG) ---
# ===============================================

with st.form(key='form_filter_utama'):
    # st.subheader("Filter Lengkap")
    
    # Baris 1: Lokasi
    col_provinsi, col_kota = st.columns(2)
    with col_provinsi:
        provinsi_pilihan = st.multiselect(
            'Pilih Provinsi:',
            options=list_provinsi_unik,
            default=[]
        )
    with col_kota:
        kota_pilihan = st.multiselect(
            'Pilih Kota/Kabupaten:',
            options=list_kota_unik,
            default=[]
        )
        
    # Baris 2: Posisi & Jurusan
    col_posisi, col_jurusan = st.columns(2)
    with col_posisi:
        posisi_search = st.text_input(
            'Cari berdasarkan Nama Posisi (tekan Enter):'
        )
    with col_jurusan:
        jurusan_pilihan = st.multiselect(
            'Pilih Jurusan (bisa lebih dari satu):',
            options=list_jurusan_unik,
            default=[]
        )
    
    # Ini adalah tombol yang akan MENGAKTIFKAN SEMUA FILTER
    submitted = st.form_submit_button('Terapkan Semua Filter')

# ===============================================
# --- 7. Logika Filtering Data ---
# ===============================================
df_hasil = df

# Filter 1 (Posisi)
if posisi_search:
    df_hasil = df_hasil[df_hasil['posisi'].str.contains(posisi_search, case=False, na=False)]
# Filter 2 (Provinsi)
if provinsi_pilihan:
    df_hasil = df_hasil[df_hasil['perusahaan.nama_provinsi'].isin(provinsi_pilihan)]
# Filter 3 (Kota)
if kota_pilihan:
    df_hasil = df_hasil[df_hasil['perusahaan.nama_kabupaten'].isin(kota_pilihan)]
# Filter 4 (Jurusan)
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
col3.metric("Total Perusahaan Unik", f"{total_perusahaan:,}")

st.markdown("---") 

# --- TAMPILAN TABEL (Dipindahkan ke atas grafik) ---
st.header(f'Menampilkan {len(df_hasil)} Lowongan Terfilter')

kolom_tampil = [
    'posisi', 
    'perusahaan.nama_perusahaan', 
    'program_studi', 
    'perusahaan.nama_kabupaten', 
    'perusahaan.nama_provinsi',
    'jumlah_kuota'
]
st.dataframe(df_hasil[kolom_tampil], use_container_width=True, hide_index=True)

# --- TAMPILKAN DATA MENTAH (TERGANTUNG SIDEBAR) ---
if tampil_data_mentah:
    st.subheader("Data Mentah Lengkap (Dirohkan dari Pengaturan)")
    st.dataframe(df_hasil, hide_index=True)

st.markdown("---") 

# --- FITUR GRAFIK (DI BAWAH) ---
st.header('Grafik Analisis')
if not df_hasil.empty:
    
    col_grafik1, col_grafik2 = st.columns(2)
    
    with col_grafik1:
        st.subheader("10 Jurusan Paling Dicari")
        jurusan_flat_list = [j for sublist in df_hasil['program_studi'].str.split(', ') if isinstance(sublist, list) for j in sublist]
        jurusan_count = pd.Series(jurusan_flat_list).value_counts().head(10)
        st.bar_chart(jurusan_count)
        
    with col_grafik2:
        st.subheader("Sebaran Kuota Magang per Lokasi")
        
        df_treemap = df_hasil.groupby(
            ['perusahaan.nama_provinsi', 'perusahaan.nama_kabupaten']
        )['jumlah_kuota'].sum().reset_index()
        
        df_treemap.columns = ['Provinsi', 'Kota', 'Total Kuota']

        fig = px.treemap(
            df_treemap, 
            path=['Provinsi', 'Kota'],
            values='Total Kuota',
            title='Sebaran Kuota Magang',
            color_continuous_scale='RdBu'
        )
        
        fig.update_traces(textinfo='label+percent entry')
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Tidak ada data terfilter untuk ditampilkan di grafik.")
