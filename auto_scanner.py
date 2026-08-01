import pandas as pd
import numpy as np
import yfinance as yf
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Konfigurasi Bot Telegram
TELEGRAM_TOKEN = "8784775406:AAFJRPUyDEbGHGm7tvkVq0epdLczjOyQn0E"
TELEGRAM_CHAT_ID = "347896274"

# Parameter Trading Plan
TOTAL_CAPITAL = 10_000_000
MAX_SPLIT = 3
ALLOCATION_PCT = 100.0 / MAX_SPLIT
TARGET_TP_PCT = 2.5
MAX_SL_PCT = 1.5

BEI_TARGETS = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "AMRT", "ANTM", "ADRO", "AKRA",
    "AMMN", "ARTO", "AUTO", "BBTN", "BRPT", "BUMI", "BUKA", "CPIN", "CUAN", "DOOH",
    "EMTK", "ENRG", "EXCL", "GOTO", "HRUM", "ICBP", "INDF", "INKP", "INET", "ISAT",
    "ITMG", "KLBF", "MDKA", "MEDC", "MYOR", "NCKL", "PGAS", "PGEO", "PTBA", "RAJA",
    "SIDO", "SMGR", "SRTG", "TBIG", "TPIA", "TOWR", "UNTR", "UNVR", "PANI", "CDIA"
]

def fetch_stock_data(ticker):
    try:
        clean_ticker = ticker.strip().upper().replace(".JK", "") + ".JK"
        stock = yf.Ticker(clean_ticker)
        df_hist = stock.history(period="2mo")

        if df_hist.empty or len(df_hist) < 20:
            return None

        latest = df_hist.iloc[-1]
        prev_close = float(df_hist['Close'].iloc[-2])
        price = float(latest['Close'])
        low_p, high_p = float(latest['Low']), float(latest['High'])
        volume = float(latest['Volume'])
        
        if price * volume < 3_000_000_000:
            return None

        price_change_pct = round(((price - prev_close) / prev_close) * 100, 2)
        df_hist['Vol_MA20'] = df_hist['Volume'].rolling(20).mean()
        vol_ma20 = float(df_hist['Vol_MA20'].iloc[-1]) if not np.isnan(df_hist['Vol_MA20'].iloc[-1]) else volume
        vol_spike = round(volume / max(vol_ma20, 1), 2)

        range_hl = max(high_p - low_p, 1)
        close_location_pct = round(((price - low_p) / range_hl) * 100, 1)

        btst_score = 0
        if 1.5 <= price_change_pct <= 7.0: btst_score += 35
        if vol_spike >= 1.2: btst_score += 35
        if close_location_pct >= 75: btst_score += 30

        return {
            "ticker": clean_ticker.replace(".JK", ""),
            "price": int(price),
            "ideal_entry_min": int(price * 0.995),
            "ideal_entry_max": int(price * 1.005),
            "btst_score": btst_score
        }
    except Exception:
        return None

def run_auto_scan():
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
    print(f"[{now_str}] Memulai Auto Scan via GitHub Actions...")
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_stock_data, t): t for t in BEI_TARGETS}
        for future in as_completed(futures):
            res = future.result()
            if res and res['btst_score'] >= 60:
                results.append(res)
                
    if not results:
        print("Tidak ada saham yang memenuhi kriteria.")
        return

    df = pd.DataFrame(results).sort_values(by="btst_score", ascending=False)
    max_buy_val = TOTAL_CAPITAL * (ALLOCATION_PCT / 100.0)
    
    tg_msg = f"🔥 *GITHUB AUTO SCANNER RESULT*\n"
    tg_msg += f"📅 _Waktu Exec: {now_str}_\n"
    tg_msg += f"💰 _Modal RDN: Rp {TOTAL_CAPITAL:,}_\n\n"
    
    for _, row in df.head(MAX_SPLIT).iterrows():
        buy_min, buy_max = row['ideal_entry_min'], row['ideal_entry_max']
        tp = int(buy_min * (1 + TARGET_TP_PCT/100))
        sl = int(buy_min * (1 - MAX_SL_PCT/100))
        min_lot = max(1, int((max_buy_val * 0.5) / (buy_min * 100)))
        max_lot = max(1, int(max_buy_val / (buy_min * 100)))
        
        badge = "🔥 [SUPER POTENTIAL]" if row['btst_score'] >= 80 else "⭐ [HIGH POTENTIAL]"
        tg_msg += f"📌 *{row['ticker']}* {badge}\n"
        tg_msg += f"• *Harga Beli:* Rp {buy_min:,} - Rp {buy_max:,}\n"
        tg_msg += f"• *Target TP:* Rp {tp:,} (+{TARGET_TP_PCT}%)\n"
        tg_msg += f"• *Stop Loss:* Rp {sl:,} (-{MAX_SL_PCT}%)\n"
        tg_msg += f"• *Lot Recomend:* {min_lot} - {max_lot} Lot\n\n"
        
    tg_msg += "⚠️ _Disiplin TP & SL. Management Risk First!_"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"}, timeout=15)
        if resp.status_code == 200:
            print("Pesan Telegram Berhasil Terkirim!")
        else:
            print(f"Gagal kirim: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_auto_scan()
