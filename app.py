"""Streamlit app for Financial Dynamics Model demo.

Interactive dashboard for market regime classification with live yfinance data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import logging
import warnings

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.config import PipelineConfig
from financial_dynamics.data_loader import fetch_ohlcv
from financial_dynamics.types import BarState, Regime, REGIME_NAMES, RegimeProbabilities
from financial_dynamics.signals.detector import SignalDetector, SignalType
from financial_dynamics.visualization.streamlit_charts import (
    COLOR_SCHEME,
    REGIME_COLORS_PLOTLY,
    plot_features,
    plot_price_with_regimes,
    plot_regime_probabilities,
    plot_transition_matrix,
)

logger = logging.getLogger(__name__)


def setup_page() -> None:
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
def load_data(symbol: str, period: str, interval: str) -> tuple[pd.DataFrame | None, str | None]:
    """Load OHLCV data from yfinance with caching."""
    try:
        df = fetch_ohlcv(symbol, period=period, interval=interval)
        return df, None
    except Exception as e:
        logger.warning("Live data fetch failed for %s: %s", symbol, e)
        return None, str(e)


@st.cache_resource
def get_pipeline() -> FinancialDynamicsPipeline:
    """Get or create pipeline instance."""
    config = PipelineConfig.from_yaml("config/default.yaml")
    return FinancialDynamicsPipeline(config)


def render_sidebar() -> tuple[str, str, str]:
    """Render the sidebar configuration controls and return (symbol, period, interval)."""
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

    return symbol, period, interval


def render_metrics(results: pd.DataFrame, pipeline: FinancialDynamicsPipeline) -> None:
    """Render the top metric cards: current regime, confidence, bars processed, status."""
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
        is_ready = "✓ Ready" if bars_processed >= warmup else "Warming up..."
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Status</div>
            <div class="metric-value">{is_ready}</div>
        </div>
        """, unsafe_allow_html=True)


def render_charts(df: pd.DataFrame, results: pd.DataFrame, pipeline: FinancialDynamicsPipeline) -> None:
    """Render the price/regime chart, probability + transition-matrix panels, and feature chart."""
    st.divider()

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


def render_forecast(pipeline: FinancialDynamicsPipeline) -> None:
    """Render the regime forecast section: expected duration, likely path, horizon chart."""
    st.divider()
    st.subheader("🔮 Regime Forecast")

    forecast = pipeline.forecast(horizon=10)
    if not forecast:
        return

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


def render_signals(results: pd.DataFrame) -> None:
    """Render the signal-detection section: recent regime-change / risk alerts."""
    st.divider()
    st.subheader("🔔 Signals & Alerts")

    detector = SignalDetector()
    signals = []
    for idx, row in results.iterrows():
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


def render_data_inspector(results: pd.DataFrame) -> None:
    """Render the collapsible raw pipeline-output table."""
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


def main() -> None:
    """Main Streamlit app."""
    setup_page()

    # Header
    st.markdown('<h1 class="main-title">📊 Financial Dynamics Model</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Transparent, Bayesian market regime classification for quantitative trading</p>',
        unsafe_allow_html=True
    )
    st.divider()

    symbol, period, interval = render_sidebar()

    # Main content
    if "run_pipeline" not in st.session_state:
        st.session_state.run_pipeline = True

    if st.session_state.run_pipeline:
        with st.spinner(f"Loading {symbol} data and running pipeline..."):
            df, error = load_data(symbol, period, interval)

            if error:
                st.warning(
                    f"⚠️ Live data unavailable for **{symbol}**: {error}. "
                    "Showing synthetic demo data instead.",
                    icon="📊",
                )
                df = _generate_synthetic_fallback()

            pipeline = get_pipeline()
            results = pipeline.run(df)

        render_metrics(results, pipeline)
        render_charts(df, results, pipeline)
        render_forecast(pipeline)
        render_signals(results)
        render_data_inspector(results)


if __name__ == "__main__":
    main()
