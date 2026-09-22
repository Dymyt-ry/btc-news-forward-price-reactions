# Changelog

## v0.6.4 — 2026-09-22

- Added leak-free backward BTC windows: `pre_event_outcomes` (719,046
  event × horizon rows) and `backward_*` / `pre_event_anchor_*` columns in both
  analysis tables. The anchor is the open of the decision minute; forward
  values are unchanged.
- Added executed research notebooks (`notebooks/`): a forward/backward timing
  test and a news-flow volatility forecast test, both with negative results.
- Documented placebo-normalized reading of forward/backward ratios and a
  1,441-minute embargo for machine learning.

## v0.6.3 — 2026-09-20

- Added analysis-first `licensed_news_price_reaction` and
  `news_price_reaction` configurations.
- Compacted all 16 configurations to one Parquet file each.
- Preserved attributed PANews, U.S. SEC, and Federal Reserve text under the
  documented source-specific terms; withheld other publisher text.
- Included Binance public market/funding data and recomputed BTC forward
  reactions at six horizons.
- Removed historical Coin Metrics tables from this compact edition.
- Added SHA-256 inventory, rights matrix, provenance, schema, and quality report.

