import investpy
import matplotlib.pyplot as plt
import yfinance as yf


class StockData:
    def __init__(self, tickers, start_date, end_date):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.indices = self._get_indices()
        self.data = self._get_stock_data()
        self.fundamentals = self._get_fundamental_data()
        self.moving_averages = MovingAverages(self.data)
        self.rsi = RSI(self.data)
        self.macd = MACD(self.data)
        self.bollinger_bands = BollingerBands(self.data)
        self.volumne = VolumeAnalysis(self.data)
        self.support_resistance = SupportResistance(self.data)
        self.trend = TrendAnalysis(self.data)
        self.fib_retracement = FibonacciRetracement(self.data)
        self.plotter = StockPlotter(self.data)

    def _get_stock_data(self):
        return {
            ticker: yf.download(
                ticker,
                start=self.start_date,
                end=self.end_date,
                actions=True,
                auto_adjust=True,
            )
            for ticker in self.tickers
        }

    def _get_fundamental_data(self):
        fundamental_data = {}
        for ticker in self.tickers:
            ticker_info = yf.Ticker(ticker).info
            fundamental_data[ticker] = ticker_info
        return fundamental_data

    def _get_indices(self):
        return investpy.indices.get_indices(country="India")

    def technical_analysis(self):
        self.moving_averages.calculate_sma(50)
        self.moving_averages.calculate_ema(50)
        self.rsi.calculate_rsi()
        self.macd.calculate_macd()
        self.bollinger_bands.calculate_bollinger_bands()
        self.volumne.calculate_volume_moving_average()
        self.support_resistance.calculate_support_resistance()
        self.trend.calculate_trend()
        self.fib_retracement.calculate_fibonacci_retracement()


class MovingAverages:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_sma(self, window):
        for ticker, df in self.stock_data.items():
            df[f"SMA_{window}"] = df["Close"].rolling(window=window).mean()

    def calculate_ema(self, window):
        for ticker, df in self.stock_data.items():
            df[f"EMA_{window}"] = df["Close"].ewm(span=window, adjust=False).mean()


class RSI:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_rsi(self, window=14):
        for ticker, df in self.stock_data.items():
            delta = df["Close"].diff(1)
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=window, min_periods=1).mean()
            avg_loss = loss.rolling(window=window, min_periods=1).mean()
            rs = avg_gain / avg_loss
            df["RSI"] = 100 - (100 / (1 + rs))


class MACD:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_macd(self):
        for ticker, df in self.stock_data.items():
            df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
            df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = df["EMA_12"] - df["EMA_26"]
            df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()


class BollingerBands:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_bollinger_bands(self, window=20, num_std_dev=2):
        for ticker, df in self.stock_data.items():
            df["SMA"] = df["Close"].rolling(window=window).mean()
            df["STD_DEV"] = df["Close"].rolling(window=window).std()
            df["Upper_Band"] = df["SMA"] + (df["STD_DEV"] * num_std_dev)
            df["Lower_Band"] = df["SMA"] - (df["STD_DEV"] * num_std_dev)


class VolumeAnalysis:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_volume_moving_average(self, window=20):
        for ticker, df in self.stock_data.items():
            df[f"Volume_MA_{window}"] = df["Volume"].rolling(window=window).mean()


class SupportResistance:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_support_resistance(self):
        for ticker, df in self.stock_data.items():
            df["Support"] = df["Close"].rolling(window=20).min()
            df["Resistance"] = df["Close"].rolling(window=20).max()


class TrendAnalysis:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_trend(self, window=20):
        for ticker, df in self.stock_data.items():
            df["Trend"] = df["Close"].rolling(window=window).mean().diff()


class CandlestickPatterns:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_candlestick_patterns(self):
        # Placeholder for candlestick pattern detection
        pass


