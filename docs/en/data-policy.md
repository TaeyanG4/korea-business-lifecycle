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

The 2026-09-08 refresh reconfirmed `이용허락범위 제한 없음` (no restriction on the permitted-use scope) on all three official MOIS OpenAPI detail pages, so the **source-use metadata gate is PASS**. The Public Data Portal policy still requires legitimate permission when third-party rights are actually included, and the project does not treat silence as legal proof that no such rights exist. The current v1 release scope approves both the existing privacy-minimized aggregate and the **3,010,802-row canonical PERMIT release**. Canonical source EPSG:5174 coordinates are included in the row-level release; the separately derived WGS84 sidecar and partial history remain unpublished. Written clarification remains optional additional assurance.

## Privacy

Under the current publication approval, the canonical row-level release preserves the canonical 26 columns, including business name, address, management number, and source EPSG:5174 coordinates. The separate aggregate still excludes direct/linkable fields and precise coordinates, coarsens exact dates to years, and suppresses cells below k=10. **k=10 is not represented as a legal privacy guarantee.** Telephone/homepage fields are not in the canonical parent and therefore are not in the row-level release.
