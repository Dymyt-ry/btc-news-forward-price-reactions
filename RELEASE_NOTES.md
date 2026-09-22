# BTC News and Price Reactions v0.6.4

This release adds leak-free **backward** BTC windows to the v0.6.3 dataset, so
every news event now carries BTC returns over 1 minute to 24 hours both before
and after it was observed. All v0.6.3 data tables and forward values are
byte-identical; only the release-metadata rows change.

## What is new

- `pre_event_outcomes`: 719,046 event × horizon backward rows, mirroring
  `outcomes`.
- `backward_return_bps_*`, `backward_status_*`, `backward_start_*` and
  `pre_event_anchor_*` columns in `licensed_news_price_reaction` and
  `news_price_reaction`.
- Executed research notebooks in `notebooks/`.

## Research findings

In this sample, CJK news neither leads BTC moves nor improves volatility
forecasts beyond price history and the weekly calendar. Both pre-registered
tests are documented with all robustness checks, including the ones that
overturned a nominal result. See the README and the notebooks.

## Assets

- `btc-news-forward-price-reactions-v0.6.4.zip` — complete 17-configuration,
  Hugging Face-compatible release
- `btc-news-forward-price-reactions-v0.6.4.zip.sha256` — archive checksum

The archive contains its own `SHA256SUMS`, `manifest.json`, `quality.json`, and
`schema.json`. See `docs/RIGHTS.md` before redistribution or model release.
