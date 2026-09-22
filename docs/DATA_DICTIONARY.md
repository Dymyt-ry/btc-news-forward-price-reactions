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
- `outcomes`: one event/horizon forward row.
- `pre_event_outcomes`: one event/horizon backward row, mirroring `outcomes`.
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

## Backward windows (v0.6.4)

- `pre_event_anchor_at`: open of the UTC minute containing
  `decision_created_at`; always at or before the decision.
- `pre_event_anchor_price_usd`: BTCUSDT open at the anchor.
- `backward_start_at_*`: anchor minus the window length.
- `backward_start_price_usd_*`: BTCUSDT open at the window start.
- `backward_return_bps_*`: `10000 * ln(anchor price / start price)`; a
  pre-event feature, available at decision time.
- `backward_status_*`: `observed`, `before_market_coverage`,
  `after_market_coverage` or `missing`; never infer a missing value as zero.
  Rows that are `after_market_coverage` backward are `pending` forward.
- Backward windows of later events overlap forward windows of earlier events;
  purge/embargo at least 1,441 minutes around chronological splits.
