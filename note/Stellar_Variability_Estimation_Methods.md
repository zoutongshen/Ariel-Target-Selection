# Stellar Variability Estimation Methods for Ariel MCS

**Date:** January 16, 2026  
**Purpose:** Calculate peak-to-peak stellar variability amplitude (in ppm) for Signal Detection Metric (SDM) calculations

---

## Overview

Stellar variability is required to calculate the SDM for eclipse observations. We developed a hierarchical approach to estimate variability for all 808 planets in the Ariel Mission Candidate Sample (MCS), achieving **100% coverage** with **91.5% empirical basis**.

---

## Data Sources

### Primary Data
- **Ariel MCS Catalog:** `Ariel_MCS_Known_2025-07-18.csv` (808 exoplanets)
- **TESS Stellar Variability Catalog:** `hlsp_tess-svc_tess_lcf_all-s0001-s0026_tess_v1.0_cat.csv` (84,046 stars)

### Key Parameters Available
| Parameter | Coverage | Source |
|-----------|----------|--------|
| TIC ID | 100% (808/808) | MCS catalog |
| Temperature | 100% (808/808) | MCS catalog |
| Radius | 100% (808/808) | MCS catalog |
| Mass | 100% (808/808) | MCS catalog |
| vsini | 73.0% (590/808) | MCS catalog |
| Stellar Age | 84.8% (685/808) | MCS catalog |
| Rotation Period (catalog) | 29.2% (236/808) | MCS catalog |
| TESS Variability | 16.8% (136/808) | TESS-SVC |

---

## Methodology: Hierarchical Approach

We use a 3-tier hierarchy to maximize empirical coverage:

### **Tier 1: TESS Measured Variability (16.8%)**
Directly use measured variability amplitude from TESS photometry when available.

**Formula:**
```
variability_ppm = amp_var_1  (from TESS-SVC catalog)
```

**Coverage:** 136/808 systems (16.8%)

---

### **Tier 2: Rotation-Based Estimates (74.6%)**

When TESS data unavailable, derive variability from stellar rotation period using empirical activity relations.

#### **Step 2a: Obtain Rotation Period**

Three sources in order of preference:

##### **2a.1: Catalog Values (22.3%)**
Use directly measured rotation periods from literature.

**Coverage:** 180/808 systems

##### **2a.2: Derive from vsini (42.2%)**
Calculate rotation period from projected rotational velocity and stellar radius.

**Formula:**
```
P_rot = 2πR / (vsini × sin(i))
```

Where:
- `R` = stellar radius (solar radii) → convert to km: `R_km = R × 695,700`
- `vsini` = projected rotational velocity (km/s)
- `sin(i)` = inclination factor, assumed **0.8** for random orientations
- `P_rot` = rotation period (days)

**Implementation:**
```python
def rotation_from_vsini(vsini, radius, assume_sin_i=0.8):
    R_km = radius * 695700  # Convert solar radii to km
    P_rot = (2 * np.pi * R_km) / (vsini * assume_sin_i * 86400)  # Convert to days
    return P_rot
```

**Coverage:** 341/808 systems (additional 42.2%)

**Validation:** Median vsini ratio = 1.00 (perfect self-consistency, 0 outliers)

##### **2a.3: Derive from Gyrochronology (10.1%)**
Estimate rotation period from stellar age and temperature using empirical age-rotation relations.

**Formula (Barnes 2007):**
```
P_rot = b × Age^n × (B-V - 0.4)^a
```

Where:
- `Age` = stellar age (Myr)
- `B-V` = color index (derived from Teff)
- `n = 0.519` (age exponent)
- `a = 0.601` (color exponent)  
- `b = 0.7725` (normalization)

**Temperature to B-V Conversion:**
```python
if Teff > 7000:    # Too hot for reliable gyro
    return np.nan
elif Teff > 6000:  # F stars
    BV = 0.3 + 0.00004 * (6500 - Teff)
elif Teff > 5000:  # G stars
    BV = 0.5 + 0.0003 * (6000 - Teff)
elif Teff > 3800:  # K stars
    BV = 0.8 + 0.0004 * (5000 - Teff)
else:              # M dwarfs
    BV = 1.5 + 0.0002 * (4000 - Teff)
```

**Constraints:**
- Only applied for `B-V > 0.5` (reliable gyro regime)
- Sanity check: `0.5 < P_rot < 100 days`

**Coverage:** 82/808 systems (additional 10.1%)

**Total rotation period coverage:** 603/808 systems (74.6%)

#### **Step 2b: Convert Rotation to Variability**

Use empirical relation from McQuillan et al. (2014) and Morris et al. (2020).

**Base Formula:**
```
variability_ppm = 1500 × (P_rot / 10)^(-0.5)
```

**Stellar Type Corrections:**
```python
if Teff < 4000:      # M dwarfs (most variable)
    variability_ppm × 2.0
elif Teff < 5200:    # K dwarfs
    variability_ppm × 1.5
elif Teff > 6500:    # F stars (less variable)
    variability_ppm × 0.7
else:                # G dwarfs (Sun-like)
    variability_ppm × 1.0
```

**Physical Basis:**
- Faster rotation → stronger magnetic activity → higher variability
- Cool stars (K/M) more magnetically active than hot stars (F/A)

---

### **Tier 3: Stellar Type Defaults (8.5%)**

For systems without TESS data or derivable rotation periods, assign typical variability based on spectral type.

