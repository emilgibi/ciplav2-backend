import pandas as pd
import re

# ════════════════════════════════════════════════════════════════════════════
# ── Step 1: Load the CSV (output_with_grade1.csv) ───────────────────────────
# ══════════════════════���═════════════════════════════════════════════════════
df = pd.read_csv("output_with_grade1.csv")

print("Columns found:", df.columns.tolist())
print("Sample data:\n", df.head(3))

# ════════════════════════════════════════════════════════════════════════════
# ── Step 2: Define grading function (already done, kept for completeness) ───
# ════════════════════════════════════════════════════════════════════════════
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

# ── Apply GRADE if not already present in the CSV ───────────────────────────
if "GRADE" not in df.columns:
    df["GRADE"] = df["ITEM"].apply(assign_grade)

# ════════════════════════════════════════════════════════════════════════════
# ── Step 3: Convert BE_DATE (YYYYMMDD int) → yyyymm string ──────────────────
# ════════════════════════════════════════════════════════════════════════════
# BE_DATE is in format "2025-09-13" → parse it → extract YYYYMM as "202509"
df["BE_DATE"] = pd.to_datetime(df["BE_DATE"], errors="coerce")
df["yyyymm"] = df["BE_DATE"].dt.strftime("%Y%m")   # → "202509"

# ════════════════════════════════════════════════════════════════════════════
# ── Step 4: Ensure numeric types for QTY and TOTAL_VALUE ────────────────────
# ════════════════════════════════════════════════════════════════════════════
df["QTY"]         = pd.to_numeric(df["QTY"],         errors="coerce").fillna(0)
df["TOTAL_VALUE"] = pd.to_numeric(df["TOTAL_VALUE"],  errors="coerce").fillna(0)

# ════════════════════════════════════════════════════════════════════════════
# ── Step 5: Aggregation ─────────────────────────────────────────────────────
# Group by: IMPORTER (buyer), yyyymm, UQC (unit of measure), GRADE
# ════════════════════════════════════════════════════════════════════════════
agg_df = (
    df.groupby(["Supp_Name", "yyyymm", "UQC", "GRADE"], as_index=False)
    .agg(
        Sum_of_QTY         = ("QTY",         "sum"),
        Sum_of_TOTAL_VALUE = ("TOTAL_VALUE",  "sum"),
    )
)

# ════════════════════════════════════════════════════════════════════════════
# ── Step 6: Avg PRICE = Sum of TOTAL_VALUE / Sum of QTY ─────────────────────
# Show '-' when QTY is 0 to avoid division by zero
# ════════════════════════════════════════════════════════════════════════════
def calc_avg_price(row):
    if row["Sum_of_QTY"] == 0:
        return "-"
    return round(row["Sum_of_TOTAL_VALUE"] / row["Sum_of_QTY"], 2)

agg_df["Avg_PRICE"] = agg_df.apply(calc_avg_price, axis=1)

# ════════════════════════════════════════════════════════════════════════════
# ── Step 7: Rename columns to match display format ──────────────────────────
# ════════════════════════════════════════════════════════════════════════════
agg_df.rename(columns={
    "Supp_Name": "supplier",
    "UQC":      "uom",
    "GRADE":    "GRADE/SPEC",
}, inplace=True)

# ── Reorder columns for clean display ───────────────────────────────────────
agg_df = agg_df[["supplier", "yyyymm", "uom", "GRADE/SPEC",
                  "Sum_of_QTY", "Sum_of_TOTAL_VALUE", "Avg_PRICE"]]

# ════════════════════════════════════════════════════════════════════════════
# ── Step 8: Print result to console ─────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════
print("\n===== Aggregated Exim Data =====")
print(agg_df.to_string(index=False))

# ════════════════════════════════════════════════════════════════════════════
# ── Step 9: Save to Excel ───────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════
agg_df.to_excel("exim_aggregated.xlsx", index=False)
print("\nAggregation saved to exim_aggregated.xlsx")