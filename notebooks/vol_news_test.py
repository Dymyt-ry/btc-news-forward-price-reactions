# %% [markdown]
# # Does crypto news improve BTC volatility forecasts beyond price history?
#
# News timing does not lead BTC direction or move size (see the
# forward/backward notebook). A weaker but economically relevant question
# remains: **does knowing how much news arrived improve a forecast of how much
# BTC will move next hour, beyond what price history already says?**
# Volatility clusters, so a price-only model is a strong baseline.
#
# ## Pre-registered primary hypothesis
#
# Written before looking at any result in this notebook:
#
# > **H1:** Adding CJK news-flow features (excluding price-report headline
# > types) to a price-only HAR model with hour-of-day effects reduces the
# > **out-of-sample** mean squared error of next-hour log realized volatility.
# > A one-sided Diebold–Mariano test gives p < 0.05 on the chronological test
# > period.
#
# Other feature sets and splits are exploratory.

# %%
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CJK = {"ko", "zh", "ja"}
PRICE_REPORT_TYPES = {"market_commentary", "liquidation_leverage", "whale_onchain"}
PRIMARY_TRAIN_SHARE = 0.6
EMBARGO = pd.Timedelta("24h")  # the longest feature lookback


def find(kaggle_name: str, release_path: str) -> Path:
    """Locate a file on Kaggle (flat names) or in a local release (hierarchical)."""
    for root, pattern in [(Path("/kaggle/input"), kaggle_name), (Path("."), release_path)]:
        if root.exists():
            matches = sorted(root.rglob(pattern))
            if len(matches) == 1:
                return matches[0]
    raise FileNotFoundError(f"Expected exactly one {kaggle_name} / {release_path}")


news_all = pd.read_parquet(find("START_HERE__all_news_price_reaction.parquet",
                                "news_price_reaction/unknown.parquet"))
market = pd.read_parquet(find("data__market_1m__unknown.parquet",
                              "market_1m/unknown.parquet"),
                         columns=["symbol", "open_time", "open"])
price = (market.loc[market.symbol.eq("BTCUSDT")]
         .set_index("open_time")["open"].sort_index())
assert (price.index.to_series().diff().dropna() == pd.Timedelta("1min")).all()

# %% [markdown]
# ## Target and price-only features
#
# One-minute log returns `r_i = ln(open[i+1] / open[i])`. On an hourly grid `t`:
#
# - **target**: log realized volatility of the next hour,
#   `log sqrt(Σ r_i²)` over minutes `t … t+59`
# - **HAR features**: log RV of the last 1 hour, and the log of the average
#   hourly RV over the last 6 and 24 hours
# - **hour-of-day** dummies, because crypto volatility has a strong intraday cycle
#
# Everything on the feature side uses only minutes before `t`.

# %%
r = np.log(price).diff().shift(-1)          # r at minute i = move from i to i+1
r2_hourly = (r ** 2).resample("1h").sum(min_count=60)
rv = np.sqrt(r2_hourly)                     # RV of hour starting at t
grid = pd.DataFrame({"y": np.log(rv)})
grid["har_1h"] = np.log(rv.shift(1))
grid["har_6h"] = np.log(np.sqrt(r2_hourly.shift(1).rolling(6).mean()))
grid["har_24h"] = np.log(np.sqrt(r2_hourly.shift(1).rolling(24).mean()))
grid["hour"] = grid.index.hour
grid["weekday"] = grid.index.dayofweek

# %% [markdown]
# ## News-flow features
#
# One RSS poll can deliver dozens of items in the same minute, so raw counts
# mostly measure polling. The features count **minutes with at least one
# event**, which is robust to batches:
#
# - `cjk_min_1h`: minutes in the last hour with a CJK event (price-report
#   types excluded)
# - `cjk_surprise`: that count relative to its trailing 24-hour hourly average
#   (log ratio). "Unusually busy" matters more than "busy".
# - exploratory extras: CJK price-report minutes, English minutes, and
#   macro-liquidity minutes
#
# An event belongs to the hour in which the collector made its decision, so it
# is known by the end of that hour.

# %%
news = news_all.loc[news_all.decision_id.notna()
                    & ~news_all.clock_drift_overlap.astype("boolean").fillna(False)].copy()
news["minute"] = news.decision_created_at.dt.floor("min")
news["cjk"] = news.feed_language_hint.isin(CJK)
news["price_report"] = news.weak_event_type.isin(PRICE_REPORT_TYPES)


