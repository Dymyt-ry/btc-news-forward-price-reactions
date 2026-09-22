<p align="center">
  <img src="assets/dataset-cover.png" width="760" alt="BTC news events connected to price reactions">
</p>

<h1 align="center">BTC News and Price Reactions</h1>

<p align="center">
  <strong>120,981 multilingual news events · weak semantic annotations · BTC returns before and after, 1 minute to 24 hours</strong>
</p>

<p align="center">
  <a href="https://huggingface.co/datasets/dymyt-ry/btc-news-forward-price-reactions"><img alt="Hugging Face dataset" src="https://img.shields.io/badge/%F0%9F%A4%97-Hugging_Face-FFD21E"></a>
  <a href="https://www.kaggle.com/datasets/dymy1ry/btc-multilingual-news-market-events"><img alt="Kaggle dataset" src="https://img.shields.io/badge/Kaggle-Dataset-20BEFF?logo=kaggle&logoColor=white"></a>
  <a href="https://github.com/Dymyt-ry/btc-news-forward-price-reactions/releases/tag/v0.6.4"><img alt="Release v0.6.4" src="https://img.shields.io/badge/release-v0.6.4-2ea44f"></a>
  <img alt="Mixed source terms" src="https://img.shields.io/badge/license-mixed--source%20terms-orange">
</p>

This repository is the documentation, citation, and immutable-release home for
a research dataset connecting timestamped crypto-news observations to weak
semantic labels and Bitcoin price movement before and after each observation. It is built for event
studies, classifier bootstrapping, temporal evaluation, and reproducible
news-to-market research.

> **Start here:** use the `licensed_news_price_reaction` configuration. It puts
> attributed reusable titles/RSS summaries, weak labels, entry prices, and all
> six forward and backward BTC windows in one analysis-ready row per event.

## Dataset at a glance

| | Coverage |
| --- | --- |
| News observations | **120,981** from 18 publisher feeds |
| Attributed reusable text rows | **12,433** |
| Languages | Korean, Chinese, English, Japanese, and undetermined |
| Observation window | 13 June–19 September 2026 |
| Forward and backward horizons | 1, 5, 15, 60, 240, and 1,440 minutes |
| Market context | Binance BTCUSDT/ETHUSDT one-minute OHLCV and BTCUSDT funding |
| Release | v0.6.4 · immutable snapshot · SHA-256 inventoried |

## Use it in thirty seconds

```python
from datasets import load_dataset

ds = load_dataset(
    "dymyt-ry/btc-news-forward-price-reactions",
    "licensed_news_price_reaction",
    split="analysis",
)

sample = ds.select_columns([
    "first_seen_at",
    "title",
    "weak_event_type",
    "backward_return_bps_60m",
    "forward_return_bps_60m",
    "outcome_status_60m",
])
print(sample[0])
```

To work directly from this GitHub checkout without any network call:

```python
import pandas as pd

df = pd.read_parquet(
    "data/licensed_news_price_reaction/unknown.parquet"
)
print(df[["title", "weak_event_type", "backward_return_bps_60m",
          "forward_return_bps_60m"]].head())
```

Or download the complete immutable snapshot from GitHub Releases:

```bash
gh release download v0.6.4 \
  --repo Dymyt-ry/btc-news-forward-price-reactions
shasum -a 256 -c btc-news-forward-price-reactions-v0.6.4.zip.sha256
```

Runnable versions are available as
[examples/quickstart.py](examples/quickstart.py) and
[examples/quickstart_local.py](examples/quickstart_local.py).

## Choose the right table

| Need | Configuration | Rows |
| --- | --- | ---: |
| Reusable text + annotations + wide BTC windows | [`licensed_news_price_reaction`](data/licensed_news_price_reaction/unknown.parquet) | 12,433 |
| All events + annotations + wide BTC windows | [`news_price_reaction`](data/news_price_reaction/unknown.parquet) | 120,981 |
| Normalized event metadata | [`news_index`](data/news_index/unknown.parquet) | 120,981 |
| Full weak-label scores and lineage | [`weak_annotations`](data/weak_annotations/unknown.parquet) | 120,981 |
| One-minute BTC/ETH bars | [`market_1m`](data/market_1m/unknown.parquet) | 282,240 |
| Long-format event × horizon forward targets | [`outcomes`](data/outcomes/unknown.parquet) | 719,046 |
| Long-format event × horizon backward windows | [`pre_event_outcomes`](data/pre_event_outcomes/unknown.parquet) | 719,046 |
| Rights decisions and evidence | [`rights_matrix`](data/rights_matrix/unknown.parquet) | 21 |

The repository's [`data/`](data) directory and the versioned release archive
both contain all 17 configurations in the same Hugging Face-compatible
hierarchy. Each configuration is one Parquet file. Historical Coin Metrics
Community tables from v0.6.2 are intentionally omitted from this compact
edition. Coin Metrics is not Coinbase.

## Backward windows (new in v0.6.4)

`backward_return_bps_<h>m` is the BTC log return over the `h` minutes that end
at `pre_event_anchor_at`, the open of the UTC minute in which the collector
made its decision. That price is known at decision time, so backward columns
are **leak-free features**. Forward columns start one minute later at
`entry_at` and remain **targets**. The long-format table `pre_event_outcomes`
mirrors `outcomes` row for row (719,046 event × horizon rows).

