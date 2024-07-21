import concurrent.futures
import datetime
import itertools
from dataclasses import dataclass
from functools import cached_property as cached
from pathlib import Path

import pandas as pd

from stocks.data import StocksDataAPI
from stocks.portfolio import PortfolioAPI

PORTFOLIO_DIR = Path("stocks/data/portfolio")


@dataclass
class StockPortfolio:
    data: pd.DataFrame
    past_dates: tuple[datetime.date, datetime.date]
    future_dates: tuple[datetime.date, datetime.date]
    col_past_perf: str
    col_future_perf: str
    col_xy_price: str
    col_x_price: str
    col_current_price: str

    @property
    def _absolute_return_future(self):
        start_price = self.data[self.col_x_price].sum()
        end_price = self.data[self.col_current_price].sum()
        return_pct = (end_price - start_price) / start_price
        return return_pct * 100

    @property
    def _mean_cagr_future(self):
        return self.data[self.col_future_perf].mean()

    @property
    def _future_cagr(self) -> float | None:
        portfolio_api = PortfolioAPI()
        return portfolio_api.calculate_combined_cagr(
            self.data["stock"].values, self.future_dates[0], self.future_dates[1]
        )

    @property
    def _absolute_return_past(self):
        start_price = self.data[self.col_xy_price].sum()
        end_price = self.data[self.col_x_price].sum()
        return_pct = (end_price - start_price) / start_price
        return return_pct * 100

    @property
    def _mean_cagr_past(self):
        return self.data[self.col_past_perf].mean()

    @property
    def _past_cagr(self) -> float | None:
        portfolio_api = PortfolioAPI()
        return portfolio_api.calculate_combined_cagr(self.data["stock"].values, self.past_dates[0], self.past_dates[1])

    @property
    def analysis(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "absolute_return_past": [self._absolute_return_past],
                "absolute_return_future": [self._absolute_return_future],
                "mean_cagr_past": [self._mean_cagr_past],
                "mean_cagr_future": [self._mean_cagr_future],
                "future_cagr": [self._future_cagr],
                "past_cagr": [self._past_cagr],
                "sum_past_xy_price": [self.data[self.col_xy_price].sum()],
                "sum_past_x_price": [self.data[self.col_x_price].sum()],
                "sum_current_price": [self.data[self.col_current_price].sum()],
            },
            index=["Portfolio Analysis"],
        ).T

    @property
    def analysis_dict(self) -> dict:
        return list(self.analysis.to_dict().values())[0]


