from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf


@dataclass
class Index:
    name: str
    file: Path
    index_code: str
    url: str | None = None

    @property
    def data(self) -> pd.DataFrame:
        """Load companies from the CSV file."""
        return pd.read_csv(self.file)

    @property
    def companies(self):
        return self.data["Company Name"].to_list()

    def download_historical_data(self, start: str, end: str) -> pd.DataFrame:
        """Download historical data for the index."""
        ticker = yf.Ticker(self.index_code)
        hist = ticker.history(start=start, end=end)
        return hist


files_dir = Path("stocks/data/base/indices/files")

index_files = {
    "Nifty 500 Multicap 50:25:25": (
        "ind_nifty500Multicap502525_list.csv",
        "NIFTY500MULTICAP502525",
    ),
    "Nifty Total Market": ("ind_niftytotalmarket_list.csv", "NIFTYTOTALMARKET"),
    "Nifty LargeMidcap 250": ("ind_niftylargemidcap250list.csv", "NIFTYLARGEMIDCAP250"),
    "Nifty Midcap 100": ("ind_niftymidcap100list.csv", "NIFTYMIDCAP100"),
    "Nifty 500 LargeMidSmall Equal Cap Weighted": (
        "ind_nifty500LargeMidSmallEqualCapWeighted_list.csv",
        "NIFTY500LARGEMIDSMALLEQUALCAP",
    ),
    "Nifty Smallcap 250": ("ind_niftysmallcap250list.csv", "NIFTYSMALLCAP250"),
    "Nifty 50": ("ind_nifty50list.csv", "NIFTY50"),
    "Nifty Smallcap 50": ("ind_niftysmallcap50list.csv", "NIFTYSMALLCAP50"),
    "Nifty Microcap 250": ("ind_niftymicrocap250_list.csv", "NIFTYMICROCAP250"),
    "Nifty Smallcap 100": ("ind_niftysmallcap100list.csv", "NIFTYSMALLCAP100"),
    "Nifty Midcap Select": ("ind_niftymidcapselect_list.csv", "NIFTYMIDCAPSELECT"),
    "Nifty 100": ("ind_nifty100list.csv", "NIFTY100"),
    "Nifty 200": ("ind_nifty200list.csv", "NIFTY200"),
    "Nifty 500": ("ind_nifty500list.csv", "NIFTY500"),
    "Nifty Midcap 50": ("ind_niftymidcap50list.csv", "NIFTYMIDCAP50"),
    "Nifty Next 50": ("ind_niftynext50list.csv", "NIFTYNEXT50"),
    "Nifty Midcap 150": ("ind_niftymidcap150list.csv", "NIFTYMIDCAP150"),
    "Nifty MidSmallcap 400": ("ind_niftymidsmallcap400list.csv", "NIFTYMIDSMALLCAP400"),
}

indices = {}

for name, (file, index_code) in index_files.items():
    index = Index(name=name, file=files_dir / file, index_code=index_code)
    indices[name] = index

print(indices)
