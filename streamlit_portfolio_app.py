# ============================================================
# Streamlit Portfolio App — Pharmaceutical Sales Analysis & Customer Segmentation  with clustering evaluation (Silhouette, DBI, CHI)
# Author: Fuad Hasyim — Data Analyst & Data Science Enthusiast
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from io import BytesIO
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import plotly.express as px

# ---------- Page config ----------
st.set_page_config(page_title="Pharma Portfolio", layout="wide")
px.defaults.template = "plotly_dark"

# ---------- Metadata ----------
AUTHOR_NAME = "Fuad Hasyim"
AUTHOR_TITLE = "Data Analyst & Data Science Enthusiast"
PHOTO_URL = "https://raw.githubusercontent.com/fuadhasyim6900/Portofolio/refs/heads/main/Profile.jpeg"

COMPANY_PROFILE_EN = (
    "This company sells drugs through distributors (not directly to consumers). "
    "Distributors share sales data down to retail level so the company can analyze sales, customers, and teams."
)
COMPANY_PROFILE_ID = (
    "Perusahaan ini menjual obat melalui distributor (bukan ke konsumen langsung). "
    "Distributor membagikan data penjualan hingga tingkat ritel sehingga perusahaan dapat menganalisis penjualan, pelanggan, dan tim."
)

EXECUTIVE_SUMMARY_EN = (
    "Revenue peaked in 2018 and has declined since. Investigate causes and design a growth strategy. "
    "Sales are concentrated in a few markets and distributors; retain VIPs and re-engage low-value customers."
)
EXECUTIVE_SUMMARY_ID = (
    "Pendapatan mencapai puncak pada 2018 dan menurun sejak itu. Selidiki penyebab dan rancang strategi pertumbuhan. "
    "Penjualan terkonsentrasi pada beberapa pasar dan distributor; pertahankan pelanggan VIP dan tarik kembali pelanggan bernilai rendah."
)
# ---------- Language Selector ----------
lang = st.sidebar.selectbox("Language / Bahasa", ["English", "Indonesia"])
def T(en, id): return en if lang == "English" else id

# ---------- Utility functions ----------
@st.cache_data
def load_df():
    candidates = [
        Path(r"D:\PORTOFOLIO\data\data-pharmacy.csv"),
        Path.cwd() / "data" / "data-pharmacy.csv",
        Path("/mnt/data/data-pharmacy.csv")
    ]
    for p in candidates:
        if p.exists():
            try:
                df = pd.read_csv(p)
                return df, str(p)
            except Exception:
                pass
    return None, None

@st.cache_data
def basic_prep(df):
    df = df.copy()
    # trim column names
    df.columns = [c.strip() for c in df.columns]

    # standard rename
    rename_map = {}
    if 'Customer Name' in df.columns: rename_map['Customer Name'] = 'Customer'
    if 'Product Name' in df.columns: rename_map['Product Name'] = 'Product'
    if 'Name of Sales Rep' in df.columns: rename_map['Name of Sales Rep'] = 'SalesRep'
    if 'Sales Team' in df.columns: rename_map['Sales Team'] = 'SalesTeam'
    if 'Product Class' in df.columns: rename_map['Product Class'] = 'ProductClass'
    # harmonize sub-channel variants (we expect 'Sub-channel' in your data)
    if 'Sub-Channel' in df.columns: rename_map['Sub-Channel'] = 'Sub-channel'
    if 'SubChannel' in df.columns: rename_map['SubChannel'] = 'Sub-channel'
    if 'Sub_Channel' in df.columns: rename_map['Sub_Channel'] = 'Sub-channel'
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # numeric conversions
    for col in ['Quantity', 'Sales', 'Revenue', 'Price']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # sales_value priority: Sales -> Revenue -> 0
    if 'Sales' in df.columns and not df['Sales'].isna().all():
        df['sales_value'] = pd.to_numeric(df['Sales'], errors='coerce').fillna(0)
    elif 'Revenue' in df.columns and not df['Revenue'].isna().all():
        df['sales_value'] = pd.to_numeric(df['Revenue'], errors='coerce').fillna(0)
    else:
        df['sales_value'] = 0

    # valid quantity
    if 'Quantity' in df.columns:
        df = df[df['Quantity'].fillna(0) >= 0]

    # invoice_date from Year & Month if available
    if 'Year' in df.columns and 'Month' in df.columns:
        try:
            # try parsing month numeric first; if not numeric, keep original
            month_num = df['Month'].astype(str).str.extract(r'(\d{1,2})')[0]
            df['Month_num'] = np.where(month_num.notna(), month_num, df['Month'].astype(str))
            df['invoice_date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month_num'].astype(str) + '-01', errors='coerce')
            df.drop(columns=['Month_num'], inplace=True)
        except Exception:
            df['invoice_date'] = pd.NaT
    else:
        df['invoice_date'] = pd.NaT

    # ensure Customer is string
    if 'Customer' in df.columns:
        df['Customer'] = df['Customer'].astype(str)

    return df

