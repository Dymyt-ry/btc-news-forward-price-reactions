"""Load the analysis-ready Parquet file from a local GitHub checkout."""

from pathlib import Path

import pandas as pd


path = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "licensed_news_price_reaction"
    / "unknown.parquet"
)
dataset = pd.read_parquet(path)

columns = [
    "first_seen_at",
    "title",
    "weak_event_type",
    "weak_btc_relevance",
    "forward_return_bps_60m",
    "outcome_status_60m",
]
print(dataset.loc[0, columns])
