from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

sns.set_theme(style="whitegrid")
BASE = Path(__file__).parent

st.set_page_config(page_title="Dashboard E-Commerce Olist", page_icon="🛒", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / "main_data.csv", parse_dates=["order_purchase_timestamp"])
    geo = pd.read_csv(BASE / "state_geo.csv")
    df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    return df, geo


df, geo = load_data()

# ---------------- Sidebar ----------------
st.sidebar.header("Filter")
min_d, max_d = df["order_purchase_timestamp"].min().date(), df["order_purchase_timestamp"].max().date()
date_range = st.sidebar.date_input("Rentang tanggal pembelian", (min_d, max_d), min_value=min_d, max_value=max_d)
states = sorted(df["customer_state"].unique())
sel_states = st.sidebar.multiselect("Negara bagian pelanggan", states, default=states)

if len(date_range) != 2:
    st.info("Pilih tanggal awal dan akhir pada sidebar.")
    st.stop()

mask = (df["order_purchase_timestamp"].dt.date.between(*date_range)) & (df["customer_state"].isin(sel_states))
f = df[mask]
if f.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# Tabel level order (satu baris per order)
orders = (f.groupby("order_id")
          .agg(order_month=("order_month", "first"), customer_unique_id=("customer_unique_id", "first"),
               customer_state=("customer_state", "first"), delivery_days=("delivery_days", "first"),
               is_late=("is_late", "first"), review_score=("review_score", "first"))
          .reset_index())

# ---------------- Header & KPI ----------------
st.title("🛒 Dashboard Analisis E-Commerce (Olist)")
st.caption("Periode data: Januari 2017 - Agustus 2018, hanya pesanan berstatus delivered.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Pesanan", f"{orders['order_id'].nunique():,}")
c2.metric("Total Revenue", f"R$ {f['price'].sum() / 1e6:,.2f} jt")
c3.metric("Rata-rata Review", f"{orders['review_score'].mean():.2f} / 5")
c4.metric("Pesanan Terlambat", f"{orders['is_late'].mean() * 100:.2f}%")

tab1, tab2, tab3 = st.tabs(["Pertanyaan 1: Tren & Kategori", "Pertanyaan 2: Keterlambatan", "Analisis Lanjutan"])

# ---------------- Tab 1 ----------------
with tab1:
    st.subheader("Tren pesanan dan revenue bulanan")
    monthly = (f.groupby("order_month").agg(orders=("order_id", "nunique"), revenue=("price", "sum")).reset_index())
    metric = st.radio("Metrik", ["Revenue (ribu BRL)", "Jumlah pesanan"], horizontal=True)
    col = "revenue" if metric.startswith("Revenue") else "orders"
    y = monthly[col] / 1e3 if col == "revenue" else monthly[col]

    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(monthly["order_month"], y, color="#1f77b4", lw=2.5, marker="o")
    pk = y.idxmax()
    ax.annotate(f"Puncak: {monthly.loc[pk, 'order_month']:%b %Y}", xy=(monthly.loc[pk, "order_month"], y[pk]),
                xytext=(-110, -5), textcoords="offset points", arrowprops=dict(arrowstyle="->", color="gray"))
    ax.set_ylabel(metric)
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
    sns.despine()
    st.pyplot(fig)

    st.subheader("Kategori produk dengan revenue terbesar")
    top_n = st.slider("Jumlah kategori ditampilkan", 5, 15, 10)
    cat = f.groupby("category")["price"].sum().sort_values(ascending=False)
    share = cat / cat.sum() * 100
    top = cat.head(top_n)
    colors = ["#1f77b4" if i < 5 else "#c7c7c7" for i in range(len(top))]

    fig, ax = plt.subplots(figsize=(11, 0.45 * len(top) + 1.5))
    ax.barh(top.index[::-1], top.values[::-1] / 1e6, color=colors[::-1])
    for i, (v, s) in enumerate(zip(top.values[::-1], share.head(top_n).values[::-1])):
        ax.text(v / 1e6 + 0.02, i, f"{v / 1e6:.2f} jt ({s:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(0, top.max() / 1e6 * 1.22)
    ax.set_xlabel("Revenue (juta BRL)")
    sns.despine()
    st.pyplot(fig)
    st.caption(f"5 kategori teratas (biru) menyumbang {share.head(5).sum():.1f}% dari revenue pada filter ini.")

# ---------------- Tab 2 ----------------
with tab2:
    st.subheader("Persentase pesanan terlambat per negara bagian")
    min_orders = st.slider("Minimal jumlah pesanan per negara bagian", 1, 500, 200)
    state = (orders.groupby("customer_state")
             .agg(orders=("order_id", "count"), late_pct=("is_late", lambda s: s.mean() * 100),
                  avg_delivery_days=("delivery_days", "mean"), avg_review=("review_score", "mean")))
    nat = orders["is_late"].mean() * 100
    s = state[state["orders"] >= min_orders].sort_values("late_pct", ascending=False).head(10).iloc[::-1]

    left, right = st.columns([3, 2])
    with left:
        if s.empty:
            st.info("Tidak ada negara bagian yang memenuhi batas minimal pesanan.")
        else:
            fig, ax = plt.subplots(figsize=(8, 4.8))
            ax.barh(s.index, s["late_pct"], color=["#d62728" if v > nat else "#c7c7c7" for v in s["late_pct"]])
            ax.axvline(nat, color="black", ls="--", lw=1)
            for i, v in enumerate(s["late_pct"]):
                ax.text(v + 0.2, i, f"{v:.1f}%", va="center", fontsize=9)
            ax.set_xlabel(f"% pesanan terlambat (garis putus-putus: rata-rata {nat:.1f}%)")
            sns.despine()
            st.pyplot(fig)
    with right:
        rv = orders.groupby("is_late")["review_score"].mean().rename({0: "Tepat waktu", 1: "Terlambat"})
        fig, ax = plt.subplots(figsize=(4.5, 4.8))
        ax.bar(rv.index, rv.values, color=["#1f77b4", "#d62728"][: len(rv)], width=0.55)
        for i, v in enumerate(rv.values):
            ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontweight="bold")
        ax.set_ylim(0, 5)
        ax.set_ylabel("Rata-rata review score")
        sns.despine()
        st.pyplot(fig)

    st.subheader("Lama pengiriman vs review (binning)")
    orders["delivery_bin"] = pd.cut(orders["delivery_days"], [0, 7, 14, 21, np.inf],
                                    labels=["<= 7 hari", "8-14 hari", "15-21 hari", "> 21 hari"])
    b = (orders.groupby("delivery_bin", observed=True)
         .agg(orders=("order_id", "count"), avg_review=("review_score", "mean"),
              late_pct=("is_late", lambda x: x.mean() * 100)).round(2))
    st.dataframe(b, width="stretch")

