from datetime import datetime
import pandas as pd
import concurrent.futures

# 1. Ambil Semua Ticker Saham Indonesia
def get_all_idx():
    try:
        url = "https://raw.githubusercontent.com/datasets/investing-idx/main/data/stock-list.csv"
        df = pd.read_csv(url)
        return [f"{code}.JK" for code in df['Code']]
    except Exception as e:
        # Fallback jika url gagal dibaca
        return ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "BUMI.JK", "ENRG.JK", "INET.JK", "SIDO.JK"]

# 2. Fungsi Scan Sederhana Per Ticker
def scan_single_stock(ticker):
    # Logika kriteria scan Anda (Contoh: Mengambil ticker bersih tanpa .JK)
    clean_ticker = ticker.replace(".JK", "")
    return clean_ticker

# 3. Jalankan Scan dan Ambil Top 50 Saham
def run_scanner():
    all_stocks = get_all_idx()
    
    # Multithreading agar scan cepat
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(scan_single_stock, all_stocks))
    
    # Ambil 50 saham pertama hasil scan
    top_50 = results[:50]
    return ", ".join(top_50)

# --- EKSEKUSI UTAMA ---
if __name__ == "__main__":
    ticker_list_str = run_scanner()
    
    # Format pesan yang siap dikirim/ditampilkan
    pesan_output = f"[{datetime.now().strftime('%d-%m-%Y %H:%M WIB')}] HASIL SCAN TOP 50: {ticker_list_str}\n"
    
    # Tulis pesan ke file auto.log agar langsung dibaca oleh Streamlit
    with open("auto.log", "w") as f:
        f.write(pesan_output)
        
    print("Scan Berhasil! Hasil telah ditulis ke auto.log")
