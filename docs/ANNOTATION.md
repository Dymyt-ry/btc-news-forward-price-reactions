# Weak annotation provenance

Weak annotations were generated from titles and RSS summaries without market
outcome features. Reusable publisher text appears only in the reviewed,
attributed PANews, U.S. SEC, and Federal Reserve subset; other publishers remain
metadata-only.

- Method: `multilingual-e5-hybrid-v1.3`
- Model: `intfloat/multilingual-e5-small`
- Revision: `614241f622f53c4eeff9890bdc4f31cfecc418b3`
- Artifact SHA-256: `84add3360f1463eb88218ef02a98e1e51f02f1d4585ccd18829266a52140aea3`
- Rules SHA-256: `c29dbc818be767f6d73a5e6b7d6e833ad5b23655e1a23cf66dfe33cc71735b96`
- Prototypes SHA-256: `bfe19a889019be59a5c4bad0ebb4b11b2459884ba196ec30a3778d0de73a5b94`

Scores and margin bands are not probabilities. No accuracy, F1, calibration, or
representativeness claim is made. The release archive stores the full output at
`data/weak_annotations/unknown.parquet` and the analysis-ready text-bearing
subset at `data/licensed_news_price_reaction/unknown.parquet`.

