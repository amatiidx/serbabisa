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
