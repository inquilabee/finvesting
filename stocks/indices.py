import pandas as pd
from pathlib import Path

files_dir = Path("stocks/data/base/indices/files")


indexes = {
    file_name.name.strip(".csv"): pd.read_csv(file_name)
    for file_name in files_dir.iterdir()
}

df_unique = pd.concat(indexes.values()).drop_duplicates(subset=["ISIN Code"])

print(df_unique)

print(df_unique.value_counts("Industry"))
