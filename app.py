# app.py
import os
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

MODELS_DIR = "Models"
FIGS_DIR = "figs"


# ---------------------------------------------------------
# 1. Load & unify all metric tables
# ---------------------------------------------------------
@st.cache_data
def load_all_metrics(models_dir: str = MODELS_DIR) -> pd.DataFrame:
    tables = []

    # --------- a) Classic models: Linear / Tree / RF (model_summary.csv) ---------
    summary_path = os.path.join(models_dir, "model_summary.csv")
    if os.path.exists(summary_path):
        df = pd.read_csv(summary_path)

        # "Model" looks like "RandomForest (hybrid)" → split into Model + FeatureSet
        df["FeatureSet"] = (
            df["Model"].str.extract(r"\((.*?)\)", expand=False).str.strip()
        )
        df["Model"] = df["Model"].str.replace(r"\s*\(.*\)", "", regex=True)

        df = df.rename(
            columns={
                "R2": "R2",
                "Train_R2": "Train_R2",
                "RMSE_$": "RMSE",
                "MAPE_%": "MAPE",
                "MdAPE_%": "MdAPE",
            }
        )
        # Keep only the columns we care about
        df = df[["Model", "FeatureSet", "Train_R2", "R2", "RMSE", "MAPE", "MdAPE"]]
        tables.append(df)

    # --------- b) LightGBM metrics_lgbm.csv ---------
    lgbm_path = os.path.join(models_dir, "metrics_lgbm.csv")
    if os.path.exists(lgbm_path):
        df = pd.read_csv(lgbm_path)
        df = df.rename(
            columns={
                "Test_R2": "R2",
                "RMSE_$": "RMSE",
                "MAPE_%": "MAPE",
                "MdAPE_%": "MdAPE",
            }
        )
        df = df[["Model", "FeatureSet", "Train_R2", "R2", "RMSE", "MAPE", "MdAPE"]]
        tables.append(df)

    # --------- c) GradientBoostingRegressor metrics_gbr.csv (many configs) ---------
    gbr_path = os.path.join(models_dir, "metrics_gbr.csv")
    if os.path.exists(gbr_path):
        df = pd.read_csv(gbr_path)
        # For each feature set, keep the config with best Test_R2
        df = (
            df.sort_values("Test_R2", ascending=False)
            .groupby("FeatureSet", as_index=False)
            .first()
        )
        df["Model"] = "GradientBoostingRegressor"
        df = df.rename(
            columns={
                "Test_R2": "R2",
                "RMSE_$": "RMSE",
                "MAPE_%": "MAPE",
                "MdAPE_%": "MdAPE",
            }
        )
        df = df[["Model", "FeatureSet", "Train_R2", "R2", "RMSE", "MAPE", "MdAPE"]]
        tables.append(df)

    # --------- d) XGBoost base + hybrid (Trimmed metrics only) ---------
    def _load_xgb_variant(filename: str, feature_set: str) -> pd.DataFrame | None:
        path = os.path.join(models_dir, filename)
        if not os.path.exists(path):
            return None
        xdf = pd.read_csv(path)
        # assume first row is best config
        row = xdf.iloc[0]
        return pd.DataFrame(
            {
                "Model": ["XGBoost"],
                "FeatureSet": [feature_set],
                "Train_R2": [np.nan],  # not stored
                "R2": [row["Trimmed_R2"]],
                "RMSE": [np.nan],  # RMSE not stored in csv
                "MAPE": [row["Trimmed_MAPE"]],
                "MdAPE": [row["MdAPE"]],
            }
        )

    xgb_base_df = _load_xgb_variant("metrics_xgb.csv", "base")
    xgb_hybrid_df = _load_xgb_variant("metrics_xgb_hybrid.csv", "hybrid")
    for xdf in (xgb_base_df, xgb_hybrid_df):
        if xdf is not None:
            tables.append(xdf)

    if not tables:
        return pd.DataFrame()

    all_metrics = pd.concat(tables, ignore_index=True)

    # Normalise feature set labels
    all_metrics["FeatureSet"] = all_metrics["FeatureSet"].str.lower().fillna("unknown")

    # Pretty rounding for display; keep originals in separate columns if needed
    for col in ["Train_R2", "R2", "RMSE", "MAPE", "MdAPE"]:
        if col in all_metrics.columns:
            all_metrics[col] = pd.to_numeric(all_metrics[col], errors="coerce")

    return all_metrics


