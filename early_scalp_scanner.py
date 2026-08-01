import pandas as pd
import numpy as np
import yfinance as yf
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Konfigurasi Bot Telegram
TELEGRAM_TOKEN = "8784775406:AAFJRPUyDEbGHGm7tvkVq0epdLczjOyQn0E"
TELEGRAM_CHAT_ID = "347896274"

BEI_TARGETS = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "AMRT", "ANTM", "ADRO", "AKRA",
    "AMMN", "ARTO", "AUTO", "BBTN", "BRPT", "BUMI", "BUKA", "CPIN", "CUAN", "DOOH",
    "EMTK", "ENRG", "EXCL", "GOTO", "HRUM", "ICBP", "INDF", "INKP", "INET", "ISAT",
    "ITMG", "KLBF", "MDKA", "MEDC", "MYOR", "NCKL", "PGAS", "PGEO", "PTBA", "RAJA",
    "SIDO", "SMGR", "SRTG", "TBIG", "TPIA", "TOWR", "UNTR", "UNVR", "PANI", "CDIA",
    "BSDE", "CTRA", "CMRY", "MBMA", "ADMR", "BRMS", "NSSS", "MIKA", "ACES", "MAPI"
]

def fetch_opening_spike(ticker):
    try:
        clean_ticker = ticker.strip().upper().replace(".JK", "") + ".JK"
        stock = yf.Ticker(clean_ticker)
        
        # Ambil data intraday 1 menit/5 menit
        df_intra = stock.history(period="1d", interval="5m")
        df_daily = stock.history(period="5d")

        if df_intra.empty or len(df_daily) < 2:
            return None

        latest_price = float(df_intra['Close'].iloc[-1])
        prev_close = float(df_daily['Close'].iloc[-2])
        
        # Hitung Persentase Kenaikan Pagi Ini
        change_pct = round(((latest_price - prev_close) / prev_close) * 100, 2)
        
        # Total Turnover Berjalan (Pagi Ini)
        total_vol = df_intra['Volume'].sum()
        turnover = latest_price * total_vol
        
        # Deteksi Lonjakan Candle Awal
        opening_vol = df_intra['Volume'].iloc[:3].sum() # 15 Menit Pertama
        avg_5d_vol = df_daily['Volume'].mean() / 12     # Estimasi porsi 15 mnt harian
        vol_ratio = round(opening_vol / max(avg_5d_vol, 1), 2)

        # Filter Scalping Buka Pasar:
        # Kenaikan 2.0% - 6.5%, Turnover minimal 3 Miliar, Lonjakan Vol > 1.2x
        if 2.0 <= change_pct <= 6.5 and turnover >= 3_000_000_000 and vol_ratio >= 1.2:
            return {
                "ticker": clean_ticker.replace(".JK", ""),
                "price": int(latest_price),
                "change_pct": change_pct,
                "vol_ratio": vol_ratio,
                "turnover": int(turnover / 1_000_000_000)
            }
        return None
    except Exception:
        return None

def run_early_scan():
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_opening_spike, t): t for t in BEI_TARGETS}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    if not results:
        print("Tidak ada saham spike di pembukaan pasar.")
        return

    df = pd.DataFrame(results).sort_values(by="vol_ratio", ascending=False)
    
    tg_msg = f"🚨 *OPENING MARKET MOMENTUM SPIKE*\n"
    tg_msg += f"📅 _Waktu Deteksi: {now_str}_\n"
    tg_msg += f"⚡ _Radar Saham Ramai & Terindikasi Akumulasi Pagi!_\n\n"
    
    for _, row in df.head(5).iterrows():
        tg_msg += f"🔥 *{row['ticker']}*\n"
        tg_msg += f"• *Harga Last:* Rp {row['price']:,} (+{row['change_pct']}%)\n"
        tg_msg += f"• *Volume Spike:* {row['vol_ratio']}x Normal Opening\n"
        tg_msg += f"• *Turnover:* Rp {row['turnover']} Miliar\n"
        tg_msg += f"🎯 _Target Fast TP: +1.5% - +2.5% | Disiplin SL!_\n\n"
        
    tg_msg += "⚠️ _Hati-hati volatility tinggi di awal sesi. Quick execution!_"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"}, timeout=15)

if __name__ == "__main__":
    run_early_scan()
