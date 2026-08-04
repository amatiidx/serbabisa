import sys
import requests
import yfinance as yf

BOT_TOKEN = "8784775406:AAG815Z3eeg4g5Aihrxiwu2fjbIZbe_qCII"
CHAT_ID = "347896274"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Berhasil terkirim ke Telegram!")
        else:
            print(f"❌ Gagal kirim ({r.status_code}):", r.text)
    except Exception as e:
        print("❌ Error Telegram:", e)

def get_stock_data(tickers):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(f"{ticker}.JK")
            df = stock.history(period="2d")
            if not df.empty and len(df) >= 2:
                last_price = int(df['Close'].iloc[-1])
                prev_price = int(df['Close'].iloc[-2])
                change_pct = round(((last_price - prev_price) / prev_price) * 100, 2)
                results.append(f"• <b>{ticker}</b>: Rp {last_price:,} ({change_pct:+}% )")
        except Exception:
            pass
    return "\n".join(results) if results else "• Data belum tersedia"

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "default"
    
    if mode == "asia":
        msg = """🌏 <b>[SERBABISA.ID] UPDATE PASAR ASIA (09:30 WIB)</b> 🌏

Sentimen bursa regional pagi ini sebagai acuan IHSG. Tetap prioritaskan manajemen risiko pada portofolio Anda.

🌐 <i>Pantau Chart Interaktif:</i> https://serbabisa.id"""

    elif mode == "rekomendasi":
        stocks_info = get_stock_data(["INET", "BRIS", "ENRG", "CDIA"])
        msg = f"""🎯 <b>[SERBABISA.ID] REKOMENDASI SAHAM (10:15 WIB)</b> 🎯

Saham potensial yang masuk radar pantauan jam bursa pagi ini:
{stocks_info}

💡 <i>Disiplin dengan Trading Plan & Stop Loss masing-masing.</i>"""

    elif mode == "sesi1":
        msg = """⏳ <b>[SERBABISA.ID] JELANG PENUTUPAN SESI 1 (11:50 WIB)</b> ⏳

10 menit menuju akhir Sesi 1. Evaluasi posisi trading harian Anda, amankan profit (*Take Profit*) untuk saham yang telah mencapai target."""

    elif mode == "sesi2":
        stocks_info = get_stock_data(["BUMI", "ENRG", "GOTO"])
        msg = f"""🔥 <b>[SERBABISA.ID] SINYAL BSJP / KONTRAK SORE (15:50 WIB)</b> 🔥

10 menit jelang penutupan Sesi 2! Pantauan saham akumulasi sore ini untuk skenario Beli Sore Jual Pagi (BSJP):
{stocks_info}

🌐 https://serbabisa.id"""

    elif mode == "rangkuman":
        stocks_info = get_stock_data(["INET", "BRIS", "ENRG", "CDIA", "BUMI", "GOTO", "TLKM"])
        msg = f"""🌙 <b>[SERBABISA.ID] WATCHLIST & RANGKUMAN (20:00 WIB)</b> 🌙

Rangkuman pergerakan saham utama hari ini untuk acuan trading besok pagi:
{stocks_info}

📊 <i>Siapkan Trading Plan & daftar antrean order untuk besok.</i>"""

    else:
        msg = "🚨 Pemindaian otomatis serbabisa.id aktif."

    send_telegram(msg)

if __name__ == "__main__":
    main()
