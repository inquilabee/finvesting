import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# https://www.nseindia.com/market-data/securities-available-for-trading
# nse_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

nse_stocks_df = pd.read_csv("./stocks/EQUITY_L.csv")
nse_stocks_df = nse_stocks_df[["SYMBOL", "NAME OF COMPANY"]]
nse_stocks_df.rename(
    columns={"SYMBOL": "Symbol", "NAME OF COMPANY": "Name"}, inplace=True
)
nse_stocks_df["Exchange"] = "NSE"

# Define the penny stock price threshold and time frame
PENNY_STOCK_THRESHOLD = 200
DONE_WELL_THRESHOLD = 0

end_date = datetime.today()
start_date = end_date - timedelta(days=180)

# Fetch additional information and filter penny stocks
penny_stocks = []

for _, row in nse_stocks_df.iterrows():
    symbol = row["Symbol"]
    exchange = row["Exchange"]
    ticker_symbol = f"{symbol}.NS"

    try:
        ticker = yf.Ticker(ticker_symbol)
        stock_data = ticker.history(start=start_date, end=end_date)
        if (
            not stock_data.empty
            and stock_data["Close"].iloc[-1] <= PENNY_STOCK_THRESHOLD
        ):
            start_price = stock_data["Close"].iloc[0]
            end_price = stock_data["Close"].iloc[-1]
            price_change = (end_price - start_price) / start_price * 100
            
            penny_stocks.append(
                {
                    "Symbol": symbol,
                    "Name": row["Name"],
                    "Exchange": exchange,
                    "Start Price": start_price,
                    "End Price": end_price,
                    "Price Change (%)": price_change,
                }
            )
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")

penny_stocks_df = pd.DataFrame(penny_stocks)
penny_stocks_df.sort_values(by="Price Change (%)", ascending=False, inplace=True)

# Save to CSV
penny_stocks_df.to_csv("performing_penny_stocks.csv", index=False)

print(penny_stocks_df.head())
