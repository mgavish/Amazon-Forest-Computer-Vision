from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_csv(df: pd.DataFrame, out_path: str | Path) -> Path:
    output = Path(out_path)
    df.to_csv(output, index=False)
    print(f"✅ Wrote: {output}")
    print(f"Rows: {len(df)}")
    return output
