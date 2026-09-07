# Data directories

All runtime source data and derived local artifacts live under `data/local/`.
That entire directory is excluded from Git.

The default `KBL_DATA_ROOT` is `data/local/`. An explicit override is still supported,
but any repository-local override must remain under `data/local/`.
