import pandas as pd
import numpy as np

# Load datasets
mcs = pd.read_csv('../../data/raw/Ariel_MCS_Known_2025-07-18.csv')
tess = pd.read_csv('../../data/raw/hlsp_tess-svc_tess_lcf_all-s0001-s0026_tess_v1.0_cat.csv')

# Extract TIC numeric
mcs['TIC_numeric'] = mcs['TIC ID'].str.replace('TIC ', '').astype(float)

# Merge with TESS variability
mcs_with_var = mcs.merge(
    tess[['tess_id', 'amp_var_1']], 
    left_on='TIC_numeric', 
    right_on='tess_id', 
    how='left'
)

# Function to derive rotation period from vsini
def rotation_from_vsini(vsini, radius, assume_sin_i=0.8):
    """
    Derive rotation period from vsini and stellar radius
    P = 2πR / (vsini × sin(i))
    
    Parameters:
    - vsini: km/s
    - radius: solar radii
    - assume_sin_i: assumed sin(i), default 0.8 for random orientations
    
    Returns: rotation period in days
    """
    if pd.isna(vsini) or pd.isna(radius) or vsini == 0:
        return np.nan
    
    # Convert radius to km (1 R_sun = 695700 km)
    R_km = radius * 695700
    
    # P = 2πR / (vsini × sin(i))
    # Convert to days: divide by (86400 s/day)
    P_rot = (2 * np.pi * R_km) / (vsini * assume_sin_i * 86400)
    
    return P_rot

# Function to estimate rotation period from age (gyrochronology)
def rotation_from_age(age_gyr, Teff, mass=None):
    """
    Gyrochronology relation from Barnes (2007) and van Saders et al. (2016)
    P_rot ≈ Age^n × f(mass, Teff)
    
    Returns: rotation period in days
    """
    if pd.isna(age_gyr) or pd.isna(Teff) or age_gyr <= 0:
        return np.nan
    
    # Convert Teff to B-V color (approximate)
    # B-V ≈ 0.68 for G2V (5780K), scales with temperature
    if Teff > 7000:  # Too hot for gyro
        return np.nan
    elif Teff > 6000:  # F stars
        BV = 0.3 + 0.00004 * (6500 - Teff)
    elif Teff > 5000:  # G stars  
        BV = 0.5 + 0.0003 * (6000 - Teff)
    elif Teff > 3800:  # K stars
        BV = 0.8 + 0.0004 * (5000 - Teff)
    else:  # M dwarfs - gyro less reliable
        BV = 1.5 + 0.0002 * (4000 - Teff)
    
    # Barnes (2007) gyrochronology relation
    # P = age^0.519 × 0.7725 × (B-V - 0.4)^0.601 (for Mamajek-Hillenbrand)
    if BV < 0.5:  # Too blue for reliable gyro
        return np.nan
        
    n = 0.519  # age exponent
    a = 0.601  # color exponent
    b = 0.7725
    
    P_rot = b * (age_gyr * 1000)**n * (BV - 0.4)**a
    
    # Sanity check: rotation periods should be 1-100 days typically
    if P_rot < 0.5 or P_rot > 100:
        return np.nan
        
    return P_rot

# Function to estimate variability from rotation period
def variability_from_rotation(P_rot, Teff):
    """
    Empirical relation from McQuillan et al. (2014) and Morris et al. (2020)
    Returns variability in ppm
    """
    if pd.isna(P_rot):
        return np.nan
    
    # Basic power-law relation (simplified)
    # More active for shorter periods
    base_var = 1500 * (P_rot / 10)**(-0.5)
    
    # Adjust for stellar type (K/M stars more variable)
    if not pd.isna(Teff):
        if Teff < 4000:  # M dwarf
            base_var *= 2.0
        elif Teff < 5200:  # K dwarf
            base_var *= 1.5
        elif Teff > 6500:  # F star
            base_var *= 0.7
    
    return base_var

