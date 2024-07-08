from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf

INDEX_FILES_DIR = Path("stocks/data/indices/files")


@dataclass
class Index:
    name: str
    file: Path
    index_code: str
    url: str | None = None

    @property
    def data(self) -> pd.DataFrame:
        """Load data from the CSV file."""
        return pd.read_csv(self.file)

    @property
    def companies(self):
        return self.data["Company Name"].to_list()

    def download_historical_data(self, start: str, end: str) -> pd.DataFrame:
        """Download historical data for the index."""
        ticker = yf.Ticker(self.index_code)
        return ticker.history(start=start, end=end)


NIFTY_500_MULTICAP_50_25_25 = Index(
    name="Nifty 500 Multicap 50:25:25",
    file=INDEX_FILES_DIR / "ind_nifty500Multicap502525_list.csv",
    index_code="^CRSLNIFTY500",
)

NIFTY_TOTAL_MARKET = Index(
    name="Nifty Total Market",
    file=INDEX_FILES_DIR / "ind_niftytotalmarket_list.csv",
    index_code="^NSEI",
)

NIFTY_LARGEMIDCAP_250 = Index(
    name="Nifty LargeMidcap 250",
    file=INDEX_FILES_DIR / "ind_niftylargemidcap250list.csv",
    index_code="^CNXLMID",
)

NIFTY_MIDCAP_100 = Index(
    name="Nifty Midcap 100",
    file=INDEX_FILES_DIR / "ind_niftymidcap100list.csv",
    index_code="^NSEMDCP100",
)

NIFTY_500_LARGEMIDSMALL_EQUAL_CAP_WEIGHTED = Index(
    name="Nifty 500 LargeMidSmall Equal Cap Weighted",
    file=INDEX_FILES_DIR / "ind_nifty500LargeMidSmallEqualCapWeighted_list.csv",
    index_code="^CRSLNIFTY500E",
)

NIFTY_SMALLCAP_250 = Index(
    name="Nifty Smallcap 250",
    file=INDEX_FILES_DIR / "ind_niftysmallcap250list.csv",
    index_code="^CRSLNSC250",
)

NIFTY_50 = Index(
    name="Nifty 50", file=INDEX_FILES_DIR / "ind_nifty50list.csv", index_code="^NSEI"
)

NIFTY_SMALLCAP_50 = Index(
    name="Nifty Smallcap 50",
    file=INDEX_FILES_DIR / "ind_niftysmallcap50list.csv",
    index_code="^NSESMLCP50",
)

NIFTY_MICROCAP_250 = Index(
    name="Nifty Microcap 250",
    file=INDEX_FILES_DIR / "ind_niftymicrocap250_list.csv",
    index_code="^CRSLNMIC250",
)

NIFTY_SMALLCAP_100 = Index(
    name="Nifty Smallcap 100",
    file=INDEX_FILES_DIR / "ind_niftysmallcap100list.csv",
    index_code="^NSESMLCP100",
)

NIFTY_MIDCAP_SELECT = Index(
    name="Nifty Midcap Select",
    file=INDEX_FILES_DIR / "ind_niftymidcapselect_list.csv",
    index_code="^NSEMDCP50",
)

NIFTY_100 = Index(
    name="Nifty 100",
    file=INDEX_FILES_DIR / "ind_nifty100list.csv",
    index_code="^NSE100",
)

NIFTY_200 = Index(
    name="Nifty 200",
    file=INDEX_FILES_DIR / "ind_nifty200list.csv",
    index_code="^NSE200",
)

NIFTY_500 = Index(
    name="Nifty 500",
    file=INDEX_FILES_DIR / "ind_nifty500list.csv",
    index_code="^NSE500",
)

NIFTY_MIDCAP_50 = Index(
    name="Nifty Midcap 50",
    file=INDEX_FILES_DIR / "ind_niftymidcap50list.csv",
    index_code="^NSEMIDCAP50",
)

NIFTY_NEXT_50 = Index(
    name="Nifty Next 50",
    file=INDEX_FILES_DIR / "ind_niftynext50list.csv",
    index_code="^NSEI",
)

NIFTY_MIDCAP_150 = Index(
    name="Nifty Midcap 150",
    file=INDEX_FILES_DIR / "ind_niftymidcap150list.csv",
    index_code="^NSEMDCP150",
)

NIFTY_MIDSMALLCAP_400 = Index(
    name="Nifty MidSmallcap 400",
    file=INDEX_FILES_DIR / "ind_niftymidsmallcap400list.csv",
    index_code="^NSEMSM400",
)

NIFTY_SMALLCAP_300 = Index(
    name="Nifty Smallcap 300",
    file=INDEX_FILES_DIR / "ind_niftysmallcap300list.csv",
    index_code="^CRSLNSC300",
)

NIFTY_MIDCAP_400 = Index(
    name="Nifty Midcap 400",
    file=INDEX_FILES_DIR / "ind_niftymidcap400list.csv",
    index_code="^CRSLNMDCP400",
)

