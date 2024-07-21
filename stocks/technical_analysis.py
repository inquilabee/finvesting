from pathlib import Path

import pandas as pd

from stocks.data import StocksDataAPI

data_api = StocksDataAPI()


class StockDataAnalysis:
    DATA_DIR = Path("stocks/data/analysed").resolve()

    def __init__(self, tickers: list[str] | None = None):
        self.tickers = tickers or data_api.history_symbols
        self._data: dict = {}

    def compute_technical_analysis(self):
        self._data = {ticker: self.technical_analysis(ticker) for ticker in self.tickers}

    @staticmethod
    def technical_analysis(symbol):
        data = data_api.price_history(symbol).sort_values("Date", ascending=True)

        # Tech Analysis Classes
        moving_averages = MovingAverages(data)
        rsi = RSI(data)
        macd = MACD(data)
        bollinger_bands = BollingerBands(data)
        volumne = VolumeAnalysis(data)
        support_resistance = SupportResistance(data)
        trend = TrendAnalysis(data)
        fib_retracement = FibonacciRetracement(data)

        # Calculate Technical Indicators
        moving_averages.calculate_sma(50)
        moving_averages.calculate_ema(50)
        rsi.calculate_rsi()
        macd.calculate_macd()
        bollinger_bands.calculate_bollinger_bands()
        volumne.calculate_volume_moving_average()
        support_resistance.calculate_support_resistance()
        trend.calculate_trend()
        fib_retracement.calculate_fibonacci_retracement()

        return data.sort_values("Date", ascending=False)

    def get_analysed_data(self, symbol: str) -> pd.DataFrame:
        return pd.read_csv(self.DATA_DIR / f"{symbol}.csv")

    def save_analysed_data(self, symbol: str):
        data = self.technical_analysis(symbol)
        data.to_csv(self.DATA_DIR / f"{symbol}.csv")

    def save(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

        for ticker, df in self._data.items():
            df.to_csv(self.DATA_DIR / f"{ticker}.csv")

    @classmethod
    def compuute_and_save(cls):
        analysis = cls()
        analysis.compute_technical_analysis()
        analysis.save()


class MovingAverages:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_sma(self, window):
        df = self.stock_data
        df[f"SMA_{window}"] = df["Close"].rolling(window=window).mean()

    def calculate_ema(self, window):
        df = self.stock_data
        df[f"EMA_{window}"] = df["Close"].ewm(span=window, adjust=False).mean()


class RSI:
    def __init__(self, data):
        self.data = data

    def calculate_rsi(self, window=14):
        delta = self.data["Close"].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window, min_periods=1).mean()
        avg_loss = loss.rolling(window=window, min_periods=1).mean()
        rs = avg_gain / avg_loss
        self.data["RSI"] = 100 - (100 / (1 + rs))


class MACD:
    def __init__(self, data):
        self.data = data

    def calculate_macd(self):
        df = self.data
        df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = df["EMA_12"] - df["EMA_26"]
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()


class BollingerBands:
    def __init__(self, data):
        self.data = data

    def calculate_bollinger_bands(self, window=20, num_std_dev=2):
        df = self.data
        df["SMA"] = df["Close"].rolling(window=window).mean()
        df["STD_DEV"] = df["Close"].rolling(window=window).std()
        df["Upper_Band"] = df["SMA"] + (df["STD_DEV"] * num_std_dev)
        df["Lower_Band"] = df["SMA"] - (df["STD_DEV"] * num_std_dev)


class VolumeAnalysis:
    def __init__(self, data):
        self.stock_data = data

    def calculate_volume_moving_average(self, window=20):
        df = self.stock_data
        df[f"Volume_MA_{window}"] = df["Volume"].rolling(window=window).mean()


class SupportResistance:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_support_resistance(self):
        df = self.stock_data
        df["Support"] = df["Close"].rolling(window=20).min()
        df["Resistance"] = df["Close"].rolling(window=20).max()


class TrendAnalysis:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_trend(self, window=20):
        df = self.stock_data
        df["Trend"] = df["Close"].rolling(window=window).mean().diff()


class FibonacciRetracement:
    def __init__(self, data):
        self.stock_data = data
        self.levels = self.calculate_fibonacci_retracement()

    def calculate_fibonacci_retracement(self):
        df = self.stock_data
        max_price = df["Close"].max()
        min_price = df["Close"].min()
        diff = max_price - min_price

        return {
            "Fib_23.6%": max_price - diff * 0.236,
            "Fib_38.2%": max_price - diff * 0.382,
            "Fib_50%": max_price - diff * 0.5,
            "Fib_61.8%": max_price - diff * 0.618,
            "Fib_78.6%": max_price - diff * 0.786,
        }

    def get_support_resistance_level(self):
        df = self.stock_data
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


class CandlestickPatterns:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def calculate_candlestick_patterns(self):
        # Placeholder for candlestick pattern detection
        pass


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
        df = self.stock_data
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


if __name__ == "__main__":
    stock_data = StockDataAnalysis()
    stock_data.compute_technical_analysis()

    stock_data.save()
