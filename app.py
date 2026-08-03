import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import time
from datetime import datetime
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    pass

# --- KONFIGURASI PENGATURAN STOCKBIT STYLE ---
st.set_page_config(
    page_title="Stockbit Pro Terminal - Serbabisa",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto Refresh 30 Detik
try:
    st_autorefresh(interval=30000, key="stockbit_refresh")
except:
    pass

# --- CSS STYLING (DARK MODE STOCKBIT COLOR PALETTE) ---
st.markdown("""
<style>
    /* Dark Theme Stockbit Background */
    .stApp {
        background-color: #121418;
        color: #E1E3E6;
    }
    
    /* Card Container Style */
    div[data-testid="stMetric"], .stMetric {
        background-color: #1A1D24;
        border: 1px solid #2A2E39;
        border-radius: 8px;
        padding: 12px;
    }
    
    /* Custom Green / Red Accent */
    .stock-up { color: #00B746; font-weight: bold; }
    .stock-down { color: #FF3B30; font-weight: bold; }
    
    /* Textarea Terminal Output */
    .stTextarea textarea {
        background-color: #0B0E11 !important;
        color: #00FF66 !important;
        font-family: 'Consolas', 'Courier New', monospace;
        border: 1px solid #2A2E39 !important;
        border-radius: 6px;
    }
    
    /* Hide Default Header Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR WATCHLIST & NAVIGATION ---
with st.sidebar:
    st.image("https://stockbit.com/favicon.ico", width=30)
    st.title("Watchlist IDX")
    
    # Quick Watchlist Stocks
    watchlist = ["INET", "BUMI", "ENRG", "CDIA", "TLKM", "SIDO"]
    selected_ticker = st.selectbox("📌 Pilih Saham Monitor", watchlist, index=0)
    
    st.divider()
    st.markdown("### 🤖 Bot Status Engine")
    
    def check_status(file_path):
        if os.path.exists(file_path):
            if (time.time() - os.path.getmtime(file_path)) < 1200:
                return "🟢 RUNNING"
        return "🟡 IDLE"

    st.caption(f"Auto Scanner: **{check_status('auto.log')}**")
    st.caption(f"Master Engine: **{check_status('engine.log')}**")
    st.caption(f"Bandar Scanner: **{check_status('bandar.log')}**")

# --- HEADER BAR METRICS ---
col_h1, col_h2, col_h3, col_h4 = st.columns([2, 1, 1, 1])

with col_h1:
    st.title(f"📊 IDX:{selected_ticker}")
    st.caption(f"Realtime Terminal View • {datetime.now().strftime('%d %b %Y %H:%M:%S WIB')}")

with col_h2:
    st.metric(label="Target Scanner", value="ACTIVE", delta="09:00 - 16:00")
with col_h3:
    st.metric(label="Telegram Alert", value="CONNECTED", delta="Online")
with col_h4:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.divider()

# --- TRADINGVIEW CHART INTEGRATION (STOCKBIT LOOK) ---
st.subheader("📈 Technical Chart (TradingView Interactive)")
tv_widget_code = f"""
<div class="tradingview-widget-container" style="height:450px;width:100%;">
  <div id="tradingview_chart" style="height:450px;width:100%;"></div>
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
components.html(tv_widget_code, height=460)

st.divider()

# --- SCANNER LOGS TERMINAL (STOCKBIT RUNNING TRADE / STREAM STYLE) ---
st.subheader("📡 Bot Scanner Logs & Signal Feed")

tab_auto, tab_engine, tab_bandar = st.tabs(["⚡ Auto Scanner (15m)", "⚙️ Master Engine", "🕵️ Bandar Accumulation"])

def load_log(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            lines = f.readlines()
            return "".join(lines[-100:])
    return "Belum ada log aktivitas."

with tab_auto:
    st.text_area("", load_log("auto.log"), height=300, key="log_auto")

with tab_engine:
    st.text_area("", load_log("engine.log"), height=300, key="log_engine")

with tab_bandar:
    st.text_area("", load_log("bandar.log"), height=300, key="log_bandar")