# ---------------------------------------------------------
# 2. Helper to show plots from figs/ safely
# ---------------------------------------------------------
def maybe_show_image(filename: str, caption: str):
    path = os.path.join(FIGS_DIR, filename)
    if os.path.exists(path):
        st.image(path, caption=caption, use_column_width=True)
    else:
        st.info(f"Add `{os.path.join(FIGS_DIR, filename)}` to show **{caption}** here.")


# ---------------------------------------------------------
# 3. Streamlit layout
# ---------------------------------------------------------
st.set_page_config(
    page_title="IDXExchange – Model & Feature Comparison",
    layout="wide",
)

st.title("IDXExchange: Model Performance Dashboard")

st.markdown(
    """
This app compares how different models perform when we change **which features we feed into them**.

We focus on two feature sets:

- **Base features** – all original MLS fields we selected for modeling.
- **Hybrid features** – base features **minus** some redundant raw counts, plus three
  **engineered ratios** derived from domain intuition and Random Forest feature importance.
"""
)

# Sidebar: explanation of feature sets
st.sidebar.header("Feature sets")

st.sidebar.markdown(
    """
**Base numeric features** (simplified):

- LivingArea  
- BedroomsTotal  
- BathroomsTotalInteger  
- GarageSpaces, ParkingTotal  
- LotSizeSquareFeet, LotSizeAcres, LotSizeArea  
- MainLevelBedrooms  
- YearBuilt, Latitude, Longitude  
- BuildingAreaTotal, StreetNumberNumeric  

**Base categorical features**

- City, CountyOrParish, StateOrProvince, PostalCode  
- Levels (story count category)  
- PoolPrivateYN, BasementYN, FireplaceYN, ViewYN  
- NewConstructionYN  

**Hybrid feature idea**

From Random Forest feature importance, the top drivers included both **raw sizes** and
**ratios** of those sizes. To reduce redundancy:

- We **add engineered features**  
  - `AvgSqftPerBed  = LivingArea / (BedroomsTotal + ε)`  
  - `BedBathRatio   = BedroomsTotal / (BathroomsTotalInteger + ε)`  
  - `FloorAreaRatio = LivingArea / (LotSizeSquareFeet + ε)`

- We **remove redundant raw columns**  
  - `BedroomsTotal`, `BathroomsTotalInteger`, `LotSizeSquareFeet`  

- We **keep `LivingArea`** even though it appears in two ratios,
  because both domain intuition and feature importance show it as a key driver.
"""
)

feature_choice = st.sidebar.radio(
    "Select feature set to view:",
    options=["base", "hybrid"],
    format_func=lambda x: x.capitalize(),
)

metric_to_plot = st.sidebar.selectbox(
    "Metric to compare across models:",
    ["R2", "RMSE", "MAPE", "MdAPE"],
    format_func=lambda m: {
        "R2": "R² (higher is better)",
        "RMSE": "RMSE (lower is better)",
        "MAPE": "MAPE % (lower is better)",
        "MdAPE": "MdAPE % (lower is better)",
    }[m],
)

st.sidebar.markdown(
    """
**Interpretation**

- **R²** – how much of price variation we explain.  
- **RMSE** – typical absolute dollar error.  
- **MAPE / MdAPE** – typical % error (mean/median).

For XGBoost we only stored R² and % errors, so RMSE will appear as **N/A**.
"""
)

# ---------------------------------------------------------
# 4. Load metrics and build main views
# ---------------------------------------------------------
metrics_df = load_all_metrics()

if metrics_df.empty:
    st.error("No metric CSVs found in the `Models/` directory.")
    st.stop()

# Filter by chosen feature set
subset = metrics_df[metrics_df["FeatureSet"] == feature_choice].copy()
subset = subset.sort_values("R2", ascending=False)

st.subheader(f"Model performance – **{feature_choice.capitalize()}** feature set")

