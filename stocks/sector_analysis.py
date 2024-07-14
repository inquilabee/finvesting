import investpy
import pandas as pd
import yfinance as yf


def get_stock_sector_info(tickers):
    stock_info = []
    for ticker in tickers:
        try:
            search_result = investpy.search_quotes(text=ticker, products=["stocks"], countries=["india"], n_results=1)
            sector = search_result.retrieve_sector()
            stock_info.append({"Ticker": ticker, "Sector": sector})
        except Exception as e:
            print(f"Could not retrieve sector for {ticker}: {e}")
            stock_info.append({"Ticker": ticker, "Sector": "Unknown"})
    return stock_info


def get_stock_market_info(tickers):
    stock_market_info = []
    for ticker in tickers:
        try:
            yf_ticker = yf.Ticker(ticker)
            indices = yf_ticker.info.get("indices", [])
            stock_market_info.append({"Ticker": ticker, "Markets": indices})
        except Exception as e:
            print(f"Could not retrieve market info for {ticker}: {e}")
            stock_market_info.append({"Ticker": ticker, "Markets": "Unknown"})
    return stock_market_info


# Example tickers
tickers = ["RELIANCE.NS", "TCS.NS"]

# Get sector information
sector_info = get_stock_sector_info(tickers)
sector_df = pd.DataFrame(sector_info)

# Get market information
market_info = get_stock_market_info(tickers)
market_df = pd.DataFrame(market_info)

# Merge sector and market information
combined_df = pd.merge(sector_df, market_df, on="Ticker")

print(combined_df)