# Function to estimate from stellar type
def variability_from_type(Teff, logg=None):
    """
    Typical variability ranges based on stellar parameters
    Returns variability in ppm
    """
    if pd.isna(Teff):
        return 500  # conservative default
    
    # Check if giant/subgiant (more variable)
    is_evolved = False
    if not pd.isna(logg) and logg < 4.0:
        is_evolved = True
    
    if Teff < 3500:  # M dwarf
        return 3000 if not is_evolved else 5000
    elif Teff < 4000:
        return 2000 if not is_evolved else 3500
    elif Teff < 5200:  # K dwarf
        return 1000 if not is_evolved else 2000
    elif Teff < 6000:  # G dwarf
        return 200 if not is_evolved else 500
    elif Teff < 7500:  # F star
        return 300 if not is_evolved else 800
    else:  # A star and hotter
        return 100 if not is_evolved else 300

# Derive rotation periods from other parameters
print("Deriving rotation periods from vsini and age...")
mcs_with_var['P_rot_derived'] = mcs_with_var['Star Rotation Period [days]']  # Start with catalog values

# Derive from vsini where rotation period is missing
no_prot = mcs_with_var['P_rot_derived'].isna()
has_vsini = mcs_with_var['Star Rotational Velocity [km/s]'].notna()
vsini_derive_mask = no_prot & has_vsini

mcs_with_var.loc[vsini_derive_mask, 'P_rot_derived'] = mcs_with_var.loc[vsini_derive_mask].apply(
    lambda row: rotation_from_vsini(row['Star Rotational Velocity [km/s]'], row['Star Radius [Rs]']),
    axis=1
)

# Derive from gyrochronology where still missing
still_no_prot = mcs_with_var['P_rot_derived'].isna()
has_age = mcs_with_var['Star Age [Gyr]'].notna()
gyro_mask = still_no_prot & has_age

mcs_with_var.loc[gyro_mask, 'P_rot_derived'] = mcs_with_var.loc[gyro_mask].apply(
    lambda row: rotation_from_age(row['Star Age [Gyr]'], row['Star Temperature [K]'], row['Star Mass [Ms]']),
    axis=1
)

print(f"  Catalog rotation periods: {mcs_with_var['Star Rotation Period [days]'].notna().sum()}")
print(f"  + Derived from vsini: {vsini_derive_mask.sum()} attempted, {mcs_with_var.loc[vsini_derive_mask, 'P_rot_derived'].notna().sum()} successful")
print(f"  + Derived from gyrochronology: {gyro_mask.sum()} attempted, {mcs_with_var.loc[gyro_mask, 'P_rot_derived'].notna().sum()} successful")
print(f"  Total with rotation period: {mcs_with_var['P_rot_derived'].notna().sum()}/{len(mcs_with_var)} ({100*mcs_with_var['P_rot_derived'].notna().sum()/len(mcs_with_var):.1f}%)")

# Apply hierarchy for variability estimation
mcs_with_var['variability_ppm'] = np.nan
mcs_with_var['variability_source'] = 'none'
mcs_with_var['rotation_source'] = 'none'

# 1. Use TESS data if available
tess_mask = mcs_with_var['amp_var_1'].notna()
mcs_with_var.loc[tess_mask, 'variability_ppm'] = mcs_with_var.loc[tess_mask, 'amp_var_1']
mcs_with_var.loc[tess_mask, 'variability_source'] = 'TESS_measured'
mcs_with_var.loc[tess_mask, 'rotation_source'] = 'not_needed'

# 2. Estimate from rotation period (catalog or derived)
no_tess_mask = ~tess_mask
has_rotation_derived = mcs_with_var['P_rot_derived'].notna()
rotation_mask = no_tess_mask & has_rotation_derived

mcs_with_var.loc[rotation_mask, 'variability_ppm'] = mcs_with_var.loc[rotation_mask].apply(
    lambda row: variability_from_rotation(row['P_rot_derived'], row['Star Temperature [K]']),
    axis=1
)
mcs_with_var.loc[rotation_mask, 'variability_source'] = 'rotation_period'

