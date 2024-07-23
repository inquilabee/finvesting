from pathlib import Path

import pandas as pd

from stocks.resource import StocksDataAPI


class SafeStocks:
    SAFE_STOCKS_DIR = Path("stocks/data/safe_stocks")

    def __init__(self):
        self.data_api = StocksDataAPI()
        self.stock_info = self.data_api.stock_info

    @property
    def df(self) -> pd.DataFrame:
        return self.stock_info

    def established_profitable_companies(
        self,
        max_market_rank=500,
        top_roa_threshold_pc=0.25,
        top_roe_threshold_pc=0.25,
        bottom_debt_to_equity_ratio=0.25,
    ) -> pd.DataFrame:
        """Focus on Established, Profitable Companies

        **Criteria:**

        *   **Market Capitalization**: Preferably large-cap stocks.
        *   **Profitability Ratios**: Positive and stable profit margins, operating margins, and gross margins.
        *   **Return Ratios**: High return on assets (ROA) and return on equity (ROE).
        *   **Debt Levels**: Low debt-to-equity ratio.
        *   **Dividend History**: Regular and stable dividends.

        **Reasoning:** Companies with strong liquidity ratios and ample cash reserves are better equipped to handle
        economic downturns and unforeseen expenses. Positive and growing free cash flow indicates that the company
        generates more cash than it spends, which can be used for reinvestment, paying dividends, or reducing debt.
        """

        columns = [
            "symbol",
            "name_of_company",
            "day_high",
            "market_cap",
            "profit_margins",
            "operating_margins",
            "gross_margins",
            "return_on_assets",
            "return_on_equity",
            "debt_to_equity",
            "ex_dividend_date",
            "last_dividend_value",
        ]

        return (
            self.df
            # Market Capitalization: Preferably large-cap stocks (manual segmentation needed)
            # Profitability Ratios: Positive and stable profit margins, operating margins, and gross margins
            .pipe(
                lambda df: df.query(
                    f"market_cap_rank < {max_market_rank} and profit_margins > 0 and operating_margins > 0 and gross_margins > 0"
                )
            )
            # Return Ratios: High return on assets (ROA) and return on equity (ROE)
            # Top top_roa_threshold_pc% ROA and Top top_roe_threshold_pc% ROE
            .pipe(
                lambda df: df.assign(
                    roa_threshold=df["return_on_assets"].quantile(1 - top_roa_threshold_pc),
                    roe_threshold=df["return_on_equity"].quantile(1 - top_roe_threshold_pc),
                )
            )
            .query("return_on_assets > roa_threshold and return_on_equity > roe_threshold")
            .pipe(lambda df: df.drop(columns=["roa_threshold", "roe_threshold"]))
            # Debt Levels: Low debt-to-equity ratio
            # Bottom bottom_debt_to_equity_ratio % debt-to-equity
            .pipe(
                lambda df: df.assign(
                    debt_to_equity_threshold=df["debt_to_equity"].quantile(bottom_debt_to_equity_ratio)
                )
            )
            .query("debt_to_equity < debt_to_equity_threshold")
            .drop(columns=["debt_to_equity_threshold"])
            # Dividend History: Regular and stable dividends
            .dropna(subset=["ex_dividend_date", "last_dividend_value"])
            .loc[:, columns]
        )

    def strong_financial_health_and_liquidity(
        self,
        min_quick_ratio=1,
        min_current_ratio=1,
        min_cash_to_debt_qn=0.8,
        min_free_cashflow=0,
        min_operating_cashflow=0,
    ):
        """Strong Financial Health and Liquidity

        **Criteria:**

        *   **Quick Ratio**: Greater than 1.
        *   **Current Ratio**: Greater than 1.
        *   **Total Cash and Cash Per Share**: High values relative to total debt.
        *   **Free Cashflow and Operating Cashflow**: Positive and growing.

        **Reasoning:** Companies with strong liquidity ratios and ample cash reserves are better equipped to handle
        economic downturns and unforeseen expenses. Positive and growing free cash flow indicates that the company
        generates more cash than it spends, which can be used for reinvestment, paying dividends, or reducing debt.
        """

        columns = [
            "symbol",
            "name_of_company",
            "day_high",
            "quick_ratio",
            "current_ratio",
            "total_cash",
            "total_cash_per_share",
            "total_debt",
            "free_cashflow",
            "operating_cashflow",
            "recommendation_key",
        ]

        df_final = (
            # Filtering criteria for strong financial health and liquidity
            self.df
            # Quick Ratio: Greater than 1
            .query(f"quick_ratio > {min_quick_ratio}")
            # Current Ratio: Greater than 1
            .query(f"current_ratio > {min_current_ratio}")
            # Total Cash and Cash Per Share: High values relative to total debt
            .pipe(
                lambda df: df.assign(
                    cash_to_debt_ratio=df["total_cash"] / df["total_debt"],
                    cash_to_debt_threshold=(df["total_cash"] / df["total_debt"]).quantile(min_cash_to_debt_qn),
                )
            )
            .query("cash_to_debt_ratio > cash_to_debt_threshold")
            .drop(columns=["cash_to_debt_ratio", "cash_to_debt_threshold"])
            # Free Cashflow and Operating Cashflow: Positive and growing
            .query(f"free_cashflow > {min_free_cashflow} and operating_cashflow > {min_operating_cashflow}")
        )

        # Assuming 'previous_free_cashflow' and 'previous_operating_cashflow' columns exist for growth calculation
        # Uncomment the following lines if historical data is available for comparison
        # df_cashflow_growth = df_final[
        #     (df_final["free_cashflow"] > df_final["previous_free_cashflow"])
        #     & (df_final["operating_cashflow"] > df_final["previous_operating_cashflow"])
        # ]

        # Display the filtered stocks
        return df_final.loc[:, columns].sort_values(by=["day_high"])

    def defensive_stocks(
        self,
        defensive_sectors=(
            "consumer-cyclical",
            "utilities",
            "healthcare",
            "consumer-defensive",
        ),
        closeness_to_52_week_low=0.30,
        max_beta=1,
        min_52_week_change=0,
    ):
        """Defensive Stocks

        **Criteria:**

        *   **Industry/Sector**: Companies in defensive sectors such as consumer staples, utilities, and healthcare.
        *   **Fifty-Two Week Low and High**: Stocks trading closer to their 52-week low may be undervalued.
        *   **Volatility**: Low historical volatility and a beta of less than 1.

        **Reasoning:** Defensive stocks are typically less sensitive to economic cycles and tend to perform well in both
        good and bad economic times. Investing in these sectors can provide a buffer against market downturns.
        Low volatility stocks are less likely to experience drastic price swings, making them safer investments.
        """
        df = self.df

        condition = (
            df["sector_key"].isin(defensive_sectors)
            & (
                df["current_price"]
                <= df["fifty_two_week_low"]
                + (df["fifty_two_week_high"] - df["fifty_two_week_low"]) * closeness_to_52_week_low
            )
            & (df["52_week_change"] > min_52_week_change)
            & (df["beta"] < max_beta)
        )

        return df[condition]

    def filter_stocks_for_consistent_growth(
        self,
        min_earnings_growth=0,
        min_revenue_growth=0,
        min_trailing_eps=0,
        max_beta=1,
    ) -> pd.DataFrame:
        """
        Filter stocks based on the criteria for consistent growth and earnings stability.

        Criteria:
        - Positive earnings growth over multiple quarters.
        - Consistent revenue growth.
        - Positive and increasing trailing EPS.
        - Low beta (less than 1).
        """
        df = self.df

        return df[
            (df["earnings_growth"] > min_earnings_growth)
            & (df["revenue_growth"] > min_revenue_growth)
            & (df["trailing_eps"] > min_trailing_eps)
            & (df["beta"] < max_beta)
        ]

    def divident_paying_stocks(self):
        """Dividend-Paying Stocks

        **Criteria:**

        *   **Dividend Yield**: Reasonable dividend yield (not too high, as that could indicate risk).
        *   **Payout Ratio**: Sustainable payout ratio (generally below 60%).
        *   **Dividend History**: Long history of paying and increasing dividends.
        *   **Ex-Dividend Date and Last Dividend Date**: Regular dividend payments.

        **Reasoning:** Dividend-paying stocks can provide a steady income stream, which can cushion against market volatility.
        Companies with a long history of dividend payments are often more financially stable. A sustainable payout ratio ensures
        that the company can continue to pay dividends without compromising its financial health.
        """
        # sourcery skip: inline-immediately-returned-variable
        df = self.df

        # Define criteria
        reasonable_dividend_yield = 0.03  # 3% dividend yield threshold
        # sustainable_payout_ratio = 0.6  # 60% payout ratio threshold

        dividend_stocks = df[
            (df["last_dividend_value"] > 0)  # Check if there is a dividend value
            & (df["last_dividend_value"] / df["current_price"] > reasonable_dividend_yield)  # Dividend yield check
            &
            # (df['payoutRatio'] < sustainable_payout_ratio) &  # Payout ratio check
            (df["ex_dividend_date"].notnull())  # Check for ex-dividend date
            & (df["last_dividend_date"].notnull())  # Check for last dividend date
        ]

        # Additional check for dividend history (optional, based on available data)
        # dividend_history = (
        #     dividend_stocks.groupby("symbol")
        #     .apply(lambda x: (x["lastDividendDate"].diff().min() > pd.Timedelta(days=30)))
        #     .reset_index()
        # )
        # dividend_history.columns = ["symbol", "LongDividendHistory"]

        # assert dividend_history["LongDividendHistory"].all(), "Dividend history is too short"

        # dividend_stocks = pd.merge(dividend_stocks, dividend_history, on="symbol")

        return dividend_stocks

    @classmethod
    def save(cls):
        safe_stocks = cls()

        cls.SAFE_STOCKS_DIR.mkdir(parents=True, exist_ok=True)

        df = safe_stocks.established_profitable_companies()
        df.to_csv(cls.SAFE_STOCKS_DIR / "established_profitable_companies.csv")

        df = safe_stocks.strong_financial_health_and_liquidity()
        df.to_csv(cls.SAFE_STOCKS_DIR / "strong_financial_health_and_liquidity.csv")

        df = safe_stocks.defensive_stocks()
        df.to_csv(cls.SAFE_STOCKS_DIR / "defensive_stocks.csv")

        df = safe_stocks.filter_stocks_for_consistent_growth()
        df.to_csv(cls.SAFE_STOCKS_DIR / "stocks_for_consistent_growth.csv")

        df = safe_stocks.divident_paying_stocks()
        df.to_csv(cls.SAFE_STOCKS_DIR / "divident_paying_stocks.csv")


if __name__ == "__main__":
    SafeStocks.save()
