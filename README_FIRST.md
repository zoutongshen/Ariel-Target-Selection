# 🎯 Eclipse Impact Parameter Analysis - START HERE

## Welcome! 👋

This repository now centers on the eclipse impact parameter MCMC analysis (`analysis/notebooks/eclipse_impact_parameter_mcmc.ipynb`) using the July 2025 Ariel MCS/TPC catalogs.

**Status:** ✅ Current & ready to use

---

## 📚 Documentation Index

1. **PROJECT_DELIVERABLES.md** – current file map and specs.
2. **analysis/PROJECT_COMPLETION_SUMMARY.md** – technical summary of the active pipeline.
3. **analysis/results/README.md** – quick reference to the active CSV outputs (and backups).

Legacy context from the earlier occultation-probability run lives in `ANALYSIS_COMPLETE.txt`; keep for historical reference only.

---

## 🚀 Quick Start

Run the notebook (current workflow):
```bash
cd analysis/notebooks/
jupyter notebook eclipse_impact_parameter_mcmc.ipynb
# Uses 2025-07-18 MCS/TPC catalogs; run cells top-to-bottom.
```

Load results in Python:
```python
import pandas as pd
mcs = pd.read_csv('analysis/results/mcs_eclipse_impact_parameter_mcmc.csv')
tpc = pd.read_csv('analysis/results/tpc_eclipse_impact_parameter_mcmc.csv')
combined = pd.read_csv('analysis/results/eclipse_impact_parameter_mcmc_combined.csv')
```

Active outputs (analysis/results/):
- `mcs_eclipse_impact_parameter_mcmc.csv` (known planets, 2025-07-18)
- `tpc_eclipse_impact_parameter_mcmc.csv` (TPCs, 2025-07-18)
- `eclipse_impact_parameter_mcmc_combined.csv` (union table)
- Backups: `archive/*_temp.csv` (not used in analysis)

---

## 📁 File Structure (essentials)

```
Ariel/
├── README_FIRST.md ← you are here
├── PROJECT_DELIVERABLES.md
├── analysis/
│   ├── notebooks/
│   │   └── eclipse_impact_parameter_mcmc.ipynb ⭐ main notebook
│   ├── results/
│   │   ├── mcs_eclipse_impact_parameter_mcmc.csv
│   │   ├── tpc_eclipse_impact_parameter_mcmc.csv
│   │   ├── eclipse_impact_parameter_mcmc_combined.csv
│   │   └── archive/ *_temp.csv backups
│   └── PROJECT_COMPLETION_SUMMARY.md
└── data/
    └── raw/
        ├── Ariel_MCS_Known_2025-07-18.csv
        └── Ariel_MCS_TPCs_2025-07-18.csv
```

---

## 📞 Need help?
- Methodology & implementation: `analysis/PROJECT_COMPLETION_SUMMARY.md`
- Outputs & columns: `analysis/results/README.md`
- File map: `PROJECT_DELIVERABLES.md`