@st.cache_data
def customer_aggregate(df):
    if 'Customer' not in df.columns:
        return pd.DataFrame(columns=['Customer','Frequency','Monetary'])
    tx = df.dropna(subset=['Customer']).copy()
    tx['Customer'] = tx['Customer'].astype(str)
    freq = tx.groupby('Customer').size().rename('Frequency')
    mon = tx.groupby('Customer')['sales_value'].sum().rename('Monetary')
    return pd.concat([freq, mon], axis=1).reset_index()

@st.cache_data
def kmeans_cluster(df_cust, k=3):
    df = df_cust.copy()
    if df.empty or not {'Frequency','Monetary'}.issubset(df.columns):
        return df, None, np.nan, np.nan, np.nan
    X = df[['Frequency','Monetary']].fillna(0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(Xs)
    df['cluster'] = labels
    sil = silhouette_score(Xs, labels) if len(np.unique(labels))>1 else np.nan
    dbi = davies_bouldin_score(Xs, labels) if len(np.unique(labels))>1 else np.nan
    chi = calinski_harabasz_score(Xs, labels) if len(np.unique(labels))>1 else np.nan
    return df, km, sil, dbi, chi

def to_xlsx_bytes(df):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='data')
    bio.seek(0)
    return bio

# mapping raw sub-channel to high-level categories (optional keywords)
def map_subchannel_category(raw):
    if pd.isna(raw): return 'Other'
    s = str(raw).lower()
    if any(k in s for k in ['retail','apotek','pharmacy','toko','retailer']):
        return 'Retail'
    if any(k in s for k in ['government','gov','pemda','puskesmas','kemenkes','public']):
        return 'Government'
    if any(k in s for k in ['hospital','clinic','rumah sakit','rs','institution','institutional','hospital/clinic']):
        return 'Institution'
    if any(k in s for k in ['private','corporate','swasta','company','wholesale']):
        return 'Private'
    # if exact known labels
    if s.strip() in ['retail','government','institution','private']:
        return s.strip().capitalize()
    return 'Other'

# ---------- Load data ----------
df_raw, path_used = load_df()
if df_raw is None:
    st.sidebar.warning(T("data-pharmacy.csv not found. Please upload manually.", "data-pharmacy.csv tidak ditemukan. Silakan upload secara manual."))
    uploaded = st.sidebar.file_uploader(T("Upload data-pharmacy.csv", "Unggah data-pharmacy.csv"), type=["csv","xlsx"])
    if uploaded is None:
        st.stop()
    try:
        df_raw = pd.read_csv(uploaded)
    except Exception:
        df_raw = pd.read_excel(uploaded)
    path_used = 'uploaded file'

df = basic_prep(df_raw)

# ensure the 'Sub-channel' column exists (your dataset shows 'Sub-channel')
if 'Sub-channel' not in df.columns:
    # try alternatives
    for alt in ['Sub Channel','SubChannel','Sub_Channel','Sub-channel']:
        if alt in df.columns:
            df.rename(columns={alt:'Sub-channel'}, inplace=True)
            break

# ---------- Global Filters (Year, Month, City) ----------
year_list = sorted(df['Year'].dropna().unique().tolist()) if 'Year' in df.columns else []
month_list = sorted(df['Month'].dropna().unique().tolist()) if 'Month' in df.columns else []
city_list = sorted(df['City'].dropna().unique().tolist()) if 'City' in df.columns else []

year_selected = st.sidebar.multiselect(T("Select Year(s)", "Pilih Tahun"), year_list, default=year_list)
month_selected = st.sidebar.multiselect(T("Select Month(s)", "Pilih Bulan"), month_list, default=month_list)
city_selected = st.sidebar.multiselect(T("Select City / Region", "Pilih Kota / Wilayah"), city_list, default=city_list)

# Apply filters
df_filtered = df.copy()
if year_list and year_selected:
    df_filtered = df_filtered[df_filtered['Year'].isin(year_selected)]
if month_list and month_selected:
    df_filtered = df_filtered[df_filtered['Month'].isin(month_selected)]
if city_list and city_selected:
    df_filtered = df_filtered[df_filtered['City'].isin(city_selected)]


