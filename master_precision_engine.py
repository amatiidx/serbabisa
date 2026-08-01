import pandas as pd
import numpy as np
import yfinance as yf
import requests
import datetime
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# Konfigurasi Bot / Channel Telegram
TELEGRAM_TOKEN = "8784775406:AAFJRPUyDEbGHGm7tvkVq0epdLczjOyQn0E"
TELEGRAM_CHAT_ID = "347896274"  # Masukkan Username Channel (@channelanda) atau ID Group Anda

COMMODITIES_MAP = {
    "GC=F": {"name": "Emas Global (Gold)", "icon": "🏆", "stocks": "ANTM, MDKA, PSAB, BRMS"},
    "CL=F": {"name": "Minyak Mentah (WTI)", "icon": "🛢️", "stocks": "MEDC, ENRG, PGAS, AKRA"},
    "HG=F": {"name": "Tembaga (Copper)", "icon": "🧱", "stocks": "AMMN, MDKA"},
    "NCF=F": {"name": "Batu Bara (Coal)", "icon": "⬛", "stocks": "ADRO, PTBA, ITMG, HRUM, BUMI"}
}

def get_all_bei_tickers():
    """ Mengambil seluruh daftar saham terdaftar di BEI secara dinamis """
    try:
        url = "https://raw.githubusercontent.com/datasets/line-of-business/master/data/idx_companies.csv"
        s = requests.get(url, timeout=10).content
        df_idx = pd.read_csv(io.StringIO(s.decode('utf-8')))
        tickers = df_idx['Ticker'].dropna().unique().tolist()
        clean_tickers = [t.strip().upper() for t in tickers if len(t.strip()) == 4]
        if clean_tickers:
            print(f"✅ Berhasil mengambil {len(clean_tickers)} saham dari BEI.")
            return clean_tickers
    except Exception as e:
        print(f"⚠️ Gagal mengambil daftar dinamis BEI ({e}). Menggunakan daftar cadangan.")
    
    # Fallback jika terjadi kendala pada server data
    return [
        "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "AMRT", "ANTM", "ADRO", "AKRA",
        "AMMN", "ARTO", "AUTO", "BBTN", "BRPT", "BUMI", "BUKA", "CPIN", "CUAN", "DOOH",
        "EMTK", "ENRG", "EXCL", "GOTO", "HRUM", "ICBP", "INDF", "INKP", "INET", "ISAT",
        "ITMG", "KLBF", "MDKA", "MEDC", "MYOR", "NCKL", "PGAS", "PGEO", "PTBA", "RAJA",
        "SIDO", "SMGR", "SRTG", "TBIG", "TPIA", "TOWR", "UNTR", "UNVR", "PANI", "CDIA",
        "BSDE", "CTRA", "CMRY", "MBMA", "ADMR", "BRMS", "NSSS", "MIKA", "ACES", "MAPI"
    ]

def check_market_index(ticker, name, flag):
    """ Memeriksa tren Indeks Pasar Asia & BEI """
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
    """ Memeriksa pergerakan komoditas global & memberikan rekomendasi saham BEI """
    comm_msgs = []
    signals = []
    
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
        # Filter Likuiditas: Hanya memproses saham dengan transaksi aktif >= Rp 3 Miliar
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
            reasons.append("Uptrend Structure")

        if vol_ratio >= 1.5:
            accuracy_score += 30
            reasons.append(f"Volume Spike {vol_ratio}x")
        elif vol_ratio >= 1.2:
            accuracy_score += 20
            reasons.append(f"Vol {vol_ratio}x")

        if close_location >= 70:
            accuracy_score += 20
            reasons.append("Strong Buying Close")

        if 45 <= rsi <= 65:
            accuracy_score += 20
            reasons.append(f"Ideal RSI ({rsi})")

        min_score = 80 if ihsg_status == "BEARISH" else 75

        if accuracy_score >= min_score and 1.0 <= change_pct <= 7.0:
            tp1 = int(price * 1.025)
            tp2 = int(price * 1.050)
            sl = int(price * 0.985)

            return {
                "ticker": clean_ticker.replace(".JK", ""),
                "price": int(price),
                "change_pct": change_pct,
                "score": accuracy_score,
                "reasons": " | ".join(reasons),
                "tp1": tp1,
                "tp2": tp2,
                "sl": sl,
                "turnover": round(turnover / 1_000_000_000, 1)
            }
        return None
    except Exception:
        return None

def run_precision_scan():
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
    
    # 1. Ambil Seluruh Daftar Saham BEI Secara Dinamis
    bei_targets = get_all_bei_tickers()
    
    # 2. Cek Tren Bursa Asia & BEI
    _, nikkei_msg, _ = check_market_index("^N225", "NIKKEI 225", "🇯🇵")
    _, kospi_msg, _ = check_market_index("^KS11", "KOSPI", "🇰🇷")
    _, hsi_msg, _ = check_market_index("^HSI", "HANG SENG", "🇭🇰")
    ihsg_status, ihsg_msg, _ = check_market_index("^JKSE", "IHSG BEI", "🇮🇩")
    
    # 3. Cek Komoditas Global
    comm_msgs, comm_signals = scan_global_commodities()
    
    results = []
    # Menggunakan Multi-threading dengan 20 Workers agar pemindaian seluruh saham BEI berjalan cepat
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(analyze_high_precision_stock, t, ihsg_status): t for t in bei_targets}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    tg_msg = f"🎯 *MASTER PRECISION & GLOBAL RADAR*\n"
    tg_msg += f"📅 _Waktu Scan: {now_str}_\n\n"
    
    tg_msg += f"🌍 *RADAR BURSA ASIA & BEI:*\n"
    tg_msg += f"• {nikkei_msg}\n• {kospi_msg}\n• {hsi_msg}\n• {ihsg_msg}\n\n"

    if comm_msgs:
        tg_msg += f"🛢️ *HARGA KOMODITAS GLOBAL:*\n"
        tg_msg += "\n".join(comm_msgs) + "\n\n"

    if comm_signals:
        tg_msg += f"💡 *SINYAL SEKTOR POTENSIAL (EFEK KOMODITAS):*\n"
        tg_msg += "\n".join(comm_signals) + "\n\n"

    if not results:
        tg_msg += "ℹ️ _Tidak ada saham yang memenuhi kriteria konfirmasi tinggi saat ini._"
    else:
        df = pd.DataFrame(results).sort_values(by=["score", "turnover"], ascending=[False, False])
        tg_msg += f"⚡ *SETUP SAHAM BEI KONFIRMASI KUAT ({len(df)} Saham Terdeteksi):*\n\n"

        # Tampilkan hingga 5 saham teratas hasil filter dari seluruh bursa
        for _, row in df.head(5).iterrows():
            tg_msg += f"💎 *{row['ticker']}* 🔥 [CONFIRM SCORE: {row['score']}%]\n"
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
