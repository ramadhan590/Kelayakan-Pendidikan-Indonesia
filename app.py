import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard Kelayakan Pendidikan Indonesia",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }


    /* Chart section headers */
    .chart-title {
        font-size: 14px; font-weight: 600; color: #1565C0;
        margin-bottom: 4px; padding-bottom: 6px;
        border-bottom: 1px solid #E3F2FD;
    }

    /* Dashboard tab title */
    .dash-title {
        font-size: 20px; font-weight: 700; color: #1565C0; margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─── DATA LOAD ───────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("kelayakan-pendidikan-indonesia.csv")
    df.columns = [c.replace('\ufeff', '').strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=['Provinsi'])
    df = df[df['Provinsi'].str.strip() != '']

    num_cols = [
        'Sekolah','Siswa','Mengulang','Putus Sekolah',
        'Kepala Sekolah dan Guru(<S1)','Kepala Sekolah dan Guru(≥ S1)',
        'Tenaga Kependidikan(SM)','Tenaga Kependidikan(>SM)',
        'Rombongan Belajar','Ruang kelas(baik)',
        'Ruang kelas(rusak ringan)','Ruang kelas(rusak sedang)','Ruang kelas(rusak berat)'
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',','').str.strip(), errors='coerce').fillna(0).astype(int)

    df['Total_Guru']   = df['Kepala Sekolah dan Guru(<S1)'] + df['Kepala Sekolah dan Guru(≥ S1)']
    df['Total_Kelas']  = (df['Ruang kelas(baik)'] + df['Ruang kelas(rusak ringan)'] +
                          df['Ruang kelas(rusak sedang)'] + df['Ruang kelas(rusak berat)'])
    df['% Guru ≥S1']   = (df['Kepala Sekolah dan Guru(≥ S1)'] / df['Total_Guru'].replace(0, np.nan) * 100).fillna(0).round(1)
    df['% Kelas Baik'] = (df['Ruang kelas(baik)'] / df['Total_Kelas'].replace(0, np.nan) * 100).fillna(0).round(1)
    df['% Putus Sekolah'] = (df['Putus Sekolah'] / df['Siswa'].replace(0, np.nan) * 100).fillna(0).round(3)
    df['Rasio Siswa/Sekolah'] = (df['Siswa'] / df['Sekolah'].replace(0, np.nan)).fillna(0).round(0).astype(int)

    def wilayah(p):
        p = str(p).lower()
        if any(x in p for x in ['jakarta','jawa','yogyakarta','banten']): return 'Jawa'
        if any(x in p for x in ['sumatera','aceh','riau','jambi','lampung','bengkulu','bangka']): return 'Sumatera'
        if 'kalimantan' in p: return 'Kalimantan'
        if any(x in p for x in ['sulawesi','gorontalo']): return 'Sulawesi'
        if 'papua' in p: return 'Papua'
        if 'maluku' in p: return 'Maluku'
        if 'bali' in p: return 'Bali'
        if 'nusa tenggara' in p: return 'Nusa Tenggara'
        return 'Lainnya'
    df['Wilayah'] = df['Provinsi'].apply(wilayah)
    return df

df_raw = load_data()

# ─── SIDEBAR ─────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center;padding:12px 0 16px;">
  <div style="font-size:24px;font-weight:800;color:#1565C0;">UNTAG</div>
  <div style="font-size:10px;letter-spacing:2px;color:#888;">SURABAYA</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("🔍 Filter Data")

all_wil  = sorted(df_raw['Wilayah'].unique())
sel_wil  = st.sidebar.multiselect("Wilayah", all_wil, default=all_wil)
avail_pv = sorted(df_raw[df_raw['Wilayah'].isin(sel_wil)]['Provinsi'].unique())
sel_pv   = st.sidebar.multiselect("Provinsi", avail_pv, default=avail_pv)
metric   = st.sidebar.selectbox("Metrik Grafik", [
    "Siswa", "Sekolah", "Putus Sekolah", "Mengulang",
    "% Guru ≥S1", "% Kelas Baik", "% Putus Sekolah", "Rasio Siswa/Sekolah"
])

# Apply filters
df = df_raw[df_raw['Wilayah'].isin(sel_wil) & df_raw['Provinsi'].isin(sel_pv)].copy()

