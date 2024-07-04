import yfinance as yf

import pandas as pd

import re


def camel_to_snake(text):
    str1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text.strip())
    str2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str1).lower()
    return re.sub(r"\s+", "_", str2)


def read_equity_data():
    return pd.read_csv("stocks/data/base/EQUITY_L.csv")


def get_stocks_info():
    df_stocks = read_equity_data()
    df_stocks = df_stocks.sample(frac=1).reset_index(drop=True)

    df_stocks["SYMBOL"] += ".NS"

    stock_info = []

    failed_download = []

    for stock_code in df_stocks["SYMBOL"]:
        try:
            stock_info.append(yf.Ticker(f"{stock_code}").info)
            print(f"Download completed for {stock_code}")
        except Exception:
            failed_download.append(stock_code)
            # print(f"Could not downoload for {stock_code} - {str(e)}")

    df_stock_info = pd.DataFrame(stock_info)

    df_stock_data = df_stocks.merge(
        df_stock_info, left_on="SYMBOL", right_on="symbol"
    ).rename(columns=lambda col: camel_to_snake(col))

    df_stock_data = df_stock_data.loc[:, ~df_stock_data.columns.duplicated()].copy()
    # df_stock_data = df_stock_data.drop_duplicates(keep="first")

    df_stock_data["industry_key"] = df_stock_data["industry_key"].fillna(
        "other_industry"
    )
    df_stock_data["sector_key"] = df_stock_data["sector_key"].fillna("other_sector")
    df_stock_data["market_cap"] = df_stock_data["market_cap"] / 10 * 7
    df_stock_data["market_cap_rank"] = df_stock_data["market_cap"].rank(ascending=False)

    return df_stock_data, failed_download


if __name__ == "__main__":
    df, failed = get_stocks_info()
    print(failed)
    df.to_csv("stocks/data/base/all_stocks.csv")
