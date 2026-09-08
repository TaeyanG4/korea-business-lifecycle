from __future__ import annotations

from .kaggle_quickstart import code, markdown


def build_notebook() -> dict[str, object]:
    cells = [
        markdown(
            """# Where Will New F&B Permits Appear? Business ML on 3 Million Korean Records

This notebook turns the **South Korea Food-Service Permits - Snapshot** into a business forecasting problem:

> **Which local authority × food-service category markets are likely to generate the most new administrative permits over the next 3 months?**

The commercial use case is territory planning for POS/payment providers, food-service suppliers, kitchen-equipment vendors, franchise development teams, and commercial real-estate analysts.

### What this notebook does

1. audits temporal coverage and source freshness;
2. converts 3,010,802 permit rows into a monthly local-market panel;
3. builds leakage-safe lag / rolling / seasonality features;
4. performs quarterly **walk-forward validation**;
5. compares seasonal naive, XGBoost Poisson, squared-error, Tweedie, and a seasonal/ML blend;
6. evaluates business metrics such as **top-10% market capture**;
7. explains the tree model with SHAP when available;
8. attaches empirical conformal-style uncertainty bands to the final holdout predictions.

**Important scope:** this dataset is a **current snapshot**, not 12 monthly snapshots. We forecast the future count of rows by their administrative `permit_date`; we do **not** reconstruct past monthly market states or claim that `permit_date` is the physical opening date.
"""
        ),
        markdown(
            """## 1. Business scenario and leakage rules

**Decision:** prioritize local markets for sales coverage / expansion research.

**Unit:** `authority_code × source_key` (general restaurants, rest cafes, bakeries).

**Target:** cumulative number of new administrative permits in the **next 3 calendar months**.

**Leakage controls:**

- only permit counts dated on or before the forecast cut-off are used as features;
- current `source_status_*`, `closure_date`, current business counts, and other present-day fields are intentionally excluded from historical backtests;
- a training row is usable only when its complete 3-month future target would already have been observable at that backtest date;
- 2026-08/09 are excluded from model evaluation because the current snapshot shows a sharp bakery-series freshness anomaly in August and September is partial.
"""
        ),
        code(
            """from pathlib import Path
import os
import warnings

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

warnings.filterwarnings('ignore', category=FutureWarning)

input_root = Path(os.environ.get('KAGGLE_INPUT_ROOT', '/kaggle/input'))
matches = sorted(input_root.rglob('korea_food_service_permits.parquet'))
if not matches:
    raise FileNotFoundError('Attach the South Korea Food-Service Permits - Snapshot dataset.')
PARQUET = matches[0]
pf = pq.ParquetFile(PARQUET)

print(f'Dataset: {PARQUET}')
print(f'Rows: {pf.metadata.num_rows:,}')
print(f'Columns: {pf.metadata.num_columns}')
"""
        ),
        markdown("## 2. Temporal EDA: what history is actually available?"),
        code(
            """raw = pq.read_table(PARQUET, columns=['permit_date', 'authority_code', 'source_key'])

freshness = (
    raw.group_by('source_key')
       .aggregate([('permit_date', 'max')])
       .to_pandas()
       .rename(columns={'permit_date_max': 'max_permit_date'})
)
freshness
"""
        ),
        code(
            """calendar = pa.table({
    'permit_year': pc.year(raw['permit_date']),
    'permit_month_num': pc.month(raw['permit_date']),
    'authority_code': raw['authority_code'],
    'source_key': raw['source_key'],
})

monthly_raw = (
    calendar.group_by(['permit_year', 'permit_month_num', 'authority_code', 'source_key'])
            .aggregate([('authority_code', 'count')])
            .to_pandas()
            .rename(columns={'authority_code_count': 'permit_count'})
            .dropna(subset=['permit_year', 'permit_month_num', 'authority_code', 'source_key'])
)
monthly_raw['permit_year'] = monthly_raw['permit_year'].astype(int)
monthly_raw['permit_month_num'] = monthly_raw['permit_month_num'].astype(int)
monthly_raw['authority_code'] = monthly_raw['authority_code'].astype(str)
monthly_raw['source_key'] = monthly_raw['source_key'].astype(str)
monthly_raw['permit_month'] = pd.to_datetime(dict(
    year=monthly_raw['permit_year'], month=monthly_raw['permit_month_num'], day=1
))

recent = monthly_raw[(monthly_raw['permit_month'] >= '2024-01-01')].groupby(
    ['permit_month', 'source_key'], as_index=False
)['permit_count'].sum()
recent.pivot(index='permit_month', columns='source_key', values='permit_count').fillna(0).tail(32)
"""
        ),
        code(
            """recent_plot = recent.pivot(index='permit_month', columns='source_key', values='permit_count').fillna(0)
ax = recent_plot.plot(figsize=(11, 5), marker='o', title='Monthly administrative permit counts by source (2024+)')
ax.axvline(pd.Timestamp('2026-08-01'), linestyle='--', alpha=0.5)
ax.set_ylabel('new permit rows')
ax.set_xlabel('permit month')
plt.tight_layout()
plt.show()
"""
        ),
        markdown(
            """The plot is also a **data-freshness control**, not just an EDA chart. The current snapshot shows an unusually sharp bakery drop in 2026-08 while all three sources have rows dated through 2026-09-04. Rather than silently treating that as a real market collapse, the model evaluation stops at **2026-06 targets**.
"""
        ),
        markdown("## 3. Stable modeling window and seasonality"),
        code(
            """stable = monthly_raw[(monthly_raw['permit_month'] >= '2018-01-01') & (monthly_raw['permit_month'] <= '2026-06-01')].copy()

yearly = stable.groupby(stable['permit_month'].dt.year)['permit_count'].sum()
print(yearly.to_string())

seasonality = (
    stable[stable['permit_year'].between(2018, 2025)]
    .groupby(['permit_month_num', 'source_key'], as_index=False)['permit_count']
    .mean()
)
seasonality_pivot = seasonality.pivot(index='permit_month_num', columns='source_key', values='permit_count')
seasonality_pivot
"""
        ),
        code(
            """ax = seasonality_pivot.plot(figsize=(10, 4), marker='o', title='Average monthly permit volume by calendar month (2018-2025)')
ax.set_xlabel('calendar month')
ax.set_ylabel('average permits')
ax.set_xticks(range(1, 13))
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 4. Build a complete authority × category × month panel"),
        code(
            """authorities = sorted(stable['authority_code'].unique())
sources = sorted(stable['source_key'].unique())
months = pd.date_range('2018-01-01', '2026-06-01', freq='MS')

observed = stable.set_index(['permit_month', 'authority_code', 'source_key'])['permit_count']
full_index = pd.MultiIndex.from_product(
    [months, authorities, sources],
    names=['permit_month', 'authority_code', 'source_key'],
)
panel = (
    observed.reindex(full_index, fill_value=0)
            .rename('permit_count')
            .reset_index()
            .sort_values(['authority_code', 'source_key', 'permit_month'])
            .reset_index(drop=True)
)

print(f'Authorities: {len(authorities):,}')
print(f'Categories:  {len(sources):,}')
print(f'Market series: {len(authorities) * len(sources):,}')
print(f'Panel rows: {len(panel):,}')
"""
        ),
        markdown("## 5. Leakage-safe feature engineering"),
        code(
            """keys = ['authority_code', 'source_key']
grouped = panel.groupby(keys)['permit_count']

LAGS = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15]
for lag in LAGS:
    panel[f'lag_{lag}'] = grouped.shift(lag)

for window in (3, 6, 12):
    panel[f'roll_sum_{window}'] = grouped.transform(
        lambda s: s.shift(1).rolling(window, min_periods=window).sum()
    )

# Direct 3-month-ahead cumulative target: t+1 + t+2 + t+3.
panel['target_3m'] = grouped.shift(-1) + grouped.shift(-2) + grouped.shift(-3)

# Same three calendar months one year earlier.
panel['seasonal_naive_3m'] = panel['lag_9'] + panel['lag_10'] + panel['lag_11']
panel['momentum_3v3'] = (
    panel['lag_1'] + panel['lag_2'] + panel['lag_3']
    - panel['lag_4'] - panel['lag_5'] - panel['lag_6']
)
panel['yoy_last_month'] = panel['lag_1'] - panel['lag_13']

forecast_start = panel['permit_month'] + pd.offsets.MonthBegin(1)
panel['month_sin'] = np.sin(2 * np.pi * forecast_start.dt.month / 12)
panel['month_cos'] = np.cos(2 * np.pi * forecast_start.dt.month / 12)

NUMERIC_FEATURES = [f'lag_{lag}' for lag in LAGS] + [
    'roll_sum_3', 'roll_sum_6', 'roll_sum_12',
    'momentum_3v3', 'yoy_last_month', 'month_sin', 'month_cos',
]
CATEGORICAL_FEATURES = ['authority_code', 'source_key']
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

model_panel = panel.dropna(subset=NUMERIC_FEATURES + ['seasonal_naive_3m']).copy()
print(model_panel[['permit_month', 'target_3m', 'seasonal_naive_3m']].describe())
"""
        ),
        markdown(
            """### Why the feature set is intentionally narrow

The current snapshot contains status, closure, names, addresses, and current coordinates, but using today's values while pretending to forecast 2024 or 2025 would leak future information. The backtest therefore uses **only historical permit-count features and stable identifiers**.

That makes this a valid demand-forecasting experiment from the current snapshot, not a disguised use of future state.
"""
        ),
        markdown("## 6. Metrics that connect to business decisions"),
        code(
            """def business_metrics(y_true, y_pred, top_share=0.10):
    y = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(y_pred, dtype=float), 0, None)
    k = max(1, int(np.ceil(len(y) * top_share)))
    top_idx = np.argsort(-p)[:k]
    actual_total = max(y.sum(), 1.0)
    capture = y[top_idx].sum() / actual_total
    return {
        'mae': mean_absolute_error(y, p),
        'rmse': float(np.sqrt(mean_squared_error(y, p))),
        'wape': float(np.abs(y - p).sum() / actual_total),
        'top10_capture': float(capture),
        'top10_lift_vs_random': float(capture / top_share),
    }

