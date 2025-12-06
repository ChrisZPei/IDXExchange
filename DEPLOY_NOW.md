# Quick Deploy Script for GitHub & Streamlit Cloud

## One-Command Deployment (Copy & Paste)

### Step 1: Initialize Git Repository
```powershell
cd "c:\Users\Chris Pei\dev\IDXExchange"
git config user.email "your.email@example.com"
git config user.name "Your Name"
git init
git add .
git commit -m "IDXExchange: ML real estate price predictor - production ready"
```

### Step 2: Create GitHub Repository
1. Go to https://github.com/new
2. Name: `IDXExchange`
3. Description: `Machine Learning Real Estate Price Predictor with XGBoost and Streamlit`
4. Make it **Public**
5. Click "Create repository"
6. Copy the HTTPS URL (looks like: `https://github.com/YOUR_USERNAME/IDXExchange.git`)

### Step 3: Push to GitHub
```powershell
git remote add origin https://github.com/YOUR_USERNAME/IDXExchange.git
git branch -M main
git push -u origin main
```

### Step 4: Deploy to Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub account
3. Click "New app"
4. Select your GitHub repo: `IDXExchange`
5. Branch: `main`
6. Main file path: `app2.py`
7. Click "Deploy"
8. Wait 3-5 minutes for deployment to complete

### Step 5: Get Your Public URL
- Once deployed, Streamlit will show: `https://YOUR_USERNAME-idxexchange.streamlit.app`
- Copy this URL
- Test it by opening in browser
- Share it in your presentation!

## All-in-One PowerShell Script

Copy and paste this entire block (after updating YOUR_USERNAME):

```powershell
# 1. Set up Git
cd "c:\Users\Chris Pei\dev\IDXExchange"
git config user.email "your.email@example.com"
git config user.name "Your Name"
git init
git add .
git commit -m "IDXExchange: ML real estate price predictor"

# 2. Create remote (REPLACE YOUR_USERNAME!)
$username = "YOUR_GITHUB_USERNAME"
git remote add origin "https://github.com/$username/IDXExchange.git"
git branch -M main
git push -u origin main

# 3. Instructions for Streamlit Cloud
Write-Host "✅ GitHub push complete!"
Write-Host ""
Write-Host "📱 Next: Deploy to Streamlit Cloud"
Write-Host "1. Go to: https://streamlit.io/cloud"
Write-Host "2. Click 'New app'"
Write-Host "3. Select your GitHub repo"
Write-Host "4. Main file: app2.py"
Write-Host "5. Click Deploy"
Write-Host ""
Write-Host "Your app will be live at:"
Write-Host "https://$username-idxexchange.streamlit.app"
```

## Checklist Before Deployment

✅ **Local Testing**
- [ ] App runs without errors: `streamlit run app2.py`
- [ ] Can load example properties
- [ ] Can make predictions
- [ ] Models load correctly

✅ **File Organization**
- [ ] `app2.py` - main app file
- [ ] `requirements.txt` - dependencies
- [ ] `.gitignore` - git exclusions
- [ ] `.streamlit/config.toml` - streamlit config
- [ ] `Models/` - directory with model files
- [ ] `README.md` - documentation

✅ **Documentation**
- [ ] README.md complete
- [ ] DEPLOYMENT.md created
- [ ] PRESENTATION_GUIDE.md created

✅ **Git Ready**
- [ ] `.gitignore` excludes `.venv/` (so repo is small)
- [ ] `.gitignore` excludes `.streamlit/secrets.toml`
- [ ] All necessary files included

## Troubleshooting

**Error: "fatal: not a git repository"**
- Make sure you're in the IDXExchange directory
- Run `git init` first

**Error: "Permission denied (publickey)"**
- Set up SSH key: https://github.com/settings/keys
- Or use HTTPS URL instead

**Streamlit Cloud deployment fails**
- Check `requirements.txt` has all packages
- Verify `app2.py` is the main file
- Check logs in Streamlit Cloud dashboard

**Models not found on Streamlit Cloud**
- Ensure `Models/` folder is committed to GitHub
- Run `git status` to check all files are tracked
- Add forgotten files with `git add .`

## After Deployment

**Test Your Live App:**
1. Open the Streamlit Cloud URL in browser
2. Load an example property
3. Make a prediction
4. Verify QR code appears in sidebar

**Add to Presentation:**
1. Copy the URL: `https://your-username-idxexchange.streamlit.app`
2. Add to Google Slides
3. Optional: Take screenshot of QR code and insert

**Enable GitHub Auto-Deploy:**
- Streamlit automatically redeploys when you push to main
- Just make changes locally, commit, and push!

## Manual Re-deployment

If you need to update the app after deployment:
```powershell
# Make your changes, then:
git add .
git commit -m "Update: improved feature X"
git push origin main

# Streamlit will automatically redeploy in 1-2 minutes
```

## Monitoring Your App

**Streamlit Cloud Dashboard:**
- App activity and resource usage
- View logs
- Manage settings
- Export analytics

## Cost

All free! 🎉
- GitHub: Free tier (unlimited public repos)
- Streamlit Cloud: Free tier (up to 3 concurrent apps)

---

**That's it! Your app will be live in ~15 minutes.** 🚀

Questions? See DEPLOYMENT.md or PRESENTATION_GUIDE.md