class FibonacciRetracement:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_fibonacci_retracement(self):
        for ticker, df in self.stock_data.items():
            max_price = df["Close"].max()
            min_price = df["Close"].min()
            diff = max_price - min_price
            levels = {
                "Fib_23.6%": max_price - diff * 0.236,
                "Fib_38.2%": max_price - diff * 0.382,
                "Fib_50%": max_price - diff * 0.5,
                "Fib_61.8%": max_price - diff * 0.618,
                "Fib_78.6%": max_price - diff * 0.786,
            }
            for level, value in levels.items():
                df[level] = value

            df["Support_Resistance"] = df.apply(self.identify_support_resistance, axis=1, levels=levels)

    @staticmethod
    def identify_support_resistance(row, levels):
        for level, value in levels.items():
            if abs(row["Close"] - value) / value < 0.01:  # within 1% of the level
                if row["Close"] > value:
                    return f"Resistance at {level}"
                else:
                    return f"Support at {level}"
        return "No significant support or resistance"

    def get_support_resistance_level(self):
        for ticker, df in self.stock_data.items():
            max_price = df["Close"].max()
            min_price = df["Close"].min()
            diff = max_price - min_price

            levels = {
                "Fib_23.6%": max_price - diff * 0.236,
                "Fib_38.2%": max_price - diff * 0.382,
                "Fib_50%": max_price - diff * 0.5,
                "Fib_61.8%": max_price - diff * 0.618,
                "Fib_78.6%": max_price - diff * 0.786,
            }

            supports = [(level, value, (df["Close"] > value).mean() * 100) for level, value in levels.items()]
            resistance = [(level, value, (df["Close"] < value).mean() * 100) for level, value in levels.items()]

            return supports, resistance


class BetaAnalysis:
    def __init__(self, stock_data, market_data):
        self.stock_data = stock_data
        self.market_data = market_data

    def calculate_beta(self):
        for ticker, df in self.stock_data.items():
            df["Daily_Return"] = df["Close"].pct_change()
            market_return = self.market_data["Close"].pct_change()
            covariance = df["Daily_Return"].cov(market_return)
            variance = market_return.var()
            df["Beta"] = covariance / variance


class SectorAnalysis:
    def __init__(self, stock_data, sector_data):
        self.stock_data = stock_data
        self.sector_data = sector_data

    def calculate_sector_performance(self):
        for sector, df in self.sector_data.items():
            df["Sector_Performance"] = df["Close"].pct_change()


class DividendAnalysis:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_dividend_yield(self):
        for ticker, df in self.stock_data.items():
            df["Dividend_Yield"] = df["Dividends"] / df["Close"]


class GrowthAnalysis:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_growth_rates(self):
        for ticker, df in self.stock_data.items():
            df["Revenue_Growth"] = df["Total_Revenue"].pct_change()
            df["Earnings_Growth"] = df["Net_Income"].pct_change()


