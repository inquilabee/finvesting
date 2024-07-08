from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from data import StocksDataAPI

stock_api = StocksDataAPI()


def calculate_annualized_return(df, start_date, end_date):
    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    df["Return"] = df["Close"].pct_change()
    return np.exp(np.log1p(df["Return"]).sum() / len(df)) - 1


def select_losers_and_compute_metrics(x, y, N):
    loser_stocks = []

    for symbol in stock_api.symbols:
        historical_df = stock_api.price_history(symbol)

        if historical_df is not None:
            end_date = pd.to_datetime("today")
            start_date = end_date - pd.Timedelta(days=365 * y)
            cutoff_date = end_date - pd.Timedelta(days=365 * x)

            historical_df["Date"] = pd.to_datetime(historical_df["Date"])
            historical_df = historical_df.loc[
                historical_df["Date"] < cutoff_date.date()
            ]

            if len(historical_df) > 0:
                annualized_return = calculate_annualized_return(
                    historical_df, start_date, end_date
                )
                if annualized_return < 0:
                    loser_stocks.append((symbol, annualized_return))

    loser_stocks = sorted(loser_stocks, key=lambda x: x[1])[:N]
    return pd.DataFrame(loser_stocks, columns=["Symbol", "Annualized Return"])


if __name__ == "__main__":
    stock_data = stock_api.stock_info

    N = 25
    x = 3
    y = 2

    loser_stocks_df = select_losers_and_compute_metrics(x, y, N)
    print(loser_stocks_df)
