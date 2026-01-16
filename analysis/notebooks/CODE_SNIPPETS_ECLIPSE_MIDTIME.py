"""
Complete code snippets for adding eclipse midtime calculation to MCMC notebook.
Copy and paste these into the appropriate locations.
"""

# ==============================================================================
# SNIPPET 1: Add to prepare_system_data() function - MCS section
# ==============================================================================
# Add after the rp_rs variables extraction:

# Transit timing parameters
transit_midtime = row.get('Transit Mid Time [days]')  # JD - 2450000
transit_midtime_err_lower = abs(row.get('Transit Mid Time Error Lower [days]', 0))
transit_midtime_err_upper = abs(row.get('Transit Mid Time Error Upper [days]', 0))
period = row.get('Planet Period [days]')
period_err_lower = abs(row.get('Planet Period Error Lower [days]', 0))
period_err_upper = abs(row.get('Planet Period Error Upper [days]', 0))

# ==============================================================================
# SNIPPET 2: Add to prepare_system_data() function - TPC section
# ==============================================================================
# Add after the rp_rs variables extraction:

# Transit timing parameters
transit_midtime = row.get('Transit Mid Time [days]')
transit_midtime_err_lower = 0.0
transit_midtime_err_upper = 0.0
period = row.get('Planet Period [days]')
period_err_lower = 0.0
period_err_upper = 0.0

# ==============================================================================
# SNIPPET 3: Update validation check in prepare_system_data()
# ==============================================================================
# Replace:
#   if all([pd.notna(x) for x in [a_over_rs, inclination]]):
# With:

if all([pd.notna(x) for x in [a_over_rs, inclination, period, transit_midtime]]):

# ==============================================================================
# SNIPPET 4: Add uncertainty defaults in prepare_system_data()
# ==============================================================================
# Add before systems.append(), after cos_i error handling:

# Handle transit timing uncertainties
if period_err_lower + period_err_upper == 0:
    # Use small default (typical precision from transits)
    period_err_lower = period * 1e-6
    period_err_upper = period * 1e-6

if transit_midtime_err_lower + transit_midtime_err_upper == 0:
    # Use small default (typical precision in days)
    transit_midtime_err_lower = 0.001
    transit_midtime_err_upper = 0.001

# ==============================================================================
# SNIPPET 5: Add to systems.append() dictionary
# ==============================================================================
# Add these fields to the dictionary:

'transit_midtime': transit_midtime,
'transit_midtime_err_lower': transit_midtime_err_lower,
'transit_midtime_err_upper': transit_midtime_err_upper,
'period': period,
'period_err_lower': period_err_lower,
'period_err_upper': period_err_upper,

# ==============================================================================
# SNIPPET 6: Replace derived quantities section in run_mcmc_for_system()
# ==============================================================================
# Replace the entire "Calculate derived quantities" section with:

# Calculate derived quantities for each sample
b_occ_samples = []
t_eclipse_samples = []
i_deg_samples = []

for s in samples:
    a_over_rs, cos_i, e, omega = s
    # Derive inclination for reporting (not needed for b_occ calculation)
    cos_i_clipped = np.clip(cos_i, -1.0, 1.0)
    i_deg = np.degrees(np.arccos(cos_i_clipped))
    i_deg_samples.append(i_deg)
    
    # Calculate b_occ directly using cos_i (no conversion needed)
    b_occ = eclipse_impact_parameter(a_over_rs, cos_i_clipped, e, omega)
    b_occ_samples.append(b_occ)
    
    # Calculate eclipse midtime
    # Sample transit midtime and period from their asymmetric distributions
    if np.random.rand() < 0.5:
        # Sample below center - use lower error
        t_tra_sample = system['transit_midtime'] - np.abs(np.random.randn()) * system['transit_midtime_err_lower']
    else:
        # Sample above center - use upper error
        t_tra_sample = system['transit_midtime'] + np.abs(np.random.randn()) * system['transit_midtime_err_upper']
    
    if np.random.rand() < 0.5:
        # Sample below center - use lower error
        period_sample = system['period'] - np.abs(np.random.randn()) * system['period_err_lower']
    else:
        # Sample above center - use upper error
        period_sample = system['period'] + np.abs(np.random.randn()) * system['period_err_upper']
    
    t_eclipse = eclipse_midtime(t_tra_sample, period_sample, e, omega)
    t_eclipse_samples.append(t_eclipse)

