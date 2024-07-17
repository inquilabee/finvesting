from stocks import perf_analyzer
from stocks.data import StocksDataAPI
from stocks.safe_stocks import SafeStocks
from stocks.technical_analysis import StockDataAnalysis

# Base data
StocksDataAPI().download_data()

# Analyse data
StockDataAnalysis.compuute_and_save()

# Safe Stocks
SafeStocks.save()

# Loosers' Portfolio
perf_analyzer.save_loosers_portfolio()
