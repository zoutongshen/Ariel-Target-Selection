# 📦 Project Deliverables — Eclipse Impact Parameter MCMC (Current)

## What’s in scope (current)
- **Main notebook:** `analysis/notebooks/eclipse_impact_parameter_mcmc.ipynb`
- **Inputs:** `data/raw/Ariel_MCS_Known_2025-07-18.csv`, `data/raw/Ariel_MCS_TPCs_2025-07-18.csv`
- **Outputs:** eclipse impact parameter posteriors + tiers in `analysis/results/`
- **Backups:** `_temp.csv` files now stored in `analysis/results/archive/`

## File map (essentials)
```
analysis/
├── notebooks/
│   └── eclipse_impact_parameter_mcmc.ipynb  ← active workflow
├── results/
│   ├── mcs_eclipse_impact_parameter_mcmc.csv
│   ├── tpc_eclipse_impact_parameter_mcmc.csv
│   ├── eclipse_impact_parameter_mcmc_combined.csv
│   ├── eclipse_impact_parameter_comprehensive_summary.png
│   └── archive/
│       ├── mcs_eclipse_impact_parameter_mcmc_temp.csv
│       └── tpc_eclipse_impact_parameter_mcmc_temp.csv
└── PROJECT_COMPLETION_SUMMARY.md
```

## Notebook (active)
`analysis/notebooks/eclipse_impact_parameter_mcmc.ipynb`
- Computes eclipse impact parameter \(b_{\text{occ}}\) via MCMC.
- Uses informative priors (cos i, e, ω; beta prior for e) and enforces occultation geometry.
- Generates tier labels and acceptance fractions; saves per-system posteriors to CSV.

## Results (CSV columns)
Common columns across the three active tables:
- `Planet`, `Dataset` (MCS/TPC)
- `eclipse_observed` (flag or blank)
- `b_occ_median`, `b_occ_16`, `b_occ_84`, `b_occ_std`, `b_occ_err_lower`, `b_occ_err_upper`
- `k_rp_rs`, `one_plus_k`
- `tier`, `tier_label`
- `acceptance_fraction`

Tables:
- `mcs_eclipse_impact_parameter_mcmc.csv` — known planets (MCS 2025-07-18)
- `tpc_eclipse_impact_parameter_mcmc.csv` — TPCs (2025-07-18)
- `eclipse_impact_parameter_mcmc_combined.csv` — union table (for convenience)
- `archive/*_temp.csv` — backups only; not used in analysis

## Legacy (kept for reference only)
- Occultation-probability notebook/results from 2023 run and the accompanying docs (`ANALYSIS_COMPLETE.txt`, `analysis/OCCULTATION_ANALYSIS_README.md`) are historical. The active workflow is the eclipse impact parameter MCMC above.
