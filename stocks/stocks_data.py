import re

import nsepython as nse
import pandas as pd
import yfinance as yf

reorganized_columns = {
    "Identification and Listing Information": [
        "symbol",
        "name_of_company",
        "series",
        "date_of_listing",
        "isin_number",
        "industry_key",
        "sector_key",
        "macro",
        # "sector",
        # "industry",
        "basic_industry",
    ],
    "Stock Performance and Trading Data": [
        "previous_close",
        "open",
        "day_low",
        "day_high",
        "regular_market_previous_close",
        "regular_market_open",
        "regular_market_day_low",
        "regular_market_day_high",
        "volume",
        "regular_market_volume",
        "average_volume",
        "average_volume10days",
        "average_daily_volume10_day",
        "fifty_two_week_low",
        "fifty_two_week_high",
        "fifty_day_average",
        "two_hundred_day_average",
        "current_price",
        "52_week_change",
        "sand_p52_week_change",
        "price_hint",
    ],
    "Balance Sheet and Liquidity Ratios": [
        "debt_to_equity",
        "quick_ratio",
        "current_ratio",
    ],
    "Corporate Governance": [
        "float_shares",
        "shares_outstanding",
        "implied_shares_outstanding",
        "held_percent_insiders",
        "compensation_as_of_epoch_date",
    ],
    "Dividends and Splits": [
        "ex_dividend_date",
        "last_dividend_value",
        "last_dividend_date",
        "last_split_factor",
        "last_split_date",
    ],
    "Financial Metrics": [
        "paid_up_value",
        "market_lot",
        "face_value",
        "market_cap",
        "enterprise_value",
        "total_cash",
        "total_cash_per_share",
        "total_debt",
        "total_revenue",
        "revenue_per_share",
        "ebitda",
        "free_cashflow",
        "operating_cashflow",
        "book_value",
        "price_to_book",
        "price_to_sales_trailing12_months",
        "enterprise_to_revenue",
        "enterprise_to_ebitda",
    ],
    "Growth Metrics": [
        "earnings_growth",
        "revenue_growth",
        "earnings_quarterly_growth",
        "net_income_to_common",
        "trailing_eps",
    ],
    "Profitability Ratios": [
        "trailing_pe",
        "profit_margins",
        "gross_margins",
        "ebitda_margins",
        "operating_margins",
    ],
    "Return Ratios": ["return_on_assets", "return_on_equity"],
    "Miscellaneous": [
        "long_business_summary",
        "beta",
        "recommendation_key",
        "market_cap_rank",
    ],
}


def camel_to_snake(text):
    str1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text.strip())
    str2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str1).lower()
    return re.sub(r"\s+", "_", str2)


def read_equity_data():
    return (
        pd.read_csv("stocks/data/base/EQUITY_L.csv")
        .sample(frac=1)
        .reset_index(drop=True)
        .rename(columns=lambda col: camel_to_snake(col))
        .drop_duplicates("symbol")
    )


def read_sector_data():
    return (
        pd.read_csv("stocks/data/base/all_stocks_sector.csv")
        .reset_index(drop=True)
        .rename(columns=lambda col: camel_to_snake(col))
        .drop_duplicates("symbol")
    )


def get_stocks_info() -> tuple[pd.DataFrame, list]:
    df_stocks_nse_base = read_equity_data()
    df_stocks_sector = read_sector_data()

    base_symbols = set(df_stocks_nse_base["symbol"])

    assert set(df_stocks_sector["symbol"]) == base_symbols, f"""
        Symbols do not match.
        Missing symbols: { base_symbols - set(df_stocks_sector["symbol"])}
        Missing symbols: { set(df_stocks_sector["symbol"]) - base_symbols}
        """

    stock_info = []
    failed_download = []

    for stock_code in base_symbols:
        try:
            stock_info.append(yf.Ticker(f"{stock_code}.NS").info)
            print(f"Download completed for {stock_code}")
        except Exception:
            failed_download.append(stock_code)
            # print(f"Could not downoload for {stock_code} - {str(e)}")

    df_stock_info = (
        pd.DataFrame(stock_info)
        .rename(columns=lambda col: camel_to_snake(col))
        .assign(symbol=lambda df: df["symbol"].str.rstrip(".NS"))
    )

    assert set(df_stock_info["symbol"]) == base_symbols, f"""
        Symbols do not match. 
        Missing symbols: { base_symbols - set(df_stock_info["symbol"])}
        Missing symbols: { set(df_stock_info["symbol"]) -base_symbols}
        """

    df_stock_data = (
        df_stock_info.merge(df_stocks_nse_base, on="symbol")
        .merge(df_stocks_sector, on="symbol")
        .loc[:, lambda df: ~df.columns.duplicated()]
        .drop_duplicates(["symbol"])
        .assign(
            industry_key=lambda df: df["industry_key"].fillna("other_industry"),
            sector_key=lambda df: df["sector_key"].fillna("other_sector"),
            market_cap=lambda df: df["market_cap"] / 10 * 7,
            market_cap_rank=lambda df: df["market_cap"].rank(ascending=False),
        )
        .loc[:, sum([cols for cols in reorganized_columns.values()], [])]
    )

    return df_stock_data, failed_download


def get_stock_sector_data():
    stocks_data = read_equity_data()
    sector_data = []

    for symbol in stocks_data["SYMBOL"]:
        data = nse.nse_eq(symbol)

        if "industryInfo" in data:
            sector_data.append({"symbol": symbol, **data["industryInfo"]})
            print(f"Download done for {symbol}")

    return pd.DataFrame(sector_data)


def download_historical_data():
    df_stocks = read_equity_data()

    df_stocks["SYMBOL"] += ".NS"

    failed_download = []

    for stock_code in df_stocks["SYMBOL"]:
        try:
            df_data = yf.Ticker(f"{stock_code}").history()

            df_data.to_csv(f"stocks/data/history/{stock_code}.csv")
        except Exception as e:
            failed_download.append(stock_code)
            print(f"Could not downoload for {stock_code} - {str(e)}")


if __name__ == "__main__":
    df, failed = get_stocks_info()
    print(failed)
    df.to_csv("stocks/data/base/all_stocks.csv")

    # sector_data = get_stock_sector_data()
    # sector_data.to_csv("stocks/data/base/all_stocks_sector.csv")
