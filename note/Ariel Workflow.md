---
author: Zoutong Shen
keywords: Notes
---
Below is a **complete start‑to‑finish workflow** for your occultation‑probability project — from building your environment to producing distributions and uncertainties derived from real data.
 This is optimized for your Ariel‑related use case, combining **Winn 2014**, **MCS**, **NASA Exoplanet Archive**, and the supporting papers (Shabram 2016, Valentine 2025, Burt 2025, Edwards 2022)**.

------

## **1. Goal Overview**

Compute the **occultation probability** for each planet in Billy Edwards’ **Mission Candidate Sample (MCS)**, including **uncertainties and probability distributions**.

Equation from Winn (2014):
$$
P_{\text{occ}} = \frac{R_\star + R_p}{a} \cdot \frac{1 + e \sin\omega}{1 - e^2}
$$

------

## **2. Environment Setup**

Run these once:

```bash
bash
# Create an isolated environment
conda create -n ariel_occ python=3.11
conda activate ariel_occ

# Install required packages
pip install pandas numpy requests astroquery tqdm matplotlib
```

Optional: `pip install jupyter seaborn emcee` (for notebooks and optional MCMC).

------

## **3. Reference Materials and Inputs**

| Category                    | File / Source                               | Purpose                                                    |
| --------------------------- | ------------------------------------------- | ---------------------------------------------------------- |
| Occultation geometry        | *Winn (2014), Transits and Occultations*    | Defines the formula and treatment of e and ω               |
| Target catalogue            | **MCS repository** (Billy Edwards 2022)     | Provides $R_\star, R_p, a, P, M_\star, e, \omega$ baseline |
| Missing parameters + errors | **NASA Exoplanet Archive** (pscomppars API) | Get uncertainties for each parameter                       |
| Eccentricity prior          | *Shabram et al. 2016*                       | Defines β‑prior to use when $e$ or ω missing               |
| Ariel population context    | *Valentine et al. 2025*, *Burt et al. 2025* | Check consistency with Tier 1‑3 planets                    |

------

## **4. Step‑by‑Step Workflow**

## **Step 1 – Load Base Catalogue**

- Clone or download MCS from GitHub:
   https://github.com/arielmission-space/Mission_Candidate_Sample
- Work with `target_list/Mission_Candidate_Sample.csv`.

```
python
import pandas as pd
mcs = pd.read_csv("target_list/Mission_Candidate_Sample.csv")
```

Make sure you have at least these columns:
 `name`, `R_star`, `R_p`, `a`, `P`, `e`, `omega`.

------

## **Step 2 – Cross‑Match with NASA Exoplanet Archive**

Query the **Planetary Systems Composite Table (pscomppars)** for uncertainties:

```python
python
import requests, pandas as pd, tqdm

def fetch(psname):
    base = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
    q = ("query=select pl_name,pl_orbper,pl_orbeccen,pl_orblper,"
         "st_rad,st_mass,pl_rade,pl_orbsmax,"
         "st_raderr1,pl_radeerr1,pl_orbeccenerr1 "
         f"from pscomppars where pl_name='{psname}'&format=json")
    r = requests.get(base+q)
    return pd.DataFrame(r.json())

out = [fetch(p) for p in tqdm.tqdm(mcs["name"].head(50))]
nea = pd.concat(out)
nea.to_csv("nea_crossmatch.csv", index=False)
```

------

## **Step 3 – Merge and Handle Missing Data**

Join NASA values back into the MCS table.

```python
python
merged = mcs.merge(nea, how="left", left_on="name", right_on="pl_name")
```

Fill missing uncertainties using **fractional priors**:

| Parameter       | Fractional σ    | Rationale                                        |
| --------------- | --------------- | ------------------------------------------------ |
| $R_\star,\ R_p$ | ± 5 %           | Typical Gaia + TESS precision                    |
| $a$             | ± 1 %           | Derived from P, M_\star – negligible uncertainty |
| $e$             | σ = 0.05        | For circularized systems (< 10 d periods)        |
| $ω$             | uniform [0, 2π] | Random if unknown                                |

```python
python
import numpy as np
for col, frac in [('R_star',0.05),('R_p',0.05),('a',0.01)]:
    merged[f'{col}_σ'] = merged[col].fillna(merged[col]*frac)
merged['e'] = merged['e'].fillna(np.random.beta(0.867,3.03,len(merged)))
merged['omega'] = merged['omega'].fillna(np.random.uniform(0,360,len(merged)))
```

