# Deployment Guide

## Quick Start (Local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Option 1: Streamlit Cloud + Custom Subdomain (Recommended)

Deploy the app on Streamlit Cloud, then point `fdm.micapai.com` to it via Porkbun DNS.

### Step 1: Push to Public Repo

```bash
# From your local machine (not cloud IDE)
cd Ominnow_private
git remote add public https://github.com/jmiaie/financial-dynamics-model.git
git push public claude/financial-dynamics-model-fnA1n:main --force
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New App**
3. Connect your GitHub account (if not already)
4. Select:
   - **Repository:** `jmiaie/financial-dynamics-model`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **Deploy**

The app will be live at: `https://financial-dynamics-model.streamlit.app`

### Step 3: Point fdm.micapai.com

In Porkbun's DNS panel for `micapai.com`:

1. Go to **Domain Management** → **micapai.com** → **DNS Records**
2. Use **URL Forwarding**:
   - **Subdomain:** `fdm`
   - **Destination:** `https://financial-dynamics-model.streamlit.app`
   - **Type:** Temporary (302)
3. Save — propagation takes 5-15 minutes

Result: `fdm.micapai.com` → live dashboard. Main site untouched.

---

## Option 2: Docker (Self-Hosted)

For production on any VPS (DigitalOcean, Hetzner, AWS, etc.):

```bash
docker build -t financial-dynamics-model .
docker run -d -p 8501:8501 --restart unless-stopped financial-dynamics-model
```

### With Nginx Reverse Proxy

If running behind Nginx at `micapai.com/fdm`:

```nginx
location /fdm/ {
    proxy_pass http://127.0.0.1:8501/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

The websocket headers are required — Streamlit uses websockets for interactivity.

### With Docker Compose

```yaml
version: "3.8"
services:
  fdm:
    build: .
    ports:
      - "8501:8501"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Environment Variables (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_CLIENT_SHOW_ERROR_DETAILS` | `true` | Set `false` in production |
| `STREAMLIT_SERVER_RUN_ON_SAVE` | `true` | Set `false` in production |
| `STREAMLIT_THEME_PRIMARY_COLOR` | `#0d7377` | Teal accent color |

---

## Post-Deployment Checklist

- [ ] App loads without errors
- [ ] Can fetch live data (SPY, QQQ, AAPL)
- [ ] Synthetic fallback works when yfinance is unavailable
- [ ] 3D phase-space renders with all toggle layers
- [ ] Regime probabilities sum to 100%
- [ ] Forecast section appears after warmup period
- [ ] Signal feed shows regime changes
- [ ] `fdm.micapai.com` resolves correctly

---

## Troubleshooting

**"yfinance data not found"** — yfinance can be flaky. The app automatically falls back to synthetic demo data.

**"Slow first load"** — First run fetches ~1 year of data + computes the full pipeline. Subsequent loads are cached for 1 hour.

**"Charts not rendering"** — Ensure `plotly>=5.17` is installed. Check browser console for JS errors.

**"Streamlit Cloud timeout"** — Cold starts take ~60s for data-heavy apps. Streamlit keeps the app warm after the first visit.

**"3D chart is slow"** — The full 3D attractor field with all layers enabled can be heavy. Disable Vol Surface and Animate for faster rendering.