# ---------- Sidebar (profile + nav) ----------
with st.sidebar:
    st.image(PHOTO_URL, width=120)
    st.markdown(f"### {AUTHOR_NAME}")
    st.markdown(AUTHOR_TITLE)
    st.markdown("---")
    st.markdown(T("**Project:** Pharmaceutical Sales Analysis", "**Proyek:** Analisis Penjualan Farmasi"))
    st.markdown(T(COMPANY_PROFILE_EN, COMPANY_PROFILE_ID))
    st.markdown("---")
    st.markdown(f"📁 {path_used}")
    st.markdown("---")
    page = st.radio(T("Navigation", "Navigasi"), [
        T("Introduction", "Pendahuluan"),
        T("Sales Overview", "Gambaran Penjualan"),
        T("Sales Manager", "Manajer Penjualan"),
        T("Head of Sales", "Kepala Penjualan"),
        T("Customer Segmentation", "Segmentasi Pelanggan"),
        T("Insights & Recommendations", "Wawasan & Rekomendasi")
    ])

# ---------- Introduction Page ----------
if page == T("Introduction", "Pendahuluan"):
    st.title(T("📦 Pharmaceutical Sales Analysis & Customer Segmentation — Portfolio", "📦 Analisis Penjualan Farmasi & klasterisasi Pelanggan — Portofolio"))

    # ---------------- Company Profile ----------------
    st.header(T("Company Profile", "Profil Perusahaan"))
    st.write(T(COMPANY_PROFILE_EN, COMPANY_PROFILE_ID))
    st.markdown("---")

    # ---------------- About the Analyst ----------------
    st.subheader(T("About the Analyst", "Tentang Analis"))
    st.write(f"{AUTHOR_NAME} — {AUTHOR_TITLE}")
    st.write(T(
        """
        - Professional in Geographic Information System (GIS) Analysis with an academic background in Geography from Universitas Negeri Semarang.
        - Experienced in collecting, processing, and analyzing data from both field research and secondary sources such as BPS, NGOs, etc.
        - Strong passion for Data Science and Analytics; skilled in data exploration, visualization, and statistical methods using Python, SQL, and data visualization tools.
        - Committed to leveraging analytical mindset and technical expertise to transform raw data into meaningful insights.
        - Career goal: grow as a Data Scientist and contribute to impactful, data-driven decision making.
        """,
        """
        - Profesional di bidang Analisis Sistem Informasi Geografis (GIS) dengan latar belakang akademik Geografi dari Universitas Negeri Semarang.
        - Berpengalaman dalam mengumpulkan, memproses, dan menganalisis data dari penelitian lapangan maupun sumber sekunder seperti BPS, LSM, dll.
        - Minat kuat di Data Science dan Analitik; terampil dalam eksplorasi data, visualisasi, dan metode statistik menggunakan Python, SQL, dan tools visualisasi data.
        - Berkomitmen untuk memanfaatkan mindset analitis dan keahlian teknis untuk mengubah data mentah menjadi wawasan bermakna.
        - Tujuan karier: berkembang sebagai Data Scientist dan berkontribusi pada pengambilan keputusan berbasis data yang berdampak.
        """
    ))
    st.markdown("---")

    # ---------------- Dataset Facts ----------------
    st.subheader(T("Dataset Facts", "Fakta Dataset"))
    st.write(f"{df.shape[0]:,} rows — {df.shape[1]} columns")
    if 'invoice_date' in df.columns and df['invoice_date'].notna().any():
        try:
            st.write(T(
                "Date range:", 
                "Rentang tanggal:"
            ), f"{df['invoice_date'].min().date()} → {df['invoice_date'].max().date()}")
        except Exception:
            pass
    st.markdown("---")

    # ---------------- About Dataset ----------------
    st.subheader(T("About Dataset", "Tentang Dataset"))
    st.write(T(
        "This dataset is a comprehensive sales record from Gottlieb-Cruickshank, detailing transactions in Poland during January 2018. "
        "It includes information on customers, products, and sales teams, focused on the pharmaceutical industry.",
        "Dataset ini merupakan catatan lengkap penjualan dari Gottlieb-Cruickshank, mencakup transaksi di Polandia pada Januari 2018. "
        "Data mencakup informasi tentang pelanggan, produk, dan tim penjualan, dengan fokus pada industri farmasi."
    ))

    st.write(T(
        """
        **Dataset Description / Columns:**
        - Distributor: Distributing company, always 'Gottlieb-Cruickshank'
        - Customer Name: Name of the customer or purchasing entity
        - City: Customer city in Poland
        - Country: Country of transaction, always 'Poland'
        - Latitude / Longitude: Coordinates of the city
        - Channel: Distribution channel ('Hospital' or 'Pharmacy')
        - Sub-channel: 'Private', 'Retail', or 'Institution'
        - Product Name: Name of the pharmaceutical product sold
        - Product Class: Product category (e.g., 'Mood Stabilizers', 'Antibiotics')
        - Quantity: Number of units sold
        - Price: Price per unit
        - Sales: Total sales amount (Quantity * Price)
        - Month / Year: Transaction date (January 2018)
        - Name of Sales Rep: Sales representative handling the transaction
        - Manager: Manager overseeing the sales representative
        - Sales Team: Sales team (e.g., Delta, Bravo, Alfa)
        
        **Example Rows:**
        1. Customer: Zieme, Doyle and Kunze | City: Lublin | Product: Topipizole | Class: Mood Stabilizers | Quantity: 4 | Price: 368 | Sales: 1472 | Rep: Mary Gerrard | Manager: Britanny Bold | Team: Delta
        2. Customer: Feest PLC | City: Świecie | Product: Choriotrisin | Class: Antibiotics | Quantity: 7 | Price: 591 | Sales: 4137 | Rep: Jessica Smith | Manager: Britanny Bold | Team: Delta
        """,
        """
        **Deskripsi Dataset / Kolom:**
        - Distributor: Perusahaan distributor, selalu 'Gottlieb-Cruickshank'
        - Customer Name: Nama pelanggan atau entitas pembeli
        - City: Kota pelanggan di Polandia
        - Country: Negara transaksi, selalu 'Polandia'
        - Latitude / Longitude: Koordinat kota
        - Channel: Kanal distribusi ('Hospital' atau 'Pharmacy')
        - Sub-channel: 'Private', 'Retail', atau 'Institution'
        - Product Name: Nama produk farmasi yang dijual
        - Product Class: Kategori produk (misal: 'Mood Stabilizers', 'Antibiotics')
        - Quantity: Jumlah unit terjual
        - Price: Harga per unit
        - Sales: Total penjualan (Quantity * Price)
        - Month / Year: Tanggal transaksi (Januari 2018)
        - Name of Sales Rep: Sales representative yang menangani transaksi
        - Manager: Manajer yang mengawasi sales rep
        - Sales Team: Tim penjualan (misal: Delta, Bravo, Alfa)
        
        **Contoh Baris:**
        1. Pelanggan: Zieme, Doyle and Kunze | Kota: Lublin | Produk: Topipizole | Kelas: Mood Stabilizers | Qty: 4 | Harga: 368 | Penjualan: 1472 | SalesRep: Mary Gerrard | Manager: Britanny Bold | Tim: Delta
        2. Pelanggan: Feest PLC | Kota: Świecie | Produk: Choriotrisin | Kelas: Antibiotics | Qty: 7 | Harga: 591 | Penjualan: 4137 | SalesRep: Jessica Smith | Manager: Britanny Bold | Tim: Delta
        """
    ))
    st.markdown("---")

    # ---------------- Project Background ----------------
    st.subheader(T("Project Background", "Latar Belakang Proyek"))
    st.write(T(
        """
        In addition to sales analysis, pharmaceutical companies want to understand customer profiles:
        - Customer segments with high revenue contribution
        - Frequent, low-value customers
        - One-time, high-value customers

        **Requirement:**
        There are three levels of report users with different focuses:
        1. Executive Committee → sales overview (trends, city, channel, top product/city)
        2. Sales Manager → sales details (by distributor, product, top 5, distribution channel)
        3. Head of Sales → team performance (by product/class, sales ranking, period filter) or customer segmentation
        """,
        """
        Selain analisis penjualan, perusahaan farmasi ingin memahami profil pelanggan:
        - Segmen pelanggan dengan kontribusi pendapatan tinggi
        - Pelanggan yang sering bertransaksi namun bernilai rendah
        - Pelanggan satu kali dengan nilai tinggi

        **Kebutuhan:**
        Terdapat tiga level pengguna laporan dengan fokus berbeda:
        1. Executive Committee → gambaran penjualan (tren, kota, kanal, produk/kota teratas)
        2. Sales Manager → rincian penjualan (berdasarkan distributor, produk, 5 teratas, kanal distribusi)
        3. Head of Sales → kinerja tim (berdasarkan produk/kelas, peringkat penjualan, filter periode) atau segmentasi pelanggan
        """
    ))
    st.markdown("---")

