<p align="center">
  <img src="assets/dataset-cover.png" width="760" alt="BTC news events connected to forward price reactions">
</p>

<h1 align="center">BTC News and Forward Price Reactions</h1>

<p align="center">
  <strong>120,981 multilingual news events · weak semantic annotations · BTC returns from 1 minute to 24 hours</strong>
</p>

<p align="center">
  <a href="https://huggingface.co/datasets/dymyt-ry/btc-news-forward-price-reactions"><img alt="Hugging Face dataset" src="https://img.shields.io/badge/%F0%9F%A4%97-Hugging_Face-FFD21E"></a>
  <a href="https://www.kaggle.com/datasets/dymy1ry/btc-multilingual-news-market-events"><img alt="Kaggle dataset" src="https://img.shields.io/badge/Kaggle-Dataset-20BEFF?logo=kaggle&logoColor=white"></a>
  <a href="https://github.com/Dymyt-ry/btc-news-forward-price-reactions/releases/tag/v0.6.3"><img alt="Release v0.6.3" src="https://img.shields.io/badge/release-v0.6.3-2ea44f"></a>
  <img alt="Mixed source terms" src="https://img.shields.io/badge/license-mixed--source%20terms-orange">
</p>

This repository is the documentation, citation, and immutable-release home for
a research dataset connecting timestamped crypto-news observations to weak
semantic labels and subsequent Bitcoin price movement. It is built for event
studies, classifier bootstrapping, temporal evaluation, and reproducible
news-to-market research.

> **Start here:** use the `licensed_news_price_reaction` configuration. It puts
> attributed reusable titles/RSS summaries, weak labels, entry prices, and all
> six BTC reaction horizons in one analysis-ready row per event.

## Dataset at a glance

| | Coverage |
| --- | --- |
| News observations | **120,981** from 18 publisher feeds |
| Attributed reusable text rows | **12,433** |
| Languages | Korean, Chinese, English, Japanese, and undetermined |
| Observation window | 13 June–19 September 2026 |
| Forward horizons | 1, 5, 15, 60, 240, and 1,440 minutes |
| Market context | Binance BTCUSDT/ETHUSDT one-minute OHLCV and BTCUSDT funding |
| Release | v0.6.3 · immutable snapshot · SHA-256 inventoried |

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
    "weak_btc_relevance",
    "forward_return_bps_60m",
    "outcome_status_60m",
])
print(sample[0])
```

Or download the complete immutable snapshot from GitHub Releases:

```bash
gh release download v0.6.3 \
  --repo Dymyt-ry/btc-news-forward-price-reactions
shasum -a 256 -c btc-news-forward-price-reactions-v0.6.3.zip.sha256
```

The same quickstart is available as [examples/quickstart.py](examples/quickstart.py).

## Choose the right table

| Need | Configuration | Rows |
| --- | --- | ---: |
| Reusable text + annotations + wide BTC reactions | `licensed_news_price_reaction` | 12,433 |
| All events + annotations + wide BTC reactions | `news_price_reaction` | 120,981 |
| Normalized event metadata | `news_index` | 120,981 |
| Full weak-label scores and lineage | `weak_annotations` | 120,981 |
| One-minute BTC/ETH bars | `market_1m` | 282,240 |
| Long-format event × horizon targets | `outcomes` | 719,046 |
| Rights decisions and evidence | `rights_matrix` | 21 |

The release archive contains all 16 configurations in the original Hugging
Face-compatible hierarchy. Each configuration is one Parquet file. Historical
Coin Metrics Community tables from v0.6.2 are intentionally omitted from this
compact edition. Coin Metrics is not Coinbase.

## What “weak annotation” means

Event type, BTC relevance, and experimental direction were generated from
title/RSS text by a pinned multilingual embedding model plus deterministic
rules. They are useful for filtering, bootstrapping, and review queues, but are
**not human gold labels**. Cosine scores and margins are not calibrated
probabilities. See [the annotation notes](docs/ANNOTATION.md) for exact lineage.

## Modeling rules that matter

- Forward returns describe what happened after observation; they do **not**
  establish that a news item caused the move.
- Keep every `target_*`, `forward_return_*`, and `outcome_status_*` field on the
  target side to prevent look-ahead leakage.
- Split chronologically and group repeated-title events before evaluation.
- Treat `pending` outcomes as unavailable, never as zero returns.
- The observed mix is publisher-concentrated, not a balanced population sample
  or a validated CJK classifier benchmark.

## Rights and integrity

This is a mixed-source, **non-commercial research release**. Reusable text is
limited to attributed PANews, U.S. SEC, and Federal Reserve Board rows covered
by documented source-specific terms; other publishers remain metadata-only.
There is deliberately no blanket GitHub license for the compiled dataset.

Read [RIGHTS.md](docs/RIGHTS.md) before redistribution or model release.
The full archive contains the machine-readable rights matrix, source registry,
and build provenance. Every published artifact is listed in
[release-metadata/SHA256SUMS](release-metadata/SHA256SUMS).

## Repository map

```text
assets/             Cover artwork
docs/               Rights, sources, annotation, and data notes
examples/           Runnable Python quickstart
release-metadata/   Manifest, schema, quality report, and checksums
CITATION.cff        GitHub-native citation metadata
```

The large Parquet files live in the versioned GitHub Release rather than git
history. For interactive browsing and streaming, use
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

