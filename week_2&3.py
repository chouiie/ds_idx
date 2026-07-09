import glob
import os
import pandas as pd

sold_dir = '/Users/chau/Desktop/internship/sold'
output_file = '/Users/chau/Desktop/internship/sold_residential_validated.csv'

print("=" * 80)
print("DATASET STRUCTURING AND VALIDATION")
print("=" * 80)

print("\nSTEP 1: LOAD AND CONCATENATE RAW SOLD FILES")
print("-" * 80)
sold_files = sorted(glob.glob(os.path.join(sold_dir, 'CRMLSSold*.csv')))
print(f"Files loaded: {[os.path.basename(f) for f in sold_files]}")

sold = pd.concat([pd.read_csv(f, low_memory=False) for f in sold_files], ignore_index=True)
print(f"Rows: {sold.shape[0]}")
print(f"Columns: {sold.shape[1]}")
print(sold.dtypes)

print("\nSTEP 2: PROPERTY TYPES")
print("-" * 80)
print("Unique property types found (raw, before filtering):")
print(sold['PropertyType'].value_counts())

print("\nFiltering logic: keep rows where PropertyType == 'Residential'")
sold = sold[sold['PropertyType'] == 'Residential'].copy()
print(f"Rows after filtering for Residential: {len(sold)}")

print("\nSTEP 3: MISSING VALUE ANALYSIS")
print("-" * 80)
missing_counts = sold.isnull().sum()
missing_pct = (missing_counts / len(sold) * 100).round(2)
missing_report = pd.DataFrame({'MissingCount': missing_counts, 'MissingPct': missing_pct})
missing_report = missing_report.sort_values('MissingPct', ascending=False)
print(missing_report)

high_missing = missing_report[missing_report['MissingPct'] > 90]
print(f"\nColumns above 90% missing: {list(high_missing.index)}")

print("\nSTEP 4: NUMERIC DISTRIBUTION SUMMARY")
print("-" * 80)
numeric_fields = [
    'ClosePrice', 'ListPrice', 'OriginalListPrice', 'LivingArea',
    'LotSizeAcres', 'BedroomsTotal', 'BathroomsTotalInteger',
    'DaysOnMarket', 'YearBuilt'
]
numeric_fields = [f for f in numeric_fields if f in sold.columns]
distribution_summary = sold[numeric_fields].describe(
    percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
).round(2)
print(distribution_summary)

print("\nSTEP 5: INTERN QUESTIONS")
print("-" * 80)

print(f"Median close price: {sold['ClosePrice'].median()}")
print(f"Average close price: {sold['ClosePrice'].mean()}")

above_list = (sold['ClosePrice'] > sold['ListPrice']).sum()
below_list = (sold['ClosePrice'] < sold['ListPrice']).sum()
total = sold['ClosePrice'].notna().sum()
print(f"Sold above list: {above_list} ({above_list / total * 100:.2f}%)")
print(f"Sold below list: {below_list} ({below_list / total * 100:.2f}%)")

if 'ListDate' in sold.columns and 'CloseDate' in sold.columns:
    close_before_list = (pd.to_datetime(sold['CloseDate']) < pd.to_datetime(sold['ListDate'])).sum()
    print(f"Records with close date before list date: {close_before_list}")

if 'CountyOrParish' in sold.columns:
    county_prices = sold.groupby('CountyOrParish')['ClosePrice'].median().sort_values(ascending=False)
    print(county_prices)

print("\nSTEP 6: SAVING OUTPUTS")
print("-" * 80)
sold.to_csv(output_file, index=False)
missing_report.to_csv('/Users/chau/Desktop/internship/missing_value_report.csv')
distribution_summary.to_csv('/Users/chau/Desktop/internship/numeric_distribution_summary.csv')

print(f"Filtered dataset saved: {output_file}")
print(f"Final dataset size: {len(sold)} rows")

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)