# %% [markdown]
# # Does crypto news lead BTC? A forward/backward timing test
#
# Every news event in this dataset has a leak-free timestamp from the collector's
# own clock. That makes one test possible that scraped news archives cannot run
# honestly: **does BTC move more in the window *after* the news was seen than in
# the equally long window *before* it, compared with ordinary moments?**
#
# | excess ratio `E` | reading |
# |---|---|
# | `E > 1` | more movement after observation: news **leads** price |
# | `E ≈ 1` | news timing has **no relationship** with price movement |
# | `E < 1` | more movement before observation: news **follows** price |
#
# ## Pre-registered primary hypothesis
#
# Written before looking at any result in this notebook:
#
# > **H1:** For CJK-language events (ko, zh, ja), at the **60-minute** horizon,
# > `E > 1`, with the lower bound of a 95% day-block bootstrap interval above 1.
#
# Everything else here (other horizons, languages, robustness variants, bursts,
# event types) is **exploratory**. It uses two-sided tests with
# Benjamini–Hochberg correction.

# %%
import math
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HORIZONS = [1, 5, 15, 60, 240, 1440]
PRIMARY_HORIZON = 60
CJK = {"ko", "zh", "ja"}
# Weak event types whose headlines typically *describe* a price move.
PRICE_REPORT_TYPES = {"market_commentary", "liquidation_leverage", "whale_onchain"}
PLACEBO_SHIFTS_DAYS = [-14, -7, 7, 14]  # same weekday and time of day
BOOTSTRAP_REPS = 2000
RNG = np.random.default_rng(20260922)


def find(kaggle_name: str, release_path: str) -> Path:
    """Locate a file on Kaggle (flat names) or in a local release (hierarchical)."""
    for root, pattern in [(Path("/kaggle/input"), kaggle_name), (Path("."), release_path)]:
        if root.exists():
            matches = sorted(root.rglob(pattern))
            if len(matches) == 1:
                return matches[0]
    raise FileNotFoundError(f"Expected exactly one {kaggle_name} / {release_path}")


NEWS_FILE = find("START_HERE__all_news_price_reaction.parquet",
                 "news_price_reaction/unknown.parquet")
MARKET_FILE = find("data__market_1m__unknown.parquet", "market_1m/unknown.parquet")

news_all = pd.read_parquet(NEWS_FILE)
market = pd.read_parquet(MARKET_FILE, columns=["symbol", "open_time", "open"])
price = (market.loc[market.symbol.eq("BTCUSDT")]
         .set_index("open_time")["open"].sort_index())
assert price.index.is_unique
assert (price.index.to_series().diff().dropna() == pd.Timedelta("1min")).all(), \
    "market_1m is expected to be gap-free"
print(f"{len(news_all):,} news events; BTC minutes {price.index.min()} → {price.index.max()}")

# %% [markdown]
# ## One definition of forward and backward, for news, bursts and placebo
#
# For an anchor minute `a` (the UTC minute in which the collector decided):
#
# - backward `h`: `ln(P[a] / P[a−h])`: known at decision time
# - forward `h`: `ln(P[a+1+h] / P[a+1])`: starts at the next minute open
#
# `P` is the Binance BTCUSDT one-minute **open**. The decision minute itself
# belongs to neither window, and placebo windows have the identical geometry.

# %%
minute_index = price.index
log_p = np.log(price.to_numpy())


