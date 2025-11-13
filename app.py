import streamlit as st
import pandas as pd
import re 
import ast 
import plotly.express as px # DIBUTUHKAN UNTUK TREEMAP

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Dashboard Magang KEMNAKER",
    page_icon="🔎",
    layout="wide"
)

# --- 2. Fungsi Load Data (Cache) ---
@st.cache_data
def load_data():
    df = pd.read_csv("data_lowongan_BERSIH.csv")
    
    # Siapkan Filter Lists
    all_jurusan_set = set()
    for item_list in df['jurusan_rapi'].str.split(', '):
        if isinstance(item_list, list):
            all_jurusan_set.update(item_list)
    list_jurusan_unik = sorted(list(all_jurusan_set))
    
    list_provinsi_unik = sorted(df['Provinsi Perusahaan'].dropna().unique())
    list_kota_unik = sorted(df['Kabupaten/Kota Perusahaan'].dropna().unique())
    
    return df, list_jurusan_unik, list_provinsi_unik, list_kota_unik

# Fungsi BANTUAN untuk membersihkan kolom 'jenjang'
def parse_jenjang(jenjang_str):
    try:
        return ast.literal_eval(jenjang_str)
    except (ValueError, SyntaxError):
        return []

# --- 3. Muat Data ---
with st.spinner('Memuat data lowongan...'):
    df, list_jurusan_unik, list_provinsi_unik, list_kota_unik = load_data()

# ===============================================
# --- 4. Tampilan Web / Interface (UI) ---
# ===============================================
st.title('🔎 Dashboard Analisis Lowongan Magang KEMNAKER')
st.write(f"Total data lowongan di-crawl: {len(df)} baris")

# --- 5. FORM FILTER UTAMA (SEMUA FILTER DIGABUNG) ---
st.markdown("---") 

with st.form(key='form_filter_utama'):
    st.subheader("Filter Lengkap")
    st.caption("Semua filter akan diterapkan setelah Anda menekan tombol 'Terapkan Semua Filter'.")
    
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
            'Cari berdasarkan Nama Posisi:'
        )
    with col_jurusan:
        jurusan_pilihan = st.multiselect(
            'Pilih Jurusan:',
            options=list_jurusan_unik,
            default=[]
        )
    
    submitted = st.form_submit_button('Terapkan Semua Filter')

# --- 5. Sidebar Pengaturan Baru ---
st.sidebar.header('⚙️ Pengaturan Aplikasi')
tampil_data_mentah = st.sidebar.checkbox('Tampilkan Data Mentah Lengkap', value=False)
if st.sidebar.button("Reset Semua Filter"):
    st.experimental_rerun()
st.sidebar.markdown("---")

# ===============================================
# --- 6. Logika Filtering Data ---
# ===============================================
df_hasil = df

if posisi_search:
    df_hasil = df_hasil[df_hasil['Posisi'].str.contains(posisi_search, case=False, na=False)]
if provinsi_pilihan:
    df_hasil = df_hasil[df_hasil['Provinsi Perusahaan'].isin(provinsi_pilihan)]
if kota_pilihan:
    df_hasil = df_hasil[df_hasil['Kabupaten/Kota Perusahaan'].isin(kota_pilihan)]
if jurusan_pilihan:
    pola_regex_jurusan = '|'.join([re.escape(j) for j in jurusan_pilihan])
    df_hasil = df_hasil[df_hasil['jurusan_rapi'].str.contains(pola_regex_jurusan, case=False, na=False)]

# ===============================================
# --- 7. Tampilkan Hasil ---
# ===============================================

# --- FITUR KPI / METRIK ---
st.header('Ringkasan Hasil Filter')
total_lowongan = len(df_hasil)
total_kuota = df_hasil['Kuota'].sum()
total_perusahaan = df_hasil['Nama Perusahaan'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Lowongan Ditemukan", f"{total_lowongan:,}")
col2.metric("Total Kuota Magang", f"{total_kuota:,}")
col3.metric("Total Perusahaan Unik", f"{total_perusahaan:,}")

st.markdown("---") 

# --- TAMPILAN TABEL ---
st.header(f'Menampilkan {len(df_hasil)} Lowongan Terfilter')

kolom_tampil = [
    'Posisi', 
    'Nama Perusahaan', 
    'jurusan_rapi', 
    'Kabupaten/Kota Perusahaan', 
    'Provinsi Perusahaan',
    'Kuota',
    'Pendaftar', 
    'Peluang Lolos'
]

st.dataframe(
    df_hasil[kolom_tampil], 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Peluang Lolos": st.column_config.NumberColumn(
            "Peluang Lolos",
            help="Peluang lolos berdasarkan (Kuota / Pendaftar) * 100%",
            format="%.1f%%"
        ),
        "Pendaftar": st.column_config.NumberColumn(
            "Total Pelamar",
        )
    }
)

# --- TAMPILKAN DATA MENTAH (TERGANTUNG SIDEBAR) ---
if tampil_data_mentah:
    st.subheader("Data Mentah Lengkap (Dirohkan dari Pengaturan)")
    st.dataframe(df_hasil, hide_index=True)

st.markdown("---") 

# --- FITUR GRAFIK (BAR CHART DAN TREEMAP) ---
st.header('Grafik Analisis')
if not df_hasil.empty:
    
    col_grafik1, col_grafik2 = st.columns(2)
    
    with col_grafik1:
        # --- GRAFIK LAMA (JURUSAN) ---
        st.subheader("10 Jurusan Paling Dicari")
        jurusan_flat_list = [j for sublist in df_hasil['jurusan_rapi'].str.split(', ') if isinstance(sublist, list) for j in sublist]
        jurusan_count = pd.Series(jurusan_flat_list).value_counts().head(10)
        st.bar_chart(jurusan_count)
        
    with col_grafik2:
        # --- GRAFIK BARU (TREEMAP) ---
        st.subheader("Sebaran Kuota Magang per Lokasi")
        
        # 1. Agregasi data untuk Treemap (Ini adalah area kode yang diperbaiki)
        df_treemap = df_hasil.groupby(
            ['Provinsi Perusahaan', 'Kabupaten/Kota Perusahaan']
        )['Kuota'].sum().reset_index() # <-- PASTIKAN KURUNG SIKU DAN KURUNG BIASA TERTUTUP DI SINI
        
        df_treemap.columns = ['Provinsi', 'Kota', 'Total Kuota']

        # 2. Buat Plotly Treemap
        fig = px.treemap( # <-- BUG SEBELUMNYA ADA DI SEKITAR SINI
            df_treemap, 
            path=['Provinsi', 'Kota'],
            values='Total Kuota',      
            title='Sebaran Kuota Magang (Kuota Total)',
            color_continuous_scale='RdBu'
        ) # <-- PASTIKAN KURUNG TUTUP HANYA ADA SATU DI SINI

        fig.update_traces(textinfo='label+percent entry')
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Tidak ada data terfilter untuk ditampilkan di grafik.")
