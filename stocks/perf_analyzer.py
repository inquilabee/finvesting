import concurrent.futures
import datetime
import itertools
import multiprocessing
from functools import cached_property as cached
from pathlib import Path

import pandas as pd

from stocks.portfolio import PortfolioAPI
from stocks.resource import StocksDataAPI

THREAD_PROC_MAX_WORKERS = multiprocessing.cpu_count()

PORTFOLIO_DIR = Path("stocks/data/portfolio")


class PerfColumns:
    COL_PAST_PERF = "past_performance_cagr_y"
    COL_FUTURE_PERF = "future_performance_cagr_x"
    COL_XY_PRICE = "price_xy_years_ago"
    COL_X_PRICE = "price_x_years_ago"
    COL_CURR_PRICE = "price_current"
    COL_PAST_CAGR = "past_cagr"
    COL_FUTURE_CAGR = "future_cagr"

    @classmethod
    def perf_columns_data_to_dict(
        cls, col_xy_price, col_x_price, col_curr_price, col_past_perf, col_future_perf
    ) -> dict:
        return {
            cls.COL_XY_PRICE: col_xy_price,
            cls.COL_X_PRICE: col_x_price,
            cls.COL_CURR_PRICE: col_curr_price,
            cls.COL_PAST_PERF: col_past_perf,
            cls.COL_FUTURE_PERF: col_future_perf,
        }


class PerfDates:
    PERF_CURRENT_DATE = "current_date"
    PERF_LAST_EVAL_DATE = "last_evaluation_date"
    PERF_FUTURE_START_DATE = "future_start_date"
    PERF_FUTURE_END_DATE = "future_end_date"
    PERF_PAST_START_DATE = "past_start_date"
    PERF_PAST_END_DATE = "past_end_date"

    @classmethod
    def data_to_dict(
        cls, curr_date, last_eval_date, future_start_date, future_end_date, past_start_date, past_end_date
    ) -> dict:
        return {
            cls.PERF_CURRENT_DATE: curr_date,
            cls.PERF_LAST_EVAL_DATE: last_eval_date,
            cls.PERF_FUTURE_START_DATE: future_start_date,
            cls.PERF_FUTURE_END_DATE: future_end_date,
            cls.PERF_PAST_START_DATE: past_start_date,
            cls.PERF_PAST_END_DATE: past_end_date,
        }


