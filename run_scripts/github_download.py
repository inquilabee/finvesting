from stocks.data import StocksDataAPI
from stocks.technical_analysis import StockDataAnalysis

# Base data
StocksDataAPI().download_data()

# Analyse data
stock_analysis = StockDataAnalysis()
stock_analysis.compute_technical_analysis()
stock_analysis.save()
