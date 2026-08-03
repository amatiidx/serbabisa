import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime, timezone, timedelta
import io
import os
import mplfinance as mpf
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed

# Konfigurasi Bot / Channel Telegram
TELEGRAM_TOKEN = "8784775406:AAFJRPUyDEbGHGm7tvkVq0epdLczjOyQn0E"
TELEGRAM_CHAT_ID = "347896274"

COMMODITIES_MAP = {
    "GC=F": {"name": "Emas Global (Gold)", "icon": "🏆", "stocks": "ANTM, MDKA, PSAB, BRMS"},
    "CL=F": {"name": "Minyak Mentah (WTI)", "icon": "🛢️", "stocks": "MEDC, ENRG, PGAS, AKRA"},
    "HG=F": {"name": "Tembaga (Copper)", "icon": "🧱", "stocks": "AMMN, MDKA"},
    "MTF=F": {"name": "Batu Bara (Coal)", "icon": "⬛", "stocks": "ADRO, PTBA, ITMG, HRUM, BUMI"}
}

def get_all_bei_tickers():
    """ Mengambil seluruh daftar saham BEI dengan fallback mutakhir """
    try:
        url = "https://raw.githubusercontent.com/harga-saham/idx-stocks/main/data/idx_companies.csv"
        s = requests.get(url, timeout=10).content
        df_idx = pd.read_csv(io.StringIO(s.decode('utf-8')))
        
        # Deteksi otomatis nama kolom ticker yang tersedia
        col_name = None
        for col in ['Ticker', 'ticker', 'Kode', 'kode', 'Symbol', 'symbol']:
            if col in df_idx.columns:
                col_name = col
                break
                
        if col_name:
            tickers = df_idx[col_name].dropna().unique().tolist()
            clean_tickers = [str(t).strip().upper() for t in tickers if len(str(t).strip()) == 4]
            if clean_tickers:
                print(f"✅ Berhasil mengambil {len(clean_tickers)} saham dari BEI.")
                return clean_tickers
    except Exception as e:
        print(f"⚠️ Gagal mengambil daftar dinamis BEI ({e}). Menggunakan daftar cadangan.")
    
    # Fallback daftar saham aktif likuiditas tinggi jika server data eksternal mati
    return [
        "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "AMRT", "ANTM", "ADRO", "AKRA",
        "AMMN", "ARTO", "AUTO", "BBTN", "BRPT", "BUMI", "BUKA", "CPIN", "CUAN", "DOOH",
        "EMTK", "ENRG", "EXCL", "GOTO", "HRUM", "ICBP", "INDF", "INKP", "INET", "ISAT",
        "ITMG", "KLBF", "MDKA", "MEDC", "MYOR", "NCKL", "PGAS", "PGEO", "PTBA", "RAJA",
        "SIDO", "SMGR", "SRTG", "TBIG", "TPIA", "TOWR", "UNTR", "UNVR", "PANI", "CDIA",
        "BSDE", "CTRA", "CMRY", "MBMA", "ADMR", "BRMS", "NSSS", "MIKA", "ACES", "MAPI"
    ]

def check_market_index(ticker, name, flag):
    try:
        idx = yf.Ticker(ticker)
        df_idx = idx.history(period="3mo")
        if df_idx.empty or len(df_idx) < 20:
            return "UNKNOWN", f"{flag} *{name}:* Data Tidak Cukup", 0.0

        df_idx['MA20'] = df_idx['Close'].rolling(20).mean()
        latest = df_idx.iloc[-1]
        prev = df_idx.iloc[-2]

        close = float(latest['Close'])
        prev_close = float(prev['Close'])
        ma20 = float(latest['MA20'])

        change_pct = round(((close - prev_close) / prev_close) * 100, 2)
        status = "BULLISH" if close >= ma20 else "BEARISH"
        symbol = "🟢" if status == "BULLISH" else "🔴"
        sign = "+" if change_pct >= 0 else ""
        
        msg = f"{symbol} {flag} *{name}:* {close:,.2f} ({sign}{change_pct}%)"
        return status, msg, change_pct
    except Exception:
        return "UNKNOWN", f"{flag} *{name}:* Gagal Membaca Data", 0.0

def scan_global_commodities():
    comm_msgs, signals = [], []
    for ticker, info in COMMODITIES_MAP.items():
        try:
            comm = yf.Ticker(ticker)
            df_comm = comm.history(period="5d")
            if not df_comm.empty and len(df_comm) >= 2:
                latest = df_comm.iloc[-1]
                prev = df_comm.iloc[-2]
                price = float(latest['Close'])
                prev_price = float(prev['Close'])
                change_pct = round(((price - prev_price) / prev_price) * 100, 2)
                
                sign = "+" if change_pct >= 0 else ""
                icon_status = "🔥" if change_pct >= 1.0 else ("🔻" if change_pct <= -1.0 else "➖")
                comm_msgs.append(f"• {info['icon']} *{info['name']}:* ${price:,.2f} ({sign}{change_pct}%) {icon_status}")
                
                if change_pct >= 0.8:
                    signals.append(f"👉 *{info['name']}* MENGUAT ({sign}{change_pct}%)\n   _Pantau Saham:_ *{info['stocks']}*")
        except Exception:
            continue
    return comm_msgs, signals

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / max(loss, 1e-9)
    return round(100 - (100 / (1 + rs)), 2)