Compare `|forward|` with `|backward|` only after normalizing by the same ratio
at placebo times (for example the same anchors shifted by whole weeks), because
intraday volatility seasonality alone moves the raw ratio away from 1.
`backward_status_<h>m` is `observed`, `before_market_coverage` (the earliest
events, 1,440-minute window only) or `after_market_coverage` (the final
snapshot hours, whose forward status is `pending`). Never treat a
non-observed window as a zero return. Backward windows of later events overlap
forward windows of earlier ones: for machine learning, split chronologically
and purge/embargo at least 1,441 minutes around each boundary.

## Research findings

Two analyses were run on this release. Each fixed one primary hypothesis in
advance; all other results are exploratory. Code and full outputs are in [`notebooks/`](notebooks) and on Kaggle:
[timing notebook](https://www.kaggle.com/code/dymy1ry/does-crypto-news-lead-btc-forward-backward-test) and
[volatility notebook](https://www.kaggle.com/code/dymy1ry/does-crypto-news-improve-btc-volatility-forecasts).

**1. Does news lead BTC moves?** The test compares BTC's absolute move after
each observation with the equally long move before it, relative to placebo
times with the same weekday and time of day. For Korean, Chinese and Japanese
(CJK) events at 60 minutes, the excess ratio is 0.98 (95% CI 0.963–0.999). The
hypothesis that news leads price is **not supported**. Ratios below 1 at 1–15
minutes come from headlines that report price moves (market commentary ≈0.91)
and from RSS poll batches. Without both, the ratio is 0.99–1.00. Bursts of
unusually dense CJK news show no effect.

**2. Does news flow improve volatility forecasts?** The test adds CJK
news-flow features to a price-only model of next-hour realized volatility. The
pre-registered version passed nominally: 1.2% lower out-of-sample error,
p = 0.019. The gain turned out to be a **weekend proxy**, because news flow and
volatility both drop at weekends. With day-of-week controls or daily rolling
refits, the change is between −0.3% and +0.1% and not significant. Its
features were chosen using the timing analysis of the same period, so its
hypothesis is pre-specified for that notebook rather than independent of the
data.

**Conclusion.** In this sample (13 June–18 September 2026; BTC between about
58k and 82k USD, including a breakout from about 63k to 78k between 18 and
21 August), CJK news flow neither leads
BTC moves nor improves volatility forecasts beyond price history and the
weekly calendar. These are negative research results about one period, not
trading advice.

## What “weak annotation” means

Event type, BTC relevance, and experimental direction were generated from
title/RSS text by a pinned multilingual embedding model plus deterministic
rules. They are useful for filtering, bootstrapping, and review queues, but are
**not human gold labels**. Cosine scores and margins are not calibrated
probabilities. See [the annotation notes](docs/ANNOTATION.md) for exact lineage.

## Modeling rules that matter

- Forward and backward returns describe what BTC did around an observation;
  they do **not** establish that a news item caused a move.
- Keep every `target_*`, `forward_return_*`, and `outcome_status_*` field on the
  target side to prevent look-ahead leakage. Backward columns are features.
- Split chronologically, embargo at least 1,441 minutes, and group
  repeated-title events before evaluation.
- Treat `pending` and non-observed backward windows as unavailable, never as
  zero returns.
- The observed mix is publisher-concentrated, not a balanced population sample
  or a validated CJK classifier benchmark.

## Rights and integrity

This is a mixed-source, **non-commercial research release**. Reusable text is
limited to attributed PANews, U.S. SEC, and Federal Reserve Board rows covered
by documented source-specific terms; other publishers remain metadata-only.
There is deliberately no blanket GitHub license for the compiled dataset.

Read [RIGHTS.md](docs/RIGHTS.md) before redistribution or model release.
The repository and full archive both contain the machine-readable
[rights matrix](data/rights_matrix/unknown.parquet),
[source registry](data/source_registry/unknown.parquet), and
[build provenance](data/build_provenance/unknown.parquet). Every published
artifact is listed in
[release-metadata/SHA256SUMS](release-metadata/SHA256SUMS).

## Repository map

```text
assets/             Cover artwork
data/               All 17 Parquet configurations
docs/               Rights, sources, annotation, and data notes
examples/           Hub and local-file Python quickstarts
notebooks/          Timing and volatility research notebooks (executed)
release-metadata/   Manifest, schema, quality report, and checksums
CITATION.cff        GitHub-native citation metadata
```

The same data is also bundled in the immutable `v0.6.4` GitHub Release. For
interactive browsing and streaming, use
[Hugging Face](https://huggingface.co/datasets/dymyt-ry/btc-news-forward-price-reactions);
for notebook workflows, use
[Kaggle](https://www.kaggle.com/datasets/dymy1ry/btc-multilingual-news-market-events).

## Documentation

- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Weak annotation provenance](docs/ANNOTATION.md)
- [Rights and license review](docs/RIGHTS.md)
- [Sources](docs/SOURCES.md)
- [Publication decision](docs/PUBLICATION.md)
- [Release history](CHANGELOG.md)

## Citation

GitHub exposes the citation controls from [CITATION.cff](CITATION.cff). A BibTeX
entry is also included in the release notes and on the Hugging Face dataset card.
