# Korea Food-Service Permit Aggregate

This Kaggle release contains only a privacy-minimized aggregate derived from the verified nationwide current permit snapshot for three Korean food-service permit categories.

## Coverage

- General restaurants
- Rest cafes
- Bakeries
- Verified parent snapshot rows: 3,010,802
- Released aggregate cells: 67,267
- Minimum released cell count: 10

## Columns

`source_key`, `authority_code`, `source_status_code`, `source_detail_status_code`, `permit_year`, `closure_year`, `cell_count`

## Important interpretation limits

- `permit_year` is not claimed to be a physical opening year.
- `closure_year` is not claimed to be a permanent terminal event.
- Status `03` is not treated as irreversible; two source-level `03->01` reversals were observed during project validation.
- Status `05` remains unresolved.
- `k=10` is a technical minimization threshold, not a legal privacy guarantee.
- This release does not contain row-level permit data, business names, exact addresses, management numbers, phone numbers, or precise coordinates.

See `SOURCES.md` for official source pages and the repository for full reproducibility/provenance.
