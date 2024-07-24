import concurrent.futures
import datetime
import re
import shutil
from pathlib import Path

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
        "payout_ratio",
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
        "forward_eps",
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


class MissingDataError(Exception):
    pass


class StocksDataAPI:
    BASE_DIR = Path(__file__).resolve().parent.parent

    HISTORICAL_DATA_DIR = BASE_DIR / Path("stocks/data/history")
    PRICE_HISTORY_DIR = HISTORICAL_DATA_DIR / "price"
    BALANCE_SHEET_HISTORY_DIR = HISTORICAL_DATA_DIR / "balance_sheet"
    DIVIDENDS_HISTORY_DIR = HISTORICAL_DATA_DIR / "dividends"
    FINANCIALS_HISTORY_DIR = HISTORICAL_DATA_DIR / "financials"
    CASHFLOW_HISTORY_DIR = HISTORICAL_DATA_DIR / "cashflow"

    ALL_STOCKS_PATH = BASE_DIR / Path("stocks/data/base/all_stocks.csv")
    SECTOR_DATA = BASE_DIR / Path("stocks/data/base/all_stocks_sector.csv")
    EQUITY_DATA = BASE_DIR / Path("stocks/data/base/EQUITY_L.csv")

    STOCK_INFO_COLUMNS: list[str] = sum(list(reorganized_columns.values()), [])

    _price_history_cache: dict[str, pd.DataFrame] = {}

    def _clear_dirs(self):
        """
        Clears the historical data directories.

        Returns:
            None
        """
        for dir in [
            self.PRICE_HISTORY_DIR,
            self.BALANCE_SHEET_HISTORY_DIR,
            self.DIVIDENDS_HISTORY_DIR,
            self.FINANCIALS_HISTORY_DIR,
            self.CASHFLOW_HISTORY_DIR,
        ]:
            if dir.exists():
                shutil.rmtree(dir)

            dir.mkdir(exist_ok=True, parents=True)

    @property
    def symbols(self) -> list[str]:
        return self.equity_data["symbol"].to_list()

    @property
    def info_symbols(self) -> list[str]:
        return self.stock_info["symbol"].to_list()

    @property
    def missing_price_history(self) -> list[str]:
        return [symbol for symbol in self.symbols if not self.is_price_history_available(symbol)]

    @property
    def history_symbols(self) -> list[str]:
        return [symbol for symbol in self.symbols if self.is_price_history_available(symbol)]

    @property
    def equity_data(self):
        return (
            pd.read_csv(self.EQUITY_DATA)
            .sample(frac=1)
            .reset_index(drop=True)
            .rename(columns=lambda col: camel_to_snake(col))
            .drop_duplicates("symbol")
        )

    @property
    def sector_data(self):
        return (
            pd.read_csv(self.SECTOR_DATA)
            .reset_index(drop=True)
            .rename(columns=lambda col: camel_to_snake(col))
            .drop_duplicates("symbol")
        )

    def _download_stock_info(self, stock_code) -> dict:
        try:
            stock_symbol_info = yf.Ticker(f"{stock_code}.NS").info

            if "dayHigh" not in stock_symbol_info:
                raise MissingDataError(
                    f"Data seems to be missing for {stock_code} as it does not have dayHigh key present."
                    f"Present keys: {stock_symbol_info.keys()}"
                )

            return stock_symbol_info | {"symbol": stock_code}
        except Exception as e:
            print(f"Could not download for {stock_code} - {str(e)}")
            return {"symbol": stock_code}

    def download_stocks_info(self) -> tuple[pd.DataFrame, list]:
        df_stocks_nse_base = self.equity_data
        df_stocks_sector = self.sector_data

        base_symbols = set(df_stocks_nse_base["symbol"])

        # Data consistency check
        # trunk-ignore(bandit/B101)
        assert (
            set(df_stocks_sector["symbol"]) == base_symbols
        ), f"""
            Symbols do not match.
            Missing symbols: {base_symbols - set(df_stocks_sector["symbol"])}
        """

        stock_info = []
        failed_download: list[str] = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(self._download_stock_info, base_symbols))

        for result in results:
            if result is not None:
                stock_info.append(result)
            else:
                failed_download.append(result["symbol"])

        df_stock_info = pd.DataFrame(stock_info).rename(columns=lambda col: camel_to_snake(col))

        # Data consistency check
        # trunk-ignore(bandit/B101)
        assert (
            set(df_stock_info["symbol"]) | set(failed_download) == base_symbols
        ), f"""
            Symbols do not match.
            Missing symbols: {base_symbols - set(df_stock_info["symbol"])}
        """

        df_stock_data = (
            df_stock_info.merge(df_stocks_nse_base, on="symbol")
            .merge(df_stocks_sector, on="symbol")
            .loc[:, lambda df: ~df.columns.duplicated()]
            .drop_duplicates(["symbol"])
            .assign(
                industry_key=lambda df: df["industry_key"].fillna("other_industry"),
                sector_key=lambda df: df["sector_key"].fillna("other_sector"),
                market_cap=lambda df: df["market_cap"] / 10**7,
                market_cap_rank=lambda df: df["market_cap"].rank(ascending=False),
            )
            .loc[:, self.STOCK_INFO_COLUMNS]
        )

        return df_stock_data, failed_download

    def _download_historical_data_for_stock(self, stock_code):
        ticker = yf.Ticker(f"{stock_code}.NS")
        file_name = f"{stock_code}.csv"

        try:
            return self._extract_and_save_historical_data(ticker, file_name)
        except Exception as e:
            print(f"Could not download for {stock_code} - {str(e)}")
            return False

    def _extract_and_save_historical_data(self, ticker, file_name):
        ticker.history(period="max").to_csv(self.PRICE_HISTORY_DIR / file_name)
        ticker.dividends.to_csv(self.DIVIDENDS_HISTORY_DIR / file_name)
        ticker.cash_flow.to_csv(self.CASHFLOW_HISTORY_DIR / file_name)
        ticker.financials.to_csv(self.FINANCIALS_HISTORY_DIR / file_name)
        ticker.balance_sheet.to_csv(self.BALANCE_SHEET_HISTORY_DIR / file_name)
        return True

    def download_historical_data(self):
        symbols = self.symbols

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(self._download_historical_data_for_stock, symbols))

        if failed_download := [symbols[i] for i, result in enumerate(results) if not result]:
            print(f"Failed to download historical data for: {failed_download}")

    def _download_sector_data_for_stock(self, symbol):
        try:
            data = nse.nse_eq(symbol)
            if "industryInfo" in data:
                return {"symbol": symbol, **data["industryInfo"]}
        except Exception as e:
            print(f"Could not download sector data for {symbol} - {str(e)}")
        return None

    def download_stock_sector_data(self):
        symbols = self.symbols
        sector_data = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(self._download_sector_data_for_stock, symbols))

        sector_data = [result for result in results if result is not None]
        return pd.DataFrame(sector_data)

    def download_data(
        self,
        stock_info: bool = True,
        historical_data: bool = True,
        sector_data: bool = False,
    ) -> None:
        self._clear_dirs()

        if stock_info:
            df, _ = self.download_stocks_info()
            df.to_csv(self.ALL_STOCKS_PATH)

        if historical_data:
            self.download_historical_data()

        if sector_data:
            df = self.download_stock_sector_data()
            df.to_csv(self.SECTOR_DATA)

    @property
    def stock_info(self) -> pd.DataFrame:
        return pd.read_csv(self.ALL_STOCKS_PATH)

    def stock_info_by_symbol(self, symbol: str) -> dict:
        info_df = self.stock_info
        return info_df[info_df["symbol"] == symbol].to_dict(orient="dict")

    @property
    def stock_sectors(self) -> pd.DataFrame:
        return pd.read_csv(self.SECTOR_DATA)

    def is_price_history_available(self, symbol: str) -> bool:
        return Path(self.PRICE_HISTORY_DIR / f"{symbol}.csv").exists()

    @classmethod
    def price_history(cls, symbol: str) -> pd.DataFrame:
        if symbol not in cls._price_history_cache:
            cls._price_history_cache[symbol] = (
                pd.read_csv(cls.PRICE_HISTORY_DIR / f"{symbol}.csv", parse_dates=["Date"])
                .assign(Date=lambda df: pd.to_datetime(df["Date"]).dt.date)
                .sort_values(by="Date", ascending=False)
            )

        return cls._price_history_cache[symbol]

    def history_lastest_date(self, symbol) -> datetime.date | None:
        history = self.price_history(symbol)

        return None if history.empty else history["Date"].max()

    def history_oldest_date(self, symbol) -> datetime.date | None:
        history = self.price_history(symbol)

        return None if history.empty else history["Date"].min()

    def history_date_range(self, symbol) -> tuple[datetime.date | None, datetime.date | None]:
        return self.history_oldest_date(symbol), self.history_lastest_date(symbol)

    def price_history_by_dates(self, symbol: str, from_date: datetime.date, to_date: datetime.date):
        # trunk-ignore(bandit/B101)
        assert from_date <= to_date, f"Supplied dates are in wrong order, {from_date} > {to_date}"

        df = self.price_history(symbol)

        return df[(df["Date"] >= from_date) & (df["Date"] <= to_date)].sort_values(by="Date", ascending=False)

    def price_at_date(self, symbol: str, date: datetime.date) -> float | None:
        df = self.price_history(symbol)
        filtered_df = df[df["Date"] <= date].sort_values(by="Date", ascending=False)
        return None if filtered_df.empty else filtered_df.iloc[0]["Close"]

    def latest_price(self, symbol: str) -> float | None:
        df = self.price_history(symbol)
        return None if df.empty else df.iloc[0]["Close"]

    def stocks_by_price(self, min_price: float = 0, max_price: float | None = None) -> list[str]:
        min_price = min_price or self.min_price
        max_price = max_price or self.max_price
        filtered_stocks = self.stock_info.query("@min_price <= day_high <= @max_price")
        return filtered_stocks["symbol"].to_list()

    @property
    def max_price(self) -> float:
        return self.stock_info["day_high"].max()

    @property
    def min_price(self) -> float:
        return self.stock_info["day_high"].min()

    def balance_sheet_history(self, symbol: str) -> pd.DataFrame:
        return pd.read_csv(self.BALANCE_SHEET_HISTORY_DIR / f"{symbol}.csv")

    def dividends_history(self, symbol: str) -> pd.DataFrame:
        return pd.read_csv(self.DIVIDENDS_HISTORY_DIR / f"{symbol}.csv")

    def financials_history(self, symbol: str) -> pd.DataFrame:
        return pd.read_csv(self.FINANCIALS_HISTORY_DIR / f"{symbol}.csv")

    def cashflow_history(self, symbol: str) -> pd.DataFrame:
        return pd.read_csv(self.CASHFLOW_HISTORY_DIR / f"{symbol}.csv")


if __name__ == "__main__":
    stock_api = StocksDataAPI()

    stock_api.download_data()
