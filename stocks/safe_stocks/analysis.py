import pandas as pd


class SafeStocks:
    def __init__(self, stock_path) -> None:
        self.stock_path = stock_path

    @property
    def df(self) -> pd.DataFrame:
        return pd.read_csv(self.stock_path)

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

        **Reasoning:** Companies with strong liquidity ratios and ample cash reserves are better equipped to handle economic downturns and unforeseen expenses. Positive and growing free cash flow indicates that the company generates more cash than it spends, which can be used for reinvestment, paying dividends, or reducing debt.

        Args:
            df (_type_): _description_
            max_market_rank (int, optional): _description_. Defaults to 500.
            top_roa_threshold_pc (float, optional): _description_. Defaults to 0.25.
            top_roe_threshold_pc (float, optional): _description_. Defaults to 0.25.
            bottom_debt_to_equity_ratio (float, optional): _description_. Defaults to 0.25.

        Returns:
            pd.DataFrame: Recommnded stocks
        """
        # Market Capitalization: Preferably large-cap stocks (manual segmentation needed)

        df_large_cap = self.df.query(f"market_cap_rank < {max_market_rank}")

        # Profitability Ratios: Positive and stable profit margins, operating margins, and gross margins
        df_profitable = df_large_cap.query("profit_margins > 0 and operating_margins > 0 and gross_margins > 0")

        # Return Ratios: High return on assets (ROA) and return on equity (ROE)
        # Top top_roa_threshold_pc% ROA and Top top_roe_threshold_pc% ROE
        roa_threshold = df_profitable["return_on_assets"].quantile(1 - top_roa_threshold_pc)
        roe_threshold = df_profitable["return_on_equity"].quantile(1 - top_roe_threshold_pc)

        df_high_return = df_profitable.query(
            f"return_on_assets > {roa_threshold} and return_on_equity > {roe_threshold}"
        )

        # Debt Levels: Low debt-to-equity ratio
        # Bottom bottom_debt_to_equity_ratio % debt-to-equity
        debt_to_equity_threshold = df_high_return["debt_to_equity"].quantile(bottom_debt_to_equity_ratio)

        df_low_debt = df_high_return.query(f"debt_to_equity < {debt_to_equity_threshold}")

        # Dividend History: Regular and stable dividends
        df_dividends = df_low_debt.dropna(subset=["ex_dividend_date", "last_dividend_value"])

        # Final filtered dataframe
        df_filtered = df_dividends

        return df_filtered[
            [
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
        ]

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

        **Reasoning:** Companies with strong liquidity ratios and ample cash reserves are better equipped to handle economic downturns and unforeseen expenses. Positive and growing free cash flow indicates that the company generates more cash than it spends, which can be used for reinvestment, paying dividends, or reducing debt.

            Args:
                df (_type_): _description_
                min_quick_ratio (int, optional): _description_. Defaults to 1.
                min_current_ratio (int, optional): _description_. Defaults to 1.
                min_cash_to_debt_qn (float, optional): _description_. Defaults to 0.8.
                min_free_cashflow (int, optional): _description_. Defaults to 0.
                min_operating_cashflow (int, optional): _description_. Defaults to 0.

            Returns:
                _type_: _description_
        """
        # Filtering criteria for strong financial health and liquidity

        # Quick Ratio: Greater than 1
        df_quick_ratio = self.df.query(f"quick_ratio > {min_quick_ratio}")

        # Current Ratio: Greater than 1
        df_current_ratio = df_quick_ratio.query(f"current_ratio > {min_current_ratio}")

        # Total Cash and Cash Per Share: High values relative to total debt

        cash_to_debt_threshold = (df_current_ratio["total_cash"] / df_current_ratio["total_debt"]).quantile(
            min_cash_to_debt_qn
        )

        df_cash = df_current_ratio[
            (df_current_ratio["total_cash"] / df_current_ratio["total_debt"]) > cash_to_debt_threshold
        ]

        # Free Cashflow and Operating Cashflow: Positive and growing
        df_cashflow = df_cash.query(
            f"free_cashflow > {min_free_cashflow} and operating_cashflow > {min_operating_cashflow}"
        )

        # Assuming 'previous_free_cashflow' and 'previous_operating_cashflow' columns exist for growth calculation
        # Uncomment the following lines if historical data is available for comparison
        # df_cashflow_growth = df_cashflow[
        #     (df_cashflow['free_cashflow'] > df_cashflow['previous_free_cashflow']) &
        #     (df_cashflow['operating_cashflow'] > df_cashflow['previous_operating_cashflow'])
        # ]

        # Display the filtered stocks
        return df_cashflow[
            [
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
        ].sort_values(by=["day_high"])

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

        **Reasoning:** Defensive stocks are typically less sensitive to economic cycles and tend to perform well in both good and bad economic times. Investing in these sectors can provide a buffer against market downturns. Low volatility stocks are less likely to experience drastic price swings, making them safer investments.

            Args:
                df (_type_): _description_
                defensive_sectors (tuple, optional): _description_. Defaults to ( "consumer-cyclical", "utilities", "healthcare", "consumer-defensive", ).
                closeness_to_52_week_low (float, optional): _description_. Defaults to 0.30.
                max_beta (int, optional): _description_. Defaults to 1.
                min_52_week_change (int, optional): _description_. Defaults to 0.

            Returns:
                _type_: _description_
        """
        df = self.df

        return df[
            (df["sector_key"].isin(defensive_sectors))
            & (
                df["current_price"]
                <= df["fifty_two_week_low"]
                + (df["fifty_two_week_high"] - df["fifty_two_week_low"]) * closeness_to_52_week_low
            )
            & (df["52_week_change"] > min_52_week_change)
            & (df["beta"] < max_beta)
        ]

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

        Parameters:
        df (pd.DataFrame): DataFrame containing stock data.

        Returns:
        pd.DataFrame: Filtered DataFrame.
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

        **Reasoning:** Dividend-paying stocks can provide a steady income stream, which can cushion against market volatility. Companies with a long history of dividend payments are often more financially stable. A sustainable payout ratio ensures that the company can continue to pay dividends without compromising its financial health.

            Args:
                df (_type_): _description_

            Returns:
                _type_: _description_

            Yields:
                _type_: _description_
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

        # # Additional check for dividend history (optional, based on available data)
        # dividend_history = dividend_stocks.groupby('symbol').apply(lambda x: (x['lastDividendDate'].diff().min() > pd.Timedelta(days=30))).reset_index()
        # dividend_history.columns = ['symbol', 'LongDividendHistory']
        # dividend_stocks = pd.merge(dividend_stocks, dividend_history, on='symbol')

        return dividend_stocks


if __name__ == "__main__":
    safe_stocks = SafeStocks(stock_path="stocks/data/base/all_stocks.csv")

    print(safe_stocks.established_profitable_companies())