def window_returns(anchors: pd.Series, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (backward_bps, forward_bps); NaN where a window leaves coverage."""
    def log_price_at(ts: pd.Series) -> np.ndarray:
        pos = minute_index.get_indexer(pd.DatetimeIndex(ts))
        out = np.full(len(pos), np.nan)
        ok = pos >= 0
        out[ok] = log_p[pos[ok]]
        return out

    one = pd.Timedelta(minutes=1)
    h = pd.Timedelta(minutes=horizon)
    backward = 1e4 * (log_price_at(anchors) - log_price_at(anchors - h))
    forward = 1e4 * (log_price_at(anchors + one + h) - log_price_at(anchors + one))
    return backward, forward


def add_windows(frame: pd.DataFrame, horizons=HORIZONS) -> pd.DataFrame:
    """Add news-time and placebo-time windows for every anchor in ``frame``."""
    frame = frame.copy()
    frame["day"] = frame.anchor.dt.floor("D")
    for h in horizons:
        frame[f"bwd_{h}"], frame[f"fwd_{h}"] = window_returns(frame.anchor, h)
        shifted = [window_returns(frame.anchor + pd.Timedelta(days=s), h)
                   for s in PLACEBO_SHIFTS_DAYS]
        # Mean over whichever placebo shifts stay inside market coverage.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # all shifts out of range
            frame[f"pbwd_{h}"] = np.nanmean(np.abs([b for b, _ in shifted]), axis=0)
            frame[f"pfwd_{h}"] = np.nanmean(np.abs([f for _, f in shifted]), axis=0)
    return frame


# %% [markdown]
# ## Event set
#
# - only events with a decision timestamp
# - drop events overlapping a collector clock-drift window
# - repeated exact titles count again only after 24 quiet hours. Syndicated
#   copies of one story are not independent evidence, but a generic headline
#   reused weeks later is a new event.

# %%
news = news_all.loc[news_all.decision_id.notna()
                    & ~news_all.clock_drift_overlap.astype("boolean").fillna(False)]
news = news.sort_values(["exact_title_group_id", "first_seen_at", "event_id"],
                        kind="stable")
gap = news.groupby("exact_title_group_id").first_seen_at.diff()
news = (news.loc[gap.isna() | (gap >= pd.Timedelta("24h"))]
            .sort_values(["first_seen_at", "event_id"], kind="stable")
            .reset_index(drop=True))
news["anchor"] = news.decision_created_at.dt.floor("min")
news["lang"] = news.feed_language_hint
news["cjk"] = news.lang.isin(CJK)
news["price_report"] = news.weak_event_type.isin(PRICE_REPORT_TYPES)
news = add_windows(news)
print(f"{len(news):,} events after filtering ({news.cjk.mean():.0%} CJK, "
      f"{news.price_report.mean():.0%} price-report types)")

# %%
# Independent check: the recomputed windows must equal the published columns.
for h in HORIZONS:
    observed = news[f"outcome_status_{h}m"].eq("observed")
    assert np.allclose(news.loc[observed, f"fwd_{h}"],
                       news.loc[observed, f"forward_return_bps_{h}m"], atol=1e-6)
    if f"backward_return_bps_{h}m" in news:
        ok = news[f"backward_status_{h}m"].eq("observed")
        assert np.allclose(news.loc[ok, f"bwd_{h}"],
                           news.loc[ok, f"backward_return_bps_{h}m"], atol=1e-6)
checked = "forward and backward" if "backward_return_bps_60m" in news else "forward"
print(f"Recomputed windows match the published {checked} columns.")

# %% [markdown]
# ## Statistic and uncertainty
#
# For a set of events and a horizon `h`:
#
# - `R_news = mean|forward| / mean|backward|` at news times
# - `R_placebo`: the same ratio at the placebo times of those events
#   (±7 and ±14 days: same weekday and time of day, so intraday and weekly
#   volatility seasonality cancel out)
# - **`E = R_news / R_placebo`**
#
# Events cluster and their windows overlap, so the interval uses a **moving
# block bootstrap over UTC days** with blocks longer than the window
# (`ceil(2h/1440)+1` days). Longer blocks (up to 21 days) keep the same
# qualitative conclusions but shift p-values noticeably, so treat p-values as
# approximate. `p_two_sided` is the percentile-bootstrap two-sided p-value.
# Each table below is its own Benjamini–Hochberg family, and every call draws a
# fresh bootstrap, so the same cell can show slightly different p-values in two
# tables.

# %%
def excess_ratio(frame: pd.DataFrame, h: int, reps: int = BOOTSTRAP_REPS) -> dict:
    cols = [f"fwd_{h}", f"bwd_{h}", f"pfwd_{h}", f"pbwd_{h}"]
    sub = frame.dropna(subset=cols)
    if len(sub) < 30:
        return {"n": len(sub)}
    # Per-day sums make each bootstrap replicate a cheap vector operation.
    daily = sub[cols].abs().groupby(sub.day).sum()
    all_days = pd.date_range(news.day.min(), news.day.max(), freq="D", tz="UTC")
    values = daily.reindex(all_days, fill_value=0.0).to_numpy()

    def ratio(sums):
        fwd, bwd, pfwd, pbwd = sums.T
        return (fwd / bwd) / (pfwd / pbwd)

    block = int(np.ceil(2 * h / 1440)) + 1
    n_days = len(values)
    n_blocks = int(np.ceil(n_days / block))
    starts = RNG.integers(0, n_days - block + 1, size=(reps, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)).reshape(reps, -1)[:, :n_days]
    boot = ratio(values[idx].sum(axis=1))
    totals = values.sum(axis=0)
    return {
        "n": len(sub),
        "R_news": totals[0] / totals[1],
        "R_placebo": totals[2] / totals[3],
        "E": ratio(totals),
        "ci_low": np.quantile(boot, 0.025),
        "ci_high": np.quantile(boot, 0.975),
        "p_two_sided": min(1.0, 2 * min((boot <= 1).mean(), (boot >= 1).mean())),
    }


def bh_adjust(p: pd.Series) -> pd.Series:
    """Benjamini–Hochberg adjusted p-values; NaN cells (too few events) stay NaN."""
    valid = p.dropna()
    order = np.argsort(valid.to_numpy())
    ranked = valid.to_numpy()[order] * len(valid) / np.arange(1, len(valid) + 1)
    adjusted = np.empty(len(valid))
    adjusted[order] = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
    return pd.Series(adjusted, index=valid.index).reindex(p.index)


def one_per_minute(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep one event per anchor minute so RSS poll batches count once."""
    return frame.drop_duplicates("anchor")


# %% [markdown]
# ## Primary result (as pre-registered)

# %%
primary = excess_ratio(news.loc[news.cjk], PRIMARY_HORIZON)
print(pd.Series(primary).round(4).to_string())
verdict = "SUPPORTED" if primary["ci_low"] > 1 else "NOT SUPPORTED"
print(f"\nH1 (CJK, {PRIMARY_HORIZON}m, E > 1 with CI low > 1): {verdict}")

# %% [markdown]
# ## Robustness: what drives departures from E = 1? (exploratory)
#
# Two effects can pull `E` below 1 without any news *timing* effect:
#
# - **Price reports.** A headline such as "BTC falls below 60k" is written
#   because the price already moved.
# - **Poll batches.** One RSS fetch can deliver dozens of items in the same
#   minute, so a few minutes dominate an event-weighted mean.
#
# The table shows CJK events under each variant. BTC broke out of a range in
# mid-August (from about 63k to 79k within a week), so the last two rows split
# the sample at 15 August. Placebo shifts near that date cross the break.

# %%
cjk = news.loc[news.cjk]
BREAK = pd.Timestamp("2026-08-15", tz="UTC")
variants = {
    "all CJK events": cjk,
    "excluding price-report types": cjk.loc[~cjk.price_report],
    "one event per minute": one_per_minute(cjk),
    "both": one_per_minute(cjk.loc[~cjk.price_report]),
    "price-report types only": cjk.loc[cjk.price_report],
    "excl. price reports, before 15 Aug": cjk.loc[~cjk.price_report & (cjk.anchor < BREAK)],
    "excl. price reports, from 15 Aug": cjk.loc[~cjk.price_report & (cjk.anchor >= BREAK)],
}
robust = pd.DataFrame([
    {"variant": name, "horizon_min": h, **excess_ratio(frame, h)}
    for name, frame in variants.items() for h in (1, 5, 15, 60, 240)
])
robust["p_bh"] = bh_adjust(robust.p_two_sided)
robust.pivot(index="variant", columns="horizon_min", values="E").round(3)

# %%
robust.round(3)

# %% [markdown]
# ## All horizons by language group (exploratory, excluding price-report types)

# %%
groups = {
    "CJK": news.cjk,
    "ko": news.lang.eq("ko"),
    "zh": news.lang.eq("zh"),
    "ja": news.lang.eq("ja"),
    "en": news.lang.eq("en"),
}
base = news.loc[~news.price_report]
by_lang = pd.DataFrame([
    {"group": name, "horizon_min": h, **excess_ratio(base.loc[mask[base.index]], h)}
    for name, mask in groups.items() for h in HORIZONS
])
by_lang["p_bh"] = bh_adjust(by_lang.p_two_sided)
by_lang.round(3)

# %%
fig, ax = plt.subplots(figsize=(10, 5))
offsets = np.linspace(-0.15, 0.15, len(groups))
for offset, (name, part) in zip(offsets, by_lang.groupby("group", sort=False)):
    x = np.arange(len(HORIZONS)) + offset
    ax.errorbar(x, part.E, yerr=[part.E - part.ci_low, part.ci_high - part.E],
                fmt="o", capsize=3, label=name)
ax.axhline(1, color="black", linewidth=1)
ax.set_xticks(range(len(HORIZONS)), [f"{h}m" for h in HORIZONS])
ax.set(title="Excess forward/backward ratio at news time vs placebo\n"
             "(price-report types excluded; 95% block bootstrap)",
       xlabel="Window length", ylabel="E = R_news / R_placebo")
ax.legend(title="feed language")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Bursts (exploratory)
#
# A **burst** is a minute when CJK news arrives far faster than its trailing
# 24-hour average, from several independent sources. The baseline ignores time
# of day, so many bursts are the Asian morning ramp-up of feeds. Placebo times
# keep the same time of day, so this does not bias `E`.
#
# - `n10`: CJK events in the last 10 minutes, including the current one
# - `λ`: the average 10-minute count over the previous 24 hours, excluding the
#   current 10-minute window
# - trigger: `n10 ≥ 4λ`, `n10 ≥ 10`, Poisson tail `P(N ≥ n10 | λ) < 0.001`, and
#   at least 3 distinct sources in the window, so one feed's batch dump does
#   not count
# - hysteresis: a burst ends when `n10 < 1.5λ`. A new start needs the previous
#   burst to have ended **and** 121 minutes since the previous start, so the
#   forward window of one burst never overlaps the backward window of the next
#   (up to 60 minutes).
#
# The burst anchor is the minute the threshold was crossed. It uses only events
# decided in or before that minute. A wave that starts while the spacing rule
# blocks it is skipped entirely, never anchored mid-wave. `λ` is undefined until
# 24 hours after the collector's first event.

# %%
def poisson_sf(k: int, lam: float) -> float:
    """P(N >= k) for N ~ Poisson(lam)."""
    if lam <= 0:
        return 0.0 if k > 0 else 1.0
    term = math.exp(-lam)
    cdf = 0.0
    for i in range(k):
        cdf += term
        term *= lam / (i + 1)
    return max(0.0, 1.0 - cdf)


cjk_events = news.loc[news.cjk, ["anchor", "source_name"]]
per_min = (cjk_events.groupby("anchor").size()
           .reindex(minute_index, fill_value=0).astype(float))
per_min[per_min.index < news.anchor.min()] = np.nan  # before the collector started
n10 = per_min.rolling(10, min_periods=10).sum()
lam = per_min.shift(10).rolling(1440, min_periods=1440).mean() * 10
sources_by_minute = cjk_events.groupby("anchor").source_name.agg(set)

burst_anchors, in_burst, last_start = [], False, None
for t in minute_index[(n10 >= 10) & (n10 >= 4 * lam) | (n10 < 1.5 * lam)]:
    n, level = n10[t], lam[t]
    if in_burst:
        in_burst = n >= 1.5 * level
        continue
    if not (n >= 10 and n >= 4 * level):
        continue
    if last_start is not None and t - last_start < pd.Timedelta("121min"):
        in_burst = True  # skip this wave instead of anchoring it mid-way later
        continue
    window = sources_by_minute.loc[t - pd.Timedelta("9min"):t]
    if len(set().union(*window)) < 3 or poisson_sf(int(n), level) >= 1e-3:
        continue
    burst_anchors.append(t)
    in_burst, last_start = True, t

bursts = add_windows(pd.DataFrame({"anchor": burst_anchors}), horizons=[1, 5, 15, 60])
print(f"{len(bursts)} burst starts "
      f"({len(bursts) / per_min.index.normalize().nunique():.1f} per day)")
burst_table = pd.DataFrame([{"horizon_min": h, **excess_ratio(bursts, h)}
                            for h in (1, 5, 15, 60)])
burst_table["p_bh"] = bh_adjust(burst_table.p_two_sided)
burst_table.round(3)

# %% [markdown]
# ## Weak event types (exploratory, CJK, BH-corrected)
#
# Event types come from the unvalidated weak labeler, so treat this as a
# screening pass, not evidence.

# %%
type_rows = [
    {"weak_event_type": event_type, "horizon_min": h, **excess_ratio(part, h)}
    for event_type, part in news.loc[news.cjk].groupby("weak_event_type")
    for h in (1, 5, 15, 60, 240)
]
by_type = pd.DataFrame(type_rows).dropna(subset=["E"])
by_type["p_bh"] = bh_adjust(by_type.p_two_sided)
by_type.sort_values("p_bh").round(3).head(15)

# %% [markdown]
# ## How to read this
#
# - **The primary hypothesis is a strict test.** A negative result means CJK
#   news seen at first sight does not precede larger BTC moves at 60 minutes.
# - **Check the robustness table before any claim of `E < 1`.** If the
#   departure disappears once price-report headlines and poll batches are
#   removed, the news simply describes moves that already happened. That is
#   content, not timing.
# - **`E ≈ 1` means no timing relationship**, not that the news "reports" moves.
# - Bootstrap p-values below 1/1000 print as 0.
#
# **Limits.** About 98 days, with BTC between roughly 58k and 82k USD: a range
# until mid-August, then a breakout of about 25% in one week and a higher range.
# There is no crash in the sample. Weak event labels are unvalidated, and
# `other_crypto` is a broad class that likely contains unlabelled price reports.
# Placebo times are often news times too (CJK news occupies about a third of all
# minutes), which pulls `E` toward 1. Magnitude is not direction. Forward
# returns remain outcomes and never prove that a news item caused a move.