NIFTY_AUTOMOBILE = Index(
    name="Nifty Automobile",
    file=INDEX_FILES_DIR / "ind_niftyautomobilelist.csv",
    index_code="^CNXAUTO",
)

NIFTY_BANK = Index(
    name="Nifty Bank",
    file=INDEX_FILES_DIR / "ind_niftybanklist.csv",
    index_code="^NSEBANK",
)

NIFTY_FINANCIAL_SERVICES = Index(
    name="Nifty Financial Services",
    file=INDEX_FILES_DIR / "ind_niftyfinancialserviceslist.csv",
    index_code="^CNXFIN",
)

NIFTY_FMCG = Index(
    name="Nifty FMCG",
    file=INDEX_FILES_DIR / "ind_niftyfmcglist.csv",
    index_code="^CNXFMCG",
)

NIFTY_IT = Index(
    name="Nifty IT",
    file=INDEX_FILES_DIR / "ind_niftyitlist.csv",
    index_code="^CNXIT",
)

NIFTY_MEDIA = Index(
    name="Nifty Media",
    file=INDEX_FILES_DIR / "ind_niftymedialist.csv",
    index_code="^CNXMEDIA",
)

NIFTY_METAL = Index(
    name="Nifty Metal",
    file=INDEX_FILES_DIR / "ind_niftymetallist.csv",
    index_code="^CNXMETAL",
)

NIFTY_PHARMA = Index(
    name="Nifty Pharma",
    file=INDEX_FILES_DIR / "ind_niftypharmalist.csv",
    index_code="^CNXPHARMA",
)

NIFTY_PRIVATE_BANK = Index(
    name="Nifty Private Bank",
    file=INDEX_FILES_DIR / "ind_niftyprivatebanklist.csv",
    index_code="^NIFTYPRIVATEBANK",
)

NIFTY_PSU_BANK = Index(
    name="Nifty PSU Bank",
    file=INDEX_FILES_DIR / "ind_niftypsubanklist.csv",
    index_code="^NIFTYPSUBANK",
)

NIFTY_REALTY = Index(
    name="Nifty Realty",
    file=INDEX_FILES_DIR / "ind_niftyrealtylist.csv",
    index_code="^CNXREALTY",
)

NIFTY_SMALLCAP_300 = Index(
    name="Nifty Smallcap 300",
    file=INDEX_FILES_DIR / "ind_niftysmallcap300list.csv",
    index_code="^CRSLNSC300",
)

NIFTY_MIDCAP_400 = Index(
    name="Nifty Midcap 400",
    file=INDEX_FILES_DIR / "ind_niftymidcap400list.csv",
    index_code="^CRSLNMDCP400",
)

NIFTY_AUTOMOBILE = Index(
    name="Nifty Automobile",
    file=INDEX_FILES_DIR / "ind_niftyautomobilelist.csv",
    index_code="^CNXAUTO",
)

NIFTY_BANK = Index(
    name="Nifty Bank",
    file=INDEX_FILES_DIR / "ind_niftybanklist.csv",
    index_code="^NSEBANK",
)

NIFTY_FINANCIAL_SERVICES = Index(
    name="Nifty Financial Services",
    file=INDEX_FILES_DIR / "ind_niftyfinancialserviceslist.csv",
    index_code="^CNXFIN",
)

NIFTY_FMCG = Index(
    name="Nifty FMCG",
    file=INDEX_FILES_DIR / "ind_niftyfmcglist.csv",
    index_code="^CNXFMCG",
)

NIFTY_IT = Index(
    name="Nifty IT",
    file=INDEX_FILES_DIR / "ind_niftyitlist.csv",
    index_code="^CNXIT",
)

NIFTY_MEDIA = Index(
    name="Nifty Media",
    file=INDEX_FILES_DIR / "ind_niftymedialist.csv",
    index_code="^CNXMEDIA",
)

NIFTY_METAL = Index(
    name="Nifty Metal",
    file=INDEX_FILES_DIR / "ind_niftymetallist.csv",
    index_code="^CNXMETAL",
)

NIFTY_PHARMA = Index(
    name="Nifty Pharma",
    file=INDEX_FILES_DIR / "ind_niftypharmalist.csv",
    index_code="^CNXPHARMA",
)

NIFTY_PRIVATE_BANK = Index(
    name="Nifty Private Bank",
    file=INDEX_FILES_DIR / "ind_niftyprivatebanklist.csv",
    index_code="^NIFTYPRIVATEBANK",
)

NIFTY_PSU_BANK = Index(
    name="Nifty PSU Bank",
    file=INDEX_FILES_DIR / "ind_niftypsubanklist.csv",
    index_code="^NIFTYPSUBANK",
)

NIFTY_REALTY = Index(
    name="Nifty Realty",
    file=INDEX_FILES_DIR / "ind_niftyrealtylist.csv",
    index_code="^CNXREALTY",
)


if __name__ == "__main__":
    print(NIFTY_50.companies)
    print(NIFTY_100.data)
    print(NIFTY_50.download_historical_data(start="2022-1-1", end="2024-1-1"))
