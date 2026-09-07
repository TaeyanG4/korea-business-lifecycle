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

The 2026-09-07 refresh reconfirmed `이용허락범위 제한 없음` (no restriction on the permitted-use scope) on all three official MOIS OpenAPI detail pages, so the project now records the **source-use metadata gate as PASS**. The reviewed license sections did not separately establish whether third-party rights are present, while the Public Data Portal policy requires legitimate permission where such rights are included. Absence of a source-specific third-party statement is not treated as proof that no such rights exist, so both raw Kaggle mirroring and external redistribution of the privacy-minimized aggregate remain `UNRESOLVED`. The exact questions and official contact routes are frozen in [Redistribution Written-Clarification Gate](redistribution-clarification.md); no inquiry or email is sent automatically.

## Privacy

Business name and address are visible upstream concepts, but nationwide republication suitability requires a separate review and row-level public builds remain blocked. The separate aggregate candidate excludes direct/linkable fields and precise coordinates, coarsens exact dates to years, and suppresses cells below k=10; those technical controls are not represented as a legal privacy guarantee or redistribution permission.
