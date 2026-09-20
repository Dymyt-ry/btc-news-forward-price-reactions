# Rights and license review

Review date: 2026-09-19. This is a technical publication review, not legal
advice. The full release archive contains the row/source-level decision table at
`data/rights_matrix/unknown.parquet` and reviewed endpoints/evidence at
`data/source_registry/unknown.parquet`.

## PANews

[PANews User Agreement §2.4](https://www.panewslab.com/en/user-agreement)
permits non-commercial reproduction of user-published content when the original
author appears prominently, the original link and `Source: PANews` are retained,
and the content is not modified. Section 2.5 requires separate authorization for
content marked `Reproduction Prohibited`.

This release includes 12,309 PANews RSS rows. Each retained row carries the
displayed byline, original/canonical link, source credit, and the unmodified
English title/RSS excerpt from the frozen collector snapshot. A conservative
restriction-marker scan is included, but a false value is not a publisher
warranty.

## Other included values

- Binance market/funding data and derived outcomes come from the
  [MIT-licensed public-data repository](https://github.com/binance/binance-public-data/blob/master/README.md?plain=1).
- U.S. SEC text follows the [SEC reuse policy](https://www.sec.gov/about/privacy-information).
- Federal Reserve text follows the [Board disclaimer and public-domain policy](https://www.federalreserve.gov/disclaimer.htm).
- Coin Metrics Community data is not included in v0.6.3.

Other publisher text remains withheld. The compiled dataset has mixed terms,
and the documented PANews conditions make the text-bearing release
non-commercial. Preserve attribution and source links whenever reuse is allowed.

