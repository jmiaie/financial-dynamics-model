"""Streamlit app for Financial Dynamics Model demo.

Interactive dashboard for market regime classification with live yfinance data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import warnings

from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.config import PipelineConfig
from financial_dynamics.data_loader import fetch_ohlcv
from financial_dynamics.types import Regime, REGIME_NAMES
from financial_dynamics.signals.detector import SignalDetector, SignalType
from financial_dynamics.visualization.phase_space import REGIME_COLORS

# Color scheme: slate and teal
COLOR_SCHEME = {
    "primary": "#1e3a5f",      # Dark slate blue
    "secondary": "#0d7377",     # Teal
    "accent": "#14919b",        # Light teal
    "calm": "#10b981",          # Green (Calm Trend)
    "volatile": "#f59e0b",      # Amber (Volatile Trend)
    "chop": "#8b5cf6",          # Purple (Chop)
    "riskoff": "#ef4444",       # Red (Risk-Off)
    "background": "#0f172a",    # Very dark slate
    "surface": "#1e293b",       # Dark slate
    "text": "#f1f5f9",          # Light slate
}

REGIME_COLORS_PLOTLY = {
    Regime.CALM_TREND: COLOR_SCHEME["calm"],
    Regime.VOLATILE_TREND: COLOR_SCHEME["volatile"],
    Regime.CHOP: COLOR_SCHEME["chop"],
    Regime.RISK_OFF: COLOR_SCHEME["riskoff"],
}


def setup_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Financial Dynamics Model",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e3a5f 100%);
    }
    .main-title {
        color: #f1f5f9;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 0.2em;
    }
    .subtitle {
        color: #cbd5e1;
        text-align: center;
        font-size: 1.1em;
        margin-bottom: 2em;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d7377 100%);
        padding: 1.5em;
        border-radius: 8px;
        border-left: 4px solid #14919b;
        color: #f1f5f9;
    }
    .metric-label {
        font-size: 0.85em;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #f1f5f9;
        margin-top: 0.5em;
    }
    </style>
    """, unsafe_allow_html=True)


def _generate_synthetic_fallback() -> pd.DataFrame:
    """Generate synthetic OHLCV data for use when live data is unavailable."""
    rng = np.random.default_rng(42)
    price = 100.0
    rows = []
    for i in range(240):
        phase = (i // 60) % 4
        if phase == 0:
            ret = 0.0015 + rng.normal(0, 0.007)
        elif phase == 1:
            ret = 0.003 + rng.normal(0, 0.020)
        elif phase == 2:
            ret = rng.normal(0, 0.008)
        else:
            ret = -0.004 + rng.normal(0, 0.018)
            if rng.random() < 0.25:
                ret += rng.choice([-0.06, -0.05, 0.035])
        close = price * (1 + ret)
        high = max(price, close) * (1 + abs(rng.normal(0, 0.002)))
        low = min(price, close) * (1 - abs(rng.normal(0, 0.002)))
        rows.append([price, high, low, close, int(rng.integers(2000, 20000))])
        price = close
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="h")
    df.index.name = "timestamp"
    return df


@st.cache_data(ttl=3600)
def load_data(symbol: str, period: str, interval: str):
    """Load OHLCV data from yfinance with caching."""
    try:
        df = fetch_ohlcv(symbol, period=period, interval=interval)
        return df, None
    except Exception as e:
        return None, str(e)


@st.cache_resource
def get_pipeline():
    """Get or create pipeline instance."""
    config = PipelineConfig.from_yaml("config/default.yaml")
    return FinancialDynamicsPipeline(config)


def render_regime_badge(regime: Regime, confidence: float):
    """Render a colored badge for a regime."""
    color = REGIME_COLORS_PLOTLY.get(regime, COLOR_SCHEME["secondary"])
    name = REGIME_NAMES.get(regime, "Unknown")
    html = f"""
    <div style="
        background: {color};
        color: white;
        padding: 0.75em 1.5em;
        border-radius: 8px;
        display: inline-block;
        margin: 0.5em;
        font-weight: bold;
    ">
        {name} — {confidence:.1%} confidence
    </div>
    """
    return html