b_occ_samples = np.array(b_occ_samples)
t_eclipse_samples = np.array(t_eclipse_samples)
i_deg_samples = np.array(i_deg_samples)

# ==============================================================================
# SNIPPET 7: Add T_eclipse statistics in run_mcmc_for_system()
# ==============================================================================
# Add after b_occ_quantiles calculation:

# Eclipse midtime statistics
t_eclipse_median = np.median(t_eclipse_samples)
t_eclipse_std = np.std(t_eclipse_samples)
t_eclipse_16, t_eclipse_84 = np.percentile(t_eclipse_samples, [16, 84])
t_eclipse_quantiles = np.percentile(t_eclipse_samples, np.linspace(0, 100, 100))

# ==============================================================================
# SNIPPET 8: Add to results dictionary in run_mcmc_for_system()
# ==============================================================================
# Add these fields to the results dictionary:

't_eclipse_samples': t_eclipse_samples,
't_eclipse_quantiles': t_eclipse_quantiles,  # Full distribution (100 quantiles)
't_eclipse_median': t_eclipse_median,
't_eclipse_std': t_eclipse_std,
't_eclipse_16': t_eclipse_16,
't_eclipse_84': t_eclipse_84,
't_eclipse_err_lower': t_eclipse_median - t_eclipse_16,
't_eclipse_err_upper': t_eclipse_84 - t_eclipse_median,

# ==============================================================================
# SNIPPET 9: Add chain storage files at beginning of Cell 10
# ==============================================================================
# Add after the other output file definitions:

mcs_chains_file = '../results/mcs_mcmc_chains.npz'  # Full MCMC chains for reuse
tpc_chains_file = '../results/tpc_mcmc_chains.npz'

# ==============================================================================
# SNIPPET 10: Initialize chains dictionary in Cell 10
# ==============================================================================
# Add after mcs_results_list initialization:

mcs_chains_dict = {}  # Store full MCMC chains by planet name

# ==============================================================================
# SNIPPET 11: Load existing chains in Cell 10
# ==============================================================================
# Add after loading existing CSV results:

# Load existing chains if available
if os.path.exists(mcs_chains_file):
    chains_data = np.load(mcs_chains_file, allow_pickle=True)
    mcs_chains_dict = {k: chains_data[k].item() for k in chains_data.files}
    print(f"Loaded existing MCMC chains for {len(mcs_chains_dict)} systems")

# ==============================================================================
# SNIPPET 12: Store chains after MCMC in Cell 10
# ==============================================================================
# Add immediately after: result = run_mcmc_for_system(...)

# Store full MCMC chains for future reuse
mcs_chains_dict[result['name']] = {
    'samples': result['samples'],  # [a/Rs, cos_i, e, omega] samples
    'b_occ_samples': result['b_occ_samples'],
    't_eclipse_samples': result['t_eclipse_samples']
}

# ==============================================================================
# SNIPPET 13: Add T_eclipse to export dictionary in Cell 10
# ==============================================================================
# Add these fields to mcs_results_list.append() dictionary:

't_eclipse_median': result['t_eclipse_median'],
't_eclipse_16': result['t_eclipse_16'],
't_eclipse_84': result['t_eclipse_84'],
't_eclipse_std': result['t_eclipse_std'],
't_eclipse_err_lower': result['t_eclipse_err_lower'],
't_eclipse_err_upper': result['t_eclipse_err_upper'],
't_eclipse_quantiles': ','.join([f"{q:.6f}" for q in result['t_eclipse_quantiles']]),

