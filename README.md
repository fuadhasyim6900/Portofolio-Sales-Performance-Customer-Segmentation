# Portofolio-Sales-Performance-Customer-Segmentation
Customer Segmentation &amp; Sales Insights Dashboard  Data analytics app for customer segmentation, sales insights, and performance monitoring using the Gottlieb-Cruickshank pharmaceutical sales dataset (Poland, 2018).  This dashboard enables interactive exploration of key sales metrics, clustering results, and actionable business insights.

# 📦 Analisis Penjualan Farmasi & Klasterisasi Pelanggan — Portofolio

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://portofoliofuad-salesdashboard-customersegmentation.streamlit.app/)

## 🏢 Profil Perusahaan
Perusahaan ini menjual obat melalui distributor (bukan ke konsumen langsung). Distributor membagikan data penjualan hingga tingkat ritel sehingga perusahaan dapat menganalisis penjualan, pelanggan, dan kinerja tim penjualan.

---

## 👨‍💻 Tentang Analis
**Fuad Hasyim — Data Analyst & Data Science Enthusiast**

Profesional di bidang **Analisis Sistem Informasi Geografis (GIS)** dengan latar belakang akademik **Geografi** dari Universitas Negeri Semarang.  
Berpengalaman dalam mengumpulkan, memproses, dan menganalisis data dari penelitian lapangan maupun sumber sekunder seperti BPS dan LSM.  

Minat kuat di **Data Science dan Analitik**, terampil dalam eksplorasi data, visualisasi, dan metode statistik menggunakan **Python**, **SQL**, dan tools visualisasi data.  
Berkomitmen untuk memanfaatkan mindset analitis dan keahlian teknis untuk mengubah data mentah menjadi wawasan bermakna.  
**Tujuan karier:** berkembang sebagai Data Scientist dan berkontribusi pada pengambilan keputusan berbasis data yang berdampak.

---

## 📊 Fakta Dataset
- **Jumlah data:** 251,449 baris  
- **Jumlah kolom:** 20  
- **Periode data:** 2017-01-01 → 2020-12-01  

---

## 🧾 Tentang Dataset
Dataset ini merupakan catatan lengkap penjualan dari **Gottlieb-Cruickshank**, mencakup transaksi di Polandia.  
Data mencakup informasi tentang pelanggan, produk, dan tim penjualan, dengan fokus pada industri farmasi.

### Deskripsi Kolom
| Kolom | Deskripsi |
|-------|------------|
| Distributor | Perusahaan distributor (selalu “Gottlieb-Cruickshank”) |
| Customer Name | Nama pelanggan atau entitas pembeli |
| City | Kota pelanggan di Polandia |
| Country | Negara transaksi (“Poland”) |
| Latitude / Longitude | Koordinat geografis kota |
| Channel | Kanal distribusi (“Hospital” atau “Pharmacy”) |
| Sub-channel | “Private”, “Retail”, atau “Institution” |
| Product Name | Nama produk farmasi yang dijual |
| Product Class | Kategori produk (misal: “Mood Stabilizers”, “Antibiotics”) |
| Quantity | Jumlah unit terjual |
| Price | Harga per unit |
| Sales | Total penjualan (Quantity × Price) |
| Month / Year | Tanggal transaksi |
| Name of Sales Rep | Sales representative yang menangani transaksi |
| Manager | Manajer yang mengawasi sales rep |
| Sales Team | Tim penjualan (misal: Delta, Bravo, Alfa) |

### Contoh Baris
**Baris 1**  
Pelanggan: Zieme, Doyle and Kunze  
Kota: Lublin  
Produk: Topipizole  
Kelas: Mood Stabilizers  
Qty: 4  
Harga: 368  
Penjualan: 1472  
SalesRep: Mary Gerrard  
Manager: Britanny Bold  
Tim: Delta  

**Baris 2**  
Pelanggan: Feest PLC  
Kota: Świecie  
Produk: Choriotrisin  
Kelas: Antibiotics  
Qty: 7  
Harga: 591  
Penjualan: 4137  
SalesRep: Jessica Smith  
Manager: Britanny Bold  
Tim: Delta  

---

## 🎯 Latar Belakang Proyek
Selain analisis penjualan, perusahaan farmasi ingin memahami profil pelanggan, mencakup:

- Segmen pelanggan dengan kontribusi pendapatan tinggi  
- Pelanggan yang sering bertransaksi namun bernilai rendah  
- Pelanggan satu kali dengan nilai tinggi  

### Kebutuhan Bisnis
Terdapat tiga level pengguna laporan dengan fokus berbeda:

| Pengguna | Fokus Analisis |
|-----------|----------------|
| **Executive Committee** | Gambaran penjualan (tren, kota, kanal, produk/kota teratas) |
| **Sales Manager** | Rincian penjualan (berdasarkan distributor, produk, top 5, kanal distribusi) |
| **Head of Sales** | Kinerja tim (berdasarkan produk/kelas, peringkat penjualan, filter periode) atau segmentasi pelanggan |

---

## 🚀 Menjalankan Aplikasi

### 🔹 Jalankan secara lokal
Pastikan Python sudah terinstall di perangkat Anda.

1. Clone repository ini  
   ```bash
   git clone https://github.com/fuadhasyim6900/Portofolio-Sales-Performance-Customer-Segmentation.git
   cd Portofolio-Sales-Performance-Customer-Segmentation
