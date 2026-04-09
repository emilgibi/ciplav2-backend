import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ═══════════════════════════════════════════════════════════════════════════════
# ── Page Config ───────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Exim Azithromycin Dashboard",
    page_icon="💊",
    layout="wide",
)

# ═══════════════════════════════════════════════════════════════════════════════
# ── Custom CSS ────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1e3a5f, #2e6da4);
        border-radius: 12px;
        padding: 20px 24px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .kpi-label {
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        color: #a8c8f0;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
    }
    .kpi-sub {
        font-size: 12px;
        color: #c0d8f0;
        margin-top: 4px;
    }
    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #1e3a5f;
        margin-top: 32px;
        margin-bottom: 8px;
        border-left: 4px solid #2e6da4;
        padding-left: 10px;
    }
    div[data-testid="stTabs"] button {
        font-size: 15px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ── Helper: yyyymm → "Mon YYYY" label ─────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
def yyyymm_to_label(yyyymm_str):
    """Convert '202501' → 'Jan 2025'"""
    try:
        return pd.to_datetime(str(yyyymm_str), format="%Y%m").strftime("%b %Y")
    except Exception:
        return str(yyyymm_str)

def add_month_label(df):
    """Add a human-readable 'month_label' column, sorted correctly."""
    df = df.copy()
    df["yyyymm"] = df["yyyymm"].astype(str)
    df["month_label"] = df["yyyymm"].apply(yyyymm_to_label)
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# ── Load Data ─────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    supp = pd.read_excel("exim_aggregated.xlsx")
    imp  = pd.read_excel("exim_aggregated_importers.xlsx")
    for df in [supp, imp]:
        df["Avg_PRICE"] = pd.to_numeric(df["Avg_PRICE"], errors="coerce")
        df["yyyymm"]    = df["yyyymm"].astype(str)
    supp = add_month_label(supp)
    imp  = add_month_label(imp)
    return supp, imp

supp_df, imp_df = load_data()

# Build sorted label→yyyymm maps for dropdowns
def build_month_options(df):
    """Returns sorted list of (yyyymm, label) tuples."""
    pairs = (
        df[["yyyymm", "month_label"]]
        .drop_duplicates()
        .sort_values("yyyymm")
    )
    return dict(zip(pairs["month_label"], pairs["yyyymm"]))  # label → yyyymm

supp_month_map = build_month_options(supp_df)   # {"Jan 2025": "202501", ...}
imp_month_map  = build_month_options(imp_df)

# ═══════════════════════════════════════════════════════════════════════════════
# ── Header ────────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 💊 Exim Azithromycin — Import Intelligence Dashboard")
st.markdown("Filtered to **Kg** UOM · Unit Value INR **₹9,000 – ₹17,000** · Outliers removed (QTY > 10% of avg)")
st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# ── KPI helper ────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
def kpi(col, label, value, sub=""):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ── Tabs ──────────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
tab_supplier, tab_importer = st.tabs(["🏭  Supplier View", "🏢  Importer View"])


# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║                         SUPPLIER TAB                                       ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab_supplier:

    with st.expander("🔽  Filters", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            all_labels_s   = list(supp_month_map.keys())   # ["Jan 2025", "Feb 2025", ...]
            sel_labels_s   = st.multiselect("Month", all_labels_s, default=all_labels_s, key="s_month")
            sel_months_s   = [supp_month_map[l] for l in sel_labels_s]   # back to yyyymm for filtering
        with col_f2:
            all_grades_s   = sorted(supp_df["GRADE/SPEC"].unique())
            sel_grades_s   = st.multiselect("Grade/Spec", all_grades_s, default=all_grades_s, key="s_grade")
        with col_f3:
            all_countries  = sorted(supp_df["country"].dropna().unique())
            sel_countries  = st.multiselect("Country", all_countries, default=all_countries, key="s_country")

    sf = supp_df[
        supp_df["yyyymm"].isin(sel_months_s) &
        supp_df["GRADE/SPEC"].isin(sel_grades_s) &
        supp_df["country"].isin(sel_countries)
    ]

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Key Metrics</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    kpi(k1, "Total Quantity",    f"{sf['Sum_of_QTY'].sum():,.0f} Kg",             "Sum of QTY")
    kpi(k2, "Total Value (INR)", f"₹{sf['Sum_of_TOTAL_VALUE'].sum()/1e7:.2f} Cr", "Sum of TOTAL_VALUE")
    kpi(k3, "Avg Unit Price",    f"₹{sf['Avg_PRICE'].mean():,.0f}",               "Avg of Avg_PRICE")
    kpi(k4, "Unique Suppliers",  f"{sf['supplier'].nunique()}",                    "Active suppliers")
    kpi(k5, "Countries",         f"{sf['country'].nunique()}",                     "Source countries")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Top Suppliers bar + Country pie ─────────────────────────────────
    st.markdown('<div class="section-title">Supplier & Country Breakdown</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns([3, 2])

    with r1c1:
        top_supp = (
            sf.groupby("supplier", as_index=False)["Sum_of_QTY"].sum()
            .sort_values("Sum_of_QTY", ascending=False).head(15)
        )
        fig_bar = px.bar(
            top_supp, x="Sum_of_QTY", y="supplier", orientation="h",
            title="Top 15 Suppliers by Volume (Kg)",
            labels={"Sum_of_QTY": "Total Qty (Kg)", "supplier": ""},
            color="Sum_of_QTY", color_continuous_scale="Blues", text_auto=".2s",
        )
        fig_bar.update_layout(showlegend=False, coloraxis_showscale=False,
                              yaxis=dict(autorange="reversed"),
                              height=420, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    with r1c2:
        country_vol = sf.groupby("country", as_index=False)["Sum_of_QTY"].sum()
        fig_pie = px.pie(
            country_vol, names="country", values="Sum_of_QTY",
            title="Volume Share by Country",
            color_discrete_sequence=px.colors.sequential.Blues_r, hole=0.4,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Row 2: Monthly trend + Avg Price by Supplier ──────────────────────────
    st.markdown('<div class="section-title">Trends & Pricing</div>', unsafe_allow_html=True)
    r2c1, r2c2 = st.columns(2)

    with r2c1:
        # Sort by yyyymm so months are chronological, then use month_label for display
        monthly_s = (
            sf.groupby(["yyyymm", "month_label"], as_index=False)
            .agg(Total_QTY=("Sum_of_QTY","sum"), Total_Value=("Sum_of_TOTAL_VALUE","sum"))
            .sort_values("yyyymm")          # sort by raw yyyymm to keep chronological order
        )
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly_s["month_label"], y=monthly_s["Total_QTY"],
            name="Total Qty (Kg)", marker_color="#2e6da4", yaxis="y1"
        ))
        fig_trend.add_trace(go.Scatter(
            x=monthly_s["month_label"], y=monthly_s["Total_Value"],
            name="Total Value (INR)", mode="lines+markers",
            line=dict(color="#f97316", width=2), yaxis="y2"
        ))
        fig_trend.update_layout(
            title="Monthly Volume & Value Trend",
            xaxis=dict(type="category", tickangle=-35),   # ← force categorical, no numeric scaling
            yaxis=dict(title="Qty (Kg)"),
            yaxis2=dict(title="Value (INR)", overlaying="y", side="right"),
            legend=dict(orientation="h", y=-0.25),
            height=400, margin=dict(l=10, r=10, t=40, b=80),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with r2c2:
        price_supp = (
            sf.groupby("supplier", as_index=False)["Avg_PRICE"].mean()
            .sort_values("Avg_PRICE", ascending=False).head(15)
        )
        fig_price = px.bar(
            price_supp, x="supplier", y="Avg_PRICE",
            title="Avg Unit Price by Supplier (₹/Kg)",
            labels={"Avg_PRICE": "Avg Price (₹)", "supplier": ""},
            color="Avg_PRICE", color_continuous_scale="RdYlGn", text_auto=".0f",
        )
        fig_price.update_layout(coloraxis_showscale=False, height=400,
                                xaxis=dict(tickangle=-35),
                                margin=dict(l=10, r=10, t=40, b=80))
        st.plotly_chart(fig_price, use_container_width=True)

    # ── Row 3: Grade/Spec split + Scatter ─────────────────────────────────────
    st.markdown('<div class="section-title">Grade Analysis & Value vs Volume</div>', unsafe_allow_html=True)
    r3c1, r3c2 = st.columns(2)

    with r3c1:
        grade_s = sf.groupby("GRADE/SPEC", as_index=False).agg(
            Total_QTY=("Sum_of_QTY","sum"), Total_Value=("Sum_of_TOTAL_VALUE","sum")
        )
        fig_grade = px.bar(
            grade_s, x="GRADE/SPEC", y=["Total_QTY", "Total_Value"], barmode="group",
            title="Volume & Value by Grade/Spec",
            labels={"value": "Amount", "GRADE/SPEC": "Grade"},
            color_discrete_map={"Total_QTY": "#2e6da4", "Total_Value": "#f97316"},
        )
        fig_grade.update_layout(height=360, legend_title="Metric",
                                margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_grade, use_container_width=True)

    with r3c2:
        scatter_s = sf.groupby("supplier", as_index=False).agg(
            Total_QTY=("Sum_of_QTY","sum"), Avg_Price=("Avg_PRICE","mean"),
            Total_Value=("Sum_of_TOTAL_VALUE","sum"), Country=("country","first"),
        )
        fig_scatter = px.scatter(
            scatter_s, x="Total_QTY", y="Avg_Price", size="Total_Value", color="Country",
            hover_name="supplier", title="Qty vs Avg Price (bubble = Total Value)",
            labels={"Total_QTY": "Total Qty (Kg)", "Avg_Price": "Avg Price (₹/Kg)"},
            size_max=60,
        )
        fig_scatter.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ── Raw Data Table ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Detailed Data</div>', unsafe_allow_html=True)
    display_sf = sf.drop(columns=["yyyymm"]).rename(columns={"month_label": "Month"})
    st.dataframe(display_sf.sort_values("Sum_of_QTY", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=320)


# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║                         IMPORTER TAB                                       ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab_importer:

    with st.expander("🔽  Filters", expanded=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            all_labels_i  = list(imp_month_map.keys())
            sel_labels_i  = st.multiselect("Month", all_labels_i, default=all_labels_i, key="i_month")
            sel_months_i  = [imp_month_map[l] for l in sel_labels_i]
        with col_f2:
            all_grades_i  = sorted(imp_df["GRADE/SPEC"].unique())
            sel_grades_i  = st.multiselect("Grade/Spec", all_grades_i, default=all_grades_i, key="i_grade")

    imf = imp_df[
        imp_df["yyyymm"].isin(sel_months_i) &
        imp_df["GRADE/SPEC"].isin(sel_grades_i)
    ]

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Key Metrics</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    kpi(k1, "Total Quantity",    f"{imf['Sum_of_QTY'].sum():,.0f} Kg",             "Sum of QTY")
    kpi(k2, "Total Value (INR)", f"₹{imf['Sum_of_TOTAL_VALUE'].sum()/1e7:.2f} Cr", "Sum of TOTAL_VALUE")
    kpi(k3, "Avg Unit Price",    f"₹{imf['Avg_PRICE'].mean():,.0f}",               "Avg of Avg_PRICE")
    kpi(k4, "Unique Importers",  f"{imf['importer'].nunique()}",                    "Active importers")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Top Importers bar + Grade pie ──────────────────────────────────
    st.markdown('<div class="section-title">Importer & Grade Breakdown</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns([3, 2])

    with r1c1:
        top_imp = (
            imf.groupby("importer", as_index=False)["Sum_of_QTY"].sum()
            .sort_values("Sum_of_QTY", ascending=False).head(15)
        )
        fig_imp_bar = px.bar(
            top_imp, x="Sum_of_QTY", y="importer", orientation="h",
            title="Top 15 Importers by Volume (Kg)",
            labels={"Sum_of_QTY": "Total Qty (Kg)", "importer": ""},
            color="Sum_of_QTY", color_continuous_scale="Teal", text_auto=".2s",
        )
        fig_imp_bar.update_layout(showlegend=False, coloraxis_showscale=False,
                                  yaxis=dict(autorange="reversed"),
                                  height=420, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_imp_bar, use_container_width=True)

    with r1c2:
        grade_imp = imf.groupby("GRADE/SPEC", as_index=False)["Sum_of_QTY"].sum()
        fig_grade_pie = px.pie(
            grade_imp, names="GRADE/SPEC", values="Sum_of_QTY",
            title="Volume Share by Grade/Spec",
            color_discrete_sequence=["#0e7490", "#06b6d4", "#67e8f9"], hole=0.4,
        )
        fig_grade_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_grade_pie.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_grade_pie, use_container_width=True)

    # ── Row 2: Monthly trend + Avg Price by Importer ──────────────────────────
    st.markdown('<div class="section-title">Trends & Pricing</div>', unsafe_allow_html=True)
    r2c1, r2c2 = st.columns(2)

    with r2c1:
        monthly_i = (
            imf.groupby(["yyyymm", "month_label"], as_index=False)
            .agg(Total_QTY=("Sum_of_QTY","sum"), Total_Value=("Sum_of_TOTAL_VALUE","sum"))
            .sort_values("yyyymm")
        )
        fig_trend_i = go.Figure()
        fig_trend_i.add_trace(go.Bar(
            x=monthly_i["month_label"], y=monthly_i["Total_QTY"],
            name="Total Qty (Kg)", marker_color="#0e7490", yaxis="y1"
        ))
        fig_trend_i.add_trace(go.Scatter(
            x=monthly_i["month_label"], y=monthly_i["Total_Value"],
            name="Total Value (INR)", mode="lines+markers",
            line=dict(color="#f97316", width=2), yaxis="y2"
        ))
        fig_trend_i.update_layout(
            title="Monthly Volume & Value Trend",
            xaxis=dict(type="category", tickangle=-35),   # ← force categorical
            yaxis=dict(title="Qty (Kg)"),
            yaxis2=dict(title="Value (INR)", overlaying="y", side="right"),
            legend=dict(orientation="h", y=-0.25),
            height=400, margin=dict(l=10, r=10, t=40, b=80),
        )
        st.plotly_chart(fig_trend_i, use_container_width=True)

    with r2c2:
        price_imp = (
            imf.groupby("importer", as_index=False)["Avg_PRICE"].mean()
            .sort_values("Avg_PRICE", ascending=False).head(15)
        )
        fig_price_i = px.bar(
            price_imp, x="importer", y="Avg_PRICE",
            title="Avg Unit Price by Importer (₹/Kg)",
            labels={"Avg_PRICE": "Avg Price (₹)", "importer": ""},
            color="Avg_PRICE", color_continuous_scale="RdYlGn", text_auto=".0f",
        )
        fig_price_i.update_layout(coloraxis_showscale=False, height=400,
                                  xaxis=dict(tickangle=-35),
                                  margin=dict(l=10, r=10, t=40, b=80))
        st.plotly_chart(fig_price_i, use_container_width=True)

    # ── Row 3: Heatmap Importer × Month ───────────────────────────────────────
    st.markdown('<div class="section-title">Importer × Month Heatmap</div>', unsafe_allow_html=True)

    top15_names = (
        imf.groupby("importer")["Sum_of_QTY"].sum()
        .nlargest(15).index.tolist()
    )
    # Build heatmap with readable month labels, sorted chronologically
    heat_src = (
        imf[imf["importer"].isin(top15_names)]
        .groupby(["importer", "yyyymm", "month_label"], as_index=False)["Sum_of_QTY"].sum()
    )
    # Pivot on yyyymm first for correct sort, then rename columns to labels
    heat_pivot = (
        heat_src.pivot(index="importer", columns="yyyymm", values="Sum_of_QTY")
        .fillna(0)
    )
    # Rename columns from yyyymm to "Mon YYYY"
    heat_pivot.columns = [yyyymm_to_label(c) for c in heat_pivot.columns]

    fig_heat = px.imshow(
        heat_pivot,
        title="Top 15 Importers — Monthly Volume Heatmap (Kg)",
        labels=dict(x="Month", y="Importer", color="Qty (Kg)"),
        color_continuous_scale="Blues", aspect="auto", text_auto=".0f",
    )
    fig_heat.update_layout(
        height=460,
        xaxis=dict(type="category", tickangle=-35),    # ← force categorical
        margin=dict(l=10, r=10, t=40, b=80)
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── Row 4: Scatter ────────────────────────────────────────���───────────────
    st.markdown('<div class="section-title">Value vs Volume</div>', unsafe_allow_html=True)
    scatter_i = imf.groupby("importer", as_index=False).agg(
        Total_QTY=("Sum_of_QTY","sum"), Avg_Price=("Avg_PRICE","mean"),
        Total_Value=("Sum_of_TOTAL_VALUE","sum"),
    )
    fig_scatter_i = px.scatter(
        scatter_i, x="Total_QTY", y="Avg_Price", size="Total_Value", color="Avg_Price",
        hover_name="importer", title="Qty vs Avg Price (bubble = Total Value)",
        labels={"Total_QTY": "Total Qty (Kg)", "Avg_Price": "Avg Price (₹/Kg)"},
        color_continuous_scale="Teal", size_max=60,
    )
    fig_scatter_i.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_scatter_i, use_container_width=True)

    # ── Raw Data Table ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Detailed Data</div>', unsafe_allow_html=True)
    display_imf = imf.drop(columns=["yyyymm"]).rename(columns={"month_label": "Month"})
    st.dataframe(display_imf.sort_values("Sum_of_QTY", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=320)