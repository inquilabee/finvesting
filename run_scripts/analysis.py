import numpy as np

from stocks import perf_analyzer

x_values = list(np.arange(1, 6, 0.5))
y_values = list(np.arange(1, 6, 0.5))
z_values = list(np.arange(0, 6, 0.5))

perf_analyzer.StockPortfolioAnalyzer.save_perf_combinations(x_values, y_values, z_values)