# ─── TABS ────────────────────────────────────────────────────
tab_dash, tab_info = st.tabs(["📊 Dashboard", "ℹ️ Tentang Data"])



# ══════════════════════════════════════════════════════════════
# TAB DASHBOARD — layout persis 2 × 2 seperti referensi
# ══════════════════════════════════════════════════════════════
with tab_dash:
    if df.empty:
        st.warning("Tidak ada data yang sesuai filter.")
    else:
        st.markdown(f'<div class="dash-title">Dashboard Kelayakan Pendidikan Indonesia</div>', unsafe_allow_html=True)

        # ─── ROW 1 ────────────────────────────────────────────
        col_tbl, col_line = st.columns([1, 1])

        # ── TOP LEFT: Tabel data ──────────────────────────────
        with col_tbl:
            st.markdown('<div class="chart-title">📋 Tabel Ringkasan Data per Provinsi</div>', unsafe_allow_html=True)
            tbl_show = df[['Provinsi', metric]].copy().reset_index(drop=True)
            tbl_show.index += 1
            tbl_show.columns = ['Provinsi', metric]

            # Format angka besar
            if metric in ['Siswa','Sekolah','Putus Sekolah','Mengulang','Rasio Siswa/Sekolah']:
                tbl_show[metric] = tbl_show[metric].apply(lambda x: f"{int(x):,}")
            else:
                tbl_show[metric] = tbl_show[metric].apply(lambda x: f"{x:.2f}%")

            st.dataframe(tbl_show, use_container_width=True, height=380)

        # ── TOP RIGHT: Line chart ─────────────────────────────
        with col_line:
            st.markdown(f'<div class="chart-title">📈 {metric} per Provinsi</div>', unsafe_allow_html=True)

            df_line = df.sort_values(metric, ascending=False).copy()

            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=df_line['Provinsi'],
                y=df_line[metric],
                mode='lines+markers',
                name=metric,
                line=dict(color='#1565C0', width=2.5),
                marker=dict(color='#1565C0', size=6),
                fill='tozeroy',
                fillcolor='rgba(21,101,192,0.08)'
            ))
            fig_line.update_layout(
                margin=dict(l=10, r=10, t=10, b=80),
                height=380,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(tickangle=-45, showgrid=False, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor='#F0F0F0'),
                showlegend=True,
                legend=dict(x=0, y=1.08, orientation='h')
            )
            st.plotly_chart(fig_line, use_container_width=True)

        # ─── ROW 2 ────────────────────────────────────────────
        col_bar, col_pie = st.columns([1, 1])

        # ── BOTTOM LEFT: Bar chart (top 10 + Others) ─────────
        with col_bar:
            st.markdown(f'<div class="chart-title">📊 Total {metric} (Top 10 + Others)</div>', unsafe_allow_html=True)

            df_bar_sorted = df.sort_values(metric, ascending=False).copy()

            # For non-percentage columns, group "Others"
            if metric in ['Siswa','Sekolah','Putus Sekolah','Mengulang','Rasio Siswa/Sekolah']:
                top10 = df_bar_sorted.head(10).copy()
                others_val = df_bar_sorted.iloc[10:][metric].sum() if len(df_bar_sorted) > 10 else 0
                if others_val > 0:
                    others_row = pd.DataFrame({'Provinsi': ['Others'], metric: [others_val]})
                    bar_df = pd.concat([top10[['Provinsi', metric]], others_row], ignore_index=True)
                else:
                    bar_df = top10[['Provinsi', metric]]

                # Shorten province names (remove "Prov. " prefix)
                bar_df['Provinsi'] = bar_df['Provinsi'].str.replace(r'^Prov\.\s*', '', regex=True)
                bar_df['Provinsi'] = bar_df['Provinsi'].str.replace(r'^D\.K\.I\.\s*', 'DKI ', regex=True)
                bar_df['Provinsi'] = bar_df['Provinsi'].str.replace(r'^D\.I\.\s*', 'DI ', regex=True)

                # Trim long names
                bar_df['Provinsi'] = bar_df['Provinsi'].apply(lambda x: x[:12] + '...' if len(x) > 12 else x)

                # Color: last bar (Others) slightly lighter
                colors = ['#1565C0'] * (len(bar_df) - (1 if others_val > 0 else 0)) + (['#90A4AE'] if others_val > 0 else [])

                fig_bar = go.Figure(go.Bar(
                    x=bar_df['Provinsi'],
                    y=bar_df[metric],
                    marker_color=colors,
                    name=metric,
                ))
            else:
                # For percentage metrics: show all, no "Others"
                bar_df = df_bar_sorted[['Provinsi', metric]].copy()
                bar_df['Provinsi'] = bar_df['Provinsi'].str.replace(r'^Prov\.\s*', '', regex=True)
                bar_df['Provinsi'] = bar_df['Provinsi'].apply(lambda x: x[:12] + '...' if len(x) > 12 else x)

                fig_bar = go.Figure(go.Bar(
                    x=bar_df['Provinsi'],
                    y=bar_df[metric],
                    marker_color='#1565C0',
                    name=metric,
                ))

            fig_bar.update_layout(
                margin=dict(l=10, r=10, t=10, b=80),
                height=340,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(tickangle=-45, tickfont=dict(size=10), showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#F0F0F0'),
                showlegend=True,
                legend=dict(x=0, y=1.1, orientation='h')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── BOTTOM RIGHT: Pie chart ───────────────────────────
        with col_pie:
            st.markdown(f'<div class="chart-title">🥧 Distribusi {metric} per Wilayah</div>', unsafe_allow_html=True)

            if metric in ['Siswa','Sekolah','Putus Sekolah','Mengulang']:
                pie_df = df.groupby('Wilayah')[metric].sum().reset_index()
            else:
                pie_df = df.groupby('Wilayah')[metric].mean().reset_index()

            pie_df = pie_df.sort_values(metric, ascending=False)

            # Top 4 + Others (same as reference image)
            if len(pie_df) > 5:
                top4    = pie_df.head(4)
                oth_val = pie_df.iloc[4:][metric].sum()
                oth_row = pd.DataFrame({'Wilayah': ['Others'], metric: [oth_val]})
                pie_df  = pd.concat([top4, oth_row], ignore_index=True)

            fig_pie = go.Figure(go.Pie(
                labels=pie_df['Wilayah'],
                values=pie_df[metric],
                hole=0,
                textinfo='percent',
                textposition='inside',
                insidetextorientation='radial',
                marker=dict(colors=[
                    '#1565C0','#EF6C00','#7B1FA2','#2E7D32','#B0BEC5'
                ]),
                showlegend=True
            ))
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=340,
                paper_bgcolor='white',
                legend=dict(
                    x=0.75, y=0.5,
                    yanchor='middle',
                    font=dict(size=12)
                )
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB INFO
# ══════════════════════════════════════════════════════════════
with tab_info:
    st.header("Tentang Dashboard")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📌 Deskripsi")
        st.write("""
        Dashboard ini menampilkan data kelayakan pendidikan seluruh provinsi di Indonesia,
        mencakup jumlah sekolah, siswa, tenaga pendidik, kondisi ruang kelas,
        serta angka putus sekolah dan siswa mengulang.
        """)
        st.subheader("📐 Metrik Tersedia")
        st.markdown("""
        | Metrik | Keterangan |
        |---|---|
        | Siswa | Jumlah total siswa |
        | Sekolah | Jumlah total sekolah |
        | Putus Sekolah | Jumlah siswa putus sekolah |
        | Mengulang | Jumlah siswa mengulang |
        | % Guru ≥S1 | Persentase guru berkualifikasi sarjana |
        | % Kelas Baik | Persentase ruang kelas kondisi baik |
        | % Putus Sekolah | Angka putus sekolah (%) |
        | Rasio Siswa/Sekolah | Rata-rata siswa per sekolah |
        """)
    with c2:
        st.subheader("📦 Sumber Data")
        st.info("""
        **File**: `kelayakan-pendidikan-indonesia.csv`  
        **Records**: 39 provinsi  
        **Sumber**: Dapodik — Kemdikbudristek RI
        """)
        st.subheader("💡 Cara Pakai")
        st.markdown("""
        1. Isi identitas kelompok di sidebar → lihat **Halaman Cover** untuk preview sampul tugas
        2. Pilih metrik dari dropdown **"Metrik Grafik"** → semua chart update otomatis
        3. Filter wilayah / provinsi untuk perbandingan spesifik
        """)

st.markdown("---")
st.markdown("<p style='text-align:center;font-size:12px;color:#aaa;'>EAS Data Science for Communication 2026 · UNTAG Surabaya</p>", unsafe_allow_html=True)
