import pandas as pd

input_file = '/Users/chau/Desktop/internship/sold_residential_validated.csv'
output_file = '/Users/chau/Desktop/internship/sold_residential_cleaned.csv'

sold = pd.read_csv(input_file, low_memory=False)
rows_before = len(sold)
cols_before = sold.shape[1]

print("=" * 80)
print("WEEKS 4-5 - DATA CLEANING AND PREPARATION")
print("=" * 80)
print(f"Rows before cleaning: {rows_before}")
print(f"Columns before cleaning: {cols_before}")

print("\nSTEP 1: DATE FIELD CONVERSION")
print("-" * 80)
date_fields = ['CloseDate', 'PurchaseContractDate', 'ListingContractDate', 'ContractStatusChangeDate']
for col in date_fields:
    before_na = sold[col].isnull().sum()
    sold[col] = pd.to_datetime(sold[col], errors='coerce')
    after_na = sold[col].isnull().sum()
    print(f"{col}: dtype -> {sold[col].dtype}, unparseable values introduced: {after_na - before_na}")

print("\nSTEP 2: REMOVING UNNECESSARY / REDUNDANT COLUMNS")
print("-" * 80)

# Columns that are >90% missing (from Week 2-3 missing value report) carry no
# usable signal for analysis.
high_missing_cols = [
    'AboveGradeFinishedArea', 'MiddleOrJuniorSchoolDistrict', 'BusinessType',
    'ElementarySchoolDistrict', 'TaxYear', 'TaxAnnualAmount', 'FireplacesTotal',
    'CoveredSpaces', 'WaterfrontYN', 'BelowGradeFinishedArea', 'BasementYN',
    'BuilderName', 'LotSizeDimensions', 'BuildingAreaTotal', 'CoBuyerAgentFirstName',
]

# True duplicates / redundant encodings of information already kept elsewhere.
redundant_cols = {
    'ListingKeyNumeric': 'identical to ListingKey',
    'OriginatingSystemName': 'constant value (CRMLS) for every row, no signal',
    'ListAgentFullName': 'derivable from ListAgentFirstName + ListAgentLastName',
    'LotSizeSquareFeet': 'perfectly correlated with LotSizeAcres (same measure, different unit)',
    'LotSizeArea': 'inconsistent/unreliable duplicate of LotSizeAcres',
}

drop_cols = [c for c in high_missing_cols + list(redundant_cols) if c in sold.columns]
print(f">90% missing, dropped: {[c for c in high_missing_cols if c in sold.columns]}")
for col, reason in redundant_cols.items():
    if col in sold.columns:
        print(f"Redundant, dropped: {col} ({reason})")

sold = sold.drop(columns=drop_cols)
print(f"Columns after removal: {sold.shape[1]} (dropped {len(drop_cols)})")

print("\nSTEP 3: MISSING VALUE HANDLING")
print("-" * 80)

# Categorical/text fields: missingness is itself meaningful (e.g. no school
# district on file) so fill with an explicit label instead of dropping rows.
categorical_cols = sold.select_dtypes(include='object').columns
filled_counts = sold[categorical_cols].isnull().sum()
filled_counts = filled_counts[filled_counts > 0]
sold[categorical_cols] = sold[categorical_cols].fillna('Unknown')
print(f"Categorical columns filled with 'Unknown' ({len(filled_counts)} columns had nulls):")
print(filled_counts.to_string())

# Numeric fields: left as NaN. Imputing price/area/etc. with mean or median
# would fabricate values and distort the distribution analysis from Week 2-3.
numeric_cols = sold.select_dtypes(include='number').columns
numeric_na = sold[numeric_cols].isnull().sum()
numeric_na = numeric_na[numeric_na > 0]
print(f"\nNumeric columns left as NaN (no imputation, {len(numeric_na)} columns affected):")
print(numeric_na.to_string())

print("\nSTEP 4: NUMERIC TYPE ENFORCEMENT")
print("-" * 80)
expected_numeric = [
    'ClosePrice', 'ListPrice', 'OriginalListPrice', 'LivingArea', 'LotSizeAcres',
    'BedroomsTotal', 'BathroomsTotalInteger', 'DaysOnMarket', 'YearBuilt',
    'Latitude', 'Longitude', 'ParkingTotal', 'GarageSpaces', 'Stories',
    'MainLevelBedrooms', 'AssociationFee',
]
for col in expected_numeric:
    if col in sold.columns:
        sold[col] = pd.to_numeric(sold[col], errors='coerce')
print(sold[[c for c in expected_numeric if c in sold.columns]].dtypes.to_string())

