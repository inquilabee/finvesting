import datetime

from stocks.resource import StocksDataAPI


class PortfolioAPI:
    def __init__(self):
        self.data_api = StocksDataAPI()

    def calculate_cagr(self, symbol, from_date: datetime.date, to_date: datetime.date) -> float | None:
        df = self.data_api.price_history_by_dates(symbol, from_date, to_date)

        if df.empty:
            raise ValueError(f"No data available for {symbol} in the given date range {from_date} to {to_date}.")

        return self._calculate_cagr(df, "Close")

    def calculate_individual_cagr(self, symbols, from_date: datetime.date, to_date: datetime.date):
        cagr_values = {}
        for symbol in symbols:
            try:
                cagr_values[symbol] = self.calculate_cagr(symbol, from_date, to_date)
            except ValueError as e:
                print(e)
                cagr_values[symbol] = None

        return cagr_values

    def calculate_combined_cagr(self, symbols, from_date: datetime.date, to_date: datetime.date) -> float | None:
        df_list = []
        for symbol in symbols:
            df = self.data_api.price_history_by_dates(symbol, from_date, to_date)

            if not df.empty:
                df_list.append(df[["Date", "Close"]].rename(columns={"Close": symbol}))

        if not df_list:
            raise ValueError("No data available for the given symbols in the date range.")

        combined_df = df_list[0]
        for df in df_list[1:]:
            combined_df = combined_df.merge(df, on="Date", how="inner")

        combined_df["Total"] = combined_df[symbols].sum(axis=1)
        return self._calculate_cagr(combined_df, "Total")

    def _calculate_cagr(self, df, column) -> float | None:
        if len(df) <= 1:
            return

        try:
            start_price = df.iloc[0][column]
            end_price = df.iloc[-1][column]
            num_years: float = (df.iloc[-1]["Date"] - df.iloc[0]["Date"]).days / 365

            if (
                not isinstance(start_price, (int, float))
                or not isinstance(end_price, (int, float))
                or not isinstance(num_years, (int, float))
            ):
                raise ValueError(f"Invalid prices. {start_price=}, {end_price=}, {num_years=}")

            cagr = (end_price / start_price) ** (1 / num_years) - 1
            return cagr * 100
        except Exception as e:
            print(f"Something weird happened. {end_price=}, {start_price=}, {num_years=} Error={e}")

        return None


def main():
    portfolio_api = PortfolioAPI()

    symbols = ["RELIANCE", "TCS", "INFY"]
    from_date = datetime.datetime(2015, 1, 1).date()
    to_date = datetime.datetime(2020, 12, 31).date()

    portfolio_cagr = portfolio_api.calculate_individual_cagr(symbols, from_date, to_date)
    combined_cagr = portfolio_api.calculate_combined_cagr(symbols, from_date, to_date)

    print("Individual CAGR:", portfolio_cagr)
    print("Combined CAGR:", combined_cagr)


if __name__ == "__main__":
    main()
