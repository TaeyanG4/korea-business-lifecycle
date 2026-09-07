# Data and privacy policy

## Never commit to Git

- raw/bulk source data;
- nationwide staging/processed data;
- logs;
- API keys or credentials;
- private prompt/task files;
- local AI/agent instructions; or
- unreviewed personal/contact fields.

Real data lives under the Git-ignored `data/local/` runtime tree by default. `KBL_DATA_ROOT` may override it, but any repository-local override must stay under `data/local/`.

## Public access vs redistribution

Access through the Public Data Portal is not treated as equivalent to permission to mirror raw records on Kaggle. The portal policy explicitly requires review of third-party rights where applicable. The v1 catalog label is therefore preserved as evidence while Kaggle redistribution remains `UNRESOLVED`.

## Privacy

Business name and address are visible upstream concepts, but nationwide republication suitability requires a separate review. A future public build must be generated from an explicit allowlist.
