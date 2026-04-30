# Streamlit App Deployment Guide

## Local Development

Run the app locally with:

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Deployment Options

### Option 1: Streamlit Cloud (Recommended — 2 minutes)

Free hosting directly on Streamlit Cloud, perfect for demos.

1. **Push code to GitHub:**
   ```bash
   git push origin claude/financial-dynamics-model-fnA1n
   ```

2. **Create a public repo** (if not already) with the code

3. **Go to** [share.streamlit.io](https://share.streamlit.io)

4. **Click "New App"** and connect your GitHub repo
   - Repository: `jmiaie/financial-dynamics-model` (or your public repo name)
   - Branch: `main` (or your branch)
   - Main file path: `app.py`

5. **Click Deploy** — done in ~2 minutes

Your app will be at: `https://<your-username>-financial-dynamics-model.streamlit.app`

---

### Option 2: Vercel + GitHub Integration

For deployment to `micapai.com` via GitHub → Vercel (if you're using that setup):

1. **Add a Vercel config** (`vercel.json`):
   ```json
   {
     "buildCommand": "pip install -r requirements.txt",
     "framework": "streamlit",
     "functions": {
       "app.py": {
         "runtime": "python3.11"
       }
     }
   }
   ```

2. **Push to GitHub:**
   ```bash
   git push origin main
   ```

3. **Connect your GitHub repo to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project" → Select your repo
   - Vercel auto-detects it's a Streamlit app
   - Click "Deploy"

4. **Add custom domain** in Vercel settings:
   - Go to Project Settings → Domains
   - Add `demo.micapai.com` or your domain
   - Follow DNS configuration instructions

---

### Option 3: Docker (Advanced)

For production on any cloud (AWS, GCP, Azure, DigitalOcean):

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t financial-dynamics-model .
docker run -p 8501:8501 financial-dynamics-model
```

---

## Environment Variables (Optional)

If deploying, you can set environment variables for customization:

- `STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false` — Hide error details in production
- `STREAMLIT_SERVER_RUN_ON_SAVE=false` — Disable auto-reload

---

## Post-Deployment Checklist

- [ ] App loads without errors
- [ ] Can fetch real yfinance data (SPY, QQQ, etc.)
- [ ] Charts render correctly
- [ ] Regime probabilities sum to 100%
- [ ] Forecast section appears after warmup
- [ ] Share link with your network!

---

## Troubleshooting

**"yfinance data not found"**
- yfinance sometimes blocks requests. Try a different ticker or period.

**"Slow first load"**
- First run fetches ~1 year of data. Subsequent loads are cached for 1 hour.

**"Charts not rendering"**
- Ensure Plotly is installed: `pip install plotly>=5.17`

**"Streamlit Cloud timeout"**
- App takes >1min on cold start. Standard for data-heavy apps. Streamlit keeps it warm after first load.

---

## Questions or Issues?

See README.md for project details, or check GitHub issues.

Good luck! 🚀
