# Eclipse Midtime Implementation Guide

This document explains what changes need to be made to add eclipse midtime calculation and full MCMC chain storage to your notebook.

## Summary of Changes Needed

The eclipse midtime calculation function has already been added to your notebook. You need to make the following additional changes:

## 1. Update Data Preparation (Cell with `prepare_system_data` function)

In the MCS data extraction section, add these parameters after `rp_rs` variables:

```python
# Transit timing parameters  
transit_midtime = row.get('Transit Mid Time [days]')  # JD - 2450000
transit_midtime_err_lower = abs(row.get('Transit Mid Time Error Lower [days]', 0))
transit_midtime_err_upper = abs(row.get('Transit Mid Time Error Upper [days]', 0))
period = row.get('Planet Period [days]')
period_err_lower = abs(row.get('Planet Period Error Lower [days]', 0))
period_err_upper = abs(row.get('Planet Period Error Upper [days]', 0))
```

In the TPC data extraction section, add:

```python
# Transit timing parameters
transit_midtime = row.get('Transit Mid Time [days]')
transit_midtime_err_lower = 0.0
transit_midtime_err_upper = 0.0
period = row.get('Planet Period [days]')
period_err_lower = 0.0
period_err_upper = 0.0
```

Update the validation check to include these parameters:

```python
# Change from:
if all([pd.notna(x) for x in [a_over_rs, inclination]]):

# To:
if all([pd.notna(x) for x in [a_over_rs, inclination, period, transit_midtime]]):
```

Add default uncertainty handling before the `systems.append()` call:

```python
# Handle transit timing uncertainties
if period_err_lower + period_err_upper == 0:
    # Use small default (typical precision from transits)
    period_err_lower = period * 1e-6
    period_err_upper = period * 1e-6

if transit_midtime_err_lower + transit_midtime_err_upper == 0:
    # Use small default (typical precision in days)
    transit_midtime_err_lower = 0.001
    transit_midtime_err_upper = 0.001
```

Add these fields to the `systems.append()` dictionary:

```python
'transit_midtime': transit_midtime,
'transit_midtime_err_lower': transit_midtime_err_lower,
'transit_midtime_err_upper': transit_midtime_err_upper,
'period': period,
'period_err_lower': period_err_lower,
'period_err_upper': period_err_upper,
```

## 2. Update MCMC Runner (Cell with `run_mcmc_for_system` function)

In the section where derived quantities are calculated, modify to:

```python
# Calculate derived quantities for each sample
b_occ_samples = []
t_eclipse_samples = []
i_deg_samples = []

for s in samples:
    a_over_rs, cos_i, e, omega = s
    # Derive inclination for reporting
    cos_i_clipped = np.clip(cos_i, -1.0, 1.0)
    i_deg = np.degrees(np.arccos(cos_i_clipped))
    i_deg_samples.append(i_deg)
    
    # Calculate b_occ
    b_occ = eclipse_impact_parameter(a_over_rs, cos_i_clipped, e, omega)
    b_occ_samples.append(b_occ)
    
    # Calculate eclipse midtime - sample from asymmetric distributions
    if np.random.rand() < 0.5:
        t_tra_sample = system['transit_midtime'] - np.abs(np.random.randn()) * system['transit_midtime_err_lower']
    else:
        t_tra_sample = system['transit_midtime'] + np.abs(np.random.randn()) * system['transit_midtime_err_upper']
    
    if np.random.rand() < 0.5:
        period_sample = system['period'] - np.abs(np.random.randn()) * system['period_err_lower']
    else:
        period_sample = system['period'] + np.abs(np.random.randn()) * system['period_err_upper']
    
    t_eclipse = eclipse_midtime(t_tra_sample, period_sample, e, omega)
    t_eclipse_samples.append(t_eclipse)

b_occ_samples = np.array(b_occ_samples)
t_eclipse_samples = np.array(t_eclipse_samples)
i_deg_samples = np.array(i_deg_samples)
```

Add T_eclipse statistics calculation:

```python
# Eclipse midtime statistics
t_eclipse_median = np.median(t_eclipse_samples)
t_eclipse_std = np.std(t_eclipse_samples)
t_eclipse_16, t_eclipse_84 = np.percentile(t_eclipse_samples, [16, 84])
t_eclipse_quantiles = np.percentile(t_eclipse_samples, np.linspace(0, 100, 100))
```

Add these fields to the results dictionary:

