# IDXExchange - Real Estate Price Prediction Dashboard

A Streamlit-based interactive application for predicting close prices of residential properties using XGBoost machine learning models trained on real estate data.

## Features

- **Interactive Price Prediction**: Use XGBoost models to predict property close prices
- **Multiple Feature Sets**: Choose between Base (original MLS fields) and Hybrid (engineered features) models
- **Example Properties**: Pre-loaded examples from actual transactions for quick testing
- **Model Performance Metrics**: View R², RMSE, MAPE, and MdAPE across different models
- **Comparative Analysis**: Compare model performance with interactive charts

## Models Included

- **XGBoost Base** - R² = 0.926, MAPE = 12.46%
- **XGBoost Hybrid** - R² = 0.924, MAPE = 12.52%
- Additional classical models: Linear Regression, Decision Tree, Random Forest, LightGBM, Gradient Boosting

## Example Properties

The app includes 5 test properties for demonstration:
1. **Atascadero** - $921,690
2. **La Jolla** - $3,700,000
3. **Northridge** - $960,000
4. **Union City** - $225,000
5. **Laguna Beach** - $2,670,000

## Installation

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/IDXExchange.git
cd IDXExchange

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app2.py
```

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Click "New app"
4. Select your repository and branch
5. Point to `app2.py` as the main file
6. Click Deploy

The app will be live at: `https://[username]-[app-name].streamlit.app`

## Project Structure

```
IDXExchange/
├── app2.py                 # Main Streamlit application
├── Models/                 # Trained model files (.joblib)
├── figs/                   # Generated figures and charts
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── .streamlit/
    └── config.toml        # Streamlit configuration
```

## Input Features

### Numeric Features
- LivingArea, BedroomsTotal, BathroomsTotalInteger
- GarageSpaces, ParkingTotal
- LotSizeSquareFeet, LotSizeAcres, LotSizeArea
- MainLevelBedrooms, YearBuilt
- Latitude, Longitude
- BuildingAreaTotal, StreetNumberNumeric

### Categorical Features
- City, CountyOrParish, StateOrProvince, PostalCode
- Levels (One, Two, Three, etc.)
- PoolPrivateYN, BasementYN, FireplaceYN, ViewYN, NewConstructionYN

## Model Performance

### XGBoost (Best Performer)
- **Training R²**: 0.926
- **Test R²**: 0.924
- **MAPE**: 12.52%
- **MdAPE**: 9.06%

The model explains 92.4% of the variance in close prices with a typical error of ~12.5%.

## Usage Tips

1. **For Best Results**: Fill in as many fields as possible for more accurate predictions
2. **Use Examples**: Load example properties to understand typical predictions
3. **Feature Importance**: The model weighs location (Latitude/Longitude) and size (LivingArea, BuildingAreaTotal) heavily
4. **Uncertainty**: All real estate predictions have inherent uncertainty; use as guidance only

## Limitations

- Model trained on properties from specific regions; may not generalize to all areas
- Missing features (e.g., property condition, renovations, market trends) can affect accuracy
- Extreme price outliers may be significantly over/underestimated
- September 2025 market data; may not reflect current conditions

## Technologies Used

- **Streamlit**: Web application framework
- **XGBoost**: Gradient boosting machine learning
- **scikit-learn**: Machine learning utilities
- **pandas**: Data manipulation
- **altair**: Interactive visualizations

## License

MIT License - See LICENSE file for details

## Contact

For questions or suggestions, please open an issue on GitHub.

---

**Note**: This application is for educational and demonstration purposes. Real estate valuations should consider professional appraisals and market expertise.
