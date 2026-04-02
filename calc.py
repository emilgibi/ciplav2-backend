import pandas as pd
import re

# ── Step 1: Load Excel ──────────────────────────────────────────────────────
df = pd.read_excel("Exim Azithromycin.xlsx")  

# ── Step 2: Define grading function ────────────────────────────────────────
def assign_grade(item_text):
    if not isinstance(item_text, str):
        return "USP"  # Default for null/empty

    text = item_text.upper()

    has_ip  = bool(re.search(r'\bIP\b', text))
    has_ep  = bool(re.search(r'\bEP\b', text))
    has_usp = bool(re.search(r'\bUSP\b', text))

    # Priority: USP > EP > IP > default USP
    if has_usp:
        return "USP"
    elif has_ep:
        return "EP"
    elif has_ip:
        return "IP"
    else:
        return "USP"

# ── Step 3: Apply the function ──────────────────────────────────────────────
df["GRADE"] = df["ITEM"].apply(assign_grade)

# ── Step 4: Save output ─────────────────────────────────────────────────────
df.to_excel("output_with_grade.xlsx", index=False)
print("Done! File saved as output_with_grade.xlsx")