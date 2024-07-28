import concurrent.futures
import itertools
from dataclasses import dataclass

import pandas as pd

from stocks.perf_analyzer import PORTFOLIO_DIR, THREAD_PROC_MAX_WORKERS, PerfColumns, PerfDates, StockPortfolioAnalyzer
from stocks.portfolio import PortfolioAPI


@dataclass
class StockPortfolio:
    data: pd.DataFrame

    def __post_init__(self):
        self.future_dates = (
            self.data[PerfDates.PERF_FUTURE_START_DATE].dt.date.values[0],
            self.data[PerfDates.PERF_FUTURE_END_DATE].dt.date.values[0],
        )
        self.past_dates = (
            self.data[PerfDates.PERF_PAST_START_DATE].dt.date.values[0],
            self.data[PerfDates.PERF_PAST_END_DATE].dt.date.values[0],
        )

        self.data.drop(
            columns=[
                PerfDates.PERF_CURRENT_DATE,
                PerfDates.PERF_LAST_EVAL_DATE,
                PerfDates.PERF_FUTURE_START_DATE,
                PerfDates.PERF_FUTURE_END_DATE,
                PerfDates.PERF_PAST_START_DATE,
                PerfDates.PERF_PAST_END_DATE,
            ],
            inplace=True,
        )

    @classmethod
    def analyze_from_file(
        cls,
        x,
        y,
        z,
        past_perf_ascending: bool = False,
        future_perf_ascending: bool = False,
        num_stocks: int = 30,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        file_path = StockPortfolioAnalyzer.perf_file_name(x, y, z)

        data = pd.read_csv(
            file_path,
            parse_dates=[
                PerfDates.PERF_CURRENT_DATE,
                PerfDates.PERF_LAST_EVAL_DATE,
                PerfDates.PERF_FUTURE_START_DATE,
                PerfDates.PERF_FUTURE_END_DATE,
                PerfDates.PERF_PAST_START_DATE,
                PerfDates.PERF_PAST_END_DATE,
            ],
        )

        selected_stock = data.sort_values(
            by=[PerfColumns.COL_PAST_PERF, PerfColumns.COL_FUTURE_PERF],
            ascending=[past_perf_ascending, future_perf_ascending],
        ).head(num_stocks)

        portfolio = cls(selected_stock)

        return selected_stock, portfolio.analysis

    @property
    def _absolute_return_future(self):
        start_price = self.data[PerfColumns.COL_X_PRICE].sum()
        end_price = self.data[PerfColumns.COL_CURR_PRICE].sum()
        return_pct = (end_price - start_price) / start_price
        return return_pct * 100

    @property
    def _future_cagr(self) -> float | None:
        portfolio_api = PortfolioAPI()
        return portfolio_api.calculate_combined_cagr(
            self.data["stock"].values, self.future_dates[0], self.future_dates[1]
        )

    @property
    def _absolute_return_past(self):
        start_price = self.data[PerfColumns.COL_XY_PRICE].sum()
        end_price = self.data[PerfColumns.COL_X_PRICE].sum()
        return_pct = (end_price - start_price) / start_price
        return return_pct * 100

    @property
    def _past_cagr(self) -> float | None:
        portfolio_api = PortfolioAPI()
        return portfolio_api.calculate_combined_cagr(self.data["stock"].values, self.past_dates[0], self.past_dates[1])

    @property
    def analysis(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                PerfDates.PERF_PAST_START_DATE: [self.past_dates[0]],
                PerfDates.PERF_PAST_END_DATE: [self.past_dates[1]],
                PerfDates.PERF_FUTURE_START_DATE: [self.future_dates[0]],
                PerfDates.PERF_FUTURE_END_DATE: [self.future_dates[1]],
                PerfColumns.COL_PAST_CAGR: [self._past_cagr],
                PerfColumns.COL_FUTURE_CAGR: [self._future_cagr],
                "absolute_return_past": [self._absolute_return_past],
                "absolute_return_future": [self._absolute_return_future],
                "sum_past_xy_price": [self.data[PerfColumns.COL_XY_PRICE].sum()],
                "sum_past_x_price": [self.data[PerfColumns.COL_X_PRICE].sum()],
                "sum_current_price": [self.data[PerfColumns.COL_CURR_PRICE].sum()],
            },
            index=["Portfolio Analysis"],
        ).T

    @property
    def analysis_dict(self) -> dict:
        return list(self.analysis.to_dict().values())[0]

    @classmethod
    def save_analysis(
        cls,
        x_values: list[float],
        y_values: list[float],
        z_values: list[float],
        past_perf_ascending: bool,
        future_perf_ascending: bool,
        num_stocks: int = 30,
    ):
        with concurrent.futures.ProcessPoolExecutor(max_workers=THREAD_PROC_MAX_WORKERS) as executor:
            future_to_combination = {
                executor.submit(
                    cls.analyze_from_file, x, y, z, past_perf_ascending, future_perf_ascending, num_stocks
                ): (x, y, z)
                for x, y, z in itertools.product(x_values, y_values, z_values)
            }

            for future in concurrent.futures.as_completed(future_to_combination):
                x, y, z = future_to_combination[future]
                port, port_analysis = future.result()

                ANALYSIS_DIR = PORTFOLIO_DIR / "contra" / f"{x}_{y}_{z}"

                ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

                port.to_csv(ANALYSIS_DIR / f"port_{x}_{y}_{z}.csv")
                port_analysis.to_csv(ANALYSIS_DIR / f"port_analysis_{x}_{y}_{z}.csv")


if __name__ == "__main__":
    x = 1.0
    y = 1.0
    z = 0.0
    past_perf_ascending = True
    future_perf_ascending = False
    num_stocks = 30

    portfolio, port_analysis = StockPortfolio.analyze_from_file(
        x, y, z, past_perf_ascending, future_perf_ascending, num_stocks
    )

    print(portfolio)
    print(port_analysis)
