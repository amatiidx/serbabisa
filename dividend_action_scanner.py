import pandas as pd
import numpy as np
import yfinance as yf
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Konfigurasi Bot Telegram
TELEGRAM_TOKEN = "8784775406:AAFJRPUyDEbGHGm7tvkVq0epdLczjOyQn0E"
TELEGRAM_CHAT_ID = "347896274"

# Daftar Saham BEI yang sering bagi Dividen & RUPS
BEI_DIVIDEND_TARGETS = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "AMRT", "ANTM", "ADRO", "AKRA",
    "AMMN", "ARTO", "AUTO", "BBTN", "BRPT", "BUMI", "BUKA", "CPIN", "CUAN", "DOOH",
    "EMTK", "ENRG", "EXCL", "GOTO", "HRUM", "ICBP", "INDF", "INKP", "INET", "ISAT",
    "ITMG", "KLBF", "MDKA", "MEDC", "MYOR", "NCKL", "PGAS", "PGEO", "PTBA", "RAJA",
    "SIDO", "SMGR", "SRTG", "TBIG", "TPIA", "TOWR", "UNTR", "UNVR", "PANI", "CDIA",
    "BSDE", "CTRA", "CMRY", "MBMA", "ADMR", "BRMS", "NSSS", "MIKA", "ACES", "MAPI"
]

def fetch_corporate_dividend_data(ticker):
    try:
        clean_ticker = ticker.strip().upper().replace(".JK", "") + ".JK"
        stock = yf.Ticker(clean_ticker)
        
        # Ambil Data Dividen
        divs = stock.dividends
        if divs.empty:
            return None
            
        last_div_date = divs.index[-1].tz_localize(None)
        last_div_amount = float(divs.iloc[-1])
        
        # Ambil Harga Terakhir
        hist = stock.history(period="5d")
        if hist.empty:
            return None
            
        latest_price = float(hist['Close'].iloc[-1])
        
        # Hitung Est. Yield Dividen Terakhir (%)
        div_yield = round((last_div_amount / latest_price) * 100, 2) if latest_price > 0 else 0
        
        today = datetime.datetime.now()
        days_diff = (today - last_div_date).days

        # Menyaring dividen/aksi terbaru (misal yang tercatat baru/dalam rentang waktu 60 hari terakhir/mendatang)
        if days_diff <= 60 and div_yield >= 1.0:
            return {
                "ticker": clean_ticker.replace(".JK", ""),
                "price": int(latest_price),
                "div_amount": last_div_amount,
                "div_yield": div_yield,
                "div_date": last_div_date.strftime("%d-%m-%Y")
            }
        return None
    except Exception:
        return None

def run_dividend_scan():
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_corporate_dividend_data, t): t for t in BEI_DIVIDEND_TARGETS}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    if not results:
        print("Tidak ada update dividen/aksi korporasi signifikan.")
        return

    df = pd.DataFrame(results).sort_values(by="div_yield", ascending=False)
    
    tg_msg = f"🎁 *DIVIDEND & CORPORATE ACTION RADAR*\n"
    tg_msg += f"📅 _Waktu Scan: {now_str}_\n"
    tg_msg += f"💰 _Daftar Saham Potensial Dividen & Sentimen Aksi Korporasi:_\n\n"
    
    for _, row in df.head(5).iterrows():
        tg_msg += f"📌 *{row['ticker']}*\n"
        tg_msg += f"• *Harga Last:* Rp {row['price']:,}\n"
        tg_msg += f"• *Est. Dividen:* Rp {row['div_amount']} / Lembar\n"
        tg_msg += f"• *Dividen Yield:* {row['div_yield']}%\n"
        tg_msg += f"• *Tanggal Record:* {row['div_date']}\n\n"
        
    tg_msg += "💡 _Manfaatkan momentum Dividen Play / Swing sebelum Cum Date!_"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": tg_msg, "parse_mode": "Markdown"}, timeout=15)

if __name__ == "__main__":
    run_dividend_scan()
