# Deployment Guide - IDXExchange to Streamlit Cloud

## Step-by-Step Deployment Instructions

### Prerequisites
- GitHub account (free)
- Streamlit account (free)

### Step 1: Push to GitHub

1. **Initialize Git** (if not already done):
```bash
cd "c:\Users\Chris Pei\dev\IDXExchange"
git init
git add .
git commit -m "Initial commit: IDXExchange real estate price predictor"
```

2. **Create GitHub Repository**:
   - Go to github.com and create a new repository named `IDXExchange`
   - Don't initialize with README (we have one)
   - Copy the remote URL

3. **Push code to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/IDXExchange.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. **Sign Up** at https://streamlit.io/cloud (free tier available)

2. **Create New App**:
   - Click "New app"
   - Select GitHub repo: `YOUR_USERNAME/IDXExchange`
   - Select branch: `main`
   - Main file path: `app2.py`
   - Click Deploy

3. **Wait for Deployment**:
   - Streamlit will install dependencies and launch your app
   - You'll get a URL: `https://your-username-idxexchange.streamlit.app`

### Step 3: Share in Google Slides

1. **Add Link to Slides**:
   - Create new slide with title "Live Demo"
   - Add the Streamlit app URL
   - Format: `https://your-username-idxexchange.streamlit.app`

2. **Optional: Generate QR Code**:
   - Go to https://qr-code-generator.com
   - Paste your Streamlit URL
   - Download QR code
   - Insert image in slide

3. **During Presentation**:
   - Option A: Share link with audience to explore in browser
   - Option B: Screen share and do live demo
   - Option C: Show screenshots + QR code for later access

### Troubleshooting

**App won't deploy**:
- Check `requirements.txt` has all dependencies
- Verify `app2.py` is the main file name
- Check Models/ directory is in repo

**Missing dependencies**:
- Update requirements.txt: `pip freeze > requirements.txt`
- Push to GitHub
- Streamlit will auto-redeploy

**Models not found**:
- Ensure Models/ folder is in GitHub repo
- Check path in app2.py: `MODELS_DIR = Path(__file__).parent / "Models"`

### Cost

- **Streamlit Cloud**: FREE tier available
- **GitHub**: FREE public repositories
- **Total deployment cost**: $0

### Useful Streamlit Cloud Commands

Monitor deployment:
```bash
# After first deployment, Streamlit remembers your app
streamlit run app2.py
# Then check streamlit.io/cloud for activity
```

Update your app:
```bash
git add .
git commit -m "Update: improved predictions"
git push origin main
# Streamlit automatically redeploys from main branch
```

---

**Your public URL will be live in ~5 minutes!** Share it in your presentation slides.