def generate_stock_chart(ticker, df_hist, tp1, sl):
    try:
        df = df_hist.tail(40).copy()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['RSI'] = calculate_rsi(df['Close'], 14)

        apdict = [
            mpf.make_addplot(df['MA20'], color='blue', width=1.2),
            mpf.make_addplot(df['MA50'], color='orange', width=1.2),
            mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI')
        ]

        filename = f"{ticker}_chart.png"
        h_lines = dict(hlines=[tp1, sl], colors=['g', 'r'], linestyle='--', linewidths=1)

        mpf.plot(
            df,
            type='candle',
            style='charles',
            title=f"\nChart Teknikal: {ticker}",
            ylabel='Harga (IDR)',
            volume=True,
            ylabel_lower='Vol',
            addplot=apdict,
            hlines=h_lines,
            savefig=filename,
            figscale=1.2
        )
        return filename
    except Exception as e:
        print(f"Gagal buat chart {ticker}: {e}")
        return None

def analyze_high_precision_stock(ticker, ihsg_status):
    try:
        clean_ticker = ticker.strip().upper().replace(".JK", "") + ".JK"
        stock = yf.Ticker(clean_ticker)
        df_hist = stock.history(period="3mo")

        if df_hist.empty or len(df_hist) < 50:
            return None

        df_hist['MA20'] = df_hist['Close'].rolling(20).mean()
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
        rsi = float(latest['RSI'])

        turnover = price * volume
        if turnover < 3_000_000_000:
            return None

        change_pct = round(((price - prev_close) / prev_close) * 100, 2)
        vol_ratio = round(volume / max(vol_ma20, 1), 2)
        is_uptrend = price >= ma20

        candle_range = max(high_p - low_p, 1)
        close_location = round(((price - low_p) / candle_range) * 100, 1)

        accuracy_score = 0
        reasons = []

        if is_uptrend:
            accuracy_score += 30
            reasons.append("Uptrend")

        if vol_ratio >= 1.5:
            accuracy_score += 30
            reasons.append(f"Vol Spike {vol_ratio}x")
        elif vol_ratio >= 1.2:
            accuracy_score += 20
            reasons.append(f"Vol {vol_ratio}x")

        if close_location >= 70:
            accuracy_score += 20
            reasons.append("Strong Close")

        if 45 <= rsi <= 65:
            accuracy_score += 20
            reasons.append(f"RSI {rsi}")

        min_score = 80 if ihsg_status == "BEARISH" else 75

        if accuracy_score >= min_score and 1.0 <= change_pct <= 7.0:
            tp1 = int(price * 1.025)
            tp2 = int(price * 1.050)
            sl = int(price * 0.985)

            raw_ticker = clean_ticker.replace(".JK", "")
            chart_file = generate_stock_chart(raw_ticker, df_hist, tp1, sl)

            return {
                "ticker": raw_ticker,
                "price": int(price),
                "change_pct": change_pct,
                "score": accuracy_score,
                "reasons": " | ".join(reasons),
                "tp1": tp1,
                "tp2": tp2,
                "sl": sl,
                "turnover": round(turnover / 1_000_000_000, 1),
                "chart_file": chart_file
            }
        return None
    except Exception:
        return None

def send_telegram_photo(photo_path, caption):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': photo}, timeout=20)
    except Exception as e:
        print(f"Gagal kirim foto Telegram: {e}")

def run_precision_scan():
    wib_tz = timezone(timedelta(hours=7))
    now_str = datetime.now(wib_tz).strftime("%d-%m-%Y %H:%M WIB")
    
    bei_targets = get_all_bei_tickers()
    
    _, nikkei_msg, _ = check_market_index("^N225", "NIKKEI 225", "🇯🇵")
    _, kospi_msg, _ = check_market_index("^KS11", "KOSPI", "🇰🇷")
    _, hsi_msg, _ = check_market_index("^HSI", "HANG SENG", "🇭🇰")
    ihsg_status, ihsg_msg, _ = check_market_index("^JKSE", "IHSG BEI", "🇮🇩")
    
    comm_msgs, comm_signals = scan_global_commodities()
    
    results = []
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(analyze_high_precision_stock, t, ihsg_status): t for t in bei_targets}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    tg_msg = f"🎯 *MASTER PRECISION & GLOBAL RADAR*\n"
    tg_msg += f"📅 _Waktu Scan: {now_str}_\n\n"
    tg_msg += f"🌍 *RADAR BURSA ASIA & BEI:*\n• {nikkei_msg}\n• {kospi_msg}\n• {hsi_msg}\n• {ihsg_msg}\n\n"

    if comm_msgs:
        tg_msg += f"🛢️ *HARGA KOMODITAS GLOBAL:*\n" + "\n".join(comm_msgs) + "\n\n"

    if comm_signals:
        tg_msg += f"💡 *SINYAL SEKTOR POTENSIAL:*\n" + "\n".join(comm_signals) + "\n\n"

    url_text = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url_text, json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"}, timeout=15)

    if results:
        df = pd.DataFrame(results).sort_values(by=["score", "turnover"], ascending=[False, False])
        for _, row in df.head(3).iterrows():
            caption = (
                f"💎 *CHART TEKNIKAL: {row['ticker']}* 🔥 [SCORE: {row['score']}%]\n"
                f"• *Harga Last:* Rp {row['price']:,} (+{row['change_pct']}%)\n"
                f"• *Turnover:* Rp {row['turnover']} Miliar\n"
                f"• *Konfirmasi:* _{row['reasons']}_\n"
                f"🎯 *TP1:* Rp {row['tp1']:,} (+2.5%) | *TP2:* Rp {row['tp2']:,} (+5%)\n"
                f"🛡️ *SL:* Rp {row['sl']:,} (-1.5%)"
            )
            if row['chart_file'] and os.path.exists(row['chart_file']):
                send_telegram_photo(row['chart_file'], caption)
                os.remove(row['chart_file'])

if __name__ == "__main__":
    run_precision_scan()
