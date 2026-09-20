# Data dictionary

## Analysis-first tables

- `licensed_news_price_reaction`: attributed reusable news text, weak
  annotations, and wide BTC reaction targets in one row per event.
- `news_price_reaction`: all observed events with restricted text omitted and
  the same target layout.
- `outcome_status_*`: `observed` or `pending`; missing returns are never zero.
- `forward_return_bps_*`: forward log return multiplied by 10,000.
- `target_at_*`: when the horizon becomes available, making it a target-time
  field rather than a contemporaneous feature.

## Normalized tables

- `news_index`: one row per observed feed event.
- `weak_annotations`: complete weak-label output and lineage.
- `trading_decisions`: pre-outcome timing and reproducibility provenance.
- `outcomes`: one event/horizon row.
- `market_1m`: Binance BTCUSDT/ETHUSDT one-minute OHLCV.
- `funding_rates`: Binance BTCUSDT funding observations.
- `market_gap_summary`: expected versus observed bars.
- source coverage/health tables: observed composition and collection health.
- `clock_drift_windows`: collector clock-drift intervals.
- `rights_matrix`: publication scope and evidence, not a license grant.
- `build_provenance`: hash-pinned release lineage.

Each configuration is stored inside the release archive as
`data/<configuration>/unknown.parquet`. Exact physical types for every field are
recorded in [schema.json](../release-metadata/schema.json).

