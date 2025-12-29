# Eclipse Impact Parameter Results (Current)

Active outputs from `analysis/notebooks/eclipse_impact_parameter_mcmc.ipynb` using the 2025-07-18 MCS/TPC catalogs.

## Active tables
- `mcs_eclipse_impact_parameter_mcmc.csv` — known planets (MCS)
- `tpc_eclipse_impact_parameter_mcmc.csv` — target planet candidates (TPC)
- `eclipse_impact_parameter_mcmc_combined.csv` — union of both
- `eclipse_impact_parameter_comprehensive_summary.png` — visualization summary

## Columns
- `Planet`, `Dataset` (MCS/TPC)
- `eclipse_observed` — flag (where available)
- `b_occ_median`, `b_occ_16`, `b_occ_84`, `b_occ_std`, `b_occ_err_lower`, `b_occ_err_upper`
- `k_rp_rs`, `one_plus_k`
- `tier`, `tier_label` — geometry-based premium/grazing classification
- `acceptance_fraction` — emcee acceptance metric

## Backups
- `archive/mcs_eclipse_impact_parameter_mcmc_temp.csv`
- `archive/tpc_eclipse_impact_parameter_mcmc_temp.csv`

These are kept only as backups; analyses should use the active tables above.
