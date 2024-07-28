import numpy as np

from stocks import contra_stocks, perf_analyzer

x_values = list(np.arange(1, 6, 0.5))
y_values = list(np.arange(1, 6, 0.5))
z_values = list(np.arange(0, 6, 0.5))

perf_analyzer.StockPortfolioAnalyzer.save_perf_combinations(x_values, y_values, z_values)

contra_stocks.StockPortfolio.save_analysis(
    x_values=x_values,
    y_values=y_values,
    z_values=z_values,
    past_perf_ascending=True,
    future_perf_ascending=False,
    num_stocks=30,
)