# Track rotation period source
catalog_prot = mcs_with_var['Star Rotation Period [days]'].notna()
mcs_with_var.loc[rotation_mask & catalog_prot, 'rotation_source'] = 'catalog'
mcs_with_var.loc[rotation_mask & ~catalog_prot & vsini_derive_mask, 'rotation_source'] = 'vsini_derived'
mcs_with_var.loc[rotation_mask & ~catalog_prot & gyro_mask, 'rotation_source'] = 'gyro_derived'

# 3. Use stellar type typical values for the rest
remaining_mask = no_tess_mask & ~has_rotation_derived
mcs_with_var.loc[remaining_mask, 'variability_ppm'] = mcs_with_var.loc[remaining_mask].apply(
    lambda row: variability_from_type(row['Star Temperature [K]'], row['Star log(g)']),
    axis=1
)
mcs_with_var.loc[remaining_mask, 'variability_source'] = 'stellar_type'
mcs_with_var.loc[remaining_mask, 'rotation_source'] = 'not_derived'

# Summary
print("="*70)
print("STELLAR VARIABILITY ESTIMATION COVERAGE")
print("="*70)

total = len(mcs_with_var)
tier23 = mcs_with_var[mcs_with_var['Max Tier'].isin([2, 3])]

print(f"\n=== Rotation Period Sources ===")
print(f"Catalog: {(mcs_with_var['rotation_source'] == 'catalog').sum()}")
print(f"Derived from vsini: {(mcs_with_var['rotation_source'] == 'vsini_derived').sum()}")
print(f"Derived from gyrochronology: {(mcs_with_var['rotation_source'] == 'gyro_derived').sum()}")
print(f"Total with rotation period: {mcs_with_var['P_rot_derived'].notna().sum()}/{total} ({100*mcs_with_var['P_rot_derived'].notna().sum()/total:.1f}%)")

print(f"\n=== All MCS systems ({total} total) ===")
for source in ['TESS_measured', 'rotation_period', 'stellar_type']:
    count = (mcs_with_var['variability_source'] == source).sum()
    print(f"  {source}: {count} ({100*count/total:.1f}%)")

print(f"\n=== Tier 2/3 systems ({len(tier23)} total) ===")
for source in ['TESS_measured', 'rotation_period', 'stellar_type']:
    count = (tier23['variability_source'] == source).sum()
    print(f"  {source}: {count} ({100*count/len(tier23):.1f}%)")

print(f"\nBreakdown of rotation_period source for Tier 2/3:")
for rot_source in ['catalog', 'vsini_derived', 'gyro_derived']:
    count = ((tier23['variability_source'] == 'rotation_period') & (tier23['rotation_source'] == rot_source)).sum()
    print(f"  {rot_source}: {count}")

# Show examples
print("\n" + "="*70)
print("Example estimates for Tier 2/3 systems:")
print("="*70)
examples = tier23[['Planet Name', 'Star Temperature [K]', 'Star Rotation Period [days]', 
                    'P_rot_derived', 'rotation_source', 'variability_ppm', 'variability_source']].sample(min(15, len(tier23)), random_state=42)
examples_display = examples.copy()
examples_display.columns = ['Planet', 'Teff', 'P_rot_cat', 'P_rot_final', 'P_source', 'Var(ppm)', 'Var_source']
print(examples_display.to_string(index=False))

# Save results
output_file = '../results/mcs_stellar_variability_estimates.csv'
mcs_with_var[['Planet Name', 'TIC ID', 'Star Temperature [K]', 'Star Rotational Velocity [km/s]',
              'Star Rotation Period [days]', 'P_rot_derived', 'rotation_source',
              'variability_ppm', 'variability_source']].to_csv(output_file, index=False)
print(f"\n✓ Saved variability estimates to: {output_file}")
