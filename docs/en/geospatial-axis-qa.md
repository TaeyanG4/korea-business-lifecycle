# Geospatial Source X/Y Axis QA

Checked: **2026-09-07**

The official catalog describes `EPSG:5174` as the source CRS for all three v1 sources, but the project does not assume that the upstream CSV fields `좌표정보(X)` / `좌표정보(Y)` are populated according to EPSG formal axis labels. Source-field placement is validated separately before any WGS84 latitude/longitude derivation.

## CRS reference

With `pyproj==3.7.2` / PROJ 9.5.1, `EPSG:5174` is `Korean 1985 / Modified Central Belt` with these formal axes:

- first axis: Northing, abbreviation `X`, north direction;
- second axis: Easting, abbreviation `Y`, east direction.

That formal CRS axis definition and the actual value placement in upstream CSV fields named `좌표정보(X)` / `좌표정보(Y)` are **different evidence questions**.

## Bounded real-data probe

The first 5,000 nonblank coordinate pairs after the header were inspected for each current snapshot, 15,000 pairs total. No row-level coordinates or addresses were printed or retained in provenance.

Two candidates were compared:

1. candidate A: source X as easting, source Y as northing;
2. candidate B: source X as northing, source Y as easting.

Both candidates placed 15,000/15,000 sampled pairs inside a deliberately broad Korea WGS84 envelope, so country-level plausibility alone could not distinguish the axis interpretation.

The probe then reduced road/lot address first-level administrative prefixes in memory to six coarse macro regions—capital, gangwon, chungcheong, jeolla, gyeongsang, and jeju—and compared only aggregate membership in broad region envelopes.

| source | eligible pairs | X=easting/Y=northing match | swapped match |
| --- | ---: | ---: | ---: |
| general_restaurants | 5,000 | 5,000 | 0 |
| rest_cafes | 5,000 | 5,000 | 0 |
| bakeries | 5,000 | 5,000 | 0 |
| **total** | **15,000** | **15,000** | **0** |

The bounded evidence therefore **strongly prefers `좌표정보(X)=easting` and `좌표정보(Y)=northing`** across all three sources.

## Full-snapshot review result

The subsequent full execution inspected all 3,010,802 rows and all 2,811,767 coordinate pairs. Of 2,631,605 pairs eligible for coarse address-region comparison, candidate A (X=easting/Y=northing) matched 2,630,497 pairs (99.958%), while candidate B matched 686,673. Candidate-A-only matches totaled 1,943,824, candidate-B-only matches were zero, and 1,108 matched neither. All three sources reached the same assessment.

The project therefore approves `좌표정보(X)=easting`, `좌표정보(Y)=northing` and local WGS84 derivation **only for the exact approved 2026-09-07 current-v1 artifacts**. Future snapshots require revalidation. Public WGS84 release remains unapproved and the frozen 26-column `PERMIT` parent is not modified.

## Full-snapshot validator

An aggregate-only validator is also implemented to test the bounded result over every current row. It scans all 3,010,802 rows and applies the same candidate comparison to the roughly 2,811,767 coordinate pairs observed during prior profiling. Before scanning, it recomputes SHA-256 from the approved raw artifact bytes.

Default mode is plan-only:

```bash
python scripts/validate_full_coordinate_axis.py
```

The long full execution is:

```bash
mkdir -p data/local/logs
python scripts/validate_full_coordinate_axis.py --execute \
  | tee data/local/logs/geospatial-full-axis-20260907.json
```

Progress is emitted on stderr and the final aggregate JSON on stdout. The reviewed aggregate result is tracked as `provenance/geospatial_full_axis.json`. The next step is a separately versioned WGS84 enrichment that leaves the frozen parent unchanged.