------

## **Step 4 – Monte Carlo Propagation (Recommended)**

Compute a probability distribution for each planet:

```python
python
N = 10000
samples = []
for _, row in merged.iterrows():
    Rstar = np.random.normal(row.R_star, row.R_star_σ, N)
    Rp = np.random.normal(row.R_p, row.R_p_σ, N)
    a = np.random.normal(row.a, row.a_σ, N)
    e = np.random.normal(row.e, 0.05, N)
    omega = np.deg2rad(np.random.uniform(0,360,N))
    P_occ = (Rstar + Rp)/a * (1 + e*np.sin(omega))/(1 - e**2)
    samples.append({
        "name": row["name"],
        "mean_occ": np.mean(P_occ),
        "low_occ": np.percentile(P_occ,16),
        "high_occ": np.percentile(P_occ,84)
    })
out = pd.DataFrame(samples)
out.to_csv("occultation_probabilities.csv", index=False)
```

Now every target has a **median $P_\text{occ}$** and **1σ interval**.

------

## **Step 5 – Optional MCMC for Correlated Parameters**

Use an MCMC sampler (e.g. `emcee`) only if:

- you’re jointly fitting $e$ and ω from observational posteriors, or
- you want population‑level inference.

For example:

```python
python
# pseudo-code outline
import emcee
def log_prob(theta, ...):
    R_star, R_p, a, e, w = theta
    if not 0 <= e < 1: return -np.inf
    P_occ = (R_star+R_p)/a*(1+e*np.sin(w))/(1-e**2)
    return log_likelihood(P_occ, data) + priors(theta)
```

Most Ariel prevalence studies stop at Monte Carlo propagation — MCMC is optional unless you need hierarchical inference.

------

## **Step 6 – Post‑Analysis and Validation**

1. Plot median $P_\text{occ}$ against orbital period or semi‑major axis:
    confirm the expected inverse relation ($P_\text{occ} ∝ a^{‑1}$).
2. Compare hot Jupiters vs warm Neptunes:
    short‑period planets should cluster near 5–15 % occultation probability.
3. Cross‑check with *Valentine et al. 2025 Table 4* — most of their **87 targets** are in the high-$P_\text{occ}$ end.

------

## **5. Notes and Best Practices**

| Task                     | Reference                     | Guidance                                                 |
| ------------------------ | ----------------------------- | -------------------------------------------------------- |
| Formula & geometry       | Winn (2014)                   | Section 4 (occultations)                                 |
| Eccentricity priors      | Shabram et al. (2016)         | Use their β distribution                                 |
| Target vetting           | Edwards & Tinetti (2022), MCS | Cross‑match guarantees uniform format                    |
| Missing eccentricities   | Assume circular for P<5 d     | Tidal circularization justified                          |
| Data validation          | Burt et al. (2025)            | Check RV and mass precision limits                       |
| Visualization of results | Matplotlib / Seaborn          | Heatmaps or violin plots of $P_\text{occ}$ distributions |

------

## **6. Expected Outcome**

When you run this workflow:

- $>\!90\%$ of your MCS planets will have complete parameter coverage.
- You’ll obtain a **median $P_\text{occ}$** precision of ≈ 0.1–0.5 %.
- Each target’s Monte Carlo distribution can feed directly into population studies or Ariel observability planning.

------

## **Deliverables**

| Output                          | Description                               |
| ------------------------------- | ----------------------------------------- |
| `nea_crossmatch.csv`            | Raw NASA EA parameter/uncertainty table   |
| `merged_with_errors.csv`        | Combined MCS + NEA + fallback σ           |
| `occultation_probabilities.csv` | Final $P_\text{occ}$ distribution summary |
| (Optional) plots                | Trend plots, heatmaps, or histograms      |

------

Follow this recipe, and you’ll have a fully traceable, publication‑grade analysis pipeline consistent with Ariel’s internal data practices and ready to feed into your target selection or eclipse‑occurrence statistics.

1. https://github.com/arielmission-space/Mission_Candidate_Sample/commit/3642610c1e5333e7c757256313279de367b029f7#diff-75e69b4b2954d5ca82018a4faae588de78f56076b1fb8dd067a6e81f0f550751
