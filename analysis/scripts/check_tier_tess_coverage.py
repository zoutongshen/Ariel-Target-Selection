import pandas as pd

# Load datasets
mcs = pd.read_csv('../../data/raw/Ariel_MCS_Known_2025-07-18.csv')
tess = pd.read_csv('../../data/raw/hlsp_tess-svc_tess_lcf_all-s0001-s0026_tess_v1.0_cat.csv')

# Extract TIC numeric and check TESS coverage
mcs['TIC_numeric'] = mcs['TIC ID'].str.replace('TIC ', '').astype(float)
mcs['in_tess_var'] = mcs['TIC_numeric'].isin(tess['tess_id'])

# Breakdown by tier
print("="*70)
print("TESS VARIABILITY COVERAGE BY MAX TIER")
print("="*70)

for tier in [1, 2, 3]:
    tier_data = mcs[mcs['Max Tier'] == tier]
    count = len(tier_data)
    with_tess = tier_data['in_tess_var'].sum()
    pct = 100*with_tess/count if count > 0 else 0
    print(f"\nMax Tier {tier}:")
    print(f"  Total planets: {count}")
    print(f"  With TESS variability: {with_tess} ({pct:.1f}%)")

# Combined Tier 2+3
tier23 = mcs[mcs['Max Tier'].isin([2, 3])]
print(f"\nMax Tier 2 or 3 combined:")
print(f"  Total planets: {len(tier23)}")
print(f"  With TESS variability: {tier23['in_tess_var'].sum()} ({100*tier23['in_tess_var'].sum()/len(tier23):.1f}%)")

# Show examples
print("\n" + "="*70)
print("Examples of Max Tier 2/3 planets WITH TESS variability:")
print("="*70)
examples = tier23[tier23['in_tess_var']][['Planet Name', 'Max Tier', 'TIC ID']].head(15)
print(examples.to_string(index=False))
