from stocks.resource import StocksDataAPI
from stocks.safe_stocks import SafeStocks
from stocks.technical_analysis import StockDataAnalysis

StocksDataAPI().download_data()

task_list = [StockDataAnalysis.compute_and_save, SafeStocks.save]

for task in task_list:
    try:
        task()
    except Exception as e:
        print(f"Error in task {task}: {e}")