# ---------- Pages ----------
if page == T("Introduction", "Pendahuluan"):
    if 'invoice_date' in df.columns and df['invoice_date'].notna().any():
        try:
            st.write("-")
        except Exception:
            pass

elif page == T("Sales Overview", "Gambaran Penjualan"):
    st.header(T("Sales Overview", "Gambaran Penjualan"))
    st.caption(T(f"Filtered by Year(s): {year_selected} | Month(s): {month_selected}", f"Filter Tahun: {year_selected} | Bulan: {month_selected}"))

    # Yearly revenue
    if 'Year' in df_filtered.columns and df_filtered['Year'].notna().any():
        yearly = df_filtered.groupby('Year', as_index=False)['sales_value'].sum().sort_values('Year')
        st.subheader(T("Yearly Revenue Trend", "Tren Pendapatan Tahunan"))
        st.plotly_chart(px.line(yearly, x='Year', y='sales_value', markers=True, title=T("Revenue per Year", "Pendapatan per Tahun")), use_container_width=True)

    st.markdown("---")

    # Monthly revenue + KPIs
    col1, col2 = st.columns([2,1])
    with col1:
        if 'invoice_date' in df_filtered.columns and df_filtered['invoice_date'].notna().any():
            monthly = df_filtered.set_index('invoice_date').resample('M')['sales_value'].sum().reset_index()
            st.subheader(T("Monthly Revenue", "Pendapatan Bulanan"))
            st.plotly_chart(px.line(monthly, x='invoice_date', y='sales_value', title=T("Monthly Revenue Trend", "Tren Pendapatan Bulanan")), use_container_width=True)
    with col2:
        st.metric(T("Total Revenue", "Total Pendapatan"), f"${df_filtered['sales_value'].sum():,.0f}")
        st.metric(T("Transactions", "Transaksi"), f"{len(df_filtered):,}")
        st.metric(T("Units Sold", "Unit Terjual"), f"{int(df_filtered['Quantity'].sum()):,}" if 'Quantity' in df_filtered.columns else "-")

    st.markdown("---")

    # Revenue by Channel
    if 'Channel' in df_filtered.columns and df_filtered['Channel'].notna().any():
        ch = df_filtered.groupby('Channel', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False)
        st.subheader(T("Revenue by Channel", "Pendapatan per Kanal"))
        st.plotly_chart(px.bar(ch, x='Channel', y='sales_value', text_auto='.2s', title=T("Revenue by Channel", "Pendapatan per Kanal")), use_container_width=True)

    st.markdown("---")

    # Revenue by Sub-channel (donut pie, label value + percent)
    if 'Sub-channel' in df_filtered.columns and df_filtered['Sub-channel'].notna().any():
        st.subheader(T("Revenue by Sub-channel (category)", "Pendapatan per Sub-channel (kategori)"))
        # Map raw sub-channel values into high-level categories (Retail/Government/Institution/Private/Other)
        df_sc = df_filtered.copy()
        df_sc['SubChannel_Category'] = df_sc['Sub-channel'].apply(map_subchannel_category)
        sc_summary = df_sc.groupby('SubChannel_Category', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False)

        c1, c2 = st.columns([2,1])
        with c1:
            st.plotly_chart(px.bar(sc_summary, x='SubChannel_Category', y='sales_value', text_auto='.2s', title=T("Revenue by Sub-channel Category", "Pendapatan per Kategori Sub-channel")), use_container_width=True)
        with c2:
            # Donut pie with default numeric format in hover and percent+label outside
            pie = px.pie(sc_summary, names='SubChannel_Category', values='sales_value', hole=0.45, title=T("Sales by Sub-channel", "Penjualan per Sub-channel"))
            pie.update_traces(textposition='outside', textinfo='label+percent',
                              hovertemplate='%{label}: %{value:,.0f} (<b>%{percent}</b>)<extra></extra>')
            pie.update_layout(showlegend=True, legend_title_text=T("Sub-channel", "Sub-channel"))
            st.plotly_chart(pie, use_container_width=True)

        if st.checkbox(T("Show raw Sub-channel values and mapped category", "Tampilkan nilai Sub-channel mentah dan kategori pemetaan")):
            raw_map = df_filtered[['Sub-channel']].dropna().drop_duplicates().reset_index(drop=True)
            raw_map['Mapped Category'] = raw_map['Sub-channel'].apply(map_subchannel_category)
            raw_map.columns = [T('Raw Sub-channel', 'Sub-channel Mentah'), T('Mapped Category', 'Kategori Terpetakan')]
            st.dataframe(raw_map, use_container_width=True)

    st.markdown("---")

    # Revenue by City
    if 'City' in df_filtered.columns and df_filtered['City'].notna().any():
        city = df_filtered.groupby('City', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False).head(20)
        st.subheader(T("Revenue by City (Top 20)", "Pendapatan per Kota (20 Teratas)"))
        st.plotly_chart(px.bar(city, x='City', y='sales_value', text_auto='.2s', title=T("Top 20 Cities by Revenue", "20 Kota Teratas Berdasarkan Pendapatan")), use_container_width=True)