def make_xgb(objective, **extra):
    prep = ColumnTransformer(
        [('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES)],
        remainder='passthrough',
    )
    model = XGBRegressor(
        objective=objective,
        n_estimators=180,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.90,
        colsample_bytree=0.90,
        min_child_weight=5,
        reg_lambda=2.0,
        n_jobs=4,
        tree_method='hist',
        random_state=42,
        **extra,
    )
    return Pipeline([('prep', prep), ('model', model)])
"""
        ),
        markdown("## 7. Quarterly walk-forward validation"),
        code(
            """CUTOFFS = pd.to_datetime([
    '2024-03-01', '2024-06-01', '2024-09-01', '2024-12-01',
    '2025-03-01', '2025-06-01', '2025-09-01', '2025-12-01',
    '2026-03-01',
])

MODEL_SPECS = {
    'xgb_poisson': ('count:poisson', {}),
    'xgb_square': ('reg:squarederror', {}),
    'xgb_tweedie': ('reg:tweedie', {'tweedie_variance_power': 1.3}),
}

fold_metrics = []
fold_predictions = []

for cutoff in CUTOFFS:
    # At cutoff t, a historical training row is allowed only if its t+1:t+3
    # target has already finished by the cutoff.
    train = model_panel[
        (model_panel['permit_month'] <= cutoff - pd.DateOffset(months=3))
        & model_panel['target_3m'].notna()
    ]
    test = model_panel[model_panel['permit_month'] == cutoff].copy()

    predictions = {'seasonal_naive': test['seasonal_naive_3m'].to_numpy(float)}
    for model_name, (objective, extra) in MODEL_SPECS.items():
        fitted = make_xgb(objective, **extra)
        fitted.fit(train[FEATURES], train['target_3m'])
        predictions[model_name] = fitted.predict(test[FEATURES])

    predictions['seasonal_ml_blend'] = (
        0.70 * np.clip(predictions['xgb_poisson'], 0, None)
        + 0.30 * np.clip(predictions['seasonal_naive'], 0, None)
    )

    for model_name, pred in predictions.items():
        metrics = business_metrics(test['target_3m'], pred)
        fold_metrics.append({'cutoff': cutoff, 'model': model_name, **metrics})

    test_out = test[['permit_month', 'authority_code', 'source_key', 'target_3m']].copy()
    for model_name, pred in predictions.items():
        test_out[model_name] = np.clip(pred, 0, None)
    fold_predictions.append(test_out)

metrics_df = pd.DataFrame(fold_metrics)
summary = metrics_df.groupby('model')[['mae', 'rmse', 'wape', 'top10_capture', 'top10_lift_vs_random']].mean()
summary.sort_values('wape')
"""
        ),
        code(
            """wape_pivot = metrics_df.pivot(index='cutoff', columns='model', values='wape')
ax = wape_pivot.plot(figsize=(11, 5), marker='o', title='Walk-forward WAPE by 3-month forecast origin')
ax.set_ylabel('WAPE (lower is better)')
ax.set_xlabel('forecast origin')
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 8. How much does ML improve on the seasonal baseline?"),
        code(
            """baseline_wape = summary.loc['seasonal_naive', 'wape']
best_model_name = summary['wape'].idxmin()
best_wape = summary.loc[best_model_name, 'wape']
relative_improvement = (baseline_wape - best_wape) / baseline_wape

print(f'Best average model: {best_model_name}')
print(f'Seasonal naive average WAPE: {baseline_wape:.2%}')
print(f'Best model average WAPE:     {best_wape:.2%}')
print(f'Relative WAPE improvement:   {relative_improvement:.1%}')
print(f'Top-10% market capture:      {summary.loc[best_model_name, "top10_capture"]:.1%}')
print(f'Lift vs random 10% targeting:{summary.loc[best_model_name, "top10_lift_vs_random"]:.2f}x')
"""
        ),
        markdown(
            """**Business interpretation:** the forecasting improvement and the targeting concentration are separate facts. In this dataset, the top 10% of authority-category markets capture roughly four times the permit volume expected from random 10% targeting. The ML model primarily improves **volume calibration** over seasonal naive; it does not magically create all of that concentration.
"""
        ),
        markdown("## 9. Final out-of-time example: forecast 2026 Q2 from March 2026"),
        code(
            """FINAL_CUTOFF = pd.Timestamp('2026-03-01')
final_train = model_panel[
    (model_panel['permit_month'] <= FINAL_CUTOFF - pd.DateOffset(months=3))
    & model_panel['target_3m'].notna()
]
final_test = model_panel[model_panel['permit_month'] == FINAL_CUTOFF].copy()

final_tweedie = make_xgb('reg:tweedie', tweedie_variance_power=1.3)
final_tweedie.fit(final_train[FEATURES], final_train['target_3m'])
final_test['xgb_tweedie'] = np.clip(final_tweedie.predict(final_test[FEATURES]), 0, None)
final_test['seasonal_ml_blend'] = (
    0.70 * np.clip(
        make_xgb('count:poisson').fit(final_train[FEATURES], final_train['target_3m']).predict(final_test[FEATURES]),
        0, None,
    )
    + 0.30 * final_test['seasonal_naive_3m']
)

for name in ['xgb_tweedie', 'seasonal_ml_blend', 'seasonal_naive_3m']:
    print(name, business_metrics(final_test['target_3m'], final_test[name]))
"""
        ),
        markdown("## 10. Opportunity ranking for a sales / expansion team"),
        code(
            """# Use the blend for a stable operating score, then rank within each category.
final_test['opportunity_score'] = (
    final_test.groupby('source_key')['seasonal_ml_blend']
              .rank(method='average', pct=True)
              .mul(100)
)

top_markets = (
    final_test.sort_values(['source_key', 'opportunity_score'], ascending=[True, False])
              .groupby('source_key', as_index=False)
              .head(10)
              [['source_key', 'authority_code', 'opportunity_score', 'seasonal_ml_blend', 'target_3m']]
              .rename(columns={
                  'seasonal_ml_blend': 'predicted_next_3m_permits',
                  'target_3m': 'actual_next_3m_permits',
              })
)
top_markets
"""
        ),
        markdown("## 11. Add a broad address-derived region label for readability"),
        code(
            """address_raw = pq.read_table(PARQUET, columns=['authority_code', 'road_address', 'lot_address'])
road = address_raw['road_address']
lot = address_raw['lot_address']
use_lot = pc.or_(pc.is_null(road), pc.equal(pc.fill_null(road, ''), ''))
address = pc.if_else(use_lot, lot, road)
region_proxy = pc.list_element(pc.split_pattern(address, pattern=' '), 0)

region_table = pa.table({
    'authority_code': pc.cast(address_raw['authority_code'], pa.string()),
    'region_proxy': region_proxy,
})
region_counts = (
    region_table.group_by(['authority_code', 'region_proxy'])
                .aggregate([('authority_code', 'count')])
                .to_pandas()
                .rename(columns={'authority_code_count': 'records'})
                .dropna(subset=['authority_code', 'region_proxy'])
)
region_map = (
    region_counts.sort_values(['authority_code', 'records'], ascending=[True, False])
                 .drop_duplicates('authority_code')
                 [['authority_code', 'region_proxy']]
)

top_markets = top_markets.merge(region_map, on='authority_code', how='left')
top_markets[['region_proxy', 'source_key', 'authority_code', 'opportunity_score', 'predicted_next_3m_permits', 'actual_next_3m_permits']]
"""
        ),
        markdown(
            """`region_proxy` is only the first address token chosen by modal frequency within an `authority_code`. It is for readable nationwide context, **not** an authoritative administrative boundary join.
"""
        ),
        markdown("## 12. Empirical uncertainty bands from walk-forward residuals"),
        code(
            """all_fold_predictions = pd.concat(fold_predictions, ignore_index=True)
all_fold_predictions['blend_abs_error'] = np.abs(
    all_fold_predictions['target_3m'] - all_fold_predictions['seasonal_ml_blend']
)

# Source-specific 90th-percentile absolute backtest residual: a simple
# distribution-free empirical uncertainty band, not a guarantee of coverage.
q90_by_source = all_fold_predictions.groupby('source_key')['blend_abs_error'].quantile(0.90)
final_test['q90_abs_error'] = final_test['source_key'].map(q90_by_source)
final_test['forecast_lower_90'] = np.clip(final_test['seasonal_ml_blend'] - final_test['q90_abs_error'], 0, None)
final_test['forecast_upper_90'] = final_test['seasonal_ml_blend'] + final_test['q90_abs_error']

coverage = (
    (final_test['target_3m'] >= final_test['forecast_lower_90'])
    & (final_test['target_3m'] <= final_test['forecast_upper_90'])
).mean()
print(f'Empirical final-holdout interval coverage: {coverage:.1%}')
final_test[['source_key', 'authority_code', 'seasonal_ml_blend', 'forecast_lower_90', 'forecast_upper_90', 'target_3m']].head()
"""
        ),
        markdown("## 13. Explainability: what drives the Tweedie tree model?"),
        code(
            """try:
    import shap

    prep = final_tweedie.named_steps['prep']
    booster = final_tweedie.named_steps['model']
    sample = final_test[FEATURES].sample(min(1200, len(final_test)), random_state=42)
    transformed = prep.transform(sample)
    names = prep.get_feature_names_out()
    explainer = shap.TreeExplainer(booster)
    values = explainer(transformed)
    importance = pd.DataFrame({
        'feature': names,
        'mean_abs_shap': np.abs(values.values).mean(axis=0),
    }).sort_values('mean_abs_shap', ascending=False)
    display(importance.head(20))
except Exception as exc:
    print('SHAP could not be rendered in this runtime; falling back to model feature importance.')
    prep = final_tweedie.named_steps['prep']
    booster = final_tweedie.named_steps['model']
    importance = pd.DataFrame({
        'feature': prep.get_feature_names_out(),
        'importance': booster.feature_importances_,
    }).sort_values('importance', ascending=False)
    display(importance.head(20))
    print(type(exc).__name__, str(exc)[:200])
"""
        ),
        markdown("## 14. Where this becomes a real product"),
        markdown(
            """### MVP: Korea F&B Permit Demand Intelligence

Deliver the model as a monthly table/API:

`forecast_origin, authority_code, category, predicted_3m_permits, opportunity_score, uncertainty_low, uncertainty_high`

Potential buyers/users:

- **POS / payments:** allocate field sales capacity toward markets with the highest expected new-permit volume;
- **food suppliers / equipment vendors:** pre-position sales inventory and prospecting effort;
- **franchise teams:** use the score as a first-pass market-growth screen before rent, population, footfall, and sales data are added;
- **commercial real estate:** monitor where F&B permitting activity is strengthening.

### What the model does *not* claim

- It predicts **administrative permit counts**, not revenue or physical store openings.
- It does not infer historical monthly active-store populations from today's snapshot.
- It does not use `closure_date` as an irreversible event.
- It does not treat `management_number` as an official business primary key.
- It should be refreshed only after source-freshness checks pass; the 2026-08 bakery anomaly is an example of why this matters.

### Highest-value next step

Once true monthly snapshots accumulate, add **survival / state-transition targets** and external population, rent, footfall, tourism, or card-spend data. That would turn this demand signal into a richer store-expansion decision system.
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