class StockPortfolioAnalyzer:
    def __init__(self, x: float, y: float, min_price: float = 0, max_price: float = 10**7, z: float = 0):
        self.x = x
        self.y = y
        self.min_price = min_price
        self.max_price = max_price

        self.portfolio_api = PortfolioAPI()
        self.data_api = StocksDataAPI()

        self.current_date = datetime.datetime.now().date()

        # current (future) performance dates (x years)
        self.future_performance_dates = (
            self.current_date - datetime.timedelta(days=int(365 * self.x)),
            self.current_date,
        )
        self.future_start_date, self.future_end_date = self.future_performance_dates

        # past performance dates (y years)
        self.past_performance_dates = (
            self.current_date - datetime.timedelta(days=int(365 * (self.x + self.y))),
            self.current_date - datetime.timedelta(days=int(365 * self.x)),
        )

        self.past_start_date, self.past_end_date = self.past_performance_dates

        # trunk-ignore(bandit/B101)
        assert (
            self.past_start_date <= self.past_end_date <= self.future_start_date <= self.future_end_date
        ), "Invalid date range"

        print(f"Past performance dates {self.past_start_date} to {self.past_end_date}")
        print(f"Future performance dates {self.future_start_date} to {self.future_end_date}")
        print(f"Analyzing data of last {self.x + self.y} years")

        # Performance dataframe (based on x and y)
        self.past_performance = pd.DataFrame()

        # column names
        self.COL_PAST_PERF = f"past_performance_cagr_{self.y}"
        self.COL_FUTURE_PERF = f"future_performance_cagr_{self.x}"
        self.COL_XY_PRICE = f"price_{self.x + self.y}_years_ago"
        self.COL_X_PRICE = f"price_{self.x}_years_ago"
        self.COL_CURR_PRICE = "price_current"

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

    def compute_past_future_returns(self) -> pd.DataFrame:
        """Compute past and future performance returns."""
        symbols = self.valid_symbols
        data = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_symbol = {executor.submit(self._calculate_cagr_for_symbol, symbol): symbol for symbol in symbols}
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]

                try:
                    result = future.result()
                    stock_symbol, past_cagr, future_cagr = result
                    history = self.data_api.price_history_by_dates(symbol, self.future_start_date, self.future_end_date)

                    past_price = self.data_api.price_at_date(symbol, self.past_start_date)

                    current_price = history["Close"].values[0]
                    buy_price = history["Close"].values[-1]

                    data.append(
                        {
                            "stock": stock_symbol,
                            self.COL_XY_PRICE: past_price,
                            self.COL_X_PRICE: buy_price,
                            self.COL_CURR_PRICE: current_price,
                            self.COL_PAST_PERF: past_cagr,
                            self.COL_FUTURE_PERF: future_cagr,
                        }
                    )
                except Exception as e:
                    print(f"Error calculating CAGR for {symbol}: {e}")

        self.past_performance = pd.DataFrame(data)

        return self.past_performance

    def _calculate_cagr_for_symbol(self, symbol: str) -> tuple[str, float | None, float | None]:
        past_cagr = self.portfolio_api.calculate_cagr(symbol, self.past_start_date, self.past_end_date)
        future_cagr = self.portfolio_api.calculate_cagr(symbol, self.future_start_date, self.future_end_date)
        return symbol, past_cagr, future_cagr

    def _filter_stocks(
        self, message_on_empty_data: str, past_perf_order_ascending: bool, future_perf_order_ascending: bool, N: int
    ):
        df = self.compute_past_future_returns() if self.past_performance.empty else self.past_performance
        df = df.dropna()

        # trunk-ignore(bandit/B101)
        assert len(df) > 0, message_on_empty_data

        selected_stocks = (
            df.sort_values(
                by=[self.COL_PAST_PERF, self.COL_FUTURE_PERF],
                ascending=[past_perf_order_ascending, future_perf_order_ascending],
            )
            .head(N)
            .reset_index(drop=True)
        )

        return StockPortfolio(
            data=selected_stocks,
            past_dates=self.past_performance_dates,
            future_dates=self.future_performance_dates,
            col_past_perf=self.COL_PAST_PERF,
            col_future_perf=self.COL_FUTURE_PERF,
            col_xy_price=self.COL_XY_PRICE,
            col_x_price=self.COL_X_PRICE,
            col_current_price=self.COL_CURR_PRICE,
        )

    ### Methods to get different types of stock portfolios

    def get_loosers_portfolio(self, N: int) -> StockPortfolio:
        """select N stocks that performed badly in y years and well in next x years."""

        return self._filter_stocks(
            message_on_empty_data="""Loosers' Stock is an empty dataframe. Something went wrong horribly.""",
            past_perf_order_ascending=True,
            future_perf_order_ascending=False,
            N=N,
        )

    def get_winners_portfolio(self, N: int) -> StockPortfolio:
        """select N stocks that performed well in y years and well in next x years."""

        return self._filter_stocks(
            message_on_empty_data="""Winners' Stock is an empty dataframe. Something went wrong horribly.""",
            past_perf_order_ascending=False,
            future_perf_order_ascending=False,
            N=N,
        )

    def get_penny_portfolio(self, N: int) -> StockPortfolio:
        """select N stocks filter by min and max price."""

        return self._filter_stocks(
            message_on_empty_data="""Penny Stock is an empty dataframe. Something went wrong horribly.""",
            past_perf_order_ascending=False,
            future_perf_order_ascending=False,
            N=N,
        )

    @classmethod
    def loosers_portfolio(cls, x, y, N=30) -> tuple["StockPortfolioAnalyzer", StockPortfolio]:
        finder = cls(x, y)
        port_folio = finder.get_loosers_portfolio(N)
        return finder, port_folio

    @classmethod
    def winners_portfolio(cls, x, y, N=30) -> tuple["StockPortfolioAnalyzer", StockPortfolio]:
        finder = cls(x, y)
        port_folio = finder.get_winners_portfolio(N)
        return finder, port_folio

    @classmethod
    def penny_portfolio(
        cls, x, y, min_price: float, max_price: float, N=30
    ) -> tuple["StockPortfolioAnalyzer", StockPortfolio]:
        finder = cls(x, y, min_price=min_price, max_price=max_price)
        port_folio = finder.get_penny_portfolio(N)
        return finder, port_folio

    @classmethod
    def find_loosers_optimal_x_y_N(cls, x_values: list, y_values: list, N_values: list) -> pd.DataFrame:
        """
        Find optimal values for x, y, and N by trying different combinations.

        Args:
        x_values (list): List of possible values for x.
        y_values (list): List of possible values for y.
        N_values (list): List of possible values for N.

        Returns:
        pd.DataFrame: Dataframe with all combinations and their performance metrics.
        """
        results = []

        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_combination = {
                executor.submit(cls._evaluate_combination, x, y, N_values, cls): (x, y)
                for x, y in itertools.product(x_values, y_values)
            }

            for future in concurrent.futures.as_completed(future_to_combination):
                result_x_y = future.result()
                results.extend(result_x_y)

        return pd.DataFrame(
            results,
        ).sort_values("future_cagr", ascending=False)

    @staticmethod
    def _evaluate_combination(
        x,
        y,
        N_values,
        cls,
    ):
        stock_finder = cls(x, y)
        stock_finder.compute_past_future_returns()
        local_results = []

        for N in N_values:
            try:
                loosers_port: StockPortfolio = stock_finder.get_loosers_portfolio(N)
                local_results.append(
                    {
                        "x": x,
                        "y": y,
                        "N": N,
                    }
                    | loosers_port.analysis_dict
                )
            except Exception as e:
                print(f"Failed for x={x}, y={y}, N={N}: {e}")

        return local_results


