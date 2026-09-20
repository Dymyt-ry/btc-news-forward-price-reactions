"""Load the default analysis-ready dataset from Hugging Face."""
from datasets import load_dataset

dataset = load_dataset(
    "dymyt-ry/btc-news-forward-price-reactions",
    "licensed_news_price_reaction",
    split="analysis",
)

columns = [
    "first_seen_at",
    "title",
    "weak_event_type",
    "weak_btc_relevance",
    "forward_return_bps_60m",
    "outcome_status_60m",
]
print(dataset.select_columns(columns)[0])

