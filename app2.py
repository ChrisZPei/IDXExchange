import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
from joblib import load
import pickle
import sys
import altair as alt
import qrcode
from io import BytesIO

st.set_page_config(
    page_title="IDXExchange: Model Performance Dashboard",
    layout="wide",
)

# Define placeholder class for XGBServingModel if it's missing
class XGBServingModel:
    """Placeholder class for unpickling models that reference XGBServingModel"""
    def __init__(self):
        self.pipeline = None
    
    def predict(self, X):
        """Delegate prediction to the wrapped pipeline"""
        if self.pipeline is not None:
            return self.pipeline.predict(X)
        # Fallback: if no pipeline is set, try to find it in __dict__
        for attr in self.__dict__.values():
            if hasattr(attr, 'predict'):
                return attr.predict(X)
        raise AttributeError("No pipeline with predict method found")
    
    def __getstate__(self):
        return self.__dict__
    
    def __setstate__(self, state):
        self.__dict__.update(state)

# Register the class in the current module so pickle can find it
sys.modules[__name__].XGBServingModel = XGBServingModel

MODELS_DIR = Path(__file__).parent / "Models"

XGB_BASE_PATH = MODELS_DIR / "xgb_base_pipeline.joblib"
XGB_HYBRID_PATH = MODELS_DIR / "xgb_hybrid_pipeline.joblib"

# Custom loader to extract the pipeline from XGBServingModel wrapper
def load_xgb_pipeline(path):
    """Load XGBoost pipeline - returns XGBServingModel wrapper or sklearn pipeline"""
    obj = load(path)
    # Just return the object as-is, we'll handle it in the prediction logic
    return obj

