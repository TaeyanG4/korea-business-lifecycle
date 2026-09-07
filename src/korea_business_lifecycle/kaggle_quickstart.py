from __future__ import annotations

import hashlib


def _cell_id(cell_type: str, source: str) -> str:
    return hashlib.sha256(f"{cell_type}\0{source}".encode("utf-8")).hexdigest()[:8]


def markdown(source: str) -> dict[str, object]:
    return {
        "cell_type": "markdown",
        "id": _cell_id("markdown", source),
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code(source: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "id": _cell_id("code", source),
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def build_notebook() -> dict[str, object]:
    cells = [
        markdown(
            """# Korea Food-Service Permits: 3M-Row Quickstart

This notebook is a lightweight starting point for the **South Korea Food-Service Permits - Snapshot** dataset.

The dataset contains **3,010,802 current permit records** for general restaurants, rest cafes, and bakeries across South Korea. The same 26-column table is available as CSV and Parquet; this notebook uses Parquet for fast selective reads.

This is a **current snapshot**, not a historical time series or lossless lifecycle event log.

### What you can do here

- compare restaurant / cafe / bakery coverage at nationwide scale;
- inspect source-reported permit statuses without forcing them into irreversible lifecycle labels;
- explore administrative permit-year patterns and business-type mix;
- measure address / coordinate completeness before geospatial preprocessing;
- switch between compact Parquet analysis and the compatibility CSV without changing row scope.
"""
        ),
        code(
            """from pathlib import Path
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pandas as pd
import matplotlib.pyplot as plt

input_root = Path('/kaggle/input')
parquet_matches = sorted(input_root.rglob('korea_food_service_permits.parquet'))
csv_matches = sorted(input_root.rglob('korea_food_service_permits.csv'))
if not parquet_matches or not csv_matches:
    visible = [str(path.relative_to(input_root)) for path in list(input_root.rglob('*'))[:80]]
    raise FileNotFoundError(f'Dataset input files not attached. Visible inputs: {visible}')
PARQUET = parquet_matches[0]
CSV = csv_matches[0]
DATA_DIR = PARQUET.parent

print('Files:')
for path in sorted(DATA_DIR.iterdir()):
    print(f'  {path.name:40s} {path.stat().st_size / 1024**2:9.1f} MiB')
"""
        ),
        markdown("## 1. Verify the published shape without loading 3 million rows into pandas"),
        code(
            """pf = pq.ParquetFile(PARQUET)
print(f'Rows:    {pf.metadata.num_rows:,}')
print(f'Columns: {pf.metadata.num_columns}')
print(f'Row groups: {pf.metadata.num_row_groups}')
print()
print('First 10 column names:')
print(pf.schema_arrow.names[:10])
"""
        ),
        markdown("## 2. Category coverage"),
        code(
            """source_table = pq.read_table(PARQUET, columns=['source_key'])
source_counts = source_table.group_by('source_key').aggregate([('source_key', 'count')]).to_pandas()
source_counts = source_counts.rename(columns={'source_key_count': 'records'}).sort_values('records', ascending=False)
source_counts
"""
        ),
        code(
            """ax = source_counts.set_index('source_key')['records'].plot(kind='bar', figsize=(8, 4), title='Records by source category')
ax.set_ylabel('records')
ax.tick_params(axis='x', rotation=0)
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 3. Regional market-size proxy from address text"),
        code(
            """address_table = pq.read_table(PARQUET, columns=['road_address', 'lot_address'])
address = pc.coalesce(address_table['road_address'], address_table['lot_address'])
region = pc.list_element(pc.split_pattern(address, pattern=' '), 0)
region_table = pa.table({'region_proxy': region})
region_counts = (
    region_table
    .group_by('region_proxy')
    .aggregate([('region_proxy', 'count')])
    .to_pandas()
    .rename(columns={'region_proxy_count': 'records'})
    .dropna()
    .query("region_proxy != ''")
    .sort_values('records', ascending=False)
)
region_counts.head(20)
"""
        ),
        code(
            """top_regions = region_counts.head(17).sort_values('records')
ax = top_regions.plot(
    x='region_proxy', y='records', kind='barh', figsize=(9, 6),
    title='Current permit records by address-derived region proxy'
)
ax.set_xlabel('records in current snapshot')
ax.set_ylabel('address first token')
plt.tight_layout()
plt.show()
"""
        ),
        markdown(
            """The regional label above is a **display-oriented proxy derived from the first token of `road_address`, falling back to `lot_address`**. It is useful for quick nationwide comparisons, but it is not presented as an authoritative administrative-region code. Use `authority_code` or an external official boundary/reference table when exact administrative joins matter.
"""
        ),
        markdown("## 4. Raw source status distribution"),
        code(
            """status_table = pq.read_table(PARQUET, columns=['source_key', 'source_status_code', 'source_status_name'])
status_counts = (
    status_table
    .group_by(['source_key', 'source_status_code', 'source_status_name'])
    .aggregate([('source_key', 'count')])
    .to_pandas()
    .rename(columns={'source_key_count': 'records'})
    .sort_values(['source_key', 'records'], ascending=[True, False])
)
status_counts.head(20)
"""
        ),
        markdown(
            """**Interpretation caution:** source status codes/names are preserved as reported. This project does not force them into a canonical active/closed/terminal label. In observed evidence, status `03` is not irreversible, and status `05` remains semantically unresolved.
"""
        ),
        markdown("## 5. Permit-year coverage"),
        code(
            """permit_dates = pq.read_table(PARQUET, columns=['permit_date'])['permit_date']
years = pc.year(permit_dates)
year_table = pa.table({'permit_year': years})
year_counts = (
    year_table
    .group_by('permit_year')
    .aggregate([('permit_year', 'count')])
    .to_pandas()
    .rename(columns={'permit_year_count': 'records'})
    .dropna()
    .sort_values('permit_year')
)
year_counts.tail(20)
"""
        ),
        code(
            """recent_years = year_counts[year_counts['permit_year'] >= 2000].copy()
ax = recent_years.plot(
    x='permit_year', y='records', kind='line', marker='o', figsize=(10, 4),
    title='Administrative permit records by permit year (2000+)'
)
ax.set_xlabel('permit year')
ax.set_ylabel('records in current snapshot')
plt.tight_layout()
plt.show()
"""
        ),
        markdown(
            """`permit_date` is an administrative permit date. It should **not** automatically be interpreted as the physical opening date of a business.
"""
        ),
        markdown("## 6. Business-type mix"),
        code(
            """type_table = pq.read_table(PARQUET, columns=['source_key', 'business_type_name'])
type_counts = (
    type_table
    .group_by(['source_key', 'business_type_name'])
    .aggregate([('source_key', 'count')])
    .to_pandas()
    .rename(columns={'source_key_count': 'records'})
    .sort_values('records', ascending=False)
)
type_counts.head(20)
"""
        ),
        markdown("## 7. Data-quality quick check"),
        code(
            """quality_columns = [
    'business_name', 'lot_address', 'road_address',
    'source_coordinate_x', 'source_coordinate_y', 'closure_date',
]
quality = pq.read_table(PARQUET, columns=quality_columns)
quality_rows = []
for name in quality_columns:
    column = quality[name]
    present = column.length() - column.null_count
    quality_rows.append({
        'column': name,
        'present_rows': present,
        'missing_rows': column.null_count,
        'present_pct': round(100 * present / column.length(), 2),
    })
quality_summary = pd.DataFrame(quality_rows).sort_values('present_pct', ascending=False)
quality_summary
"""
        ),
        markdown(
            """`closure_date` completeness is **not** a generic quality target: null can be expected for records without a source-reported closure date. The table is meant to show field availability, not to imply that every field should be populated.
"""
        ),
        markdown(
            """## 8. Practical analysis ideas

This snapshot is especially useful for questions that do **not** require a reconstructed event history:

- compare the current permit-record footprint of restaurants, cafes, and bakeries across address-derived regions;
- identify regions or business types with unusually high concentrations of source-reported statuses;
- compare permit-year composition across categories without treating permit date as a physical opening date;
- quantify address and coordinate coverage before geocoding or mapping;
- create market-screening features by combining this snapshot with official population, tourism, rent, or commercial-area datasets.

For reproducible downstream work, keep the raw source status fields and documented semantic cautions rather than collapsing them into an invented active/closed binary.
"""
        ),
        markdown("## 9. Human-readable sample"),
        code(
            """sample_columns = [
    'source_key', 'authority_code', 'management_number', 'permit_date',
    'source_status_name', 'source_detail_status_name', 'closure_date',
    'business_name', 'business_type_name', 'road_address',
    'source_coordinate_x', 'source_coordinate_y',
]
sample = pf.read_row_group(0, columns=sample_columns).slice(0, 10).to_pandas()
sample
"""
        ),
        markdown(
            """## 10. CSV users

The CSV contains the **same 3,010,802 rows and 26 columns** as the Parquet file. It is about 1.4 GB, so for exploratory work you may want to read only selected columns or use chunked loading.
"""
        ),
        code(
            """# Small CSV preview without loading the full 1.4 GB file
csv_preview = pd.read_csv(CSV, nrows=5)
csv_preview
"""
        ),
        markdown(
            """## 11. Important semantic and geospatial notes

- `management_number` is retained as a **bounded continuity candidate**, not asserted as an official primary key.
- `permit_date` is not necessarily the physical opening date.
- `closure_date` is contextual and is not assumed to be a permanent terminal event.
- `source_coordinate_x` / `source_coordinate_y` use **EPSG:5174** for this verified snapshot (X=easting, Y=northing).
- The separately derived WGS84 sidecar is **not included** in this public dataset.
- Partial history is **not included**; this release should not be described as a time series.

See `DATA_DICTIONARY.md`, `schema.json`, `SOURCES.md`, and `release-manifest.json` in the dataset for exact documentation and provenance.
"""
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
