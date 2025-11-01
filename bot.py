import pandas as pd
import numpy as np
import ccxt
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
import time, sys

# ========== FORCE INSTANT PRINT (Pydroid-safe) ==========
def p(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

# ========== SETTINGS ==========
symbol = 'ZEC/USDT'
capital = 100.0
commission = 0.001
start_date = '2025-10-01T00:00:00Z'
end_date   = '2025-10-01T23:59:00Z'
tf = '5m'
exchange = ccxt.binance()

# ========== FETCH DATA ==========
def fetch_ohlcv(symbol, timeframe, start, end):
    p("📡 Fetching 5m data from Binance...")
    since = exchange.parse8601(start)
    end_ts = exchange.parse8601(end)
    all_data = []

    while since < end_ts:
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        except Exception as e:
            p("❌ Error fetching data:", e)
            break

        if not data:
            p("⚠️ No data returned. Maybe wrong symbol or network issue.")
            break

        all_data += data
        p(f"Fetched {len(data)} candles. Total: {len(all_data)}")

        since = data[-1][0] + (exchange.parse_timeframe(timeframe) * 1000)
        time.sleep(0.4)

        if data[-1][0] >= end_ts:
            break

    if not all_data:
        p("❌ No data fetched at all. Exiting.")
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.set_index('timestamp', inplace=True)
    df = df.loc[start:end]
    p(f"✅ Data fetched: {len(df)} rows ({df.index[0]} → {df.index[-1]})")
    return df


# ========== MAIN ==========
df = fetch_ohlcv(symbol, tf, start_date, end_date)
if df.empty:
    p("❌ No data. Check network or symbol.")
    sys.exit()

# ========== 1H DATA ==========
df_1h = df[['open','close']].resample('1h').agg({'open':'first','close':'last'}).dropna()
df_1h['ch1'] = df_1h['open']
df_1h['ch2'] = df_1h['close']

df = df.join(df_1h[['ch1','ch2']], how='left')
df[['ch1','ch2']] = df[['ch1','ch2']].ffill()

# ========== STRATEGY ==========
df['longCondition'] = (df['ch2'].shift(1) < df['ch1'].shift(1)) & (df['ch2'] > df['ch1'])
df['shortCondition'] = (df['ch2'].shift(1) > df['ch1'].shift(1)) & (df['ch2'] < df['ch1'])

# ========== BACKTEST ==========
equity = capital
position = 0
entry_price = 0
balance_history = []
trade_count = 0

for i in range(1, len(df)):
    price = df['close'].iloc[i]

    if df['longCondition'].iloc[i]:
        if position == -1:
            equity *= (entry_price / price) * (1 - commission)
            position = 0
        if position == 0:
            position = 1
            entry_price = price * (1 + commission)
            trade_count += 1

    elif df['shortCondition'].iloc[i]:
        if position == 1:
            equity *= (price / entry_price) * (1 - commission)
            position = 0
        if position == 0:
            position = -1
            entry_price = price * (1 - commission)
            trade_count += 1

    if position == 1:
        cur_equity = equity * (price / entry_price)
    elif position == -1:
        cur_equity = equity * (entry_price / price)
    else:
        cur_equity = equity

    balance_history.append(cur_equity)

if position != 0:
    final_price = df['close'].iloc[-1]
    if position == 1:
        equity *= (final_price / entry_price) * (1 - commission)
    else:
        equity *= (entry_price / final_price) * (1 - commission)

final_equity = equity
profit_pct = (final_equity - capital) / capital * 100

p("\n📊 ===== BACKTEST RESULTS =====")
p(f"Symbol:          {symbol}")
p(f"Timeframe:       5m (with 1h logic)")
p(f"Period:          {start_date[:10]} → {end_date[:10]}")
p(f"Initial capital: ${capital:.2f}")
p(f"Final equity:    ${final_equity:.2f}")
p(f"Net return:      {profit_pct:.2f}%")
p(f"Trade signals:   {trade_count}")