elif page == T("Sales Manager", "Manajer Penjualan"):
    st.header(T("Sales Manager View", "Tampilan Manajer Penjualan"))
    distributors = ['All']
    if 'Distributor' in df_filtered.columns:
        distributors += sorted(df_filtered['Distributor'].dropna().unique().tolist())
    dsel = st.selectbox(T("Select Distributor", "Pilih Distributor"), distributors)

    df_d = df_filtered if dsel == 'All' else df_filtered[df_filtered['Distributor'] == dsel]

    if 'Product' in df_d.columns and df_d['Product'].notna().any():
        top_prod = df_d.groupby('Product', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False).head(10)
        st.subheader(T("Top Products", "Produk Teratas"))
        st.plotly_chart(px.bar(top_prod, x='Product', y='sales_value', text_auto='.2s', title=T("Top Products by Revenue", "Produk Teratas berdasarkan Pendapatan")), use_container_width=True)
    else:
        st.info(T("No product data available.", "Data produk tidak tersedia."))

    st.markdown("---")

    if 'SalesRep' in df_d.columns and df_d['SalesRep'].notna().any():
        rep_perf = df_d.groupby('SalesRep', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False).head(15)
        st.subheader(T("Sales Representative Performance", "Kinerja Perwakilan Penjualan"))
        st.plotly_chart(px.bar(rep_perf, x='SalesRep', y='sales_value', text_auto='.2s', title=T("Top Sales Reps by Revenue", "Sales Rep Teratas berdasarkan Pendapatan")), use_container_width=True)
    else:
        st.info(T("No SalesRep data available.", "Data SalesRep tidak tersedia."))

    st.markdown("---")

    if 'Distributor' in df_filtered.columns:
        dist_summary = df_filtered.groupby('Distributor', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False).head(20)
        st.subheader(T("Distributor Contribution (Top 20)", "Kontribusi Distributor (20 Teratas)"))
        st.plotly_chart(px.bar(dist_summary, x='Distributor', y='sales_value', text_auto='.2s'), use_container_width=True)