def busy_minutes_per_hour(mask: pd.Series) -> pd.Series:
    minutes = news.loc[mask, "minute"].drop_duplicates()
    per_hour = minutes.dt.floor("h").value_counts()
    # Shift by one hour: the value at t describes the hour *before* t.
    return per_hour.reindex(grid.index, fill_value=0).sort_index().shift(1)


grid["cjk_min_1h"] = busy_minutes_per_hour(news.cjk & ~news.price_report)
trailing = grid.cjk_min_1h.shift(1).rolling(24).mean()
grid["cjk_surprise"] = np.log((grid.cjk_min_1h + 1) / (trailing + 1))
grid["cjk_price_min_1h"] = busy_minutes_per_hour(news.cjk & news.price_report)
grid["en_min_1h"] = busy_minutes_per_hour(news.feed_language_hint.eq("en"))
grid["macro_min_1h"] = busy_minutes_per_hour(news.weak_event_type.eq("macro_liquidity"))
grid = grid.dropna()
print(f"{len(grid):,} hourly observations, {grid.index.min()} → {grid.index.max()}")

# %% [markdown]
# ## Models and evaluation
#
# OLS fitted on the first part of the sample and evaluated on the later part,
# with a 24-hour embargo between them. Losses are compared with the
# **Diebold–Mariano** test using Newey–West standard errors (24 lags), because
# hourly forecast errors are autocorrelated. Every model is compared with its
# own price-only baseline.

# %%
HAR = ["har_1h", "har_6h", "har_24h"]
CJK_NEWS = ["cjk_min_1h", "cjk_surprise"]
ALL_NEWS = CJK_NEWS + ["cjk_price_min_1h", "en_min_1h", "macro_min_1h"]
# name: (features, weekday dummies?, baseline name)
MODELS = {
    "price only (HAR + hour)": (HAR, False, None),
    "+ CJK news [primary]": (HAR + CJK_NEWS, False, "price only (HAR + hour)"),
    "price only + weekday": (HAR, True, None),
    "+ weekday + CJK news": (HAR + CJK_NEWS, True, "price only + weekday"),
    "+ weekday + all news": (HAR + ALL_NEWS, True, "price only + weekday"),
}


def design(frame: pd.DataFrame, columns: list[str], weekday: bool) -> np.ndarray:
    parts = [np.ones((len(frame), 1)), frame[columns].to_numpy()]
    for name, levels in [("hour", range(1, 24))] + ([("weekday", range(1, 7))] if weekday else []):
        dummies = pd.get_dummies(frame[name], dtype=float)
        parts.append(dummies.reindex(columns=list(levels), fill_value=0.0).to_numpy())
    return np.column_stack(parts)


def forecast(train: pd.DataFrame, test: pd.DataFrame, model: str) -> np.ndarray:
    columns, weekday, _ = MODELS[model]
    beta, *_ = np.linalg.lstsq(design(train, columns, weekday), train.y.to_numpy(), rcond=None)
    return design(test, columns, weekday) @ beta


def diebold_mariano(loss_base: np.ndarray, loss_new: np.ndarray, lags: int = 24) -> float:
    """DM statistic, positive when the new model has lower loss (Newey–West)."""
    d = loss_base - loss_new
    n = len(d)
    d_c = d - d.mean()
    var = d_c @ d_c / n
    for k in range(1, lags + 1):
        weight = 1 - k / (lags + 1)
        var += 2 * weight * (d_c[k:] @ d_c[:-k]) / n
    return d.mean() / np.sqrt(var / n)


def normal_sf(x: float) -> float:
    return 0.5 * math.erfc(x / math.sqrt(2))


def compare(losses: dict[str, pd.Series], label) -> pd.DataFrame:
    rows = []
    for name, (_, _, baseline) in MODELS.items():
        if baseline is None:
            continue
        stat = diebold_mariano(losses[baseline].to_numpy(), losses[name].to_numpy())
        rows.append({
            "evaluation": label,
            "model": name,
            "baseline": baseline,
            "test_hours": len(losses[name]),
            "mse_vs_baseline_pct": 100 * (losses[name].mean() / losses[baseline].mean() - 1),
            "dm_stat": stat,
            "p_one_sided": normal_sf(stat),
        })
    return pd.DataFrame(rows)


def evaluate_split(train_share: float) -> pd.DataFrame:
    cut = grid.index[int(len(grid) * train_share)]
    train = grid.loc[grid.index < cut]
    test = grid.loc[grid.index >= cut + EMBARGO]
    losses = {m: (test.y - forecast(train, test, m)) ** 2 for m in MODELS}
    return compare(losses, f"split {train_share:.0%}")


