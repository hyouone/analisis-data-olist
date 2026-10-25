# Proyek Analisis Data: E-Commerce Public Dataset (Olist)

Analisis tren penjualan, kategori produk, dan keterlambatan pengiriman pada E-Commerce Public Dataset
(periode Januari 2017 - Agustus 2018), dilengkapi RFM analysis, geospatial analysis, dan clustering (binning).

- **Nama:** Khaylia Puspita Anjani
- **Email:** khaylianjani@gmail.com
- **ID Dicoding:** Khayp

## Struktur Direktori
```
submission
├───dashboard
| ├───main_data.csv
| ├───state_geo.csv
| └───dashboard.py
├───data
| └───*.csv  (9 tabel dataset asli)
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

## Menjalankan Notebook
Buka `notebook.ipynb` dengan Jupyter/Colab dan jalankan semua sel dari atas ke bawah (jalankan dari folder `submission`
agar folder `data/` terbaca). Sel terakhir membuat ulang `dashboard/main_data.csv` dan `dashboard/state_geo.csv`.

## Menjalankan Dashboard
Dari folder `submission`:
```
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di http://localhost:8501.