elif page == T("Head of Sales", "Kepala Penjualan"):
    st.header(T("Head of Sales View", "Tampilan Kepala Penjualan"))
    st.caption(T(f"Filtered by Year(s): {year_selected} | Month(s): {month_selected}", f"Filter Tahun: {year_selected} | Bulan: {month_selected}"))

    total_sales = df_filtered['sales_value'].sum()
    total_teams = int(df_filtered['SalesTeam'].nunique()) if 'SalesTeam' in df_filtered.columns else 0
    total_reps = int(df_filtered['SalesRep'].nunique()) if 'SalesRep' in df_filtered.columns else 0
    c1, c2, c3 = st.columns(3)
    c1.metric(T("Total Revenue", "Total Pendapatan"), f"${total_sales:,.0f}")
    c2.metric(T("Sales Teams", "Tim Penjualan"), total_teams)
    c3.metric(T("Sales Representatives", "Perwakilan Penjualan"), total_reps)

    st.markdown("---")

    if 'SalesTeam' in df_filtered.columns and df_filtered['SalesTeam'].notna().any():
        team_perf = df_filtered.groupby('SalesTeam', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False)
        team_perf['% of Total'] = (team_perf['sales_value'] / total_sales * 100).round(2) if total_sales>0 else 0
        st.subheader(T("Revenue by Sales Team", "Pendapatan per Tim Penjualan"))
        st.plotly_chart(px.bar(team_perf, x='SalesTeam', y='sales_value', text_auto='.2s'), use_container_width=True)
        st.dataframe(team_perf, use_container_width=True)
    else:
        st.info(T("No SalesTeam data available.", "Data SalesTeam tidak tersedia."))

    st.markdown("---")

    if 'SalesRep' in df_filtered.columns and df_filtered['SalesRep'].notna().any():
        rep_perf = df_filtered.groupby('SalesRep', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False).head(15)
        st.subheader(T("Top Sales Representatives", "Perwakilan Penjualan Terbaik"))
        st.plotly_chart(px.bar(rep_perf, x='SalesRep', y='sales_value', text_auto='.2s'), use_container_width=True)
    else:
        st.info(T("No SalesRep data available.", "Data SalesRep tidak tersedia."))

    st.markdown("---")

    if 'Country' in df_filtered.columns and df_filtered['Country'].notna().any():
        country = df_filtered.groupby('Country', as_index=False)['sales_value'].sum().sort_values('sales_value', ascending=False)
        st.subheader(T("Revenue by Country", "Pendapatan per Negara"))
        try:
            st.plotly_chart(px.choropleth(country, locations='Country', locationmode='country names', color='sales_value', title=T("Sales by Country", "Penjualan per Negara")), use_container_width=True)
        except Exception:
            st.plotly_chart(px.bar(country, x='Country', y='sales_value', text_auto='.2s'), use_container_width=True)
    else:
        st.info(T("No Country data available.", "Data Country tidak tersedia."))

