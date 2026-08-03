import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import re
import time
from datetime import datetime
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    pass

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Stockbit Pro - Scanner Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-Refresh Halaman Setiap 30 Detik
try:
    st_autorefresh(interval=30000, key="stockbit_refresh")
except:
    pass

# --- STYLING DARK MODE (STOCKBIT PALETTE) ---
st.markdown("""
<style>
    .stApp {
        background-color: #121418;
        color: #E1E3E6;
    }
    div[data-testid="stMetric"], .stMetric {
        background-color: #1A1D24;
        border: 1px solid #2A2E39;
        border-radius: 8px;
        padding: 12px;
    }
    .stDataFrame {
        background-color: #1A1D24;
        border-radius: 8px;
    }
    .stTextarea textarea {
        background-color: #0B0E11 !important;
        color: #00FF66 !important;
        font-family: 'Consolas', 'Courier New', monospace;
        border: 1px solid #2A2E39 !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- FUNGSI PARSING HASIL LOG SCANNER ---
def parse_scanner_output(filename):
    """Membaca file log dan mengekstrak entri / tabel sinyal saham"""
    if not os.path.exists(filename):
        return [], "File log belum tersedia."
    
    with open(filename, "r") as f:
        content = f.read()
    
    if not content.strip():
        return [], "Log masih kosong."

    # Cari pola ticker saham 4 huruf kapital (misal: INET, BUMI, ENRG, CDIA, SIDO, TLKM)
    tickers = list(set(re.findall(r'\b[A-Z]{4}\b', content)))
    
    # Filter kata umum yang bukan ticker saham
    ignore_words = {"AUTO", "MAIN", "WIB", "POST", "JSON", "DATA", "INFO", "WARN", "NONE", "NULL", "TRUE", "ECHO", "BASH", "CRON", "LIST", "VIEW", "CALL", "HTTP", "PATH", "FILE"}
    valid_tickers = [t for t in tickers if t not in ignore_words]
    
    return valid_tickers, content

# --- SIDEBAR WATCHLIST & CONTROL ---
with st.sidebar:
    st.markdown("## 📈 **STOCKBIT TERMINAL**")
    st.caption("IDX Realtime Scanner Dashboard")
    st.divider()

    # Ambil Ticker Hasil Scan Auto Scanner untuk Quick Choice
    auto_tickers, _ = parse_scanner_output("auto.log")
    engine_tickers, _ = parse_scanner_output("engine.log")
    bandar_tickers, _ = parse_scanner_output("bandar.log")
    
    all_scanned_tickers = list(set(auto_tickers + engine_tickers + bandar_tickers + ["SIDO", "TLKM", "INET", "BUMI", "ENRG", "CDIA"]))
    all_scanned_tickers.sort()

    selected_ticker = st.selectbox("📌 Pilih Ticker Saham Chart", all_scanned_tickers, index=0)

    st.divider()
    st.markdown("### 🤖 Bot Engine Status")
    
    def check_status(file_path):
        if os.path.exists(file_path):
            if (time.time() - os.path.getmtime(file_path)) < 1200:
                return "🟢 RUNNING"
        return "🟡 IDLE"

    st.caption(f"Auto Scanner: **{check_status('auto.log')}**")
    st.caption(f"Master Engine: **{check_status('engine.log')}**")
    st.caption(f"Bandar Scanner: **{check_status('bandar.log')}**")

# --- HEADER TERMINAL ---
col_h1, col_h2, col_h3, col_h4 = st.columns([2, 1, 1, 1])

with col_h1:
    st.title(f"📊 IDX:{selected_ticker}")
    st.caption(f"Realtime Scan Monitor • {datetime.now().strftime('%d %b %Y %H:%M:%S WIB')}")

with col_h2:
    st.metric(label="Scanner Engine", value="ACTIVE", delta="09:00 - 16:00")
with col_h3:
    st.metric(label="Telegram Alert", value="CONNECTED", delta="Online")
with col_h4:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

st.divider()

# --- MAIN SECTION: TABEL HASIL SCANNER MASING-MASING ---
st.subheader("🎯 Hasil Deteksi Scanner Saham")

tab1, tab2, tab3 = st.tabs([
    "⚡ Auto Scanner (15m)", 
    "⚙️ Master Precision Engine", 
    "🕵️ Bandar Accumulation Scanner"
])

# TAB 1: AUTO SCANNER
with tab1:
    tickers, raw_log = parse_scanner_output("auto.log")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 🎯 Ticker Terdeteksi")
        if tickers:
            df_auto = pd.DataFrame({"Ticker Saham": tickers, "Sinyal": "BUY / ACCUM", "Source": "Auto Scanner 15m"})
            st.dataframe(df_auto, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada signal saham terdeteksi di run terbaru.")
    with c2:
        st.markdown("#### 📝 Raw Executed Log")
        st.text_area("Log Auto Scanner", raw_log, height=200, key="log_auto_tab")

# TAB 2: MASTER PRECISION ENGINE
with tab2:
    tickers, raw_log = parse_scanner_output("engine.log")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 🎯 Ticker Terdeteksi")
        if tickers:
            df_engine = pd.DataFrame({"Ticker Saham": tickers, "Setup": "PRECISION SIGNAL", "Source": "Master Engine"})
            st.dataframe(df_engine, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada signal saham terdeteksi di run terbaru.")
    with c2:
        st.markdown("#### 📝 Raw Executed Log")
        st.text_area("Log Master Engine", raw_log, height=200, key="log_engine_tab")

# TAB 3: BANDAR ACCUMULATION SCANNER
with tab3:
    tickers, raw_log = parse_scanner_output("bandar.log")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("#### 🎯 Ticker Terdeteksi")
        if tickers:
            df_bandar = pd.DataFrame({"Ticker Saham": tickers, "Deteksi": "BIG MONEY ACCUM", "Source": "Bandarmologi"})
            st.dataframe(df_bandar, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada signal saham terdeteksi di run terbaru.")
    with c2:
        st.markdown("#### 📝 Raw Executed Log")
        st.text_area("Log Bandar Scanner", raw_log, height=200, key="log_bandar_tab")

st.divider()

# --- INTERACTIVE CHART TRADINGVIEW ---
st.subheader(f"📈 Chart Analisis Technical - {selected_ticker}")
tv_widget_code = f"""
<div class="tradingview-widget-container" style="height:480px;width:100%;">
  <div id="tradingview_chart" style="height:480px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "IDX:{selected_ticker}",
    "interval": "D",
    "timezone": "Asia/Jakarta",
    "theme": "dark",
    "style": "1",
    "locale": "id",
    "toolbar_bg": "#121418",
    "enable_publishing": false,
    "hide_top_toolbar": false,
    "save_image": false,
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""
components.html(tv_widget_code, height=490)
