import pandas as pd
import glob
import os


sold_dir = '/Users/chau/Desktop/internship/sold/'

# Get all sold CSV files and sort them chronologically
sold_files = sorted(glob.glob(os.path.join(sold_dir, 'CRMLSSold*.csv')))

print("=" * 80)
print("SOLD DATA PROCESSING")
print("=" * 80)

# Step 1: Concatenate all sold files
print("\nSTEP 1: CONCATENATING ALL SOLD MONTHLY FILES")
print("-" * 80)

# Read and concatenate all sold files
sold_dataframes = [pd.read_csv(file) for file in sold_files]
sold_combined = pd.concat(sold_dataframes, ignore_index=True)

# Row count before filtering
rows_before_filter = len(sold_combined)
print(f"Total rows after concatenation: {rows_before_filter}")
print(f"Files concatenated: {len(sold_files)}")
for file in sold_files:
    print(f"  - {os.path.basename(file)}")

# Step 2: Filter for Residential properties only
print("\nSTEP 2: FILTERING FOR RESIDENTIAL PROPERTIES ONLY")
print("-" * 80)

# Filter to only Residential property type
sold_residential = sold_combined[sold_combined['PropertyType'] == 'Residential'].copy()

# Row count after filtering
rows_after_filter = len(sold_residential)
print(f"Total rows after filtering for Residential: {rows_after_filter}")
print(f"Rows removed by filter: {rows_before_filter - rows_after_filter}")
print(f"Percentage of Residential properties: {(rows_after_filter / rows_before_filter * 100):.2f}%")

# Step 3: Save the filtered dataset
print("\nSTEP 3: SAVING FILTERED RESIDENTIAL SOLD DATASET")
print("-" * 80)

output_file = '/Users/chau/Desktop/internship/sold_residential_combined.csv'
sold_residential.to_csv(output_file, index=False)
print(f"File saved: {output_file}")
print(f"Final dataset size: {len(sold_residential)} rows")

print("\n" + "=" * 80)
print("PROCESSING COMPLETE")
print("=" * 80)