# Generate QR code from URL
def generate_qr_code(url):
    """Generate a QR code from a URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes for Streamlit
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

xgb_pipelines = {
    "base": load_xgb_pipeline(XGB_BASE_PATH),
    "hybrid": load_xgb_pipeline(XGB_HYBRID_PATH),
}

# -----------------------------
# Feature definitions for XGBoost
# -----------------------------

BASE_NUMERIC_FEATURES = [
    "LivingArea",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "GarageSpaces",
    "ParkingTotal",
    "LotSizeSquareFeet",
    "LotSizeAcres",
    "LotSizeArea",
    "MainLevelBedrooms",
    "YearBuilt",
    "Latitude",
    "Longitude",
    "BuildingAreaTotal",
    "StreetNumberNumeric",
]

BASE_CATEGORICAL_FEATURES = [
    "City",
    "CountyOrParish",
    "StateOrProvince",
    "PostalCode",
    "Levels",
    "PoolPrivateYN",
    "BasementYN",
    "FireplaceYN",
    "ViewYN",
    "NewConstructionYN",
]

# Hybrid keeps LivingArea and adds ratios, drops raw bed/bath/lot sqft
HYBRID_NUMERIC_FEATURES = [
    "LivingArea",
    "GarageSpaces",
    "ParkingTotal",
    "LotSizeAcres",
    "LotSizeArea",
    "MainLevelBedrooms",
    "YearBuilt",
    "Latitude",
    "Longitude",
    "BuildingAreaTotal",
    "StreetNumberNumeric",
    "AvgSqftPerBed",
    "BedBathRatio",
    "FloorAreaRatio",
]

HYBRID_CATEGORICAL_FEATURES = BASE_CATEGORICAL_FEATURES  # same cats

@st.cache_data
def load_all_metrics() -> pd.DataFrame:
    """Load and unify metrics from all CSVs into one tidy DataFrame."""
    # --- 1. Classical models: LinearRegression / DecisionTree / RandomForest ---
    summary_path = MODELS_DIR / "model_summary.csv"
    classical = pd.read_csv(summary_path)

    # Standardize column names
    if "RMSE_$" in classical.columns:
        pass
    elif "RMSE" in classical.columns:
        classical = classical.rename(columns={"RMSE": "RMSE_$"})
    else:
        # if there really is no RMSE column, create an empty one
        classical["RMSE_$"] = np.nan

    # Parse "Model" column like "RandomForest (hybrid)" → ModelName + FeatureSet
    classical["ModelName"] = (
        classical["Model"]
        .str.extract(r"^\s*([^(]+)")[0]
        .str.strip()
    )
    classical["FeatureSet"] = (
        classical["Model"]
        .str.extract(r"\(([^)]+)\)")[0]
        .str.strip()
    )

    classical_df = classical[
        ["ModelName", "FeatureSet", "Train_R2", "R2", "RMSE_$", "MAPE_%", "MdAPE_%"]
    ].copy()

    # --- 2. LightGBM metrics ---
    lgb_path = MODELS_DIR / "metrics_lgbm.csv"
    lgb = pd.read_csv(lgb_path)
    lgb_df = lgb[
        ["Model", "FeatureSet", "Train_R2", "Test_R2", "RMSE_$", "MAPE_%", "MdAPE_%"]
    ].copy()
    lgb_df = lgb_df.rename(columns={"Model": "ModelName", "Test_R2": "R2"})

    # --- 3. GradientBoostingRegressor metrics (pick best per feature set) ---
    gbr_path = MODELS_DIR / "metrics_gbr.csv"
    gbr_raw = pd.read_csv(gbr_path)
    best_idx = gbr_raw.groupby("FeatureSet")["Test_R2"].idxmax()
    gbr = gbr_raw.loc[
        best_idx,
        ["Model", "FeatureSet", "Train_R2", "Test_R2", "RMSE_$", "MAPE_%", "MdAPE_%"],
    ].copy()
    gbr = gbr.rename(columns={"Model": "ModelName", "Test_R2": "R2"})

    # --- 4. XGBoost metrics (base & hybrid) ---
    xgb_base_path = MODELS_DIR / "metrics_xgb.csv"
    xgb_hybrid_path = MODELS_DIR / "metrics_xgb_hybrid.csv"

    xgb_base = pd.read_csv(xgb_base_path)
    xgb_hybrid = pd.read_csv(xgb_hybrid_path)

    def xgb_to_row(df: pd.DataFrame, feature_set: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "ModelName": ["XGBoost"],
                "FeatureSet": [feature_set],
                "Train_R2": [np.nan],  # not tracked for XGB in these files
                "R2": [df.loc[0, "Trimmed_R2"]],
                "RMSE_$": [np.nan],  # not in metrics_xgb; will show as N/A
                "MAPE_%": [df.loc[0, "Trimmed_MAPE"]],
                "MdAPE_%": [df.loc[0, "MdAPE"]],
            }
        )
    

    xgb_df = pd.concat(
        [xgb_to_row(xgb_base, "base"), xgb_to_row(xgb_hybrid, "hybrid")],
        ignore_index=True,
    )

    # --- Combine everything ---
    full = pd.concat([classical_df, lgb_df, gbr, xgb_df], ignore_index=True)

    # Nice display name column
    full["Model"] = full["ModelName"]

    # Ensure consistent column order
    full = full[
        ["Model", "ModelName", "FeatureSet", "Train_R2", "R2", "RMSE_$", "MAPE_%", "MdAPE_%"]
    ]

    return full


def format_main_table(df: pd.DataFrame) -> pd.DataFrame:
    """Format metrics as strings for the top table."""
    fmt = df.copy()
    fmt["Train_R2"] = fmt["Train_R2"].map(
        lambda x: f"{x:.3f}" if pd.notnull(x) else "N/A"
    )
    fmt["R2"] = fmt["R2"].map(lambda x: f"{x:.3f}" if pd.notnull(x) else "N/A")
    fmt["RMSE_$"] = fmt["RMSE_$"].map(
        lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A"
    )
    fmt["MAPE_%"] = fmt["MAPE_%"].map(
        lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"
    )
    fmt["MdAPE_%"] = fmt["MdAPE_%"].map(
        lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A"
    )
    return fmt


def format_single_metric(value: float, metric: str) -> str:
    if pd.isna(value):
        return "N/A"
    if metric == "R2":
        return f"{value:.3f}"
    if metric == "RMSE_$":
        return f"${value:,.0f}"
    # percentage metrics
    return f"{value:.2f}%"


# ============  APP ============

summary_df = load_all_metrics()

metric_labels = {
    "R2": "R²",
    "RMSE_$": "RMSE ($)",
    "MAPE_%": "MAPE (%)",
    "MdAPE_%": "MdAPE (%)",
}

st.title("IDXExchange: Model Performance Dashboard")

# ========== Sidebar - Share/QR Code ==========
st.sidebar.markdown("## 📱 Share This App")
st.sidebar.markdown(
    """
