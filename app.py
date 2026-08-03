import streamlit as st
import os
import time
from datetime import datetime
try:
    from streamlit_autorefresh import st_autorefresh
    from streamlit_extras.metric_cards import style_metric_cards
except ImportError:
    st.warning("Jalankan 'pip3 install streamlit-autorefresh streamlit-extras' di VPS untuk tampilan penuh.")

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IDX Stock Scanner - Serbabisa Dev",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- AUTO REFRESH (Setiap 30 detik) ---
try:
    st_autorefresh(interval=30000, key="datarefresh")
except:
    pass

# --- CSS CUSTOM UNTUK TAMPILAN PREMIUM ---
st.markdown("""
<style>
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    .block-container {padding-top: 1rem;}
    h1 {color: #FF4B4B; font-weight: 800;}
    .stTextarea textarea {
        font-family: 'Courier New', Courier, monospace;
        background-color: #0E1117;
        color: #00FF00 !important;
        border: 1px solid #30363D;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI HELPER ---
def get_log_content(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            lines = f.readlines()
            return "".join(lines[-100:]) # Ambil 100 baris terakhir
    return "Log belum tersedia."

def get_last_modified(filename):
    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        return datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
    return "N/A"

def check_bot_status(filename):
    if os.path.exists(filename):
        # Asumsi jika log diupdate dalam 20 menit terakhir, bot dianggap aktif (kecuali bandar yg jalan sekali)
        mtime = os.path.getmtime(filename)
        if (time.time() - mtime) < 1200:
            return "🟢 Active"
    return "⚪ Idle"

# ==========================================
# --- TAMPILAN UTAMA DASHBOARD ---
# ==========================================

# HEADER
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
    st.title("📈 IDX Stock Scanner Production")
    st.caption(f"Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
with col_head2:
    if st.button("🔄 Refresh Manual"):
        st.rerun()

st.divider()

# --- BAGIAN 1: STATUS METRICS (Paling Elegan) ---
st.subheader("🤖 Bot Status Summary")
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

status_auto = check_bot_status("auto.log")
status_engine = check_bot_status("engine.log")
# Bandar log specifik, kita cek jam 16:00
time_now = datetime.now().time()
is_bandar_time = time_now.hour >= 16 and time_now.hour < 17
status_bandar = "🟢 Ran" if os.path.exists("bandar.log") and get_last_modified("bandar.log") > "16:00:00" else ("🟡 Waiting" if is_bandar_time else "⚪ Scheduled")

with m_col1:
    st.metric(label="Auto Scanner (15m)", value=status_auto, help="Jalan setiap 15 menit 09-15 WIB")
with m_col2:
    st.metric(label="Master Engine", value=status_engine, help="Jalan jam 09:00 & 13:00 WIB")
with m_col3:
    st.metric(label="Bandar Accum", value=status_bandar, help="Jalan sekali jam 16:00 WIB")
with m_col4:
    total_logs = sum(1 for f in ["auto.log", "engine.log", "bandar.log"] if os.path.exists(f))
    st.metric(label="Active Logs", value=f"{total_logs} / 3")

try:
    style_metric_cards(background_color="#1A1D24", border_left_color="#FF4B4B", border_color="#30363D", box_shadow=True)
except:
    pass

st.divider()

# --- BAGIAN 2: LOG VIEWER (Rapi dengan Expander) ---
st.subheader("📝 Live Logs Monitor")

# Buat Tab untuk setiap log agar hemat tempat
tab1, tab2, tab3 = st.tabs(["⚡ Auto Scanner", "⚙️ Master Engine", "🕵️ Bandar Accum"])

with tab1:
    col_t1a, col_t1b = st.columns([3, 1])
    with col_t1a: st.caption(f"File: `auto.log`")
    with col_t1b: st.caption(f"Last Update: `{get_last_modified('auto.log')}`")
    st.text_area("Auto Output (Last 100 lines)", get_log_content("auto.log"), height=400, key="ta_auto")

with tab2:
    col_t2a, col_t2b = st.columns([3, 1])
    with col_t2a: st.caption(f"File: `engine.log`")
    with col_t2b: st.caption(f"Last Update: `{get_last_modified('engine.log')}`")
    st.text_area("Engine Output (Last 100 lines)", get_log_content("engine.log"), height=400, key="ta_engine")

with tab3:
    col_t3a, col_t3b = st.columns([3, 1])
    with col_t3a: st.caption(f"File: `bandar.log`")
    with col_t3b: st.caption(f"Last Update: `{get_last_modified('bandar.log')}`")
    st.text_area("Bandar Output (Last 100 lines)", get_log_content("bandar.log"), height=400, key="ta_bandar")

# FOOTER
st.divider()
st.caption("Developed by Serbabisa Dev | © 2026")