def save_loosers_portfolio():
    def _save_loosers_portolio(x, y, N, portfolio_name, portfolio_analysis_name):
        _, result = StockPortfolioAnalyzer.loosers_portfolio(x=x, y=y, N=N)
        result.data.to_csv(portfolio_name)
        result.analysis.to_csv(portfolio_analysis_name)

        return result

    # x_values = list(np.arange(0.5, 6, 0.5))
    # y_values = list(np.arange(0.5, 6, 0.5))
    # N_values = list(np.arange(10, 55, 5))

    # StockPortfolioAnalyzer.find_loosers_optimal_x_y_N(x_values, y_values, N_values)

    # Optimal Results: x = 1, y = 4, N = 30, Expected CAGR ~= 100%

    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

    PORTFOLIO_CURRENT_DIR = PORTFOLIO_DIR / "loosers_current"
    PORTFOLIO_CURRENT_DIR.mkdir(parents=True, exist_ok=True)

    PORTFOLIO_HISTORY_DIR = PORTFOLIO_DIR / "loosers_history"
    PORTFOLIO_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    _save_loosers_portolio(
        0.02,
        4,
        30,
        PORTFOLIO_CURRENT_DIR / "loosers_portfolio.csv",
        PORTFOLIO_CURRENT_DIR / "loosers_portfolio_analysis.csv",
    )

    _save_loosers_portolio(
        1,
        4,
        30,
        PORTFOLIO_HISTORY_DIR / "loosers_portfolio_history.csv",
        PORTFOLIO_HISTORY_DIR / "loosers_portfolio_analysis_history.csv",
    )


if __name__ == "__main__":
    save_loosers_portfolio()
