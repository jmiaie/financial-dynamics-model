<div align="center">

# Financial Dynamics Model
### 金融ダイナミクスモデル

### ベイズシステムダイナミクスパイプライン — 市場レジーム分類

[![PyPI version](https://img.shields.io/pypi/v/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Python](https://img.shields.io/pypi/pyversions/financial-dynamics?style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0d7377.svg?style=flat-square)](../LICENSE)
[![Tests](https://img.shields.io/badge/tests-268%20passed-0d7377?style=flat-square)](#テスト)
[![Downloads](https://img.shields.io/pypi/dm/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Coverage](https://img.shields.io/badge/coverage-98%25-0d7377?style=flat-square)](#テスト)
[![mypy](https://img.shields.io/badge/type%20checked-mypy-0d7377?style=flat-square)](https://mypy-lang.org/)
[![Streamlit](https://img.shields.io/badge/demo-live-0d7377?style=flat-square&logo=streamlit)](https://financial-dynamics-model.streamlit.app)

**生のOHLCVデータを、定量トレーディングおよびリスク管理のための説明可能なレジーム確率に変換します。**

[ライブデモ](https://financial-dynamics-model.streamlit.app) &nbsp;|&nbsp; [ドキュメント](#ドキュメント) &nbsp;|&nbsp; [インストール](#インストール) &nbsp;|&nbsp; [APIリファレンス](#python-api)

[English](../README.md) &nbsp;|&nbsp; [中文](README_zh.md) &nbsp;|&nbsp; **[日本語](README_ja.md)** &nbsp;|&nbsp; [한국어](README_ko.md) &nbsp;|&nbsp; [Español](README_es.md) &nbsp;|&nbsp; [Português](README_pt.md)

---

<table>
<tr>
<td align="center"><strong>80.6%</strong><br><sub>精度</sub></td>
<td align="center"><strong>268</strong><br><sub>テスト</sub></td>
<td align="center"><strong>5</strong><br><sub>パイプライン段階</sub></td>
<td align="center"><strong>4</strong><br><sub>市場レジーム</sub></td>
<td align="center"><strong>12</strong><br><sub>3Dレイヤー</sub></td>
</tr>
</table>

</div>

---

## なぜ Financial Dynamics なのか？

多くのレジーム検出ツールは、ブラックボックス型ニューラルネットワークか、単純な閾値ルールのいずれかです。Financial Dynamics はその中間に位置し、**完全に透明なベイズ推論**と**プロダクショングレードのエンジニアリング**を両立しています。

すべての確率はトレース可能。すべての遷移は説明可能。すべてのシグナルは明確な数学的根拠を持ちます。

```
                         ┌─────────────────────────────────┐
                         │     Financial Dynamics Model     │
                         └────────────────┬────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
     ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
     │   Python API    │        │   Streamlit App  │        │    CLIツール     │
     │                 │        │                  │        │                 │
     │ pipeline.run()  │        │  インタラクティブ3D │        │  run_pipeline   │
     │ pipeline.step() │        │  ライブチャート    │        │  run_backtest   │
     │ pipeline.fore-  │        │  シグナルフィード   │        │  run_calibrate  │
     │   cast()        │        │  予測             │        │  run_benchmark  │
     └─────────────────┘        └──────────────────┘        └─────────────────┘
```

---

## インストール

```bash
# コアライブラリ
pip install financial-dynamics

# ライブデータ取得（yfinance）
pip install financial-dynamics[data]

# フルダッシュボード（Streamlit + Plotly + yfinance）
pip install financial-dynamics[dashboard]

# 開発ツール含むすべて
pip install financial-dynamics[all]
```

ソースからのインストール:

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
```

---

## クイックスタート

### インタラクティブダッシュボード

```bash
streamlit run app.py
```

任意のティッカー（SPY、QQQ、AAPL、BTC-USD）を読み込み、リアルタイムでレジーム分類を確認できます。チャートは即時更新され、予測は自動計算され、レジームが変化するとシグナルが発火します。

> **今すぐ試す:** [financial-dynamics-model.streamlit.app](https://financial-dynamics-model.streamlit.app)

### Python API

```python
from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv

# データ取得とパイプライン実行
df = fetch_ohlcv("SPY", period="1y", interval="1d")
pipeline = FinancialDynamicsPipeline()
results = pipeline.run(df)

# 現在のレジームと信頼度
current = results["risk_adjusted_regime"].iloc[-1]
confidence = results["post_prob_CALM_TREND"].iloc[-1]
print(f"レジーム: {current} (信頼度 {confidence:.1%})")

# 今後10バーの予測
forecast = pipeline.forecast(horizon=10)
print(f"予想持続期間: {forecast.expected_duration:.1f} バー")
print(f"経路: {' → '.join(r.name for r in forecast.most_likely_path[:5])}")
```

### CLI

```bash
python scripts/run_pipeline.py --symbol SPY --period 1y --interval 1d
python scripts/run_backtest.py --data historical.csv --labels regimes.csv --rolling
python scripts/run_calibration.py --output calibrated.yaml
python scripts/run_benchmark.py --config config/default.yaml
```

---

## パイプラインアーキテクチャ

<div align="center">

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                     生 OHLCV データ                          ║
 ╚══════════════════════════╦═══════════════════════════════════╝
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 0 │ 特徴量エンジニアリング                              │
 │          │ 5次元正規化: vol · trend · drawdown · corr · shock │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 1 │ セントロイド分類                                    │
 │          │ P(Sᵢ|Xₜ) = exp(−‖Xₜ − Cᵢ‖ / τ) / Z             │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 2 │ ベイズマルコフ遷移                                  │
 │          │ P_post = P_centroid × T[prev, :] / Z              │
 │          │ ディリクレ事前分布 · オンライン学習                     │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 3 │ 時間安定化                                         │
 │          │ ヒステリシス · 持続性フィルタ · 多数決投票              │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 4 │ リスク条件付け                                      │
 │          │ リスクオフ確認 · 過剰伸長 · チョップループ              │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ╔══════════════════════════════════════════════════════════════╗
 ║              レジーム + 信頼度 + 予測                          ║
 ╚══════════════════════════════════════════════════════════════╝
```

</div>

---

## 市場レジーム

<table>
<tr>
<th width="180">レジーム</th>
<th>特性</th>
<th width="60">特徴量シグネチャ</th>
<th width="140">トレーディングシグナル</th>
</tr>
<tr>
<td>
  <strong>穏やかトレンド</strong><br>
  <sub>Calm Trend — 低リスク・方向性あり</sub>
</td>
<td>低ボラティリティ、強い上昇トレンド、最小限のドローダウン、安定した相関</td>
<td><code>[0.1, 0.8, 0.05, 0.1, 0.1]</code></td>
<td>ロング蓄積</td>
</tr>
<tr>
<td>
  <strong>変動トレンド</strong><br>
  <sub>Volatile Trend — 高エネルギー・方向性あり</sub>
</td>
<td>高ボラティリティ、方向性モメンタム、ディップからの回復</td>
<td><code>[0.8, 0.7, 0.3, 0.5, 0.6]</code></td>
<td>トレンドフォロー</td>
</tr>
<tr>
<td>
  <strong>レンジ相場</strong><br>
  <sub>Chop — 低エネルギー・方向性なし</sub>
</td>
<td>低ボラティリティ、弱いトレンド、平均回帰、レンジバウンド</td>
<td><code>[0.4, 0.2, 0.15, 0.3, 0.3]</code></td>
<td>レンジトレーディング</td>
</tr>
<tr>
<td>
  <strong>リスクオフ</strong><br>
  <sub>Risk-Off — 高リスク・ディフェンシブ</sub>
</td>
<td>高ボラティリティ、深いドローダウン、ショッククラスター、ストレス伝染</td>
<td><code>[0.9, 0.3, 0.8, 0.9, 0.9]</code></td>
<td>ヘッジ / ディフェンシブ</td>
</tr>
</table>

---

## 3D位相空間アトラクターフィールド

インタラクティブ3D可視化は、5次元特徴量空間を3つの主成分に射影し、市場レジームの幾何学的構造を明らかにします。

<table>
<tr>
<td width="50%">

**構造レイヤー**
- レジーム吸引域（凸包）
- 1.5&sigma; 共分散楕円体
- マルコフ遷移フローアロー
- PCA負荷量ベクトル（特徴量軸）
- セントロイドマーカーとラベル

</td>
<td width="50%">

**動的レイヤー**
- 速度エンコード軌道（ティール &rarr; レッド）
- レジーム遷移点でのシフトマーカー
- 定常分布ハロー
- ボラティリティ危険域等値面
- 指数減衰コメットトレイル

</td>
</tr>
</table>

> **10のインタラクティブトグル** — 各レイヤーを個別に有効/無効化できます。ドラッグで回転、スクロールでズーム、ホバーで詳細表示。

---

## 設定

すべてのパラメータは [`config/default.yaml`](../config/default.yaml) で管理:

```yaml
features:
  volatility_span: 20          # EWMA ルックバック期間
  trend_window: 14             # 線形回帰ウィンドウ
  drawdown_window: 60          # ローリングピークウィンドウ
  normalization_method: zscore # zscore | minmax

regimes:
  temperature: 1.0             # ソフトマックス温度（低い = よりシャープ）

transitions:
  prior_strength: 10.0         # ディリクレ事前分布の集中度
  learning_rate: 0.05          # ベイズ更新速度

stabilization:
  hysteresis_threshold: 0.15   # 遷移に必要な最小確率差
  min_persistence_bars: 5      # 変更確認までの最小バー数
  majority_vote_window: 10     # ローリング投票ウィンドウ

risk:
  riskoff_confirmation_count: 3  # リスクオフ確認に必要なストレッサー数
  overextension_decay: 0.02      # レジーム疲労率
```

---

## テスト

```bash
pytest tests/ -v                          # 全268テスト
pytest tests/test_phase0_features.py -v   # 特徴量エンジニアリング
pytest tests/test_pipeline_integration.py # エンドツーエンド
pytest tests/test_stress.py               # 数値安定性
pytest tests/test_visualization.py        # 3Dレンダリング
```

<details>
<summary><strong>モジュール別テストカバレッジ</strong></summary>

| モジュール | テスト数 | カバレッジ |
|-----------|------:|---------|
| Phase 0 — 特徴量 | 35 | コアパイプライン |
| Phase 1 — レジーム | 20 | コアパイプライン |
| Phase 2 — 遷移 | 25 | コアパイプライン |
| Phase 3 — 安定化 | 30 | コアパイプライン |
| Phase 4 — リスク | 22 | コアパイプライン |
| パイプライン統合 | 18 | エンドツーエンド |
| 可視化 | 16 | 2D + 3D |
| シグナル | 12 | 検出 |
| ストレス / 数値 | 20 | エッジケース |
| キャリブレーション他 | 31 | ツーリング |

</details>

---

## プロジェクト構成

```
src/financial_dynamics/
├── pipeline.py                  # オーケストレーター（バッチ + ストリーミング）
├── types.py                     # Regime, FeatureVector, BarState
├── config.py                    # 型付き設定 + YAMLローダー
├── phase0_features/             # EWMA vol, trend, drawdown, corr, shock
├── phase1_regimes/              # ソフトマックスセントロイド分類
├── phase2_transitions/          # ディリクレベイズマルコフ学習
├── phase3_stabilization/        # ヒステリシス, 持続性, 多数決投票
├── phase4_risk/                 # リスクオフ確認, 過剰伸長
├── visualization/               # 2D/3D位相空間, ダッシュボード, 軌道
├── calibration/                 # セントロイドフィッティング, ハイパーパラメータ調整
├── backtesting/                 # ローリングウィンドウ評価
├── benchmarks/                  # ベースライン分類器
├── forecasting/                 # kステップレジーム予測
├── signals/                     # レジーム変化 / リスク検出
├── data_loader.py               # yfinance統合
└── persistence/                 # 状態シリアライゼーション

app.py                           # Streamlit インタラクティブダッシュボード
config/default.yaml              # 全チューニングパラメータ
```

---

## ユースケース

<table>
<tr>
<td width="50%">

**ヘッジファンド & プロップデスク**
- システマティック戦略のための説明可能なレジームフィルター
- レジーム別ポジションサイジング（ベガ/デルタのスケーリング）
- リスクオフ確認の早期警告

**クオンツ研究者**
- モジュール式でテスト可能なレジーム検出
- 学習済み遷移行列
- マルチアセットバックテスト

</td>
<td width="50%">

**リスク管理**
- ストレステスト向けの透明なレジーム予測
- マルチアセット伝染シグナル
- リアルタイムのプレシフト警告

**フィンテック & ロボアドバイザー**
- 顧客向けの分かりやすいレジームラベル
- 説明可能なアロケーション変更
- 自動ディフェンシブリバランス

</td>
</tr>
</table>

---

## デプロイ

<details>
<summary><strong>Streamlit Cloud（2分）</strong></summary>

```bash
git push origin main
```
その後: [share.streamlit.io](https://share.streamlit.io) &rarr; リポジトリ接続 &rarr; デプロイ

</details>

<details>
<summary><strong>Docker</strong></summary>

```bash
docker build -t financial-dynamics .
docker run -d -p 8501:8501 --restart unless-stopped financial-dynamics
```

</details>

<details>
<summary><strong>カスタムドメイン（fdm.micapai.com）</strong></summary>

Porkbun DNS + Streamlit Cloud のセットアップについては [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) を参照してください。

</details>

---

## ドキュメント

| リソース | 説明 |
|----------|------|
| [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Streamlit Cloud、Docker、カスタムドメイン |
| [STREAMLIT_QUICK_START.md](../STREAMLIT_QUICK_START.md) | ダッシュボードをローカルで実行 |
| [config/default.yaml](../config/default.yaml) | 全チューニングパラメータ |
| `scripts/run_pipeline.py --help` | CLIリファレンス |

---

## コントリビューション

コントリビューションを歓迎します。大きな変更については、まずIssueを開いて議論してください。

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
pytest tests/ -v
```

---

## ライセンス

[MIT](../LICENSE) — Jeff Milam & [Micap.AI](https://micap.ai)

---

<div align="center">

**Built by [Micap.AI](https://micap.ai)**

<sub>Python · NumPy · Pandas · SciPy · scikit-learn · Streamlit · Plotly · yfinance · ベイズ推論 · マルコフ連鎖</sub>

<br>

[![GitHub stars](https://img.shields.io/github/stars/jmiaie/financial-dynamics-model?style=social)](https://github.com/jmiaie/financial-dynamics-model)

</div>
