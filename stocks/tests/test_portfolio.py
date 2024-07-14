from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

from stocks.portfolio import PortfolioAPI


@pytest.fixture
def portfolio():
    return PortfolioAPI()


@pytest.mark.parametrize(
    "symbol, from_date, to_date, price_data, expected_cagr",
    [
        (
            "AAPL",
            "2020-01-01",
            "2021-01-01",
            pd.DataFrame(
                {"Close": [100, 150]},
                index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
            ),
            0.5,
        ),
        (
            "GOOGL",
            "2019-01-01",
            "2020-01-01",
            pd.DataFrame(
                {"Close": [200, 300]},
                index=[datetime(2019, 1, 1), datetime(2020, 1, 1)],
            ),
            0.5,
        ),
        (
            "MSFT",
            "2018-01-01",
            "2019-01-01",
            pd.DataFrame({"Close": [50, 100]}, index=[datetime(2018, 1, 1), datetime(2019, 1, 1)]),
            1.0,
        ),
    ],
    ids=["AAPL_2020", "GOOGL_2019", "MSFT_2018"],
)
def test_calculate_cagr_happy_path(portfolio, symbol, from_date, to_date, price_data, expected_cagr):
    # Arrange
    portfolio.data_api = MagicMock()
    portfolio.data_api.price_history_by_dates.return_value = price_data
    portfolio._calculate_cagr = MagicMock(return_value=expected_cagr)

    # Act
    result = portfolio.calculate_cagr(symbol, from_date, to_date)

    # Assert
    assert result == expected_cagr
    portfolio.data_api.price_history_by_dates.assert_called_once_with(symbol, from_date, to_date)
    portfolio._calculate_cagr.assert_called_once_with(price_data, "Close")


@pytest.mark.parametrize(
    "symbol, from_date, to_date, price_data",
    [
        ("AAPL", "2020-01-01", "2021-01-01", pd.DataFrame({"Close": []}, index=[])),
        ("GOOGL", "2019-01-01", "2020-01-01", pd.DataFrame({"Close": []}, index=[])),
    ],
    ids=["AAPL_no_data", "GOOGL_no_data"],
)
def test_calculate_cagr_no_data(portfolio, symbol, from_date, to_date, price_data):
    # Arrange
    portfolio.data_api = MagicMock()
    portfolio.data_api.price_history_by_dates.return_value = price_data

    # Act & Assert
    with pytest.raises(ValueError, match=f"No data available for {symbol} in the given date range."):
        portfolio.calculate_cagr(symbol, from_date, to_date)
    portfolio.data_api.price_history_by_dates.assert_called_once_with(symbol, from_date, to_date)


@pytest.mark.parametrize(
    "symbol, from_date, to_date, price_data",
    [
        (
            "AAPL",
            "2020-01-01",
            "2021-01-01",
            pd.DataFrame(
                {"Close": [100, 150]},
                index=[datetime(2020, 1, 1), datetime(2021, 1, 1)],
            ),
        ),
    ],
    ids=["AAPL_invalid_cagr"],
)
def test_calculate_cagr_invalid_cagr(portfolio, symbol, from_date, to_date, price_data):
    # Arrange
    portfolio.data_api = MagicMock()
    portfolio.data_api.price_history_by_dates.return_value = price_data
    portfolio._calculate_cagr = MagicMock(side_effect=Exception("Invalid CAGR calculation"))

    # Act & Assert
    with pytest.raises(Exception, match="Invalid CAGR calculation"):
        portfolio.calculate_cagr(symbol, from_date, to_date)
    portfolio.data_api.price_history_by_dates.assert_called_once_with(symbol, from_date, to_date)
    portfolio._calculate_cagr.assert_called_once_with(price_data, "Close")
