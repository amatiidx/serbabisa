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

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / max(loss, 1e-9)
    return round(100 - (100 / (1 + rs)), 2)

def fetch_oversold_data(ticker):
    try:
        clean_ticker = ticker.strip().upper().replace(".JK", "") + ".JK"
        stock = yf.Ticker(clean_ticker)
        df_hist = stock.history(period="3mo")

        if df_hist.empty or len(df_hist) < 20:
            return None

        # Hitung RSI 14
        df_hist['RSI'] = calculate_rsi(df_hist['Close'], 14)
        latest_rsi = float(df_hist['RSI'].iloc[-1])

        latest = df_hist.iloc[-1]
        prev_close = float(df_hist['Close'].iloc[-2])
        price = float(latest['Close'])
        low_p, high_p = float(latest['Low']), float(latest['High'])
        volume = float(latest['Volume'])

        if price * volume < 3_000_000_000:
            return None

        # Hitung Reversal Score
        # Kriteria: RSI <= 38 (Jenuh Jual) & Mulai ada pantulan/kenaikan (+0.5% s/d +5%)
        change_pct = round(((price - prev_close) / prev_close) * 100, 2)
        
        # Ekstrim Oversold
        if latest_rsi <= 38 and change_pct >= -0.5:
            # Hitung Support Area & Entry Target
            ideal_entry = price
            tp1 = int(price * 1.03) # Target TP Swing 3%
            tp2 = int(price * 1.05) # Target TP Swing 5%
            sl = int(price * 0.97)  # Stop Loss 3%

            return {
                "ticker": clean_ticker.replace(".JK", ""),
                "price": int(price),
                "rsi": latest_rsi,
                "change_pct": change_pct,
                "tp1": tp1,
                "tp2": tp2,
                "sl": sl
            }
        return None
    except Exception:
        return None

def run_oversold_scan():
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_oversold_data, t): t for t in BEI_TARGETS}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    if not results:
        print("Tidak ada saham jenuh jual (oversold) saat ini.")
        return

    # Urutkan dari RSI terkecil (paling jenuh jual)
    df = pd.DataFrame(results).sort_values(by="rsi", ascending=True)

    tg_msg = f"📉 *OVERSOLD & BULLISH REVERSAL RADAR*\n"
    tg_msg += f"📅 _Waktu Scan: {now_str}_\n"
    tg_msg += f"🎯 _Daftar Saham Jenuh Jual Potensi Rebound/Pembalikan Arah:_\n\n"

    for _, row in df.head(5).iterrows():
        status_badge = "🔥 [EXTREME OVERSOLD]" if row['rsi'] <= 30 else "⭐ [POTENTIAL REBOUND]"
        tg_msg += f"📌 *{row['ticker']}* {status_badge}\n"
        tg_msg += f"• *Harga Last:* Rp {row['price']:,} ({row['change_pct']}%)\n"
        tg_msg += f"• *Indikator RSI:* {row['rsi']} (Jenuh Jual <= 38)\n"
        tg_msg += f"• *Area Entry:* Rp {row['price']:,}\n"
        tg_msg += f"• *Target TP:* Rp {row['tp1']:,} (+3%) - Rp {row['tp2']:,} (+5%)\n"
        tg_msg += f"• *Stop Loss:* Rp {row['sl']:,} (-3%)\n\n"

    tg_msg += "💡 _Cocok untuk strategi Bottom Fishing / Swing Trade 2-5 Hari!_"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"}, timeout=15)

if __name__ == "__main__":
    run_oversold_scan()
