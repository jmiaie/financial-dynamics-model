<div align="center">

# Financial Dynamics Model
### 金融动力学模型

### 贝叶斯系统动力学管道 — 市场体制分类

[![PyPI version](https://img.shields.io/pypi/v/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Python](https://img.shields.io/pypi/pyversions/financial-dynamics?style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0d7377.svg?style=flat-square)](../LICENSE)
[![Tests](https://img.shields.io/badge/tests-268%20passed-0d7377?style=flat-square)](#测试)
[![Downloads](https://img.shields.io/pypi/dm/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Coverage](https://img.shields.io/badge/coverage-98%25-0d7377?style=flat-square)](#测试)
[![mypy](https://img.shields.io/badge/type%20checked-mypy-0d7377?style=flat-square)](https://mypy-lang.org/)
[![Streamlit](https://img.shields.io/badge/demo-live-0d7377?style=flat-square&logo=streamlit)](https://financial-dynamics-model.streamlit.app)

**将原始 OHLCV 数据转化为可解释的体制概率，服务于量化交易与风险管理。**

[在线演示](https://financial-dynamics-model.streamlit.app) &nbsp;|&nbsp; [技术文档](#技术文档) &nbsp;|&nbsp; [安装](#安装) &nbsp;|&nbsp; [API 参考](#python-api)

[English](../README.md) &nbsp;|&nbsp; **[中文](README_zh.md)** &nbsp;|&nbsp; [日本語](README_ja.md) &nbsp;|&nbsp; [한국어](README_ko.md) &nbsp;|&nbsp; [Español](README_es.md) &nbsp;|&nbsp; [Português](README_pt.md)

---

<table>
<tr>
<td align="center"><strong>80.6%</strong><br><sub>准确率</sub></td>
<td align="center"><strong>268</strong><br><sub>单元测试</sub></td>
<td align="center"><strong>5</strong><br><sub>管道阶段</sub></td>
<td align="center"><strong>4</strong><br><sub>市场体制</sub></td>
<td align="center"><strong>12</strong><br><sub>3D 可视化层</sub></td>
</tr>
</table>

</div>

---

## 为什么选择 Financial Dynamics？

市面上大多数体制检测工具，要么是黑箱神经网络，要么是过于简化的阈值规则。Financial Dynamics 恰好处于最佳平衡点：**完全透明的贝叶斯推理** 与 **生产级工程架构** 的有机结合。

每一个概率都可追溯。每一次体制转换都可解释。每一个信号都有清晰的数学来源。

```
                         ┌─────────────────────────────────┐
                         │     Financial Dynamics Model     │
                         └────────────────┬────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
     ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
     │   Python API    │        │   Streamlit 应用 │        │    CLI 工具     │
     │                 │        │                  │        │                 │
     │ pipeline.run()  │        │  交互式 3D 可视化│        │  run_pipeline   │
     │ pipeline.step() │        │  实时图表        │        │  run_backtest   │
     │ pipeline.fore-  │        │  信号流          │        │  run_calibrate  │
     │   cast()        │        │  预测            │        │  run_benchmark  │
     └─────────────────┘        └──────────────────┘        └─────────────────┘
```

---

## 安装

```bash
# 核心库
pip install financial-dynamics

# 附带实时数据（yfinance）
pip install financial-dynamics[data]

# 完整仪表板（Streamlit + Plotly + yfinance）
pip install financial-dynamics[dashboard]

# 全部组件，含开发工具
pip install financial-dynamics[all]
```

从源代码安装：

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
```

---

## 快速入门

### 交互式仪表板

```bash
streamlit run app.py
```

加载任意标的（SPY、QQQ、AAPL、BTC-USD），即可实时观测体制分类。图表即时更新，预测自动计算，信号随体制转换实时触发。

> **立即体验：** [financial-dynamics-model.streamlit.app](https://financial-dynamics-model.streamlit.app)

### Python API

```python
from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv

# 获取数据并运行管道
df = fetch_ohlcv("SPY", period="1y", interval="1d")
pipeline = FinancialDynamicsPipeline()
results = pipeline.run(df)

# 当前体制及置信度
current = results["risk_adjusted_regime"].iloc[-1]
confidence = results["post_prob_CALM_TREND"].iloc[-1]
print(f"体制: {current} (置信度 {confidence:.1%})")

# 预测未来 10 根 K 线
forecast = pipeline.forecast(horizon=10)
print(f"预期持续时间: {forecast.expected_duration:.1f} 根 K 线")
print(f"路径: {' → '.join(r.name for r in forecast.most_likely_path[:5])}")
```

### 命令行工具

```bash
python scripts/run_pipeline.py --symbol SPY --period 1y --interval 1d
python scripts/run_backtest.py --data historical.csv --labels regimes.csv --rolling
python scripts/run_calibration.py --output calibrated.yaml
python scripts/run_benchmark.py --config config/default.yaml
```

---

## 管道架构

<div align="center">

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                     原始 OHLCV 数据                         ║
 ╚══════════════════════════╦═══════════════════════════════════╝
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  阶段 0 │ 特征工程                                          │
 │         │ 5 维归一化: 波动率·趋势·回撤·相关性·冲击           │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  阶段 1 │ 质心分类                                          │
 │         │ P(Sᵢ|Xₜ) = exp(−‖Xₜ − Cᵢ‖ / τ) / Z              │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  阶段 2 │ 贝叶斯马尔可夫转移                                │
 │         │ P_post = P_centroid × T[prev, :] / Z               │
 │         │ 狄利克雷先验 · 在线学习                             │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  阶段 3 │ 时序稳定化                                        │
 │         │ 滞后效应 · 持续性约束 · 多数投票                   │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  阶段 4 │ 风险调节                                          │
 │         │ 风险规避确认 · 超伸衰减 · 震荡循环                 │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ╔══════════════════════════════════════════════════════════════╗
 ║              体制 + 置信度 + 预测                            ║
 ╚══════════════════════════════════════════════════════════════╝
```

</div>

---

## 市场体制

<table>
<tr>
<th width="180">体制</th>
<th>特征描述</th>
<th width="60">特征向量</th>
<th width="140">交易信号</th>
</tr>
<tr>
<td>
  <strong>平稳趋势</strong><br>
  <sub>低风险，方向明确</sub>
</td>
<td>低波动率，强上行趋势，回撤极小，相关性稳定</td>
<td><code>[0.1, 0.8, 0.05, 0.1, 0.1]</code></td>
<td>逢低建仓</td>
</tr>
<tr>
<td>
  <strong>波动趋势</strong><br>
  <sub>高能量，方向明确</sub>
</td>
<td>高波动率，方向性动量显著，回调后快速恢复</td>
<td><code>[0.8, 0.7, 0.3, 0.5, 0.6]</code></td>
<td>趋势跟踪</td>
</tr>
<tr>
<td>
  <strong>震荡</strong><br>
  <sub>低能量，无方向</sub>
</td>
<td>低波动率，趋势微弱，均值回归，价格区间震荡</td>
<td><code>[0.4, 0.2, 0.15, 0.3, 0.3]</code></td>
<td>区间交易</td>
</tr>
<tr>
<td>
  <strong>风险规避</strong><br>
  <sub>高风险，防御性</sub>
</td>
<td>高波动率，深度回撤，冲击聚集，压力传导</td>
<td><code>[0.9, 0.3, 0.8, 0.9, 0.9]</code></td>
<td>对冲 / 防御</td>
</tr>
</table>

---

## 3D 相空间吸引子场

交互式 3D 可视化将 5 维特征空间投影至 3 个主成分，揭示市场体制的几何结构：

<table>
<tr>
<td width="50%">

**结构层**
- 体制吸引盆（凸包）
- 1.5&sigma; 协方差椭球体
- 马尔可夫转移流向箭头
- PCA 载荷向量（特征轴）
- 质心标记与标签

</td>
<td width="50%">

**动态层**
- 速度编码轨迹（青色 &rarr; 红色）
- 体制转换标记点
- 平稳分布光晕
- 波动率危险区域等值面
- 指数衰减彗尾轨迹

</td>
</tr>
</table>

> **10 个交互开关** — 可独立启用/禁用每一层。拖拽旋转，滚轮缩放，悬停查看详情。

---

## 配置

所有参数位于 [`config/default.yaml`](../config/default.yaml)：

```yaml
features:
  volatility_span: 20          # EWMA 回看周期
  trend_window: 14             # 线性回归窗口
  drawdown_window: 60          # 滚动峰值窗口
  normalization_method: zscore # zscore | minmax

regimes:
  temperature: 1.0             # Softmax 温度参数（越低越锐利）

transitions:
  prior_strength: 10.0         # 狄利克雷先验浓度
  learning_rate: 0.05          # 贝叶斯更新速率

stabilization:
  hysteresis_threshold: 0.15   # 体制切换最小概率差
  min_persistence_bars: 5      # 确认切换前的最少 K 线数
  majority_vote_window: 10     # 滚动投票窗口

risk:
  riskoff_confirmation_count: 3  # 触发风险规避所需的压力因子数
  overextension_decay: 0.02      # 体制疲劳衰减率
```

---

## 测试

```bash
pytest tests/ -v                          # 全部 268 项测试
pytest tests/test_phase0_features.py -v   # 特征工程
pytest tests/test_pipeline_integration.py # 端到端测试
pytest tests/test_stress.py               # 数值稳定性
pytest tests/test_visualization.py        # 3D 渲染
```

<details>
<summary><strong>各模块测试覆盖</strong></summary>

| 模块 | 测试数 | 覆盖范围 |
|------|------:|---------|
| 阶段 0 — 特征工程 | 35 | 核心管道 |
| 阶段 1 — 体制分类 | 20 | 核心管道 |
| 阶段 2 — 转移矩阵 | 25 | 核心管道 |
| 阶段 3 — 时序稳定化 | 30 | 核心管道 |
| 阶段 4 — 风险调节 | 22 | 核心管道 |
| 管道集成 | 18 | 端到端 |
| 可视化 | 16 | 2D + 3D |
| 信号 | 12 | 检测 |
| 压力 / 数值 | 20 | 边界案例 |
| 校准 + 其他 | 31 | 工具链 |

</details>

---

## 项目结构

```
src/financial_dynamics/
├── pipeline.py                  # 编排器（批处理 + 流式）
├── types.py                     # Regime, FeatureVector, BarState
├── config.py                    # 类型化配置 + YAML 加载器
├── phase0_features/             # EWMA 波动率、趋势、回撤、相关性、冲击
├── phase1_regimes/              # Softmax 质心分类
├── phase2_transitions/          # 狄利克雷-贝叶斯马尔可夫学习
├── phase3_stabilization/        # 滞后效应、持续性、多数投票
├── phase4_risk/                 # 风险规避确认、超伸衰减
├── visualization/               # 2D/3D 相空间、仪表板、轨迹
├── calibration/                 # 质心拟合、超参数调优
├── backtesting/                 # 滚动窗口回测
├── benchmarks/                  # 基准分类器
├── forecasting/                 # k 步体制预测
├── signals/                     # 体制变化 / 风险检测
├── data_loader.py               # yfinance 数据接口
└── persistence/                 # 状态序列化

app.py                           # Streamlit 交互式仪表板
config/default.yaml              # 全部可调参数
```

---

## 应用场景

<table>
<tr>
<td width="50%">

**对冲基金与自营交易台**
- 系统化策略的可解释体制过滤器
- 基于体制的仓位管理（调整 vega/delta 敞口）
- 风险规避体制的早期预警

**量化研究员**
- 模块化、可测试的体制检测框架
- 可学习的转移矩阵
- 多资产回测支持

</td>
<td width="50%">

**风险管理**
- 透明的体制预测，服务于压力测试
- 多资产传导信号
- 实时体制前移预警

**金融科技与智能投顾**
- 面向客户的直观体制标签
- 可解释的资产配置调整
- 自动化防御性再平衡

</td>
</tr>
</table>

---

## 部署

<details>
<summary><strong>Streamlit Cloud（2 分钟部署）</strong></summary>

```bash
git push origin main
```
然后访问 [share.streamlit.io](https://share.streamlit.io) &rarr; 连接仓库 &rarr; 部署

</details>

<details>
<summary><strong>Docker</strong></summary>

```bash
docker build -t financial-dynamics .
docker run -d -p 8501:8501 --restart unless-stopped financial-dynamics
```

</details>

<details>
<summary><strong>自定义域名（fdm.micapai.com）</strong></summary>

参见 [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) 了解 Porkbun DNS + Streamlit Cloud 配置。

</details>

---

## 技术文档

| 资源 | 说明 |
|------|------|
| [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Streamlit Cloud、Docker、自定义域名 |
| [STREAMLIT_QUICK_START.md](../STREAMLIT_QUICK_START.md) | 本地运行仪表板 |
| [config/default.yaml](../config/default.yaml) | 全部可调参数 |
| `scripts/run_pipeline.py --help` | CLI 参考 |

---

## 参与贡献

欢迎贡献代码。重大变更请先提交 Issue 进行讨论。

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
pytest tests/ -v
```

---

## 许可证

[MIT](../LICENSE) — Jeff Milam & [Micap.AI](https://micap.ai)

---

<div align="center">

**Built by [Micap.AI](https://micap.ai)**

<sub>Python · NumPy · Pandas · SciPy · scikit-learn · Streamlit · Plotly · yfinance · 贝叶斯推理 · 马尔可夫链</sub>

<br>

[![GitHub stars](https://img.shields.io/github/stars/jmiaie/financial-dynamics-model?style=social)](https://github.com/jmiaie/financial-dynamics-model)

</div>
