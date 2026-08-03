import os
import pandas as pd

def export_to_csv(candidates):

    os.makedirs(
        "exports",
        exist_ok=True
    )

    df = pd.DataFrame(
        candidates
    )

    df.to_csv(
        "exports/results.csv",
        index=False
    )

    print(
        "CSV Exported Successfully"
    )