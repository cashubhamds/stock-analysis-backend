# Indian Equity Intelligence Backend - Deployment Guide

This guide explains how to deploy this FastAPI backend to [Render.com](https://render.com).

## Prerequisites
1. A GitHub or GitLab repository with the code.
2. A free Render.com account.

## Steps to Deploy

### 1. Push Code to GitHub
Ensure your repository structure looks like this:
```
/stock_analysis_backend
  /modules
    __init__.py
    technical.py
    ...
  main.py
  requirements.txt
```

### 2. Create a New Web Service on Render
1. Log in to Render.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.

### 3. Configure the Web Service
- **Name**: `indian-equity-intelligence`
- **Region**: Select the one closest to your users (e.g., Singapore).
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt && python -m textblob.download_corpora`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 4. Advanced Settings
- **Plan Type**: Free (or Starter if you need more memory).
- **Environment Variables**: None required by default, but you can add your own if you extend the app.

### 5. Deployment
- Click **Deploy Web Service**.
- Render will install dependencies and start the server.
- Your API will be available at `https://indian-equity-intelligence.onrender.com`.

## Testing the Deployed API
Visit: `https://your-app-name.onrender.com/analyze?ticker=RELIANCE.NS`