elif page == T("Customer Segmentation", "Segmentasi Pelanggan"):
    st.header(T("Customer Segmentation", "Segmentasi Pelanggan"))
    st.caption(T(f"Filtered by Year(s): {year_selected} | Month(s): {month_selected}", f"Filter Tahun: {year_selected} | Bulan: {month_selected}"))

    cust = customer_aggregate(df_filtered)
    if cust.empty:
        st.info(T("No customer-level data available to segment.", "Tidak ada data pelanggan untuk disegmentasi."))
    else:
        k = st.slider(T("Choose number of clusters (k)", "Pilih jumlah klaster (k)"), 2, 8, 3)
        clustered, km, sil, dbi, chi = kmeans_cluster(cust[['Customer','Frequency','Monetary']], k=k)

        c1, c2, c3 = st.columns(3)
        c1.metric("Silhouette", f"{sil:.3f}" if not pd.isna(sil) else "n/a")
        c2.metric("Davies-Bouldin", f"{dbi:.3f}" if not pd.isna(dbi) else "n/a")
        c3.metric("Calinski-Harabasz", f"{chi:,.1f}" if not pd.isna(chi) else "n/a")
        st.markdown("---")

        cluster_summary = clustered.groupby('cluster', as_index=False).agg(
            Customers=('Customer','count'),
            Avg_Monetary=('Monetary','mean'),
            Total_Revenue=('Monetary','sum')
        ).sort_values('cluster')
        total_rev = cluster_summary['Total_Revenue'].sum() if not cluster_summary.empty else 0
        cluster_summary['% of Total Revenue'] = (cluster_summary['Total_Revenue'] / total_rev * 100).round(2) if total_rev>0 else 0
        cluster_summary['Avg_Monetary'] = cluster_summary['Avg_Monetary'].round(2)
        st.subheader(T("Cluster Summary", "Ringkasan Klaster"))
        st.dataframe(cluster_summary.style.format({'Avg_Monetary':'{:,.2f}','Total_Revenue':'{:,.0f}','% of Total Revenue':'{:.2f}%'}), use_container_width=True)

        st.markdown("---")

        st.subheader(T("Customer Clusters Visualization", "Visualisasi Klaster Pelanggan"))
        scatter_fig = px.scatter(clustered, x='Frequency', y='Monetary', color=clustered['cluster'].astype(str), size='Monetary', hover_data=['Customer'], title=T("Customer Clusters", "Klaster Pelanggan"))
        st.plotly_chart(scatter_fig, use_container_width=True)

        st.markdown("---")
        st.subheader(T("Average Monetary by Cluster", "Rata-rata Nilai Penjualan per Klaster"))
        bar_fig = px.bar(
            cluster_summary, 
            x='cluster', 
            y='Avg_Monetary', 
            text_auto='.2s', 
            title=T("Average Monetary per Cluster", "Rata-rata Nilai Penjualan per Klaster"))
        st.plotly_chart(bar_fig, use_container_width=True)
        st.markdown("---")
        st.markdown(T(
            """
            **Cluster 2 (VIP / High Value Customers)**  
            - Smallest number of customers (99 customers)  
            - Total revenue is quite large ($3.2 billion)  
            - Highest average monetary per customer ($32.32 million)  
            👉 Characteristics: Few customers but very valuable because their average spending is higher than others.
            
            **Cluster 0 (Mass Customers, Mid Value)**  
            - Largest number of customers (452 customers)  
            - Largest revenue ($8.05 billion) due to high customer base  
            - Average monetary per customer is moderate ($17.86 million)  
            👉 Characteristics: Many customers with moderate contribution.
            
            **Cluster 1 (Low Value Customers)**  
            - Decent customer base (200 customers)  
            - Revenue is relatively small ($0.68 billion)  
            - Lowest average monetary ($3.24 million)  
            👉 Characteristics: Low-value customers, possibly disloyal or low-volume.
            """,
            """
            **Klaster 2 (Pelanggan VIP / Bernilai Tinggi)**  
            - Jumlah pelanggan paling sedikit (99 pelanggan)  
            - Total pendapatan cukup besar ($3,2 miliar)  
            - Rata-rata nilai penjualan per pelanggan tertinggi ($32,32 juta)  
            👉 Karakteristik: Sedikit pelanggan namun sangat bernilai karena rata-rata pembelian lebih tinggi.
            
            **Klaster 0 (Pelanggan Massal, Bernilai Menengah)**  
            - Jumlah pelanggan terbesar (452 pelanggan)  
            - Pendapatan terbesar ($8,05 miliar) karena basis pelanggan banyak  
            - Rata-rata nilai penjualan per pelanggan masih moderat ($17,86 juta)  
            👉 Karakteristik: Banyak pelanggan dengan kontribusi moderat.
            
            **Klaster 1 (Pelanggan Bernilai Rendah)**  
            - Basis pelanggan cukup (200 pelanggan)  
            - Pendapatan relatif kecil ($0,68 miliar)  
            - Rata-rata nilai penjualan terendah ($3,24 juta)  
            👉 Karakteristik: Pelanggan bernilai rendah, mungkin kurang loyal atau volume pembelian rendah.
            """))

        st.subheader(T("Revenue by Cluster over Time", "Pendapatan Tiap Klaster dari Waktu ke Waktu"))
        if {'Customer','invoice_date','sales_value'}.issubset(df_filtered.columns):
            labels_map = clustered[['Customer','cluster']].drop_duplicates()
            tx = df_filtered.merge(labels_map, on='Customer', how='left').dropna(subset=['invoice_date','cluster'])
            if not tx.empty:
                tx['YearMonth'] = tx['invoice_date'].dt.to_period('M').astype(str)
                rev_time = tx.groupby(['YearMonth','cluster'], as_index=False)['sales_value'].sum().sort_values(['YearMonth','cluster'])
                ts_fig = px.line(rev_time, x='YearMonth', y='sales_value', color=rev_time['cluster'].astype(str), markers=True, title=T("Revenue by Cluster per Month", "Pendapatan per Klaster per Bulan"))
                ts_fig.update_xaxes(type='category')
                st.plotly_chart(ts_fig, use_container_width=True)
            else:
                st.info(T("No transactions matched to clusters with valid invoice dates.", "Tidak ada transaksi yang terhubung ke klaster dengan tanggal faktur valid."))
        else:
            st.info(T("Invoice date or transaction data missing; cannot plot revenue-by-cluster time series.", "Data tanggal faktur atau transaksi tidak tersedia; tidak dapat membuat grafik waktu per klaster."))

        st.markdown("---")
        st.download_button(T("Download Clustered Data", "Unduh Data Klaster"), to_xlsx_bytes(clustered), file_name="clustered_customers.xlsx")

