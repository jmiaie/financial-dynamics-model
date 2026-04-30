# Streamlit App — Quick Start

## Run Locally (60 seconds)

```bash
cd /home/user/Ominnow_private
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## What You Get

✅ **Interactive Dashboard**
- Real-time price chart with regime backgrounds
- Regime probability stacked area chart
- Transition matrix heatmap
- 5D feature time series
- Forecast panel (k-step ahead)
- Signal feed (regime changes, Risk-Off warnings, etc.)

✅ **Live Data**
- Load any ticker (SPY, QQQ, AAPL, BTC, etc.)
- Configure period (3mo, 6mo, 1y, 2y, 5y)
- Select interval (daily, hourly, 5-min)
- Auto-caches for 1 hour

✅ **Responsive Design**
- Slate + teal color scheme
- Dark theme (easy on the eyes)
- Mobile-friendly
- Instant chart updates

---

## Deploy to Streamlit Cloud (FREE, 2 minutes)

1. **Push code to GitHub:**
   ```bash
   git push origin main
   ```
   (or your current branch)

2. **Go to** [share.streamlit.io](https://share.streamlit.io)

3. **Click "New App"**
   - Repository: `jmiaie/financial-dynamics-model`
   - Branch: `main`
   - Main file path: `app.py`

4. **Click Deploy**

Your app is live! Share the URL with anyone. It's public and free.

---

## Deploy to Custom Domain (e.g., micapai.com)

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for Vercel setup.

---

## Features Breakdown

| Feature | Example |
|---------|---------|
| **Current Regime** | "Calm Trend — 87% confidence" |
| **Price Chart** | Green band (Calm), amber (Volatile), purple (Chop), red (Risk-Off) |
| **Probability Chart** | Stacked area showing real-time probabilities for all 4 regimes |
| **Transition Matrix** | 4×4 heatmap showing learned probabilities (From → To) |
| **Features Over Time** | 5 lines: volatility, trend, drawdown, stress, shock |
| **Forecast** | Bar chart showing most likely regime for next 10 bars |
| **Signals** | Real-time alerts (regime changes, confidence drops, Risk-Off warnings) |
| **Data Inspector** | View raw pipeline output for debugging |

---

## Configuration

All parameters in `config/default.yaml`:

```yaml
features:
  volatility_span: 20
  trend_window: 14
  drawdown_window: 60
  correlation_window: 20
  normalization_method: zscore

regimes:
  temperature: 1.0
  centroids: {...}

transitions:
  prior_strength: 10.0
  learning_rate: 0.05

stabilization:
  hysteresis_threshold: 0.15
  min_persistence_bars: 5
  majority_vote_window: 10

risk:
  drawdown_threshold: 0.5
  correlation_stress_threshold: 0.6
  shock_threshold: 0.7
  riskoff_confirmation_count: 3
```

Edit any parameter, reload the app, and re-run to see impact.

---

## Troubleshooting

**"yfinance: No data for ticker"**
- Try a different ticker (SPY, QQQ, AAPL are reliable)
- yfinance occasionally has timeouts; refresh the page

**"Slow first load"**
- First load fetches ~1 year of data. This takes 10-30 seconds.
- Subsequent loads use cache (1 hour TTL)
- Once deployed, Streamlit Cloud keeps the app warm

**"Charts not showing"**
- Make sure Plotly installed: `pip install plotly`
- Ensure at least 50 bars of data (warmup period ~20 bars)

**"Missing columns in pipeline output"**
- This is normal for first ~20 bars (warmup/NaN for features)
- App skips them automatically
- Data Inspector shows when output becomes valid

---

## Next Steps

1. **Test locally:** `streamlit run app.py`
2. **Deploy to Streamlit Cloud:** [share.streamlit.io](https://share.streamlit.io)
3. **Share on LinkedIn:** Use LINKEDIN_FINAL.md
4. **Send to recruiters:** Use HIGHLIGHTS_FOR_RECRUITERS.md

---

## Customization

Want to modify colors, add more indicators, or change the layout?

- **Colors:** Update `COLOR_SCHEME` dict in `app.py` (line ~28)
- **Regimes:** Add/remove to `phase1_regimes/regime_definitions.py` (requires retraining)
- **Layout:** Modify Streamlit columns/rows using `st.columns()`, `st.rows()`, etc.
- **Deployment:** See DEPLOYMENT_GUIDE.md for Vercel/Docker

---

**Questions?** Check README.md or DEPLOYMENT_GUIDE.md

🚀 **Ready to launch!**
