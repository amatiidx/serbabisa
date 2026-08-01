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

def fetch_bandar_accumulation_data(ticker):
    try:
        clean_ticker = ticker.strip().upper().replace(".JK", "") + ".JK"
        stock = yf.Ticker(clean_ticker)
        df_hist = stock.history(period="2mo")

        if df_hist.empty or len(df_hist) < 20:
            return None

        # Hitung Rata-rata Volume 20 hari
        df_hist['Vol_MA20'] = df_hist['Volume'].rolling(20).mean()
        
        latest = df_hist.iloc[-1]
        prev = df_hist.iloc[-2]
        
        price = float(latest['Close'])
        prev_close = float(prev['Close'])
        volume = float(latest['Volume'])
        vol_ma20 = float(latest['Vol_MA20']) if not np.isnan(latest['Vol_MA20']) else volume
        
        # Likuiditas minimal 5 Miliar
        if price * volume < 5_000_000_000:
            return None

        # 1. Volum Spike (RVOL >= 1.4x dari Rata-rata 20 Hari)
        vol_ratio = round(volume / max(vol_ma20, 1), 2)
        
        # 2. Perubahan Harga Masih Terkontrol (-1% s/d +4%) -> Ciri Akumulasi Diam-diam
        price_change_pct = round(((price - prev_close) / prev_close) * 100, 2)
        
        # 3. Konsistensi Volume 3 Hari Terakhir (Apakah volume meningkat secara bertahap?)
        vol_3d_avg = df_hist['Volume'].iloc[-3:].mean()
        vol_growth = round(vol_3d_avg / max(vol_ma20, 1), 2)

        # Kriteria Akumulasi Bandar:
        # Volume hari ini melonjak, volume 3 hari stabil tinggi, tapi harga belum naik tinggi (masih disimpan)
        if vol_ratio >= 1.35 and vol_growth >= 1.25 and -1.0 <= price_change_pct <= 4.5:
            tp_swing = int(price * 1.05) # Target Swing Breakout +5%
            sl_level = int(price * 0.97) # Stop Loss -3%

            return {
                "ticker": clean_ticker.replace(".JK", ""),
                "price": int(price),
                "change_pct": price_change_pct,
                "vol_ratio": vol_ratio,
                "vol_growth": vol_growth,
                "tp": tp_swing,
                "sl": sl_level
            }
        return None
    except Exception:
        return None

def run_bandar_scan():
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_bandar_accumulation_data, t): t for t in BEI_TARGETS}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    if not results:
        print("Tidak ada indikasi akumulasi konsisten saat ini.")
        return

    df = pd.DataFrame(results).sort_values(by="vol_ratio", ascending=False)

    tg_msg = f"🕵️‍♂️ *BANDAR SILENT ACCUMULATION RADAR*\n"
    tg_msg += f"📅 _Waktu Scan: {now_str}_\n"
    tg_msg += f"🐋 _Terdeteksi Akumulasi Konsisten Sebelum Breakout:_\n\n"

    for _, row in df.head(5).iterrows():
        tg_msg += f"📌 *{row['ticker']}* 🔥 [SILENT ACCUMULATION]\n"
        tg_msg += f"• *Harga Last:* Rp {row['price']:,} ({row['change_pct']}%)\n"
        tg_msg += f"• *Spike Volum:* {row['vol_ratio']}x Normal (3D Avg: {row['vol_growth']}x)\n"
        tg_msg += f"• *Target Breakout:* Rp {row['tp']:,} (+5%)\n"
        tg_msg += f"• *Stop Loss:* Rp {row['sl']:,} (-3%)\n\n"

    tg_msg += "💡 _Bandar sedang mengumpulkan barang di area sideways. Siap-siap Breakout!_"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"}, timeout=15)

if __name__ == "__main__":
    run_bandar_scan()