class StockPortfolioAnalyzer:

    PERFORMANCE_DIR = PORTFOLIO_DIR / "performance"

    def __init__(
        self,
        x: float,
        y: float,
        z: float = 0,
        min_price: float = 0,
        max_price: float = 10**7,
        autosave_performance_data: bool = True,
    ):
        """
        Initialize the object with given parameters and calculate various date ranges for past and future performance analysis.

        ### Args:
        - x (float): Number of years for future performance analysis.
        - y (float): Number of years for past performance analysis.
        - z (float, optional): Offset in years for date calculations. Defaults to 0.
        - min_price (float, optional): Minimum price value. Defaults to 0.
        - max_price (float, optional): Maximum price value. Defaults to 10^7.

        ### Returns:
        None

        ### Raises:
        AssertionError: If the date ranges are invalid.
        """

        self.x = x
        self.y = y
        self.z = z
        self.min_price = min_price
        self.max_price = max_price
        self.autosave_data = autosave_performance_data

        self.portfolio_api = PortfolioAPI()
        self.data_api = StocksDataAPI()

        self.current_date = datetime.datetime.now().date()

        self.last_evaluation_date = self.current_date - datetime.timedelta(days=int(365 * z))

        # current (future) performance dates (x years)
        self.future_performance_dates = (
            self.last_evaluation_date - datetime.timedelta(days=int(365 * self.x)),
            self.last_evaluation_date,
        )
        self.future_start_date, self.future_end_date = self.future_performance_dates

        # past performance dates (y years)
        self.past_performance_dates = (
            self.last_evaluation_date - datetime.timedelta(days=int(365 * (self.x + self.y))),
            self.last_evaluation_date - datetime.timedelta(days=int(365 * self.x)),
        )

        self.past_start_date, self.past_end_date = self.past_performance_dates

        # trunk-ignore(bandit/B101)
        assert (
            self.past_start_date <= self.past_end_date <= self.future_start_date <= self.future_end_date
        ), "Invalid date range"

        print(f"Past performance dates {self.past_start_date} to {self.past_end_date}")
        print(f"Future performance dates {self.future_start_date} to {self.future_end_date}")
        print(f"Ignoring last {self.z} years of data from {self.last_evaluation_date} to {self.current_date}")
        print(f"Analyzing data of last {self.x + self.y} years, (ignoring last {self.z} years)")

        # Performance dataframe (based on x and y)
        self._past_performance = pd.DataFrame()

        # Create performance directory
        self.PERFORMANCE_DIR.mkdir(parents=True, exist_ok=True)
        self.PERFORMANCE_FILE = self.perf_file_name(x, y, z)

    @cached
    def valid_symbols(self) -> list[str]:
        return [
            symbol
            for symbol in self.data_api.history_symbols
            if (
                self.data_api.history_oldest_date(symbol)
                and self.data_api.history_oldest_date(symbol) <= self.past_start_date
            )
            and (
                self.data_api.price_at_date(symbol, self.past_start_date)
                and self.min_price <= self.data_api.price_at_date(symbol, self.past_start_date) <= self.max_price
            )
        ]

    @classmethod
    def perf_file_name(cls, x: float, y: float, z: float):
        return cls.PERFORMANCE_DIR / f"{x}_{y}_{z}.csv"

    @property
    def past_performance(self) -> pd.DataFrame:
        if self._past_performance.empty:
            self._past_performance = self._compute_past_future_returns()

        if self.autosave_data:
            self.save_data()

        return self._past_performance

    def read_from_file(self) -> pd.DataFrame:
        return pd.read_csv(self.PERFORMANCE_FILE)

    def save_data(self):
        if self._past_performance.empty:
            self._past_performance = self._compute_past_future_returns()

        self._past_performance.to_csv(self.PERFORMANCE_FILE)

    @classmethod
    def save_perf_combinations(
        cls,
        x_values: list[float],
        y_values: list[float],
        z_values: list[float],
    ) -> None:

        with concurrent.futures.ProcessPoolExecutor(max_workers=THREAD_PROC_MAX_WORKERS) as executor:
            future_to_combination = {
                executor.submit(
                    cls._save_combination,
                    x,
                    y,
                    z,
                ): (x, y, z)
                for x, y, z in itertools.product(x_values, y_values, z_values)
            }

            for future in concurrent.futures.as_completed(future_to_combination):
                future.result()

    def _calculate_cagr_for_symbol(self, symbol: str) -> tuple[str, float | None, float | None]:
        past_cagr = self.portfolio_api.calculate_cagr(symbol, self.past_start_date, self.past_end_date)
        future_cagr = self.portfolio_api.calculate_cagr(symbol, self.future_start_date, self.future_end_date)
        return symbol, past_cagr, future_cagr

    @classmethod
    def _save_combination(
        cls,
        x: float,
        y: float,
        z: float,
    ):

        stock_analyzer = cls(x, y, z)

        stock_analyzer.save_data()

    def _compute_past_future_returns(self) -> pd.DataFrame:
        """Compute past and future performance returns."""
        symbols = self.valid_symbols
        data = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_PROC_MAX_WORKERS) as executor:
            future_to_symbol = {executor.submit(self._calculate_cagr_for_symbol, symbol): symbol for symbol in symbols}
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]

                try:
                    result = future.result()
                    _, past_cagr, future_cagr = result
                    history = self.data_api.price_history_by_dates(symbol, self.future_start_date, self.future_end_date)

                    past_price = self.data_api.price_at_date(symbol, self.past_start_date)

                    current_price = history["Close"].values[0]
                    buy_price = history["Close"].values[-1]

                    data.append(
                        {
                            "stock": symbol,
                            **PerfDates.data_to_dict(
                                curr_date=self.current_date,
                                last_eval_date=self.last_evaluation_date,
                                future_start_date=self.future_start_date,
                                future_end_date=self.future_end_date,
                                past_start_date=self.past_start_date,
                                past_end_date=self.past_end_date,
                            ),
                            **PerfColumns.perf_columns_data_to_dict(
                                col_xy_price=past_price,
                                col_x_price=buy_price,
                                col_curr_price=current_price,
                                col_past_perf=past_cagr,
                                col_future_perf=future_cagr,
                            ),
                        }
                    )
                except Exception as e:
                    print(f"Error calculating CAGR for {symbol}: {e}")

        return pd.DataFrame(data).dropna()
