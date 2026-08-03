import streamlit as st
from data_manager import get_stored_stock_info, init_db

# Inisialisasi DB saat aplikasi terbuka
init_db()

st.set_page_config(
    page_title="Stockbit Engine Dashboard", page_icon="📈", layout="wide"
)
st.title("📈 Market Analysis & Scanner Dashboard")

# Input Ticker Saham
ticker = st.text_input(
    "Masukkan Kode Saham (Contoh: INET, BUMI, SIDO, TLKM):", "INET"
).upper()

if ticker:
  # Mengambil data harga (yfinance) & profil emiten (GoAPI) dari SQLite
  df_price, profile = get_stored_stock_info(ticker)

  # 1. Tampilkan Profil Emiten dari GoAPI
  if profile:
    st.subheader(f"🏢 {profile.get('name', ticker)} ({ticker})")
    col1, col2 = st.columns(2)
    with col1:
      st.info(f"**Sektor:** {profile.get('sector', '-')}")
    with col2:
      st.info(f"**Sub-Sektor:** {profile.get('sub_sector', '-')}")

  # 2. Tampilkan Grafik & Tabel Harga
  if not df_price.empty:
    st.markdown("### 📊 Pergerakan Harga Historis")
    st.line_chart(df_price.set_index("date")["close"])
    st.dataframe(df_price.tail(10), use_container_width=True)
  else:
    st.warning(
        f"Data untuk {ticker} belum ada di database. Jalankan scanner untuk"
        " memperbarui."
    )
