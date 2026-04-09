import pandas as pd
import re

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 1: Load the main Excel file "Exim Azithromycin.xlsx" ─────────────────
# ═══════════════════════════════════════════════════════════════════════════════
df = pd.read_excel("Exim Azithromycin.xlsx")

print("Columns found:", df.columns.tolist())
print("Sample data:\n", df.head(3))

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 2: Define grading function ───────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
def assign_grade(item_text):
    if not isinstance(item_text, str):
        return "USP"
    text = item_text.upper()
    has_ip  = bool(re.search(r'\bIP\b', text))
    has_ep  = bool(re.search(r'\bEP\b', text))
    has_usp = bool(re.search(r'\bUSP\b', text))
    if has_usp:
        return "USP"
    elif has_ep:
        return "EP"
    elif has_ip:
        return "IP"
    else:
        return "USP"

# ── Apply GRADE if not already present ────────────────────────────────────────
if "GRADE" not in df.columns:
    df["GRADE"] = df["ITEM"].apply(assign_grade)

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 3: Convert BE_DATE → yyyymm string ────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
df["BE_DATE"] = pd.to_datetime(df["BE_DATE"], errors="coerce")
df["yyyymm"]  = df["BE_DATE"].dt.strftime("%Y%m")

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 4: Ensure numeric types ──────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
df["QTY"]            = pd.to_numeric(df["QTY"],            errors="coerce").fillna(0)
df["TOTAL_VALUE"]    = pd.to_numeric(df["TOTAL_VALUE"],    errors="coerce").fillna(0)
df["UNIT_VALUE_INR"] = pd.to_numeric(df["UNIT_VALUE_INR"], errors="coerce")

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 4a: Filter UOM — keep only "Kg" rows ─────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
df = df[df["UQC"].str.strip() == "Kg"]
print(f"\nRows after UOM filter (Kg only): {len(df)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 4b: Filter UNIT_VALUE_INR within [9000, 17000] ───────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
df = df[(df["UNIT_VALUE_INR"] >= 9000) & (df["UNIT_VALUE_INR"] <= 17000)]
print(f"Rows after UNIT_VALUE_INR filter [9000–17000]: {len(df)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 4c: Remove outliers — keep only rows where QTY > 10% of avg QTY ──────
# ═══════════════════════════════════════════════════════════════════════════════
avg_qty       = df["QTY"].mean()
qty_threshold = 0.10 * avg_qty
df = df[df["QTY"] > qty_threshold]

print(f"Average QTY: {avg_qty:.2f} | 10% threshold: {qty_threshold:.2f}")
print(f"Rows after QTY outlier filter (>10% of avg): {len(df)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 5a: Supplier aggregation — grouped by Supp_Name + COUNTRY ─────────────
# ═══════════════════════════════════════════════════════════════════════════════
supp_agg = (
    df.groupby(["Supp_Name", "COUNTRY", "yyyymm", "UQC", "GRADE"], as_index=False)
    .agg(
        Sum_of_QTY         = ("QTY",         "sum"),
        Sum_of_TOTAL_VALUE = ("TOTAL_VALUE",  "sum"),
    )
)

def calc_avg_price(row):
    if row["Sum_of_QTY"] == 0:
        return "-"
    return round(row["Sum_of_TOTAL_VALUE"] / row["Sum_of_QTY"], 2)

supp_agg["Avg_PRICE"] = supp_agg.apply(calc_avg_price, axis=1)

supp_agg.rename(columns={
    "Supp_Name": "supplier",
    "COUNTRY":   "country",
    "UQC":       "uom",
    "GRADE":     "GRADE/SPEC",
}, inplace=True)

supp_agg = supp_agg[[
    "supplier", "country", "yyyymm", "uom", "GRADE/SPEC",
    "Sum_of_QTY", "Sum_of_TOTAL_VALUE", "Avg_PRICE"
]]

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 5b: Importer aggregation — grouped by IMPORTER (no COUNTRY) ──────────
# ═══════════════════════════════════════════════════════════════════════════════
imp_agg = (
    df.groupby(["IMPORTER", "yyyymm", "UQC", "GRADE"], as_index=False)
    .agg(
        Sum_of_QTY         = ("QTY",         "sum"),
        Sum_of_TOTAL_VALUE = ("TOTAL_VALUE",  "sum"),
    )
)

imp_agg["Avg_PRICE"] = imp_agg.apply(calc_avg_price, axis=1)

imp_agg.rename(columns={
    "IMPORTER": "importer",
    "UQC":      "uom",
    "GRADE":    "GRADE/SPEC",
}, inplace=True)

imp_agg = imp_agg[[
    "importer", "yyyymm", "uom", "GRADE/SPEC",
    "Sum_of_QTY", "Sum_of_TOTAL_VALUE", "Avg_PRICE"
]]

# ═══════════════════════════════════════════════════════════════════════════════
# ── Step 6: Print results to console ──────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
print("\n===== Aggregated Exim Data (Supplier) =====")
print(supp_agg.to_string(index=False))

print("\n===== Aggregated Exim Data (Importer) =====")
print(imp_agg.to_string(index=False))

# ═════════════════════════════════════════════════════════════════════════════
# ── Step 7: Save to Excel ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
supp_agg.to_excel("exim_aggregated.xlsx",          index=False)
imp_agg.to_excel("exim_aggregated_importers.xlsx", index=False)

print("\nSupplier aggregation saved to  → exim_aggregated.xlsx")
print("Importer aggregation saved to  → exim_aggregated_importers.xlsx")