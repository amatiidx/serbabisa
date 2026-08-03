import sqlite3
import pandas as pd
import requests
import yfinance as yf

DB_NAME = "stock_data.db"
GOAPI_KEY = "c8aee938-c226-5f6c-852e-0a42b3b9"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, date)
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_profiles (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            sub_sector TEXT
        )
    """)
  conn.commit()
  conn.close()


def fetch_yfinance_data(ticker_symbol):
  formatted_ticker = (
      f"{ticker_symbol}.JK"
      if not ticker_symbol.endswith(".JK")
      else ticker_symbol
  )
  df = yf.download(formatted_ticker, period="1mo", interval="1d", progress=False)

  if df.empty:
    return None

  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

  df = df.reset_index()
  df["ticker"] = ticker_symbol.replace(".JK", "")
  df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

  return df[["ticker", "Date", "Open", "High", "Low", "Close", "Volume"]]


def fetch_and_save_goapi_profile(ticker_symbol):
  url = f"https://api.goapi.io/v1/stock/idx/{ticker_symbol}"
  headers = {"X-API-KEY": GOAPI_KEY}

  try:
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
      data = response.json().get("data", {})
      if data:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT OR REPLACE INTO stock_profiles (ticker, name, sector, sub_sector)
                    VALUES (?, ?, ?, ?)
                """,
            (
                ticker_symbol,
                data.get("name", "-"),
                data.get("sector", "-"),
                data.get("sub_sector", "-"),
            ),
        )
        conn.commit()
        conn.close()
        return data
  except Exception as e:
    print(f"Err GoAPI {ticker_symbol}: {e}")
  return {}


def save_to_db(df):
  if df is None or df.empty:
    return

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  for _, row in df.iterrows():
    cursor.execute(
        """
            INSERT OR REPLACE INTO stock_prices (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["ticker"],
            row["Date"],
            row["Open"],
            row["High"],
            row["Low"],
            row["Close"],
            row["Volume"],
        ),
    )
  conn.commit()
  conn.close()


def get_stored_stock_info(ticker_symbol):
  conn = sqlite3.connect(DB_NAME)
  df_price = pd.read_sql_query(
      f"SELECT * FROM stock_prices WHERE ticker='{ticker_symbol}' ORDER BY"
      " date ASC",
      conn,
  )
  df_profile = pd.read_sql_query(
      f"SELECT * FROM stock_profiles WHERE ticker='{ticker_symbol}'", conn
  )
  conn.close()

  profile_dict = (
      df_profile.to_dict("records")[0] if not df_profile.empty else {}
  )
  return df_price, profile_dict


if __name__ == "__main__":
  init_db()
  watchlist = ["TLKM", "BUMI", "SIDO", "INET", "ENRG", "CDIA"]
  for t in watchlist:
    df = fetch_yfinance_data(t)
    if df is not None:
      save_to_db(df)
    fetch_and_save_goapi_profile(t)
