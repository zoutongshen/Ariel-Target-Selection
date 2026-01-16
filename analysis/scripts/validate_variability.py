import pandas as pd
import numpy as np
import os

# Get script directory and navigate to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..', '..')

var = pd.read_csv(os.path.join(project_root, 'analysis/results/mcs_stellar_variability_estimates.csv'))
mcs = pd.read_csv(os.path.join(project_root, 'data/raw/Ariel_MCS_Known_2025-07-18.csv'))

print('='*70)
print('PHYSICAL VALIDATION OF DERIVED PARAMETERS')
print('='*70)

# 1. Rotation Period Validation
print('\n=== ROTATION PERIOD VALIDATION ===')
prot = var['P_rot_derived'].dropna()
print(f'Total: {len(prot)}')
print(f'Range: {prot.min():.2f} - {prot.max():.2f} days')
print(f'Median: {prot.median():.2f} days')
print(f'Very fast (<0.5d): {(prot < 0.5).sum()}')
print(f'Very slow (>100d): {(prot > 100).sum()}')

if (prot < 0.5).sum() > 0:
    print('\nVery fast rotators (<0.5d):')
    fast = var[var['P_rot_derived'] < 0.5][['Planet Name', 'P_rot_derived', 'rotation_source']]
    print(fast.to_string(index=False))

if (prot > 100).sum() > 0:
    print('\nVery slow rotators (>100d):')
    slow = var[var['P_rot_derived'] > 100][['Planet Name', 'P_rot_derived', 'rotation_source']]
    print(slow.head(10).to_string(index=False))

# 2. Variability Validation
print('\n=== VARIABILITY VALIDATION ===')
vvar = var['variability_ppm'].dropna()
print(f'Range: {vvar.min():.0f} - {vvar.max():.0f} ppm')
print(f'Median: {vvar.median():.0f} ppm')
print(f'Very low (<10 ppm): {(vvar < 10).sum()}')
print(f'Very high (>10000 ppm): {(vvar > 10000).sum()}')

if (vvar > 10000).sum() > 0:
    print('\nVery high variability (>10000 ppm):')
    high = var[var['variability_ppm'] > 10000][['Planet Name', 'variability_ppm', 'P_rot_derived']]
    print(high.head(10).to_string(index=False))

# 3. vsini Self-Consistency Check
print('\n=== VSINI SELF-CONSISTENCY ===')
vsini_df = var[var['rotation_source'] == 'vsini_derived'].copy()
vsini_df = vsini_df.merge(mcs[['Planet Name', 'Star Radius [Rs]']], on='Planet Name')
# Calculate what vsini should be given the derived P_rot
vsini_df['vsini_calc'] = (2 * np.pi * vsini_df['Star Radius [Rs]'] * 695700) / (vsini_df['P_rot_derived'] * 86400 * 0.8)
vsini_df['ratio'] = vsini_df['vsini_calc'] / vsini_df['Star Rotational Velocity [km/s]']
print(f'Total vsini-derived: {len(vsini_df)}')
print(f'vsini ratio (should be ~1.0): median={vsini_df["ratio"].median():.2f}, mean={vsini_df["ratio"].mean():.2f}')
outliers = ((vsini_df['ratio'] < 0.5) | (vsini_df['ratio'] > 2.0)).sum()
print(f'Outliers (ratio <0.5 or >2.0): {outliers}')

if outliers > 0:
    print('\nvsini outliers:')
    out = vsini_df[((vsini_df['ratio'] < 0.5) | (vsini_df['ratio'] > 2.0))][
        ['Planet Name', 'P_rot_derived', 'Star Rotational Velocity [km/s]', 'vsini_calc', 'ratio']
    ]
    print(out.head(10).to_string(index=False))

# 4. Rotation-Variability Correlation
print('\n=== ROTATION-VARIABILITY CORRELATION ===')
rot_var = var[(var['variability_source'] == 'rotation_period') & var['P_rot_derived'].notna()].copy()
corr = rot_var[['P_rot_derived', 'variability_ppm']].corr().iloc[0, 1]
print(f'Correlation: {corr:.3f} (should be negative: faster rotation → higher variability)')

# Bin by rotation period
rot_var['P_bin'] = pd.cut(rot_var['P_rot_derived'], bins=[0, 5, 10, 20, 50, 200])
print('\nMedian variability by rotation period bin:')
binned = rot_var.groupby('P_bin', observed=False)['variability_ppm'].agg(['median', 'count'])
print(binned)

# 5. Sample comparisons
print('\n=== SAMPLE COMPARISONS ===')
print('Systems with both TESS measured and rotation-derived (for comparison):')
var_merged = var.merge(mcs[['Planet Name', 'Star Temperature [K]']], on='Planet Name')
both = var_merged[(var_merged['variability_source'] == 'TESS_measured') & 
                  var_merged['P_rot_derived'].notna()].copy()
if len(both) > 0:
    # Calculate what variability would be from rotation
    both['var_from_rot'] = both.apply(
        lambda row: 1500 * (row['P_rot_derived'] / 10)**(-0.5) * 
                    (2.0 if row['Star Temperature [K]'] < 4000 else
                     1.5 if row['Star Temperature [K]'] < 5200 else
                     0.7 if row['Star Temperature [K]'] > 6500 else 1.0),
        axis=1
    )
    both['ratio'] = both['variability_ppm'] / both['var_from_rot']
    print(f'Total with both: {len(both)}')
    print(f'TESS/rotation_estimate ratio: median={both["ratio"].median():.2f}')
    print('\nSample:')
    sample = both[['Planet Name', 'variability_ppm', 'var_from_rot', 'ratio']].head(10)
    sample.columns = ['Planet', 'TESS_var', 'Rot_estimate', 'Ratio']
    print(sample.to_string(index=False))

print('\n' + '='*70)
print('✓ Validation complete')