def plot_price_with_regimes(df: pd.DataFrame, results: pd.DataFrame):
    """Interactive price chart with regime background bands."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["close"],
        mode="lines",
        name="Close Price",
        line=dict(color=COLOR_SCHEME["text"], width=2),
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Price: $%{y:.2f}<extra></extra>",
    ))

    # Add regime background bands
    regime_col = results["risk_adjusted_regime"]
    valid = regime_col.dropna()

    if len(valid) > 0:
        y_min, y_max = df["close"].min() * 0.95, df["close"].max() * 1.05
        for i in range(len(valid) - 1):
            try:
                regime = Regime[valid.iloc[i]]
                color = REGIME_COLORS_PLOTLY[regime]
                fig.add_vrect(
                    x0=valid.index[i],
                    x1=valid.index[i + 1],
                    fillcolor=color,
                    opacity=0.15,
                    layer="below",
                    line_width=0,
                )
            except KeyError:
                warnings.warn(
                    f"Unknown regime '{valid.iloc[i]}' at index {valid.index[i]}",
                    stacklevel=2,
                )

    fig.update_layout(
        title="Market Price with Regime Classification",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=400,
    )

    return fig


def plot_regime_probabilities(results: pd.DataFrame):
    """Stacked area chart of regime probabilities."""
    prob_cols = [f"post_prob_{r.name}" for r in Regime]
    valid = results.dropna(subset=prob_cols)

    if len(valid) < 2:
        return None

    fig = go.Figure()
    for regime in Regime:
        col = f"post_prob_{regime.name}"
        fig.add_trace(go.Scatter(
            x=valid.index,
            y=valid[col],
            mode="lines",
            name=REGIME_NAMES[regime],
            stackgroup="one",
            fillcolor=REGIME_COLORS_PLOTLY[regime],
            line=dict(width=0.5, color=REGIME_COLORS_PLOTLY[regime]),
            hovertemplate=f"{REGIME_NAMES[regime]}: %{{y:.1%}}<extra></extra>",
        ))

    fig.update_layout(
        title="Regime Probability Distribution (Posterior)",
        xaxis_title="Date",
        yaxis_title="Probability",
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=350,
        yaxis=dict(range=[0, 1]),
    )

    return fig


def plot_transition_matrix(tm: np.ndarray):
    """Heatmap of transition probabilities."""
    labels = [REGIME_NAMES[r] for r in Regime]

    fig = go.Figure(data=go.Heatmap(
        z=tm,
        x=labels,
        y=labels,
        colorscale="Greys",
        zmin=0,
        zmax=1,
        text=np.round(tm, 2),
        texttemplate="%{text:.2f}",
        textfont={"size": 12},
        colorbar=dict(title="Probability"),
        hovertemplate="From %{y} → To %{x}: %{z:.2%}<extra></extra>",
    ))

    fig.update_layout(
        title="Transition Probability Matrix",
        xaxis_title="To State",
        yaxis_title="From State",
        template="plotly_dark",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=350,
    )

    return fig


def plot_features(results: pd.DataFrame):
    """Time series of the 5 engineered features."""
    feat_cols = [
        "feat_volatility",
        "feat_trend",
        "feat_drawdown",
        "feat_corr_stress",
        "feat_shock",
    ]
    feat_names = [
        "Volatility",
        "Trend Strength",
        "Drawdown Pressure",
        "Correlation Stress",
        "Shock Intensity",
    ]

    valid = results.dropna(subset=feat_cols)
    if len(valid) < 2:
        return None

    fig = go.Figure()
    colors = [COLOR_SCHEME["calm"], COLOR_SCHEME["volatile"], COLOR_SCHEME["chop"],
              COLOR_SCHEME["riskoff"], COLOR_SCHEME["accent"]]

    for col, name, color in zip(feat_cols, feat_names, colors):
        fig.add_trace(go.Scatter(
            x=valid.index,
            y=valid[col],
            mode="lines",
            name=name,
            line=dict(color=color, width=2),
            hovertemplate=f"{name}: %{{y:.3f}}<extra></extra>",
        ))

    fig.update_layout(
        title="Engineered Features Over Time",
        xaxis_title="Date",
        yaxis_title="Normalized Value",
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=350,
    )

    return fig


def main():
    """Main Streamlit app."""
    setup_page()

    # Header
    st.markdown('<h1 class="main-title">📊 Financial Dynamics Model</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Transparent, Bayesian market regime classification for quantitative trading</p>',
        unsafe_allow_html=True
    )
    st.divider()

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        symbol = st.text_input(
            "Stock/Ticker Symbol",
            value="SPY",
            help="e.g., SPY, QQQ, AAPL, etc."
        ).upper()

        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox(
                "Data Period",
                options=["3mo", "6mo", "1y", "2y", "5y"],
                index=2,
            )
        with col2:
            interval = st.selectbox(
                "Bar Interval",
                options=["1d", "1h", "5m"],
                index=0,
            )

        st.divider()
        st.markdown("**Pipeline Config**")

        if st.button("🔄 Load Data & Run Pipeline", use_container_width=True):
            st.session_state.run_pipeline = True

        st.divider()
        st.markdown("**About**")
        st.info(
            "This model classifies market regimes using a 5-phase Bayesian system:\n\n"
            "1. **Feature Engineering** — 5D normalized features\n"
            "2. **Centroid Classification** — Softmax probability mapping\n"
            "3. **Markov Transitions** — Learned transition matrix\n"
            "4. **Temporal Stabilization** — Noise filtering\n"
            "5. **Risk Overlays** — Risk-Off confirmation & rebalancing\n\n"
            "**Authors:** Jeff Milam & Micap AI LLC"
        )

    # Main content
    if "run_pipeline" not in st.session_state:
        st.session_state.run_pipeline = True

    if st.session_state.run_pipeline:
        with st.spinner(f"Loading {symbol} data and running pipeline..."):
            df, error = load_data(symbol, period, interval)

            if error:
                st.warning(
                    f"⚠️ Live data unavailable for **{symbol}** (Yahoo Finance rate limit on shared cloud IPs). "
                    "Showing synthetic demo data instead.",
                    icon="📊",
                )
                df = _generate_synthetic_fallback()

            pipeline = get_pipeline()
            results = pipeline.run(df)

        # Metrics row
        st.divider()
        col1, col2, col3, col4 = st.columns(4)

        current_regime = results["risk_adjusted_regime"].iloc[-1] if len(results) > 0 else None
        confidence = 0.0

        if current_regime:
            current_regime = Regime[current_regime]
            prob_cols = [f"post_prob_{r.name}" for r in Regime]
            if all(col in results.columns for col in prob_cols):
                probs = results[prob_cols].iloc[-1].values
                confidence = probs[int(current_regime)]

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Current Regime</div>
                <div class="metric-value">{REGIME_NAMES.get(current_regime, 'Unknown')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Confidence</div>
                <div class="metric-value">{confidence:.1%}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            bars_processed = len(results)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Bars Processed</div>
                <div class="metric-value">{bars_processed:,}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            warmup = pipeline.warmup_bars
            is_ready = "✓ Ready" if bars_processed >= warmup else f"Warming up..."
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Status</div>
                <div class="metric-value">{is_ready}</div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Charts
        st.subheader("📈 Price & Regime Analysis")
        fig_price = plot_price_with_regimes(df, results)
        st.plotly_chart(fig_price, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Regime Probabilities")
            fig_probs = plot_regime_probabilities(results)
            if fig_probs:
                st.plotly_chart(fig_probs, use_container_width=True)

        with col2:
            st.subheader("🔄 Transition Matrix")
            tm = pipeline._transition_engine.get_transition_matrix()
            fig_tm = plot_transition_matrix(tm)
            st.plotly_chart(fig_tm, use_container_width=True)

        st.subheader("🎯 Engineered Features")
        fig_features = plot_features(results)
        if fig_features:
            st.plotly_chart(fig_features, use_container_width=True)

        # Forecast section
        st.divider()
        st.subheader("🔮 Regime Forecast")

        forecast = pipeline.forecast(horizon=10)
        if forecast:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("**Expected Duration:**")
                st.metric("Bars", f"{forecast.expected_duration:.1f}")
                st.markdown("**Most Likely Path:**")
                path_str = " → ".join([REGIME_NAMES[r] for r in forecast.most_likely_path[:5]])
                st.caption(path_str)

            with col2:
                forecast_data = []
                for i, probs in enumerate(forecast.horizon_probabilities, 1):
                    for regime in Regime:
                        forecast_data.append({
                            "Step": i,
                            "Regime": REGIME_NAMES[regime],
                            "Probability": probs[regime],
                        })

                forecast_df = pd.DataFrame(forecast_data)
                fig_forecast = px.bar(
                    forecast_df,
                    x="Step",
                    y="Probability",
                    color="Regime",
                    color_discrete_map={REGIME_NAMES[r]: REGIME_COLORS_PLOTLY[r] for r in Regime},
                    barmode="stack",
                    labels={"Step": "Steps Ahead", "Probability": "Probability"},
                )
                fig_forecast.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=COLOR_SCHEME["background"],
                    paper_bgcolor=COLOR_SCHEME["surface"],
                    font=dict(color=COLOR_SCHEME["text"]),
                    height=300,
                )
                st.plotly_chart(fig_forecast, use_container_width=True)

        # Signal detection
        st.divider()
        st.subheader("🔔 Signals & Alerts")

        detector = SignalDetector()
        signals = []
        for idx, row in results.iterrows():
            from financial_dynamics.types import BarState, RegimeProbabilities

            bar_state = BarState(
                timestamp=idx,
                ohlcv=row.to_dict(),
                stabilized_regime=Regime[row["stabilized_regime"]] if pd.notna(row.get("stabilized_regime")) else None,
                risk_adjusted_regime=Regime[row["risk_adjusted_regime"]] if pd.notna(row.get("risk_adjusted_regime")) else None,
            )

            prob_cols = [f"post_prob_{r.name}" for r in Regime]
            if all(col in row.index for col in prob_cols):
                bar_state.posterior_probabilities = RegimeProbabilities(
                    probs=row[prob_cols].values
                )

            signals.extend(detector.check(bar_state))

        if signals:
            # Show recent signals
            recent_signals = signals[-10:]
            for signal in reversed(recent_signals):
                icon = {
                    SignalType.REGIME_CHANGE: "🔄",
                    SignalType.RISKOFF_WARNING: "⚠️",
                    SignalType.CONFIDENCE_DROP: "📉",
                    SignalType.REGIME_STABILIZED: "✅",
                }

                st.info(
                    f"{icon.get(signal.signal_type, '•')} **{signal.signal_type.name}** — {signal.message}\n\n"
                    f"Bar {signal.bar_index} | Confidence: {signal.confidence:.1%}"
                )
        else:
            st.info("No signals detected yet. Data is still warming up or regime is stable.")

        # Data inspector
        with st.expander("📋 Data Inspector"):
            st.write("**Recent Pipeline Output**")
            display_cols = [
                "risk_adjusted_regime",
                "stabilized_regime",
                "feat_volatility",
                "feat_trend",
                "feat_drawdown",
                "post_prob_CALM_TREND",
                "post_prob_VOLATILE_TREND",
                "post_prob_CHOP",
                "post_prob_RISK_OFF",
            ]
            available_cols = [col for col in display_cols if col in results.columns]
            st.dataframe(
                results[available_cols].tail(20),
                use_container_width=True,
                height=300,
            )


if __name__ == "__main__":
    main()