```python
't_eclipse_samples': t_eclipse_samples,
't_eclipse_quantiles': t_eclipse_quantiles,
't_eclipse_median': t_eclipse_median,
't_eclipse_std': t_eclipse_std,
't_eclipse_16': t_eclipse_16,
't_eclipse_84': t_eclipse_84,
't_eclipse_err_lower': t_eclipse_median - t_eclipse_16,
't_eclipse_err_upper': t_eclipse_84 - t_eclipse_median,
```

## 3. Update Results Export (Cell 10 - Full Analysis)

Add chain storage file paths at the beginning:

```python
mcs_chains_file = '../results/mcs_mcmc_chains.npz'  # Full MCMC chains
tpc_chains_file = '../results/tpc_mcmc_chains.npz'
```

Initialize chains dictionary:

```python
mcs_chains_dict = {}  # Store full MCMC chains by planet name
```

Load existing chains if available:

```python
# Load existing chains if available
if os.path.exists(mcs_chains_file):
    chains_data = np.load(mcs_chains_file, allow_pickle=True)
    mcs_chains_dict = {k: chains_data[k].item() for k in chains_data.files}
    print(f"Loaded existing MCMC chains for {len(mcs_chains_dict)} systems")
```

After running MCMC for each system, store the chains:

```python
# Store full MCMC chains for future reuse
mcs_chains_dict[result['name']] = {
    'samples': result['samples'],  # [a/Rs, cos_i, e, omega] samples
    'b_occ_samples': result['b_occ_samples'],
    't_eclipse_samples': result['t_eclipse_samples']
}
```

Add T_eclipse fields to the results list:

```python
't_eclipse_median': result['t_eclipse_median'],
't_eclipse_16': result['t_eclipse_16'],
't_eclipse_84': result['t_eclipse_84'],
't_eclipse_std': result['t_eclipse_std'],
't_eclipse_err_lower': result['t_eclipse_err_lower'],
't_eclipse_err_upper': result['t_eclipse_err_upper'],
't_eclipse_quantiles': ','.join([f"{q:.6f}" for q in result['t_eclipse_quantiles']]),
```

At checkpoints, save chains:

```python
# Save checkpoint
if new_mcs_count % 50 == 0:
    checkpoint_df = pd.DataFrame(mcs_results_list)
    checkpoint_df.to_csv(mcs_output_file, index=False)
    # Save chains
    np.savez_compressed(mcs_chains_file, **mcs_chains_dict)
    print(f"  Checkpoint saved ({len(mcs_results_list)} systems, {len(mcs_chains_dict)} chains)")
```

At final save, save chains:

```python
# Save MCS final results
if len(mcs_results_list) > 0:
    mcs_df = pd.DataFrame(mcs_results_list)
    mcs_df.to_csv(mcs_output_file, index=False)
    # Save all MCMC chains
    np.savez_compressed(mcs_chains_file, **mcs_chains_dict)
    print(f"  MCMC chains saved: {len(mcs_chains_dict)} systems")
```

Update completion message:

```python
print("\nResults saved to:")
print(f"  Summary (CSV):  {mcs_output_file}")
print(f"  MCMC Chains:    {mcs_chains_file}")
print("\nNote: Full MCMC chains saved - no need to re-run 90 min analysis!")
```

## 4. Using Saved Chains Later

To load and use the saved chains:

```python
# Load chains
chains_data = np.load('../results/mcs_mcmc_chains.npz', allow_pickle=True)

# Access specific planet
planet_name = 'WASP-121 b'
planet_chains = chains_data[planet_name].item()

# Use the samples
samples = planet_chains['samples']  # [N, 4] array of [a/Rs, cos_i, e, omega]
b_occ = planet_chains['b_occ_samples']
t_eclipse = planet_chains['t_eclipse_samples']

# Derive new quantities from samples without re-running MCMC
# Example: calculate something new
new_quantity = your_function(samples[:, 0], samples[:, 1], samples[:, 2], samples[:, 3])
```

## File Outputs

After running with these changes, you'll have:

1. **`mcs_eclipse_impact_parameter_mcmc.csv`** - Summary statistics
   - Includes b_occ and T_eclipse medians, errors, quantiles
   - Human-readable, easy to share

2. **`mcs_mcmc_chains.npz`** - Full MCMC chains (compressed)
   - ~6-10 MB per system (compressed)
   - Can derive ANY quantity later without re-running
   - Preserves all parameter correlations

## Benefits

- **Time saved**: No need to re-run 90-minute MCMC analyses
- **Flexibility**: Can calculate new derived quantities anytime
- **Accuracy**: Preserves full correlation structure between parameters
- **Storage efficient**: Compressed NPZ format (~100 MB for 100 systems)

## Questions?

The implementation is straightforward - just add these code blocks to the appropriate cells in your notebook and run!