elif page == T("Insights & Recommendations", "Wawasan & Rekomendasi"):
    st.header(T("Insights & Recommendations", "Wawasan & Rekomendasi"))
    
    # Executive Summary
    st.subheader(T("Executive Summary", "Ringkasan Eksekutif"))
    st.write(T(EXECUTIVE_SUMMARY_EN, EXECUTIVE_SUMMARY_ID))
    st.markdown("---")
    
    # Customer Segmentation Insights
    st.subheader(T("Customer Segmentation – Insight", "Segmentasi Pelanggan – Wawasan"))
    st.markdown(T(
        """
        - **Cluster 0** → consistently contributes the largest revenue, with an upward trend after 2020. This indicates they are backbone customers.  
        - **Cluster 1** → contributes the smallest amount, tends to be flat and shows no significant growth. They are considered low-value customers.  
        - **Cluster 2** → despite having fewer customers, contributes significantly to revenue, even experiencing a sharp spike in mid-2019. It has high potential, but is also more volatile.
        """,
        """
        - **Klaster 0** → secara konsisten menyumbang pendapatan terbesar, dengan tren naik setelah 2020. Ini menunjukkan mereka adalah pelanggan tulang punggung.  
        - **Klaster 1** → menyumbang jumlah terkecil, cenderung datar dan tidak menunjukkan pertumbuhan signifikan. Mereka dianggap pelanggan bernilai rendah.  
        - **Klaster 2** → meskipun jumlah pelanggan lebih sedikit, menyumbang pendapatan secara signifikan, bahkan mengalami lonjakan tajam pada pertengahan 2019. Memiliki potensi tinggi, namun lebih volatil.
        """
    ))
    st.markdown("---")
    
    # Conclusions
    st.subheader(T("Conclusions", "Kesimpulan"))
    st.markdown(T(
        """
        📉 Revenue declining since 2018 → needs action.  
        🏥 Highly dependent on VIP customers → concentration risk.  
        👥 Cluster 0 & 2 dominate, Cluster 1 adds little value.
        """,
        """
        📉 Pendapatan menurun sejak 2018 → perlu tindakan.  
        🏥 Sangat tergantung pada pelanggan VIP → risiko konsentrasi.  
        👥 Klaster 0 & 2 mendominasi, Klaster 1 menyumbang sedikit nilai.
        """
    ))
    st.markdown("---")
    
    # Recommended Actions
    st.subheader(T("Recommended Actions", "Rekomendasi"))
    st.markdown(T(
        "- Retain VIP customers and re-engage low-value ones.\n- Diversify markets and products.\n- Strengthen sales team data monitoring.",
        "- Pertahankan pelanggan VIP dan tarik kembali pelanggan bernilai rendah.\n- Diversifikasi pasar dan produk.\n- Perkuat pemantauan data tim penjualan."
    ))


