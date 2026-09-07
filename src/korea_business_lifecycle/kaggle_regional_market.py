from __future__ import annotations

from .kaggle_quickstart import code, markdown


def build_regional_market_notebook() -> dict[str, object]:
    cells = [
        markdown(
            """# South Korea Food-Service Market Map: Regional Opportunity Signals

This notebook turns **3,010,802 current food-service permit records** into a compact regional market atlas for South Korea.

It is designed to answer a practical first question: **where is the current permit-record footprint concentrated, and how does the mix differ by region?**

The analysis is deliberately **supply-side and descriptive**. Permit-record density is not demand, profitability, foot traffic, or investment return. Treat the regional indicators below as screening signals to combine with population, tourism, rent, commercial-area, and mobility data.

The source dataset is a **current snapshot**, not a historical time series or a lossless event log.
"""
        ),
        code(
            """from pathlib import Path
import os
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pandas as pd
import matplotlib.pyplot as plt

input_root = Path(os.environ.get('KAGGLE_INPUT_ROOT', '/kaggle/input'))
matches = sorted(input_root.rglob('korea_food_service_permits.parquet'))
if not matches:
    visible = [str(path.relative_to(input_root)) for path in list(input_root.rglob('*'))[:80]]
    raise FileNotFoundError(f'Dataset input not attached. Visible inputs: {visible}')
PARQUET = matches[0]
pf = pq.ParquetFile(PARQUET)
print(f'{pf.metadata.num_rows:,} rows x {pf.metadata.num_columns} columns')
print(PARQUET)
"""
        ),
        markdown(
            """## 1. Build a stable 17-region display layer

The public table does not include a separately normalized province-name field. For this atlas, the first token of `road_address` (falling back to `lot_address`) is mapped to an English display label for the 17 first-level regions. This is a visualization convenience, **not an authoritative administrative-code join**.
"""
        ),
        code(
            """REGION_EN = {
    '서울특별시': 'Seoul',
    '부산광역시': 'Busan',
    '대구광역시': 'Daegu',
    '인천광역시': 'Incheon',
    '광주광역시': 'Gwangju',
    '대전광역시': 'Daejeon',
    '울산광역시': 'Ulsan',
    '세종특별자치시': 'Sejong',
    '경기도': 'Gyeonggi',
    '강원특별자치도': 'Gangwon',
    '강원도': 'Gangwon',
    '충청북도': 'Chungbuk',
    '충청남도': 'Chungnam',
    '전북특별자치도': 'Jeonbuk',
    '전라북도': 'Jeonbuk',
    '전라남도': 'Jeonnam',
    '경상북도': 'Gyeongbuk',
    '경상남도': 'Gyeongnam',
    '제주특별자치도': 'Jeju',
    '제주도': 'Jeju',
}

base = pq.read_table(
    PARQUET,
    columns=[
        'source_key', 'road_address', 'lot_address', 'permit_date',
        'source_status_code', 'source_coordinate_x', 'source_coordinate_y',
    ],
)
address = pc.coalesce(base['road_address'], base['lot_address'])
region_proxy = pc.list_element(pc.split_pattern(address, pattern=' '), 0)
permit_year = pc.year(base['permit_date'])
coordinates_present = pc.cast(
    pc.and_(pc.invert(pc.is_null(base['source_coordinate_x'])), pc.invert(pc.is_null(base['source_coordinate_y']))),
    pa.int8(),
)
analysis = pa.table({
    'region_proxy': region_proxy,
    'source_key': base['source_key'],
    'permit_year': permit_year,
    'source_status_code': base['source_status_code'],
    'coordinates_present': coordinates_present,
})
"""
        ),
        markdown("## 2. Current permit-record footprint by region"),
        code(
            """region_counts_raw = (
    analysis
    .group_by('region_proxy')
    .aggregate([('source_key', 'count')])
    .to_pandas()
    .rename(columns={'source_key_count': 'records'})
)
region_counts_raw['region'] = region_counts_raw['region_proxy'].map(REGION_EN)
region_counts = (
    region_counts_raw.dropna(subset=['region'])
    .groupby('region', as_index=False)['records'].sum()
    .sort_values('records', ascending=False)
)
region_counts['share_pct'] = 100 * region_counts['records'] / region_counts['records'].sum()
region_counts
"""
        ),
        code(
            """plot_regions = region_counts.sort_values('records')
ax = plot_regions.plot(
    x='region', y='records', kind='barh', figsize=(10, 7),
    title='Current food-service permit records by first-level region'
)
ax.set_xlabel('records in current snapshot')
ax.set_ylabel('region')
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 3. Restaurant / cafe / bakery mix"),
        code(
            """category_raw = (
    analysis
    .group_by(['region_proxy', 'source_key'])
    .aggregate([('source_key', 'count')])
    .to_pandas()
    .rename(columns={'source_key_count': 'records'})
)
category_raw['region'] = category_raw['region_proxy'].map(REGION_EN)
category = (
    category_raw.dropna(subset=['region'])
    .groupby(['region', 'source_key'], as_index=False)['records'].sum()
)
category_mix = category.pivot(index='region', columns='source_key', values='records').fillna(0)
category_share = category_mix.div(category_mix.sum(axis=1), axis=0) * 100
category_share = category_share.loc[region_counts['region']]
category_share.round(1)
"""
        ),
        code(
            """fig, ax = plt.subplots(figsize=(9, 7))
image = ax.imshow(category_share.values, aspect='auto')
ax.set_yticks(range(len(category_share.index)), labels=category_share.index)
ax.set_xticks(range(len(category_share.columns)), labels=category_share.columns, rotation=25, ha='right')
ax.set_title('Category share within each region (%)')
for i in range(category_share.shape[0]):
    for j in range(category_share.shape[1]):
        ax.text(j, i, f'{category_share.iloc[i, j]:.1f}', ha='center', va='center', fontsize=8)
fig.colorbar(image, ax=ax, label='share (%)')
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 4. Recent administrative permit-date share"),
        code(
            """recent_mask = pc.and_(pc.greater_equal(analysis['permit_year'], 2023), pc.less_equal(analysis['permit_year'], 2025))
recent_raw = (
    analysis.filter(recent_mask)
    .group_by('region_proxy')
    .aggregate([('source_key', 'count')])
    .to_pandas()
    .rename(columns={'source_key_count': 'recent_2023_2025'})
)
recent_raw['region'] = recent_raw['region_proxy'].map(REGION_EN)
recent = recent_raw.dropna(subset=['region']).groupby('region', as_index=False)['recent_2023_2025'].sum()
regional_metrics = region_counts.merge(recent, on='region', how='left').fillna({'recent_2023_2025': 0})
regional_metrics['recent_admin_permit_share_pct'] = 100 * regional_metrics['recent_2023_2025'] / regional_metrics['records']
regional_metrics[['region', 'records', 'recent_2023_2025', 'recent_admin_permit_share_pct']].sort_values(
    'recent_admin_permit_share_pct', ascending=False
).round(2)
"""
        ),
        markdown(
            """`permit_date` is an **administrative permit date**, not guaranteed physical opening date. The 2023–2025 share is therefore a composition signal for the current snapshot, not a business-opening or growth rate. 2026 is intentionally excluded because the snapshot year is incomplete.
"""
        ),
        markdown("## 5. Coordinate coverage and raw status composition"),
        code(
            """coord_raw = (
    analysis
    .group_by('region_proxy')
    .aggregate([('coordinates_present', 'sum')])
    .to_pandas()
    .rename(columns={'coordinates_present_sum': 'coordinate_rows'})
)
coord_raw['region'] = coord_raw['region_proxy'].map(REGION_EN)
coord = coord_raw.dropna(subset=['region']).groupby('region', as_index=False)['coordinate_rows'].sum()

status_raw = (
    analysis
    .group_by(['region_proxy', 'source_status_code'])
    .aggregate([('source_key', 'count')])
    .to_pandas()
    .rename(columns={'source_key_count': 'records'})
)
status_raw['region'] = status_raw['region_proxy'].map(REGION_EN)
status = status_raw.dropna(subset=['region']).groupby(['region', 'source_status_code'], as_index=False)['records'].sum()
status_pivot = status.pivot(index='region', columns='source_status_code', values='records').fillna(0)

regional_metrics = regional_metrics.merge(coord, on='region', how='left')
regional_metrics['coordinate_coverage_pct'] = 100 * regional_metrics['coordinate_rows'] / regional_metrics['records']
status01 = status_pivot.get('01', pd.Series(0, index=status_pivot.index))
regional_metrics['source_status_01_pct'] = regional_metrics['region'].map(
    100 * status01 / status_pivot.sum(axis=1)
).fillna(0)
regional_metrics[['region', 'coordinate_coverage_pct', 'source_status_01_pct']].round(2)
"""
        ),
        markdown(
            """Status codes remain **raw source semantics**. In the project evidence, status `03` is reversible, so `01`/`03` must not be relabeled as a guaranteed active/terminal-closed lifecycle without additional semantics. Status `05` remains unresolved where encountered in broader source semantics.
"""
        ),
        markdown("## 6. Regional screening table"),
        code(
            """cafe_bakery = category_share.reindex(columns=['rest_cafes', 'bakeries'], fill_value=0).sum(axis=1)
regional_metrics['cafe_bakery_share_pct'] = regional_metrics['region'].map(cafe_bakery).fillna(0)
screen = regional_metrics[[
    'region', 'records', 'share_pct', 'recent_admin_permit_share_pct',
    'cafe_bakery_share_pct', 'coordinate_coverage_pct', 'source_status_01_pct',
]].sort_values('records', ascending=False)
screen.round(2)
"""
        ),
        code(
            """fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(screen['records'], screen['recent_admin_permit_share_pct'], s=80)
for _, row in screen.iterrows():
    ax.annotate(row['region'], (row['records'], row['recent_admin_permit_share_pct']), xytext=(4, 4), textcoords='offset points', fontsize=8)
ax.set_xscale('log')
ax.set_xlabel('current permit records (log scale)')
ax.set_ylabel('2023-2025 administrative permit-date share (%)')
ax.set_title('Regional screening: market footprint vs recent permit-date composition')
plt.tight_layout()
plt.show()
"""
        ),
        markdown(
            """## 7. How to turn this into a real opportunity model

The table above is intentionally **not an opportunity score**. A stronger market model should join the permit snapshot to independent demand/cost variables such as:

- resident and daytime population;
- domestic/international visitor volumes;
- commercial rent or assessed land values;
- card-spend or foot-traffic indicators where legally available;
- transit accessibility and commercial-area boundaries;
- competition density normalized by population or spending.

The dataset contributes the supply-side establishment/permit footprint. The external datasets contribute demand, cost, and accessibility context.
"""
        ),
        markdown(
            """## 8. Semantic guardrails

- This is a **current snapshot**, not a historical time series.
- `management_number` is a bounded continuity candidate, not an official primary key.
- `permit_date` is administrative and is not guaranteed to equal physical opening date.
- `closure_date` is contextual and is not assumed to be an irreversible terminal event.
- `source_coordinate_x` / `source_coordinate_y` are **EPSG:5174** in this verified snapshot (X=easting, Y=northing).
- The public dataset does not include the separately derived WGS84 sidecar.
- Address-derived region labels are visualization helpers; use official code/reference joins for authoritative administrative analysis.

This notebook is exploratory analysis, **not investment advice**.
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
