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

The 2026-09-08 refresh reconfirmed `이용허락범위 제한 없음` (no restriction on the permitted-use scope) on all three official MOIS OpenAPI detail pages, so the **source-use metadata gate is PASS**. The Public Data Portal policy still requires legitimate permission when third-party rights are actually included, and the project does not treat silence as legal proof that no such rights exist. The final v1 release scope uses the displayed no-restriction metadata as the operational basis to approve **only the verified privacy-minimized aggregate** for Kaggle publication. Raw/row-level mirroring and precise coordinates remain private. Written clarification remains optional additional assurance.

## Privacy

Business name and address are visible upstream concepts, but row-level public builds remain blocked. The released aggregate excludes direct/linkable fields and precise coordinates, coarsens exact dates to years, and suppresses cells below k=10. It has passed technical verification and the separate release-scope decision, while **k=10 is still not represented as a legal privacy guarantee.**