**Live Interactive Demo** powered by Streamlit
    
Use this app to:
- Compare ML model performance
- Make real-time price predictions
- Test different feature sets
    """
)

# Add QR code for deployment URL (only when deployed)
try:
    # st.request only exists in deployed Streamlit Cloud
    if hasattr(st, 'request') and st.request and "streamlit.app" in st.request.host:
        url = f"https://{st.request.host}"
        try:
            qr_img = generate_qr_code(url)
            st.sidebar.markdown("### QR Code")
            st.sidebar.image(qr_img, use_container_width=True, caption="Scan to open app")
            st.sidebar.markdown(f"**URL:** `{url}`")
        except Exception as e:
            st.sidebar.info(f"QR code generation note: {str(e)}")
    else:
        st.sidebar.info(
            """
            **Local Development Mode**
            
            QR code appears when deployed to Streamlit Cloud.
            
            See `DEPLOYMENT.md` for instructions.
            """
        )
except AttributeError:
    st.sidebar.info(
        """
        **Local Development Mode**
        
        QR code appears when deployed to Streamlit Cloud.
        
        See `DEPLOYMENT.md` for instructions.
        """
    )

st.write(
    """
This app compares how different models perform when we change **which features we feed into them**.

We focus on two main feature sets:

**Base features** – all original MLS fields we selected for modeling:

*Base numeric features* (simplified):

- LivingArea  
- BedroomsTotal  
- BathroomsTotalInteger  
- GarageSpaces, ParkingTotal  
- LotSizeSquareFeet, LotSizeAcres, LotSizeArea  
- MainLevelBedrooms  
- YearBuilt, Latitude, Longitude  
- BuildingAreaTotal, StreetNumberNumeric  

*Base categorical features*

- City, CountyOrParish, StateOrProvince, PostalCode  
- Levels (story count category)  
- PoolPrivateYN, BasementYN, FireplaceYN, ViewYN  
- NewConstructionYN  

**Hybrid Features**

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

# --- Feature-set choice for detailed view ---
st.markdown("### Model performance by feature set")

feature_choice = st.radio(
    "Choose feature set to inspect:",
    options=["base", "hybrid"],
    horizontal=True,
)

fs_df = summary_df[summary_df["FeatureSet"] == feature_choice].copy()

if fs_df.empty:
    st.warning(f"No rows found for feature set '{feature_choice}'. Double-check your CSVs.")
else:
    display_cols = ["Model", "FeatureSet", "Train_R2", "R2", "RMSE_$", "MAPE_%", "MdAPE_%"]
    st.dataframe(
        format_main_table(fs_df[display_cols]),
        use_container_width=True,
    )

    # Best model on this feature set (by R²)
    best_idx = fs_df["R2"].idxmax()
    best = fs_df.loc[best_idx]

    st.markdown(f"#### Best model for the **{feature_choice}** feature set")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"- **Model:** `{best['Model']}`")
        st.markdown(f"- **R²:** `{best['R2']:.3f}`")
    with col_b:
        st.markdown(f"- **MAPE:** `{format_single_metric(best['MAPE_%'], 'MAPE_%')}`")
        st.markdown(f"- **MdAPE:** `{format_single_metric(best['MdAPE_%'], 'MAPE_%')}`")
    st.markdown(f"- **RMSE:** `{format_single_metric(best['RMSE_$'], 'RMSE_$')}`")
st.markdown("---")
st.write(
    """
**Interpretation**

- **R²** (Residuals Squared) – how much of price variation we explain. **Higher is better.**
- **RMSE** (Root Mean Square Error) – typical absolute dollar error.  **Lower is better.**
- **MAPE / MdAPE** (Mean/Median Absolute Percentage Error) – typical % error (mean/median). **Lower is better.**

For XGBoost we only stored R² and % errors, so RMSE will appear as **N/A**.
"""
)
st.markdown("---")

