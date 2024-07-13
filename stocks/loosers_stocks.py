import concurrent.futures
import itertools
from datetime import datetime, timedelta

import pandas as pd

from stocks.data import StocksDataAPI
from stocks.portfolio import PortfolioAPI


class LoosersStock:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

        self.portfolio_api = PortfolioAPI()
        self.stocks_data_api = StocksDataAPI()

        self.current_date = datetime.now().date()

        # current (future) performance dates (x years)
        self.future_start_date = self.current_date - timedelta(days=int(365 * x))
        self.future_end_date = self.current_date

        # past performance dates (y years)
        self.past_end_date = self.future_start_date
        self.past_start_date = self.past_end_date - timedelta(days=int(365 * y))

        # Performance dataframe (based on x and y)
        self.past_performance = pd.DataFrame()

    def compute_past_future_returns(self) -> pd.DataFrame:
        """Compute past and future performance returns."""
        symbols = self.stocks_data_api.symbols
        data = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_symbol = {
                executor.submit(self._calculate_cagr_for_symbol, symbol): symbol
                for symbol in symbols
            }
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    data.append(result)
                except Exception as e:
                    print(f"Error calculating CAGR for {symbol}: {e}")

        self.past_performance = pd.DataFrame(
            data,
            columns=[
                "stock",
                f"past_performance_{self.y}",
                f"future_performance_{self.x}",
            ],
        )

        return self.past_performance

    def _calculate_cagr_for_symbol(self, symbol: str):
        past_cagr = self.portfolio_api.calculate_cagr(
            symbol, self.past_start_date, self.past_end_date
        )
        future_cagr = self.portfolio_api.calculate_cagr(
            symbol, self.future_start_date, self.future_end_date
        )
        return [symbol, past_cagr, future_cagr]

    def get_loosers_stocks(self, N: int) -> tuple[pd.DataFrame, float, float]:
        """Use compute_past_future_returns to select N stocks that performed badly in y years and well in next years.

        Calculate the aggregated CAGR of the chosen N stocks in the last x years.
        """
        df = (
            self.compute_past_future_returns()
            if self.past_performance.empty
            else self.past_performance
        )
        df = df.dropna()

        # Select N stocks which performed badly in the past y years and well in the future x years
        # TODO: query further: past < 0, future > 0 and past < future and so on.
        selected_stocks = df.sort_values(
            by=[f"past_performance_{self.y}", f"future_performance_{self.x}"],
            ascending=[True, False],
        ).head(N)

        # Calculate the aggregated CAGR for the chosen N stocks
        aggregated_cagr_future = selected_stocks[f"future_performance_{self.x}"].mean()
        aggregated_cagr_past = selected_stocks[f"past_performance_{self.y}"].mean()

        return selected_stocks, aggregated_cagr_past, aggregated_cagr_future

    @classmethod
    def find_optimal_x_y_N(
        cls, x_values: list, y_values: list, N_values: list
    ) -> pd.DataFrame:
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

        def evaluate_combination(x, y):
            stock_finder = cls(x, y)
            stock_finder.compute_past_future_returns()
            for N in N_values:
                try:
                    _, aggregated_cagr_past, aggregated_cagr_future = (
                        stock_finder.get_loosers_stocks(N)
                    )
                    results.append(
                        (x, y, N, aggregated_cagr_past, aggregated_cagr_future)
                    )
                except Exception as e:
                    print(f"Failed for x={x}, y={y}, N={N}: {e}")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_combination = {
                executor.submit(evaluate_combination, x, y): (x, y)
                for x, y in itertools.product(x_values, y_values)
            }
            for future in concurrent.futures.as_completed(future_to_combination):
                future.result()

        return pd.DataFrame(
            results,
            columns=["x", "y", "N", "aggregated_cagr_past", "aggregated_cagr_future"],
        ).sort_values(by="aggregated_cagr_future", ascending=False)


def main():
    x_values = [1, 2, 3]
    y_values = [1, 2, 3]
    N_values = list(range(1, 10))

    df = LoosersStock.find_optimal_x_y_N(x_values, y_values, N_values)
    df.to_csv("optimization_results.csv", index=False)
    print("Optimization results saved to 'optimization_results.csv'.")


if __name__ == "__main__":
    N = 30
    x = 2
    y = 3

    stock_finder = LoosersStock(x, y)

    selected_stocks, aggregated_cagr_past, aggregated_cagr_future = (
        stock_finder.get_loosers_stocks(N)
    )