def evaluate_rolling(first_days: int = 30) -> pd.DataFrame:
    """Expanding window, refit every day, forecast the next day's hours."""
    days = grid.index.normalize().unique()
    losses = {m: [] for m in MODELS}
    for day in days[first_days:]:
        train = grid.loc[grid.index < day]
        test = grid.loc[(grid.index >= day) & (grid.index < day + pd.Timedelta("1D"))]
        for m in MODELS:
            losses[m].append((test.y - forecast(train, test, m)) ** 2)
    return compare({m: pd.concat(v) for m, v in losses.items()}, "rolling daily")


# %% [markdown]
# ## Primary result (exactly as pre-registered)

# %%
primary = evaluate_split(PRIMARY_TRAIN_SHARE)
row = primary.set_index("model").loc["+ CJK news [primary]"]
verdict = ("SUPPORTED" if row.p_one_sided < 0.05 and row.mse_vs_baseline_pct < 0
           else "NOT SUPPORTED")
print(f"H1 as registered: {verdict} (MSE change {row.mse_vs_baseline_pct:+.2f}%, "
      f"DM p = {row.p_one_sided:.3f})")

# %% [markdown]
# ## Post-hoc robustness: calendar control and evaluation design
#
# **Added after seeing the primary result**, following an independent review.
# CJK news flow is much lower at weekends (correlation with a weekend indicator
# about −0.5), and weekend volatility is much lower too. The registered
# baseline has hour-of-day but no day-of-week effects, so a news count can
# "win" simply by recognising Saturdays. The rows with `+ weekday` give both
# models day-of-week dummies. Rolling daily refits replace the single split,
# whose result depends on where the cut falls. p-values in this table are
# Benjamini–Hochberg adjusted (`p_bh`).

# %%
robust = pd.concat(
    [evaluate_split(s) for s in (0.5, 0.6, 0.7, 0.8)] + [evaluate_rolling()],
    ignore_index=True,
)
p = robust.p_one_sided.to_numpy()
order = np.argsort(p)
ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
robust.loc[robust.index[order], "p_bh"] = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
robust.pivot(index="model", columns="evaluation", values="mse_vs_baseline_pct").round(2)

# %%
robust.round(4)

# %% [markdown]
# ## Why the registered result passed
#
# The weekday baseline alone, with no news, against the registered baseline:

# %%
cut = grid.index[int(len(grid) * PRIMARY_TRAIN_SHARE)]
train, test = grid.loc[grid.index < cut], grid.loc[grid.index >= cut + EMBARGO]
base = (test.y - forecast(train, test, "price only (HAR + hour)")) ** 2
weekday_only = (test.y - forecast(train, test, "price only + weekday")) ** 2
news_only = (test.y - forecast(train, test, "+ CJK news [primary]")) ** 2
print(f"weekday dummies, no news: {100 * (weekday_only.mean() / base.mean() - 1):+.2f}% MSE")
print(f"CJK news, no weekday:     {100 * (news_only.mean() / base.mean() - 1):+.2f}% MSE")
print(f"corr(cjk_min_1h, weekend): "
      f"{grid.cjk_min_1h.corr((grid.weekday >= 5).astype(float)):+.2f}")

# %%
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(test.index, test.y, linewidth=0.6, label="realized (log RV)")
ax.plot(test.index, forecast(train, test, "price only + weekday"),
        linewidth=0.9, label="price + weekday")
ax.plot(test.index, forecast(train, test, "+ weekday + CJK news"),
        linewidth=0.9, label="+ CJK news", alpha=0.8)
ax.set(title="Next-hour log realized volatility, out-of-sample", ylabel="log RV")
ax.legend()
plt.tight_layout()
plt.show()

# %% [markdown]
# ## How to read this
#
# - **The registered test can pass for the wrong reason.** If news gains vanish
#   once day-of-week is controlled, news flow was only a calendar proxy. The
#   honest conclusion is then that news adds nothing beyond price history plus
#   the weekly calendar.
# - A negative `mse_vs_baseline_pct` that survives weekday controls, rolling
#   evaluation and BH correction would be a real, if small, signal.
# - Even a real signal is not a trading edge. Option prices (implied
#   volatility) already embed market expectations, so a forecast has to beat
#   implied volatility, not just a price-only model.
# - The DM test is conservative for nested models with estimated parameters
#   (Clark–West would be sharper). That matters for power, not for the
#   calendar confound.
#
# **Limits.** About 98 days, with BTC between roughly 58k and 82k USD (a range
# until mid-August, then a breakout of about 25% and a higher range), one
# exchange's prices, and hourly resolution. The news features were chosen using the
# forward/backward analysis of the same period. A clean confirmation needs data
# collected after 2026-09-18.