# --- Metric comparison section ---
st.markdown("### Compare models across metrics")

metric_choice = st.selectbox(
    "Metric for chart and base vs hybrid table:",
    options=list(metric_labels.keys()),
    format_func=lambda m: metric_labels[m],
)

# Bar chart for current feature set
if not fs_df.empty:
    st.markdown(
        f"#### {metric_labels[metric_choice]} by model "
        f"— **{feature_choice}** feature set"
    )
    chart_df = fs_df[["Model", metric_choice]].set_index("Model").reset_index()
    
    # Create Altair chart with horizontal x-axis labels
    chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("Model:N", title="Model", axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{metric_choice}:Q", title=metric_labels[metric_choice]),
        tooltip=["Model:N", f"{metric_choice}:Q"]
    ).properties(
        width=600,
        height=400
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

# --- Base vs Hybrid comparison table for chosen metric ---
st.markdown(
    f"### Base vs Hybrid comparison per model ({metric_labels[metric_choice]})"
)

# Keep only base & hybrid rows
bh_df = summary_df[summary_df["FeatureSet"].isin(["base", "hybrid"])]

if bh_df.empty:
    st.warning("No base / hybrid rows found in metrics.")
else:
    wide = (
        bh_df.pivot_table(
            index="Model",
            columns="FeatureSet",
            values=metric_choice,
            aggfunc="mean",
        )
        .reindex(columns=["base", "hybrid"])
    )

    # Sort: higher is better for R², lower is better for error metrics
    ascending = metric_choice in ["RMSE_$", "MAPE_%", "MdAPE_%"]
    sort_col = "hybrid" if "hybrid" in wide.columns else "base"
    wide = wide.sort_values(sort_col, ascending=ascending)

    # Format for display
    disp = wide.copy()
    for col in disp.columns:
        disp[col] = disp[col].map(lambda v: format_single_metric(v, metric_choice))

    st.dataframe(
        disp.reset_index().rename(columns={"base": "base", "hybrid": "hybrid"}),
        use_container_width=True,
    )

    st.markdown(
        f"""
- Rows where **hybrid {metric_labels[metric_choice]}** is better than base show models
  that **benefit from the engineered ratios**.
- Rows where **base and hybrid are very similar**
  suggest the model can already capture similar information from the raw base features,
  or that the extra engineered features add more noise than signal for that model.
"""
    )

st.markdown("---")

st.markdown("#### Since XGBoost has the best metrics overall, we will use that model for the app.")

st.markdown("---")

# =====================================
# XGBoost price prediction (inference)
# =====================================

st.header("Interactive Close Price Prediction (XGBoost)")

st.write(
    """
Use the best-performing XGBoost model to predict **ClosePrice** for a single listing.

You can choose whether to use the **Base** feature set (original MLS fields) or the
**Hybrid** feature set (with engineered ratios replacing some raw size fields).
"""
)

feature_set_for_pred = st.radio(
    "Feature set for prediction:",
    options=["base", "hybrid"],
    horizontal=True,
)

# Helper: build input UI for numeric + categorical features
def collect_base_inputs():
    st.subheader("Base feature set inputs")
    
    # Load example data if requested
    example_key = st.session_state.get("load_example")
    example = EXAMPLE_DATA.get(example_key, {}) if example_key else {}

    col1, col2 = st.columns(2)

    with col1:
        living_area = st.number_input("LivingArea (sqft)", min_value=0.0, value=float(example.get("LivingArea", 2000.0)), step=10.0)
        bedrooms = st.number_input("BedroomsTotal", min_value=0, value=int(example.get("BedroomsTotal", 3)), step=1)
        bathrooms = st.number_input("BathroomsTotalInteger", min_value=0, value=int(example.get("BathroomsTotalInteger", 2)), step=1)
        garage = st.number_input("GarageSpaces", min_value=0.0, value=float(example.get("GarageSpaces", 2.0)), step=1.0)
        parking = st.number_input("ParkingTotal", min_value=0.0, value=float(example.get("ParkingTotal", 2.0)), step=1.0)
        lot_sqft = st.number_input("LotSizeSquareFeet", min_value=0.0, value=float(example.get("LotSizeSquareFeet", 5000.0)), step=50.0)
        lot_acres = st.number_input("LotSizeAcres", min_value=0.0, value=float(example.get("LotSizeAcres", 0.11)), step=0.01)

    with col2:
        lot_area = st.number_input("LotSizeArea (MLS units)", min_value=0.0, value=float(example.get("LotSizeArea", 0.0)), step=0.1)
        main_beds = st.number_input("MainLevelBedrooms", min_value=0, value=int(example.get("MainLevelBedrooms", 1)), step=1)
        # Ensure YearBuilt is within valid range
        year_built_val = int(example.get("YearBuilt", 1995))
        year_built_val = max(1800, min(2100, year_built_val))
        year_built = st.number_input("YearBuilt", min_value=1800, max_value=2100, value=year_built_val, step=1)
        latitude = st.number_input("Latitude", value=float(example.get("Latitude", 34.05)), step=0.0001, format="%.6f")
        longitude = st.number_input("Longitude", value=float(example.get("Longitude", -118.25)), step=0.0001, format="%.6f")
        building_area = st.number_input("BuildingAreaTotal (sqft)", min_value=0.0, value=float(example.get("BuildingAreaTotal", 2000.0)), step=10.0)
        street_num = st.number_input("StreetNumberNumeric", min_value=0.0, value=float(example.get("StreetNumberNumeric", 100.0)), step=1.0)

    st.subheader("Location / categorical fields")

    city = st.text_input("City", value=example.get("City", "Los Angeles"))
    county = st.text_input("CountyOrParish", value=example.get("CountyOrParish", "Los Angeles"))
    state = st.text_input("StateOrProvince", value=example.get("StateOrProvince", "CA"))
    postal = st.text_input("PostalCode", value=example.get("PostalCode", "90001"))

    levels = st.text_input("Levels (e.g. One, Two, Three)", value=example.get("Levels", "One"))
    pool = st.selectbox("PoolPrivateYN", options=["Yes", "No"], index=["Yes", "No"].index(example.get("PoolPrivateYN", "No")))
    basement = st.selectbox("BasementYN", options=["No", "Yes"], index=["No", "Yes"].index(example.get("BasementYN", "No")))
    fireplace = st.selectbox("FireplaceYN", options=["Yes", "No"], index=["Yes", "No"].index(example.get("FireplaceYN", "Yes")))
    view = st.selectbox("ViewYN", options=["No", "Yes"], index=["No", "Yes"].index(example.get("ViewYN", "No")))
    new_const = st.selectbox("NewConstructionYN", options=["No", "Yes"], index=["No", "Yes"].index(example.get("NewConstructionYN", "No")))

    # Build row as dict matching BASE_* feature lists
    row = {
        "LivingArea": living_area,
        "BedroomsTotal": bedrooms,
        "BathroomsTotalInteger": bathrooms,
        "GarageSpaces": garage,
        "ParkingTotal": parking,
        "LotSizeSquareFeet": lot_sqft,
        "LotSizeAcres": lot_acres,
        "LotSizeArea": lot_area,
        "MainLevelBedrooms": main_beds,
        "YearBuilt": year_built,
        "Latitude": latitude,
        "Longitude": longitude,
        "BuildingAreaTotal": building_area,
        "StreetNumberNumeric": street_num,
        "City": city,
        "CountyOrParish": county,
        "StateOrProvince": state,
        "PostalCode": postal,
        "Levels": levels,
        "PoolPrivateYN": pool,
        "BasementYN": basement,
        "FireplaceYN": fireplace,
        "ViewYN": view,
        "NewConstructionYN": new_const,
    }

    return row


def collect_hybrid_inputs():
    st.subheader("Hybrid feature set inputs")

    st.write(
        """
Hybrid keeps **LivingArea** and engineered ratios instead of raw bed/bath/lot sqft in the model.

Raw values are collected here to compute the engineered ratios.
"""
    )

    col1, col2 = st.columns(2)

    with col1:
        living_area = st.number_input("LivingArea (sqft)", min_value=0.0, value=2000.0, step=10.0)
        bedrooms = st.number_input("BedroomsTotal (for ratios only)", min_value=0, value=3, step=1)
        bathrooms = st.number_input("BathroomsTotalInteger (for ratios only)", min_value=0, value=2, step=1)
        lot_sqft = st.number_input("LotSizeSquareFeet (for ratios only)", min_value=0.0, value=5000.0, step=50.0)
        garage = st.number_input("GarageSpaces", min_value=0.0, value=2.0, step=1.0)
        parking = st.number_input("ParkingTotal", min_value=0.0, value=2.0, step=1.0)

    with col2:
        lot_acres = st.number_input("LotSizeAcres", min_value=0.0, value=0.11, step=0.01)
        lot_area = st.number_input("LotSizeArea (MLS units)", min_value=0.0, value=0.0, step=0.1)
        main_beds = st.number_input("MainLevelBedrooms", min_value=0, value=1, step=1)
        year_built = st.number_input("YearBuilt", min_value=1800, max_value=2100, value=1995, step=1)
        latitude = st.number_input("Latitude", value=34.05, step=0.0001, format="%.6f")
        longitude = st.number_input("Longitude", value=-118.25, step=0.0001, format="%.6f")
        building_area = st.number_input("BuildingAreaTotal (sqft)", min_value=0.0, value=2000.0, step=10.0)
        street_num = st.number_input("StreetNumberNumeric", min_value=0.0, value=100.0, step=1.0)

    st.subheader("Location / categorical fields")

    city = st.text_input("City", value="Los Angeles")
    county = st.text_input("CountyOrParish", value="Los Angeles")
    state = st.text_input("StateOrProvince", value="CA")
    postal = st.text_input("PostalCode", value="90001")

    levels = st.text_input("Levels (e.g. One, Two, Three)", value="One")
    pool = st.selectbox("PoolPrivateYN", options=["Yes", "No"])
    basement = st.selectbox("BasementYN", options=["No", "Yes"])
    fireplace = st.selectbox("FireplaceYN", options=["Yes", "No"])
    view = st.selectbox("ViewYN", options=["No", "Yes"])
    new_const = st.selectbox("NewConstructionYN", options=["No", "Yes"])

    # Compute engineered features
    eps = 1e-6
    avg_sqft_per_bed = living_area / (bedrooms + eps) if bedrooms > 0 else 0.0
    bed_bath_ratio = bedrooms / (bathrooms + eps) if bathrooms > 0 else 0.0
    floor_area_ratio = living_area / (lot_sqft + eps) if lot_sqft > 0 else 0.0

    # Build row dict for HYBRID_* feature lists
    row = {
        "LivingArea": living_area,
        "GarageSpaces": garage,
        "ParkingTotal": parking,
        "LotSizeAcres": lot_acres,
        "LotSizeArea": lot_area,
        "MainLevelBedrooms": main_beds,
        "YearBuilt": year_built,
        "Latitude": latitude,
        "Longitude": longitude,
        "BuildingAreaTotal": building_area,
        "StreetNumberNumeric": street_num,
        "AvgSqftPerBed": avg_sqft_per_bed,
        "BedBathRatio": bed_bath_ratio,
        "FloorAreaRatio": floor_area_ratio,
        "City": city,
        "CountyOrParish": county,
        "StateOrProvince": state,
        "PostalCode": postal,
        "Levels": levels,
        "PoolPrivateYN": pool,
        "BasementYN": basement,
        "FireplaceYN": fireplace,
        "ViewYN": view,
        "NewConstructionYN": new_const,
    }

    # For transparency, show the engineered values
    with st.expander("Show engineered hybrid features"):
        st.write(
            {
                "AvgSqftPerBed": avg_sqft_per_bed,
                "BedBathRatio": bed_bath_ratio,
                "FloorAreaRatio": floor_area_ratio,
            }
        )

    return row


# Example data for quick testing
EXAMPLE_DATA = {
    "base": {
        "LivingArea": 2630,
        "BedroomsTotal": 4,
        "BathroomsTotalInteger": 2,
        "GarageSpaces": 3.0,
        "ParkingTotal": 3.0,
        "LotSizeSquareFeet": 11398.0,
        "LotSizeAcres": 0.2617,
        "LotSizeArea": 11398.0,
        "MainLevelBedrooms": 4,
        "YearBuilt": 2010,
        "Latitude": 35.509722,
        "Longitude": -120.699487,
        "BuildingAreaTotal": 2630.0,
        "StreetNumberNumeric": 2215.0,
        "City": "Atascadero",
        "CountyOrParish": "San Luis Obispo",
        "StateOrProvince": "CA",
        "PostalCode": "93422",
        "Levels": "One",
        "PoolPrivateYN": "No",
        "BasementYN": "No",
        "FireplaceYN": "Yes",
        "ViewYN": "Yes",
        "NewConstructionYN": "No",
    },
    "san_diego": {
        "LivingArea": 3072,
        "BedroomsTotal": 3,
        "BathroomsTotalInteger": 3,
        "GarageSpaces": 3.0,
        "ParkingTotal": 3.0,
        "LotSizeSquareFeet": 0.0,
        "LotSizeAcres": 0.0,
        "LotSizeArea": 0.0,
        "MainLevelBedrooms": 2,
        "YearBuilt": 1969,
        "Latitude": 32.8534778,
        "Longitude": -117.2467414,
        "BuildingAreaTotal": 3072.0,
        "StreetNumberNumeric": 8129.0,
        "City": "La Jolla",
        "CountyOrParish": "San Diego",
        "StateOrProvince": "CA",
        "PostalCode": "92037",
        "Levels": "Two",
        "PoolPrivateYN": "Yes",
        "BasementYN": "No",
        "FireplaceYN": "No",
        "ViewYN": "Yes",
        "NewConstructionYN": "No",
    },
    "northridge": {
        "LivingArea": 1956,
        "BedroomsTotal": 3,
        "BathroomsTotalInteger": 2,
        "GarageSpaces": 2.0,
        "ParkingTotal": 2.0,
        "LotSizeSquareFeet": 15344.0,
        "LotSizeAcres": 0.3522,
        "LotSizeArea": 15344.0,
        "MainLevelBedrooms": 1,
        "YearBuilt": 1959,
        "Latitude": 34.253778,
        "Longitude": -118.544561,
        "BuildingAreaTotal": 1956.0,
        "StreetNumberNumeric": 10101.0,
        "City": "Northridge",
        "CountyOrParish": "Los Angeles",
        "StateOrProvince": "CA",
        "PostalCode": "91324",
        "Levels": "One",
        "PoolPrivateYN": "No",
        "BasementYN": "No",
        "FireplaceYN": "Yes",
        "ViewYN": "No",
        "NewConstructionYN": "No",
    },
    "union_city": {
        "LivingArea": 0.0,
        "BedroomsTotal": 2,
        "BathroomsTotalInteger": 2,
        "GarageSpaces": 1.0,
        "ParkingTotal": 1.0,
        "LotSizeSquareFeet": 1440.0,
        "LotSizeAcres": 0.0331,
        "LotSizeArea": 1440.0,
        "MainLevelBedrooms": 0,
        "YearBuilt": 1980,
        "Latitude": 37.587201,
        "Longitude": -122.048103,
        "BuildingAreaTotal": 0.0,
        "StreetNumberNumeric": 51.0,
        "City": "Union City",
        "CountyOrParish": "Alameda",
        "StateOrProvince": "CA",
        "PostalCode": "94587",
        "Levels": "One",
        "PoolPrivateYN": "No",
        "BasementYN": "No",
        "FireplaceYN": "No",
        "ViewYN": "No",
        "NewConstructionYN": "No",
    },
    "laguna_beach": {
        "LivingArea": 1811,
        "BedroomsTotal": 2,
        "BathroomsTotalInteger": 3,
        "GarageSpaces": 2.0,
        "ParkingTotal": 2.0,
        "LotSizeSquareFeet": 9720.0,
        "LotSizeAcres": 0.2231,
        "LotSizeArea": 9720.0,
        "MainLevelBedrooms": 1,
        "YearBuilt": 1964,
        "Latitude": 33.546477,
        "Longitude": -117.776673,
        "BuildingAreaTotal": 1811.0,
        "StreetNumberNumeric": 1223.0,
        "City": "Laguna Beach",
        "CountyOrParish": "Orange",
        "StateOrProvince": "CA",
        "PostalCode": "92651",
        "Levels": "One",
        "PoolPrivateYN": "No",
        "BasementYN": "No",
        "FireplaceYN": "Yes",
        "ViewYN": "Yes",
        "NewConstructionYN": "No",
    }
}

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### Enter property details to predict close price")
with col2:
    example_choice = st.selectbox(
        "Load example:",
        options=[
            "None",
            "Atascadero ($921k)",
            "La Jolla ($3.7M)",
            "Northridge ($960k)",
            "Union City ($225k)",
            "Laguna Beach ($2.67M)"
        ],
    )
    if example_choice == "Atascadero ($921k)":
        st.session_state.load_example = "base"
    elif example_choice == "La Jolla ($3.7M)":
        st.session_state.load_example = "san_diego"
    elif example_choice == "Northridge ($960k)":
        st.session_state.load_example = "northridge"
    elif example_choice == "Union City ($225k)":
        st.session_state.load_example = "union_city"
    elif example_choice == "Laguna Beach ($2.67M)":
        st.session_state.load_example = "laguna_beach"
    else:
        st.session_state.load_example = None

with st.form(key="xgb_prediction_form"):
    if feature_set_for_pred == "base":
        input_row = collect_base_inputs()
        expected_cols = BASE_NUMERIC_FEATURES + BASE_CATEGORICAL_FEATURES
        model_key = "base"
    else:
        input_row = collect_hybrid_inputs()
        expected_cols = HYBRID_NUMERIC_FEATURES + HYBRID_CATEGORICAL_FEATURES
        model_key = "hybrid"

    submitted = st.form_submit_button("Predict Close Price with XGBoost")

    if submitted:
        # Make sure DataFrame has columns in the order used during training
        input_df = pd.DataFrame([[input_row[col] for col in expected_cols]], columns=expected_cols)

        pipe = xgb_pipelines[model_key]
        
        try:
            import xgboost as xgb
            
            # Check if it's an XGBServingModel with booster and preprocess attributes
            # Use __dict__ directly since hasattr might not work reliably with unpickled objects
            if 'booster' in pipe.__dict__ and 'preprocess' in pipe.__dict__:
                # Apply preprocessing - this should output a numpy array
                transformed = pipe.__dict__['preprocess'].transform(input_df)
                
                # If it's a sparse matrix, convert to dense
                if hasattr(transformed, 'toarray'):
                    transformed = transformed.toarray()
                
                # Create DMatrix from the fully preprocessed numeric data
                dmatrix = xgb.DMatrix(transformed)
                pred_price = pipe.__dict__['booster'].predict(dmatrix)[0]
            
            # Check if it's a sklearn pipeline
            elif hasattr(pipe, 'named_steps'):
                # Apply all steps except the final one
                transformed_df = input_df.copy()
                for name, step in list(pipe.named_steps.items())[:-1]:
                    if hasattr(step, 'transform'):
                        transformed_df = step.transform(transformed_df)
                
                # Convert sparse matrices to dense
                if hasattr(transformed_df, 'toarray'):
                    transformed_df = transformed_df.toarray()
                
                # Get the final model and predict
                final_model = list(pipe.named_steps.values())[-1]
                dmatrix = xgb.DMatrix(transformed_df)
                pred_price = final_model.predict(dmatrix)[0]
            
            else:
                # Fallback: just try to predict directly
                # This shouldn't happen for XGBServingModel
                st.warning("Using fallback prediction method")
                pred_price = pipe.predict(input_df)[0]
                    
        except Exception as e:
            st.error(f"Prediction error: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            st.stop()

        st.success(f"Predicted Close Price: **${pred_price:,.0f}**")
        st.caption(
            f"Model: XGBoost ({model_key} feature set). "
            f"Prediction uses the same preprocessing and training pipeline as in the metrics above."
        )
