from datetime import datetime
import pandas as pd
import concurrent.futures

# 1. Ambil Semua Ticker Saham Indonesia
def get_all_idx():
    url = "https://raw.githubusercontent.com/datasets/investing-idx/main/data/stock-list.csv"
    df = pd.read_csv(url)
    return [f"{code}.JK" for code in df['Code']]

# 2. Filter Hanya Top 50 Saham Terbaik
def filter_top_50(scan_results):
    # Urutkan berdasarkan skor sinyal / volume terbanyak
    sorted_stocks = sorted(scan_results, key=lambda x: x.get('score', 0), reverse=True)
    return sorted_stocks[:50]
    
# Tulis hasil scan ke file log agar terbaca oleh Streamlit
with open("auto.log", "w") as f:
    f.write(f"[{datetime.now().strftime('%d-%m-%Y %H:%M WIB')}] HASIL SCAN: BBCA, BUMI, ENRG, INET, SIDO, TLKM, AMRT, BRIS\n")
# Tulis ulang pesan ke auto.log agar sama persis dengan Telegram
with open("auto.log", "w") as f:
    f.write(message)