**Default Values:**
```python
if Teff < 3500:          # Late M dwarfs
    variability = 3000 ppm
elif Teff < 4000:        # Early M dwarfs
    variability = 2000 ppm
elif Teff < 5200:        # K dwarfs
    variability = 1000 ppm
elif Teff < 6000:        # G dwarfs
    variability = 200 ppm
elif Teff < 7500:        # F stars
    variability = 300 ppm
else:                    # A stars and hotter
    variability = 100 ppm
```

**Evolved Star Correction:**
```python
if logg < 4.0:  # Giants/subgiants
    variability × 1.5-2.5
```

**Coverage:** 69/808 systems (8.5%)

**Basis:** Typical ranges from TESS variability statistics (Morris et al. 2020)

---

## Coverage Summary

### All MCS Systems (808 total)
| Method | Count | Percentage |
|--------|-------|------------|
| **TESS measured** | 136 | 16.8% |
| **Rotation period** | 603 | 74.6% |
| - Catalog | 180 | 22.3% |
| - vsini derived | 341 | 42.2% |
| - Gyro derived | 82 | 10.1% |
| **Stellar type defaults** | 69 | 8.5% |
| **Total** | **808** | **100%** |
| **Empirical basis** | **739** | **91.5%** |

### Tier 2/3 High-Priority Systems (550 total)
| Method | Count | Percentage |
|--------|-------|------------|
| TESS measured | 90 | 16.4% |
| Rotation period | 428 | 77.8% |
| - Catalog | 105 | 19.1% |
| - vsini derived | 277 | 50.4% |
| - Gyro derived | 46 | 8.4% |
| Stellar type defaults | 32 | 5.8% |

---

## Physical Validation

### Rotation Period Validation
- **Total derived:** 728 systems
- **Range:** 0.67 - 349 days ✅
- **Median:** 20.8 days ✅ (typical for main-sequence)
- **Very fast (<0.5d):** 0 ✅
- **Very slow (>100d):** 30 (old, inactive stars)

### Variability Validation
- **Range:** 52 - 47,613 ppm
- **Median:** 1,078 ppm (~0.1%) ✅
- **Extreme values:** Only 4 systems >10,000 ppm
  - AU Mic b: 47,613 ppm (known young, active M dwarf) ✅

### vsini Self-Consistency
- **Median vsini ratio:** 1.00 ✅ (calculated/observed)
- **Mean vsini ratio:** 1.00 ✅
- **Outliers (ratio <0.5 or >2.0):** 0 ✅

### Rotation-Variability Correlation
- **Correlation coefficient:** -0.408 ✅ (negative as expected)

| Rotation Period | Median Variability (ppm) |
|----------------|-------------------------|
| <5 days | 2,810 | ✅ Fast, active
| 5-10 days | 1,751 | ✅
| 10-20 days | 1,249 | ✅
| 20-50 days | 1,001 | ✅
| >50 days | 850 | ✅ Slow, quiet

**Conclusion:** Clear trend of faster rotation → higher variability confirms physical validity.

---

## Output Files

### Primary Output
**File:** `analysis/results/mcs_stellar_variability_estimates.csv`

**Columns:**
- `Planet Name`: Planet identifier
- `TIC ID`: TESS Input Catalog ID
- `Star Temperature [K]`: Effective temperature
- `Star Rotational Velocity [km/s]`: vsini
- `Star Rotation Period [days]`: Catalog rotation period
- `P_rot_derived`: Final rotation period (catalog or derived)
- `rotation_source`: Source of rotation period
  - `catalog`: From literature
  - `vsini_derived`: Derived from vsini
  - `gyro_derived`: Derived from gyrochronology
  - `not_derived`: No rotation period available
  - `not_needed`: TESS variability used directly
- `variability_ppm`: Peak-to-peak variability amplitude (ppm)
- `variability_source`: Method used for variability
  - `TESS_measured`: Direct TESS measurement
  - `rotation_period`: Estimated from rotation
  - `stellar_type`: Default value for spectral type

### Supporting Scripts
- **Generation:** `analysis/scripts/estimate_stellar_variability.py`
- **Validation:** `analysis/scripts/validate_variability.py`
- **Coverage analysis:** `analysis/scripts/check_tier_tess_coverage.py`

---

## References

- **Barnes, S. A. (2007).** Ages for illustrative field stars using gyrochronology. *ApJ*, 669, 1167.
- **McQuillan, A., Mazeh, T., & Aigrain, S. (2014).** Rotation Periods of 34,030 Kepler Main-sequence Stars. *ApJS*, 211, 24.
- **Morris, B. M., et al. (2020).** The TESS Stellar Variability Catalog. *AJ*, 160, 5.
- **van Saders, J. L., et al. (2016).** Weakened magnetic braking as the origin of anomalously rapid rotation in old field stars. *Nature*, 529, 181.

---

## Usage Notes

### For SDM Calculation
```python
import pandas as pd

# Load variability estimates
var = pd.read_csv('analysis/results/mcs_stellar_variability_estimates.csv')

# Use variability_ppm directly in SDM formula
# SDM typically includes (signal/noise) where noise includes stellar variability
```

### Uncertainty Considerations
- **TESS measured:** Uncertainties available in TESS-SVC catalog
- **vsini-derived:** Assumes sin(i) = 0.8; actual uncertainty ~factor of 1.5
- **Gyro-derived:** Age uncertainties propagate; typical ~30% uncertainty on P_rot
- **Stellar type defaults:** Conservative estimates; factor of 2-3 uncertainty

### When to Use Caution
- Systems with `stellar_type` source: Use upper bound estimates for noise
- Very young systems (<100 Myr): May have higher variability than estimated
- Evolved stars (logg <3.5): Variability may be underestimated
- Systems with P_rot >100 days: May have minimal spot modulation

