import os
import time
import pandas as pd
import mftool


def dowload_and_save(scheme):
    output_file = f"data/history/{scheme}.csv"

    if os.path.exists(output_file):
        return

    mf = mftool.Mftool()
    df = mf.get_scheme_historical_nav(scheme, as_Dataframe=True)
    df.to_csv(output_file)


def get_historical_nav(download_chunk: int = 10, sleep: int = 0):
    all_schemes = pd.read_csv("data/schemes.csv").sort_values(
        by=["start_nav"], ascending=False
    )

    scheme_codes = all_schemes["scheme_code"].to_list()

    while scheme_codes:
        codes_to_download = scheme_codes[:download_chunk]

        tasks = []

        for scheme_code in codes_to_download:
            dowload_and_save(scheme_code)

        scheme_codes = scheme_codes[download_chunk:]
        time.sleep(sleep)


if __name__ == "__main__":
    get_historical_nav()
