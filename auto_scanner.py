from datetime import datetime
import pandas as pd
import yfinance as yf
import concurrent.futures

# 1. Ambil Seluruh Daftar Ticker IHSG
def get_all_idx_tickers():
    try:
        url = "https://raw.githubusercontent.com/datasets/investing-idx/main/data/stock-list.csv"
        df = pd.read_csv(url)
        return [f"{code}.JK" for code in df['Code']]
    except Exception:
        # Ticker fallback jika internet/github dataset gagal
        return ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "BUMI.JK", "ENRG.JK", "INET.JK", "SIDO.JK", "CDIA.JK", "ASII.JK", "GOTO.JK", "BRIS.JK", "AMRT.JK"]

# 2. Analisis Real-Time Saham (Cek Kenaikan Harga & Volume)
def scan_single_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="5d")
        
        if df.empty or len(df) < 2:
            return None
        
        # Ambil harga penutupan & volume 2 hari terakhir
        close_now = df['Close'].iloc[-1]
        close_prev = df['Close'].iloc[-2]
        vol_now = df['Volume'].iloc[-1]
        
        # Syarat Sinyal: Harga Naik (>0%) dan Ada Volume Transaksi Real
        change_pct = ((close_now - close_prev) / close_prev) * 100
        
        if change_pct > 0 and vol_now > 100000:
            clean_ticker = ticker.replace(".JK", "")
            return {
                "ticker": clean_ticker,
                "change": change_pct,
                "volume": vol_now
            }
    except Exception:
        return None
    return None

# 3. Eksekusi Multithreading & Ambil Top 50 Saham
def run_scanner():
    all_tickers = get_all_idx_tickers()
    valid_signals = []
    
    # Gunakan ThreadPoolExecutor agar scan cepat (1-2 menit)
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(scan_single_stock, all_tickers)
        for res in results:
            if res:
                valid_signals.append(res)
                
    # Urutkan berdasarkan Kenaikan Persentase Harga Terbesar
    sorted_signals = sorted(valid_signals, key=lambda x: x['change'], reverse=True)
    
    # Ambil Top 50 Ticker Saham
    top_50 = [s['ticker'] for s in sorted_signals[:50]]
    
    return top_50

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    top_tickers = run_scanner()
    
    if top_tickers:
        tickers_str = ", ".join(top_tickers)
        log_message = f"[{datetime.now().strftime('%d-%m-%Y %H:%M WIB')}] TOP 50 SIGNAL: {tickers_str}\n"
    else:
        log_message = f"[{datetime.now().strftime('%d-%m-%Y %H:%M WIB')}] TIDAK ADA SIGNAL TERDETEKSI\n"
        
    with open("auto.log", "w") as f:
        f.write(log_message)
        
    print("Scan Pasar Real-Time Selesai!")