# ---------------- Tab 3 ----------------
with tab3:
    st.subheader("RFM Analysis (segmentasi pelanggan)")
    st.caption("Recency: hari sejak pembelian terakhir, Frequency: jumlah order, Monetary: total belanja (harga produk).")
    snapshot = f["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = (f.groupby("customer_unique_id")
           .agg(last_purchase=("order_purchase_timestamp", "max"), frequency=("order_id", "nunique"),
                monetary=("price", "sum")).reset_index())
    rfm["recency"] = (snapshot - rfm["last_purchase"]).dt.days
    rfm["r_score"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    conds = [(rfm["frequency"] >= 2) & (rfm["m_score"] >= 4), rfm["frequency"] >= 2,
             (rfm["r_score"] >= 4) & (rfm["m_score"] >= 4), rfm["r_score"] >= 4,
             (rfm["r_score"] <= 3) & (rfm["m_score"] >= 4)]
    names = ["Repeat - High Value", "Repeat Customer", "New - High Value", "New Customer", "At Risk - High Value"]
    rfm["segment"] = np.select(conds, names, default="Dormant")

    seg = rfm.groupby("segment").agg(customers=("customer_unique_id", "count"), avg_recency=("recency", "mean"),
                                     avg_frequency=("frequency", "mean"), avg_monetary=("monetary", "mean"),
                                     total_monetary=("monetary", "sum")).sort_values("customers", ascending=False)
    seg["customer_%"] = seg["customers"] / seg["customers"].sum() * 100
    seg["revenue_%"] = seg["total_monetary"] / seg["total_monetary"].sum() * 100

    pal = {"Repeat - High Value": "#08519c", "Repeat Customer": "#6baed6", "New - High Value": "#2ca02c",
           "New Customer": "#a1d99b", "At Risk - High Value": "#d62728", "Dormant": "#c7c7c7"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    order = seg.index.tolist()
    for ax, col, ttl in zip(axes, ["customer_%", "revenue_%"], ["Proporsi pelanggan (%)", "Kontribusi revenue (%)"]):
        ax.barh(order[::-1], seg[col][::-1], color=[pal[x] for x in order[::-1]])
        for i, v in enumerate(seg[col][::-1]):
            ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=9)
        ax.set_xlim(0, seg[col].max() * 1.2)
        ax.set_title(ttl, loc="left", fontweight="bold")
    axes[1].set_yticklabels([])
    sns.despine()
    plt.tight_layout()
    st.pyplot(fig)
    st.dataframe(seg.drop(columns="total_monetary").round(1), width="stretch")

    st.subheader("Geospatial: sebaran pesanan per negara bagian")
    gm = state.reset_index().merge(geo, on="customer_state", how="inner")
    gm["status"] = np.where(gm["late_pct"] > nat, "#d62728", "#1f77b4")
    gm["size"] = gm["orders"] * 20
    st.caption("Ukuran titik = jumlah pesanan, merah = persentase keterlambatan di atas rata-rata, biru = di bawah.")
    st.map(gm, latitude="lat", longitude="lng", size="size", color="status")
    st.dataframe(gm.drop(columns=["lat", "lng", "status", "size"]).sort_values("late_pct", ascending=False).round(2),
                 width="stretch")
