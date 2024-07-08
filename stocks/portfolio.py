from datetime import datetime

from stocks.data import StocksDataAPI


class PortfolioAPI:
    def __init__(self, data_api):
        self.data_api = data_api

    def calculate_cagr(self, symbol, from_date, to_date):
        df = self.data_api.price_history(symbol)
        df["Date"] = df["Date"].dt.date
        df = df[(df["Date"] >= from_date) & (df["Date"] <= to_date)]

        if df.empty:
            raise ValueError(f"No data available for {symbol} in the given date range.")

        return self._calculate_cagr(df, "Close")

    def calculate_portfolio_cagr(self, symbols, from_date, to_date):
        cagr_values = {}
        for symbol in symbols:
            try:
                cagr_values[symbol] = self.calculate_cagr(symbol, from_date, to_date)
            except ValueError as e:
                print(e)
                cagr_values[symbol] = None

        return cagr_values

    def calculate_combined_cagr(self, symbols, from_date, to_date):
        df_list = []
        for symbol in symbols:
            df = self.data_api.price_history(symbol)
            df["Date"] = df["Date"].dt.date
            df = df[(df["Date"] >= from_date) & (df["Date"] <= to_date)]
            if not df.empty:
                df_list.append(df[["Date", "Close"]].rename(columns={"Close": symbol}))

        if not df_list:
            raise ValueError(
                "No data available for the given symbols in the date range."
            )

        combined_df = df_list[0]
        for df in df_list[1:]:
            combined_df = combined_df.merge(df, on="Date", how="inner")

        combined_df["Total"] = combined_df[symbols].sum(axis=1)
        return self._calculate_cagr(combined_df, "Total")

    def _calculate_cagr(self, df, column):
        start_price = df.iloc[0][column]
        end_price = df.iloc[-1][column]
        num_years = (df.iloc[-1]["Date"] - df.iloc[0]["Date"]).days / 365.25
        return (end_price / start_price) ** (1 / num_years) - 1


def main():
    data_api = StocksDataAPI()
    portfolio_api = PortfolioAPI(data_api)

    symbols = ["RELIANCE", "TCS", "INFY"]
    from_date = datetime(2015, 1, 1).date()
    to_date = datetime(2020, 12, 31).date()

    portfolio_cagr = portfolio_api.calculate_portfolio_cagr(symbols, from_date, to_date)
    combined_cagr = portfolio_api.calculate_combined_cagr(symbols, from_date, to_date)

    print("Individual CAGR:", portfolio_cagr)
    print("Combined CAGR:", combined_cagr)


if __name__ == "__main__":
    main()
