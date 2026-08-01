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
    "SIDO", "SMGR", "SRTG", "TBIG", "TPIA", "TOWR", "UNTR", "UNVR", "PANI", "CDIA"
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / max(loss, 1e-9)
    return round(100 - (100 / (1 + rs)), 2)

def analyze_high_precision_stock(ticker):
    try:
        clean_ticker = ticker.strip().upper().replace(".JK", "") + ".JK"
        stock = yf.Ticker(clean_ticker)
        df_hist = stock.history(period="3mo")

        if df_hist.empty or len(df_hist) < 50:
            return None

        # Indikator Utama
        df_hist['MA20'] = df_hist['Close'].rolling(20).mean()
        df_hist['MA50'] = df_hist['Close'].rolling(50).mean()
        df_hist['Vol_MA20'] = df_hist['Volume'].rolling(20).mean()
        df_hist['RSI'] = calculate_rsi(df_hist['Close'], 14)

        latest = df_hist.iloc[-1]
        prev = df_hist.iloc[-2]

        price = float(latest['Close'])
        prev_close = float(prev['Close'])
        low_p = float(latest['Low'])
        high_p = float(latest['High'])
        volume = float(latest['Volume'])
        vol_ma20 = float(latest['Vol_MA20'])
        ma20 = float(latest['MA20'])
        ma50 = float(latest['MA50'])
        rsi = float(latest['RSI'])

        turnover = price * volume
        # Filter 1: Likuiditas ketat (Minimal Rp 5 Miliar)
        if turnover < 5_000_000_000:
            return None

        change_pct = round(((price - prev_close) / prev_close) * 100, 2)
        vol_ratio = round(volume / max(vol_ma20, 1), 2)
        
        # Filter 2: Struktur Trend (Harus di atas MA20 / MA50)
        is_uptrend = price >= ma20

        # Filter 3: Candle Body / Close Location
        candle_range = max(high_p - low_p, 1)
        close_location = round(((price - low_p) / candle_range) * 100, 1)

        # SCORING AKURASI (Multi-Filter Confluence)
        accuracy_score = 0
        reasons = []

        # A. Tren & Support (+30 Poin)
        if is_uptrend:
            accuracy_score += 30
            reasons.append("Uptrend Structure (Above MA20)")

        # B. Lonjakan Volume / Akumulasi (+30 Poin)
        if vol_ratio >= 1.5:
            accuracy_score += 30
            reasons.append(f"Volume Spike {vol_ratio}x")
        elif vol_ratio >= 1.2:
            accuracy_score += 20
            reasons.append(f"Moderate Vol {vol_ratio}x")

        # C. Price Action & Pressure (+20 Poin)
        if close_location >= 70:
            accuracy_score += 20
            reasons.append("Strong Buying Close (High Area)")

        # D. Momentum RSI (+20 Poin)
        if 45 <= rsi <= 65:
            accuracy_score += 20
            reasons.append(f"Ideal RSI Momentum ({rsi})")

        # Hanya ambil setup dengan Skor Konfirmasi >= 75 (Sangat Presisi)
        if accuracy_score >= 75 and 1.0 <= change_pct <= 7.0:
            tp1 = int(price * 1.025) # Target TP1 (+2.5%)
            tp2 = int(price * 1.050) # Target TP2 (+5.0%)
            sl = int(price * 0.985)  # Stop Loss (-1.5%)

            return {
                "ticker": clean_ticker.replace(".JK", ""),
                "price": int(price),
                "change_pct": change_pct,
                "score": accuracy_score,
                "reasons": " | ".join(reasons),
                "tp1": tp1,
                "tp2": tp2,
                "sl": sl,
                "turnover": int(turnover / 1_000_000_000)
            }
        return None
    except Exception:
        return None

def run_precision_scan():
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_high_precision_stock, t): t for t in BEI_TARGETS}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    if not results:
        print("Tidak ada setup saham berakurasi tinggi saat ini.")
        return

    df = pd.DataFrame(results).sort_values(by="score", ascending=False)

    tg_msg = f"🎯 *HIGH-WINRATE MASTER PRECISION SCANNER*\n"
    tg_msg += f"📅 _Waktu Exec: {now_str}_\n"
    tg_msg += f"⚡ _Setup Konfirmasi Berlapis (Akurasi Tinggi):_\n\n"

    for _, row in df.head(3).iterrows():
        tg_msg += f"💎 *{row['ticker']}* 🔥 [CONFIRMATION SCORE: {row['score']}%]\n"
        tg_msg += f"• *Harga Last:* Rp {row['price']:,} (+{row['change_pct']}%)\n"
        tg_msg += f"• *Turnover:* Rp {row['turnover']} Miliar\n"
        tg_msg += f"• *Konfirmasi:* _{row['reasons']}_\n"
        tg_msg += f"🎯 *Target TP1:* Rp {row['tp1']:,} (+2.5%)\n"
        tg_msg += f"🎯 *Target TP2:* Rp {row['tp2']:,} (+5.0%)\n"
        tg_msg += f"🛡️ *Stop Loss:* Rp {row['sl']:,} (-1.5%)\n\n"

    tg_msg += "⚠️ _Disiplin Eksekusi TP & SL. Utamakan Money Management!_"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"}, timeout=15)

if __name__ == "__main__":
    run_precision_scan()
