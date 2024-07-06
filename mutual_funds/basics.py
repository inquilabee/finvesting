import logging

import mftool
import pandas as pd

logging.basicConfig()

logger = logging.getLogger(__name__)

logger.info = print


def get_all_mfs(output_file: str, debug: bool = False, log_enabled: bool = False):
    mf = mftool.Mftool()
    all_schemes = mf.get_scheme_codes()
    scheme_df = pd.DataFrame()

    logger.info(f"A total of {len(all_schemes)} values to be fetched.")

    for idx, scheme in enumerate(all_schemes):
        try:
            scheme_details = mf.get_scheme_details(scheme)
            scheme_df = pd.concat([scheme_df, pd.Series(scheme_details)], axis=1)

            if log_enabled and idx % 10 == 0:
                logger.info(f"{idx} values fetched.")

            if debug and idx == 10:
                break
        except:
            logger.info(f"could not fetch for {scheme}")
            pass

    log_enabled and logger.info("Finalising data.")

    scheme_df = (
        scheme_df.T.assign(
            start_date=scheme_df.T["scheme_start_date"].apply(lambda x: x["date"]),
            start_nav=scheme_df.T["scheme_start_date"].apply(lambda x: x["nav"]),
        )
        .drop("scheme_start_date", axis=1)
        .reset_index(drop=True)
    )

    return scheme_df.to_csv(output_file)


if __name__ == "__main__":
    get_all_mfs("data/schemes.csv", debug=False, log_enabled=True)