# Nicely formatted table
display_df = subset.copy()
display_df["R2"] = display_df["R2"].map(lambda x: f"{x:.3f}" if pd.notnull(x) else "N/A")
display_df["Train_R2"] = display_df["Train_R2"].map(
    lambda x: f"{x:.3f}" if pd.notnull(x) else "N/A"
)
display_df["RMSE"] = display_df["RMSE"].map(
    lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A"
)
display_df["MAPE"] = display_df["MAPE"].map(
    lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"
)
display_df["MdAPE"] = display_df["MdAPE"].map(
    lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"
)

st.dataframe(
    display_df.set_index("Model"),
    use_container_width=True,
)

# Highlight best model by R² within this feature set
best_row = subset.sort_values("R2", ascending=False).iloc[0]
best_model_name = best_row["Model"]
best_r2 = best_row["R2"]

st.markdown(
    f"""
**Best model for the {feature_choice} feature set**

- **Model:** `{best_model_name}`  
- **R²:** `{best_r2:.3f}`  
- **MAPE:** `{best_row['MAPE']:.2f}%`  
- **MdAPE:** `{best_row['MdAPE']:.2f}%`  
- **RMSE:** `{('N/A' if pd.isna(best_row['RMSE']) else f"${best_row['RMSE']:,.0f}")}`
"""
)

# ---------------------------------------------------------
# 5. Metric comparison bar chart (within chosen feature set)
# ---------------------------------------------------------
plot_ready = subset.dropna(subset=["R2"], how="all").copy()

if not plot_ready.empty:
    metric_label_map = {
        "R2": "R² (higher is better)",
        "RMSE": "RMSE ($, lower is better)",
        "MAPE": "MAPE % (lower is better)",
        "MdAPE": "MdAPE % (lower is better)",
    }

    st.markdown(f"### {metric_label_map[metric_to_plot]} by model")

    chart = (
        alt.Chart(plot_ready)
        .mark_bar()
        .encode(
            x=alt.X("Model:N", sort="-y"),
            y=alt.Y(f"{metric_to_plot}:Q"),
            tooltip=[
                "Model",
                "FeatureSet",
                alt.Tooltip("Train_R2", format=".3f"),
                alt.Tooltip("R2", format=".3f"),
                alt.Tooltip("RMSE", format=",.0f"),
                alt.Tooltip("MAPE", format=".2f"),
                alt.Tooltip("MdAPE", format=".2f"),
            ],
        )
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No numeric data to plot for this metric / feature set.")

# ---------------------------------------------------------
# 6. Base vs Hybrid comparison per model (R² focus)
# ---------------------------------------------------------
st.subheader("Base vs Hybrid comparison per model (R²)")

pivot_r2 = (
    metrics_df[metrics_df["FeatureSet"].isin(["base", "hybrid"])]
    .pivot_table(index="Model", columns="FeatureSet", values="R2")
    .sort_values("hybrid", ascending=False)
)

st.dataframe(pivot_r2.style.format("{:.3f}"), use_container_width=True)

st.markdown(
    """
- Rows where **hybrid R² > base R²** show models that **benefit** from the engineered features.
- Rows where **base R² ≥ hybrid R²** (for example XGBoost in your results) suggest the model can
  already extract similar information from the raw inputs, or that the extra engineered features
  add noise rather than signal.
"""
)

# ---------------------------------------------------------
# 7. Optional: show diagnostic plots if you exported them
# ---------------------------------------------------------
#st.subheader("Diagnostic plots (optional)")

#col1, col2 = st.columns(2)

#with col1:
#    maybe_show_image(
#        "actual_vs_pred_base.png",
#        "Actual vs Predicted – Base feature set (example model)",
#    )
#    maybe_show_image(
#        "error_hist_base.png",
#        "Prediction error distribution – Base feature set",
#    )

#with col2:
#    maybe_show_image(
#        "actual_vs_pred_hybrid.png",
#        "Actual vs Predicted – Hybrid feature set (example model)",
#    )
#    maybe_show_image(
#        "error_hist_hybrid.png",
#        "Prediction error distribution – Hybrid feature set",
#    )

#st.markdown(
#    """
#Use these plots to visually check **bias** (systematic under/over-pricing at certain price
#ranges) and **spread of errors**. In your slide deck, you can pair these images with:

#- A short note that trimming the top/bottom 0.5% of prices stabilised evaluation.
#- An observation that hybrid features tighten predictions for some models,
#  but XGBoost still prefers the richer base feature set.
#"""
#)