# ==============================================================================
# SNIPPET 14: Save chains at checkpoint in Cell 10
# ==============================================================================
# Modify the checkpoint section to include:

# Save checkpoint every 50 NEW systems
if new_mcs_count % 50 == 0:
    checkpoint_df = pd.DataFrame(mcs_results_list)
    checkpoint_df.to_csv(mcs_output_file, index=False)
    # Save chains checkpoint
    np.savez_compressed(mcs_chains_file, **mcs_chains_dict)
    print(f"  Checkpoint saved ({len(mcs_results_list)} systems, {len(mcs_chains_dict)} chains)")

# ==============================================================================
# SNIPPET 15: Save final chains in Cell 10
# ==============================================================================
# Modify the final save section:

# Save MCS final results
if len(mcs_results_list) > 0:
    mcs_df = pd.DataFrame(mcs_results_list)
    mcs_df.to_csv(mcs_output_file, index=False)
    # Save all MCMC chains
    np.savez_compressed(mcs_chains_file, **mcs_chains_dict)
    if new_mcs_count > 0:
        mcs_elapsed = time.time() - mcs_start_time
        print(f"✓ MCS complete: {new_mcs_count} new systems processed in {mcs_elapsed/60:.1f} min ({mcs_elapsed/new_mcs_count:.1f} sec/planet)")
        print(f"  Total MCS results: {len(mcs_results_list)}")
        print(f"  MCMC chains saved: {len(mcs_chains_dict)} systems")
    else:
        print(f"✓ MCS: All {len(mcs_results_list)} systems already processed")

# ==============================================================================
# SNIPPET 16: Update completion message in Cell 10
# ==============================================================================
# Update the "Results saved to:" section:

print("\nResults saved to:")
print(f"  Summary (CSV):  {mcs_output_file}")
print(f"  MCMC Chains:    {mcs_chains_file}")
print("\nNote: Using asymmetric error bounds and cos(i) constrained to [0,1]")
print("      Full MCMC chains saved for reuse (no need to re-run 90 min analysis!)")

# ==============================================================================
# BONUS: Code to load and use saved chains later
# ==============================================================================

# Load all chains
chains_data = np.load('../results/mcs_mcmc_chains.npz', allow_pickle=True)

# Get list of all planets
planet_names = chains_data.files
print(f"Loaded chains for {len(planet_names)} systems")

# Access specific planet
planet_name = 'WASP-121 b'
if planet_name in chains_data.files:
    planet_chains = chains_data[planet_name].item()
    
    # Extract samples
    samples = planet_chains['samples']  # Shape: (N, 4) - [a/Rs, cos_i, e, omega]
    b_occ_samples = planet_chains['b_occ_samples']
    t_eclipse_samples = planet_chains['t_eclipse_samples']
    
    print(f"\n{planet_name}:")
    print(f"  Number of samples: {len(samples)}")
    print(f"  a/Rs:      {np.median(samples[:, 0]):.3f} ± {np.std(samples[:, 0]):.3f}")
    print(f"  cos(i):    {np.median(samples[:, 1]):.4f} ± {np.std(samples[:, 1]):.4f}")
    print(f"  e:         {np.median(samples[:, 2]):.4f} ± {np.std(samples[:, 2]):.4f}")
    print(f"  ω [deg]:   {np.median(samples[:, 3]):.2f} ± {np.std(samples[:, 3]):.2f}")
    print(f"  b_occ:     {np.median(b_occ_samples):.4f} ± {np.std(b_occ_samples):.4f}")
    print(f"  T_eclipse: {np.median(t_eclipse_samples):.6f} ± {np.std(t_eclipse_samples):.6f} [JD-2450000]")
    
    # Derive new quantity from samples (example: something that depends on correlations)
    # This is INSTANT - no need to re-run MCMC!
    new_quantity = samples[:, 0] * samples[:, 1]  # Example: a/Rs * cos(i)
    print(f"  New qty:   {np.median(new_quantity):.4f} ± {np.std(new_quantity):.4f}")