class StockPlotter:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def plot_moving_averages(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Close"], label="Close Price")
        for col in df.columns:
            if "SMA" in col or "EMA" in col:
                plt.plot(df[col], label=col)
        plt.title(f"{ticker} Moving Averages")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    def plot_rsi(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["RSI"], label="RSI")
        plt.axhline(70, color="r", linestyle="--")
        plt.axhline(30, color="g", linestyle="--")
        plt.title(f"{ticker} Relative Strength Index (RSI)")
        plt.xlabel("Date")
        plt.ylabel("RSI")
        plt.legend()
        plt.show()

    def plot_macd(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["MACD"], label="MACD")
        plt.plot(df["Signal_Line"], label="Signal Line")
        plt.title(f"{ticker} MACD")
        plt.xlabel("Date")
        plt.ylabel("Value")
        plt.legend()
        plt.show()

    def plot_bollinger_bands(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Close"], label="Close Price")
        plt.plot(df["Upper_Band"], label="Upper Bollinger Band", linestyle="--")
        plt.plot(df["Lower_Band"], label="Lower Bollinger Band", linestyle="--")
        plt.fill_between(df.index, df["Upper_Band"], df["Lower_Band"], alpha=0.2)
        plt.title(f"{ticker} Bollinger Bands")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    def plot_volume(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Volume"], label="Volume")
        plt.plot(df["Volume_MA_20"], label="Volume Moving Average (20)")
        plt.title(f"{ticker} Volume Analysis")
        plt.xlabel("Date")
        plt.ylabel("Volume")
        plt.legend()
        plt.show()

    def plot_support_resistance(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Close"], label="Close Price")
        plt.plot(df["Support"], label="Support", linestyle="--")
        plt.plot(df["Resistance"], label="Resistance", linestyle="--")
        plt.title(f"{ticker} Support and Resistance Levels")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    def plot_trend(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Close"], label="Close Price")
        plt.plot(df["Trend"], label="Trend", linestyle="--")
        plt.title(f"{ticker} Trend Analysis")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    def plot_fibonacci_retracement(self, ticker):
        df = self.stock_data[ticker]
        max_price = df["Close"].max()
        min_price = df["Close"].min()
        diff = max_price - min_price
        levels = [max_price - diff * ratio for ratio in [0.236, 0.382, 0.5, 0.618, 0.786]]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Close"], label="Close Price")
        for level in levels:
            plt.axhline(level, linestyle="--")
        plt.title(f"{ticker} Fibonacci Retracement")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    def plot_candlestick_patterns(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Close"], label="Close Price")
        plt.title(f"{ticker} Candlestick Patterns")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    def plot_beta(self, ticker, market_data):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Beta"], label="Beta")
        plt.title(f"{ticker} Beta Analysis")
        plt.xlabel("Date")
        plt.ylabel("Beta")
        plt.legend()
        plt.show()

    def plot_sector_performance(self, sector, sector_data):
        df = sector_data[sector]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Sector_Performance"], label="Sector Performance")
        plt.title(f"{sector} Sector Performance")
        plt.xlabel("Date")
        plt.ylabel("Performance")
        plt.legend()
        plt.show()

    def plot_dividend_yield(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Dividend_Yield"], label="Dividend Yield")
        plt.title(f"{ticker} Dividend Yield")
        plt.xlabel("Date")
        plt.ylabel("Yield")
        plt.legend()
        plt.show()

    def plot_growth_rates(self, ticker):
        df = self.stock_data[ticker]
        plt.figure(figsize=(14, 7))
        plt.plot(df["Revenue_Growth"], label="Revenue Growth")
        plt.plot(df["Earnings_Growth"], label="Earnings Growth")
        plt.title(f"{ticker} Growth Rates")
        plt.xlabel("Date")
        plt.ylabel("Growth Rate")
        plt.legend()
        plt.show()


if __name__ == "__main__":
    # Example usage:
    tickers = ["RELIANCE.NS", "TCS.NS"]
    start_date = "2020-01-01"
    end_date = "2023-01-01"

    # Initialize and fetch stock data
    stock_data = StockData(tickers, start_date, end_date)
    market_data = yf.download("^NSEI", start=start_date, end=end_date)
    sector_data = {"Technology": yf.download("^CNXIT", start=start_date, end=end_date)}

    stock_data.technical_analysis()

    candlestick_patterns = CandlestickPatterns(stock_data)
    candlestick_patterns.calculate_candlestick_patterns()

    fibonacci = FibonacciRetracement(stock_data)
    fibonacci.calculate_fibonacci_retracement()

    beta_analysis = BetaAnalysis(stock_data, market_data)
    beta_analysis.calculate_beta()

    sector_analysis = SectorAnalysis(stock_data, sector_data)
    sector_analysis.calculate_sector_performance()

    # dividend_analysis = DividendAnalysis(stock_data)
    # dividend_analysis.calculate_dividend_yield()

    # growth_analysis = GrowthAnalysis(stock_data)
    # growth_analysis.calculate_growth_rates()

    # Plot results
    stock_data.plotter.plot_moving_averages("RELIANCE.NS")
    stock_data.plotter.plot_rsi("RELIANCE.NS")
    stock_data.plotter.plot_macd("RELIANCE.NS")
    stock_data.plotter.plot_bollinger_bands("RELIANCE.NS")
    stock_data.plotter.plot_volume("RELIANCE.NS")
    stock_data.plotter.plot_support_resistance("RELIANCE.NS")
    stock_data.plotter.plot_trend("RELIANCE.NS")
    stock_data.plotter.plot_fibonacci_retracement("RELIANCE.NS")
    stock_data.plotter.plot_candlestick_patterns("RELIANCE.NS")
    stock_data.plotter.plot_beta("RELIANCE.NS", market_data)
    stock_data.plotter.plot_sector_performance("Technology", sector_data)
    # plotter.plot_dividend_yield("RELIANCE.NS")
    # plotter.plot_growth_rates("RELIANCE.NS")