print("\nSTEP 5: INVALID NUMERIC VALUE FLAGS")
print("-" * 80)
# Flagged rather than dropped so records stay available for audit; downstream
# analysis can filter on these flags as needed.
sold['invalid_price_flag'] = sold['ClosePrice'] <= 0
sold['invalid_area_flag'] = sold['LivingArea'] <= 0
sold['invalid_dom_flag'] = sold['DaysOnMarket'] < 0
sold['invalid_beds_baths_flag'] = (sold['BedroomsTotal'] < 0) | (sold['BathroomsTotalInteger'] < 0)

print(f"invalid_price_flag (ClosePrice <= 0): {sold['invalid_price_flag'].sum()}")
print(f"invalid_area_flag (LivingArea <= 0): {sold['invalid_area_flag'].sum()}")
print(f"invalid_dom_flag (DaysOnMarket < 0): {sold['invalid_dom_flag'].sum()}")
print(f"invalid_beds_baths_flag (negative Bedrooms/Bathrooms): {sold['invalid_beds_baths_flag'].sum()}")

print("\nSTEP 6: DATE CONSISTENCY CHECKS")
print("-" * 80)
# Logical ordering should be ListingContractDate -> PurchaseContractDate -> CloseDate.
# Comparisons naturally skip rows where either date is NaT (NaT comparisons are False).
sold['listing_after_close_flag'] = sold['ListingContractDate'] > sold['CloseDate']
sold['purchase_after_close_flag'] = sold['PurchaseContractDate'] > sold['CloseDate']
sold['negative_timeline_flag'] = (
    sold['listing_after_close_flag']
    | sold['purchase_after_close_flag']
    | (sold['ListingContractDate'] > sold['PurchaseContractDate'])
)

print(f"listing_after_close_flag (ListingContractDate > CloseDate): {sold['listing_after_close_flag'].sum()}")
print(f"purchase_after_close_flag (PurchaseContractDate > CloseDate): {sold['purchase_after_close_flag'].sum()}")
print(f"negative_timeline_flag (any date-order violation): {sold['negative_timeline_flag'].sum()}")

print("\nSTEP 7: GEOGRAPHIC DATA CHECKS")
print("-" * 80)
# California bounding box (generous) used only to catch grossly implausible
# coordinates, not to validate precise parcel location.
CA_LAT_MIN, CA_LAT_MAX = 32.0, 42.5
CA_LON_MIN, CA_LON_MAX = -124.5, -114.0

sold['missing_coords_flag'] = sold['Latitude'].isnull() | sold['Longitude'].isnull()
sold['zero_coords_flag'] = (sold['Latitude'] == 0) | (sold['Longitude'] == 0)
sold['positive_longitude_flag'] = sold['Longitude'] > 0

has_coords = ~sold['missing_coords_flag']
sold['implausible_coords_flag'] = has_coords & (
    ~sold['Latitude'].between(CA_LAT_MIN, CA_LAT_MAX)
    | ~sold['Longitude'].between(CA_LON_MIN, CA_LON_MAX)
)

print(f"missing_coords_flag (Latitude or Longitude null): {sold['missing_coords_flag'].sum()}")
print(f"zero_coords_flag (Latitude = 0 or Longitude = 0): {sold['zero_coords_flag'].sum()}")
print(f"positive_longitude_flag (Longitude > 0): {sold['positive_longitude_flag'].sum()}")
print(f"implausible_coords_flag (outside CA bounding box): {sold['implausible_coords_flag'].sum()}")

print("\nSTEP 8: SAVING CLEANED DATASET")
print("-" * 80)
sold.to_csv(output_file, index=False)

print("\nSUMMARY")
print("-" * 80)
print(f"Rows before: {rows_before}  |  Rows after: {len(sold)} (no rows dropped, only flagged)")
print(f"Columns before: {cols_before}  |  Columns after: {sold.shape[1]}")
print("Data types confirmed: date fields -> datetime64[ns], expected numeric fields -> numeric dtype")
print("\nDate consistency flag counts:")
print(f"  listing_after_close_flag: {sold['listing_after_close_flag'].sum()}")
print(f"  purchase_after_close_flag: {sold['purchase_after_close_flag'].sum()}")
print(f"  negative_timeline_flag: {sold['negative_timeline_flag'].sum()}")
print("\nGeographic data quality summary:")
print(f"  missing_coords_flag: {sold['missing_coords_flag'].sum()}")
print(f"  zero_coords_flag: {sold['zero_coords_flag'].sum()}")
print(f"  positive_longitude_flag: {sold['positive_longitude_flag'].sum()}")
print(f"  implausible_coords_flag: {sold['implausible_coords_flag'].sum()}")
print(f"Cleaned dataset saved: {output_file}")
