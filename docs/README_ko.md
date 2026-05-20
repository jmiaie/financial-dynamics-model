<div align="center">

# Financial Dynamics Model
### 금융 다이내믹스 모델

### 베이지안 시스템 다이내믹스 파이프라인 — 시장 레짐 분류

[![PyPI version](https://img.shields.io/pypi/v/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Python](https://img.shields.io/pypi/pyversions/financial-dynamics?style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0d7377.svg?style=flat-square)](../LICENSE)
[![Tests](https://img.shields.io/badge/tests-268%20passed-0d7377?style=flat-square)](#테스트)
[![Downloads](https://img.shields.io/pypi/dm/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Coverage](https://img.shields.io/badge/coverage-98%25-0d7377?style=flat-square)](#테스트)
[![mypy](https://img.shields.io/badge/type%20checked-mypy-0d7377?style=flat-square)](https://mypy-lang.org/)
[![Streamlit](https://img.shields.io/badge/demo-live-0d7377?style=flat-square&logo=streamlit)](https://financial-dynamics-model.streamlit.app)

**원시 OHLCV 데이터를 설명 가능한 레짐 확률로 변환하여 퀀트 트레이딩과 리스크 관리에 활용합니다.**

[라이브 데모](https://financial-dynamics-model.streamlit.app) &nbsp;|&nbsp; [문서](#문서) &nbsp;|&nbsp; [설치](#설치) &nbsp;|&nbsp; [API 레퍼런스](#python-api)

[English](../README.md) &nbsp;|&nbsp; [中文](README_zh.md) &nbsp;|&nbsp; [日本語](README_ja.md) &nbsp;|&nbsp; **[한국어](README_ko.md)** &nbsp;|&nbsp; [Español](README_es.md) &nbsp;|&nbsp; [Português](README_pt.md)

---

<table>
<tr>
<td align="center"><strong>80.6%</strong><br><sub>정확도</sub></td>
<td align="center"><strong>268</strong><br><sub>테스트</sub></td>
<td align="center"><strong>5</strong><br><sub>파이프라인 단계</sub></td>
<td align="center"><strong>4</strong><br><sub>시장 레짐</sub></td>
<td align="center"><strong>12</strong><br><sub>3D 시각화 레이어</sub></td>
</tr>
</table>

</div>

---

## 왜 Financial Dynamics인가?

대부분의 레짐 탐지 도구는 블랙박스 신경망이거나 단순한 임계값 규칙에 불과합니다. Financial Dynamics는 그 사이의 최적점에 위치합니다: **완전히 투명한 베이지안 추론**과 **프로덕션 수준의 엔지니어링**을 결합합니다.

모든 확률은 추적 가능합니다. 모든 전이는 설명 가능합니다. 모든 시그널은 명확한 수학적 근거를 가집니다.

```
                         ┌─────────────────────────────────┐
                         │     Financial Dynamics Model     │
                         └────────────────┬────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
     ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
     │   Python API    │        │   Streamlit App  │        │    CLI 도구     │
     │                 │        │                  │        │                 │
     │ pipeline.run()  │        │  인터랙티브 3D   │        │  run_pipeline   │
     │ pipeline.step() │        │  실시간 차트     │        │  run_backtest   │
     │ pipeline.fore-  │        │  시그널 피드     │        │  run_calibrate  │
     │   cast()        │        │  예측            │        │  run_benchmark  │
     └─────────────────┘        └──────────────────┘        └─────────────────┘
```

---

## 설치

```bash
# 코어 라이브러리
pip install financial-dynamics

# 실시간 데이터 포함 (yfinance)
pip install financial-dynamics[data]

# 전체 대시보드 (Streamlit + Plotly + yfinance)
pip install financial-dynamics[dashboard]

# 개발 도구 포함 전체 설치
pip install financial-dynamics[all]
```

소스에서 설치:

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
```

---

## 빠른 시작

### 인터랙티브 대시보드

```bash
streamlit run app.py
```

임의의 종목 코드(SPY, QQQ, AAPL, BTC-USD)를 입력하면 레짐 분류가 실시간으로 갱신됩니다. 차트는 즉시 업데이트되고, 예측은 자동으로 계산되며, 레짐 전환 시 시그널이 발생합니다.

> **지금 체험하기:** [financial-dynamics-model.streamlit.app](https://financial-dynamics-model.streamlit.app)

### Python API

```python
from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv

# 데이터 가져오기 및 파이프라인 실행
df = fetch_ohlcv("SPY", period="1y", interval="1d")
pipeline = FinancialDynamicsPipeline()
results = pipeline.run(df)

# 현재 레짐 및 신뢰도 확인
current = results["risk_adjusted_regime"].iloc[-1]
confidence = results["post_prob_CALM_TREND"].iloc[-1]
print(f"레짐: {current} (신뢰도 {confidence:.1%})")

# 향후 10봉 예측
forecast = pipeline.forecast(horizon=10)
print(f"예상 지속 기간: {forecast.expected_duration:.1f}봉")
print(f"경로: {' → '.join(r.name for r in forecast.most_likely_path[:5])}")
```

### CLI

```bash
python scripts/run_pipeline.py --symbol SPY --period 1y --interval 1d
python scripts/run_backtest.py --data historical.csv --labels regimes.csv --rolling
python scripts/run_calibration.py --output calibrated.yaml
python scripts/run_benchmark.py --config config/default.yaml
```

---

## 파이프라인 아키텍처

<div align="center">

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                     원시 OHLCV 데이터                        ║
 ╚══════════════════════════╦═══════════════════════════════════╝
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 0 │ 특성 엔지니어링                                    │
 │          │ 5차원 정규화: 변동성·추세·낙폭·상관관계·충격         │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 1 │ 센트로이드 분류                                    │
 │          │ P(Sᵢ|Xₜ) = exp(−‖Xₜ − Cᵢ‖ / τ) / Z             │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 2 │ 베이지안 마르코프 전이                              │
 │          │ P_post = P_centroid × T[prev, :] / Z              │
 │          │ 디리클레 사전분포 · 온라인 학습                      │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 3 │ 시간 안정화                                        │
 │          │ 히스테리시스 · 지속성 · 다수결 투표                   │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  Phase 4 │ 리스크 컨디셔닝                                    │
 │          │ 리스크오프 확인 · 과확장 · 횡보 루프                  │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ╔══════════════════════════════════════════════════════════════╗
 ║              레짐 + 신뢰도 + 예측                             ║
 ╚══════════════════════════════════════════════════════════════╝
```

</div>

---

## 시장 레짐

<table>
<tr>
<th width="180">레짐</th>
<th>특성</th>
<th width="60">특성 시그니처</th>
<th width="140">트레이딩 시그널</th>
</tr>
<tr>
<td>
  <strong>안정 추세 (Calm Trend)</strong><br>
  <sub>저위험, 방향성</sub>
</td>
<td>낮은 변동성, 강한 상승 추세, 최소 낙폭, 안정적 상관관계</td>
<td><code>[0.1, 0.8, 0.05, 0.1, 0.1]</code></td>
<td>매수 축적</td>
</tr>
<tr>
<td>
  <strong>변동 추세 (Volatile Trend)</strong><br>
  <sub>고에너지, 방향성</sub>
</td>
<td>높은 변동성, 방향성 모멘텀, 조정 후 반등</td>
<td><code>[0.8, 0.7, 0.3, 0.5, 0.6]</code></td>
<td>추세 추종</td>
</tr>
<tr>
<td>
  <strong>횡보 (Chop)</strong><br>
  <sub>저에너지, 비방향성</sub>
</td>
<td>낮은 변동성, 약한 추세, 평균 회귀, 박스권</td>
<td><code>[0.4, 0.2, 0.15, 0.3, 0.3]</code></td>
<td>박스권 트레이딩</td>
</tr>
<tr>
<td>
  <strong>리스크오프 (Risk-Off)</strong><br>
  <sub>고위험, 방어적</sub>
</td>
<td>높은 변동성, 깊은 낙폭, 충격 군집, 스트레스 전이</td>
<td><code>[0.9, 0.3, 0.8, 0.9, 0.9]</code></td>
<td>헤지 / 방어 전략</td>
</tr>
</table>

---

## 3D 위상 공간 어트랙터 필드

인터랙티브 3D 시각화는 5차원 특성 공간을 3개의 주성분으로 사영하여 시장 레짐의 기하학적 구조를 드러냅니다:

<table>
<tr>
<td width="50%">

**구조 레이어**
- 레짐 끌개 분지 (볼록 껍질)
- 1.5&sigma; 공분산 타원체
- 마르코프 전이 흐름 화살표
- PCA 적재 벡터 (특성 축)
- 센트로이드 마커 및 라벨

</td>
<td width="50%">

**동적 레이어**
- 속도 인코딩 궤적 (청록 &rarr; 적색)
- 레짐 전환점의 전이 마커
- 정상 분포 후광
- 변동성 위험 구역 등가면
- 지수 감쇠 혜성 궤적

</td>
</tr>
</table>

> **10개의 인터랙티브 토글** — 각 레이어를 독립적으로 활성화/비활성화할 수 있습니다. 드래그하여 회전, 스크롤하여 확대/축소, 호버하여 상세 정보를 확인하세요.

---

## 설정

모든 파라미터는 [`config/default.yaml`](../config/default.yaml)에서 관리됩니다:

```yaml
features:
  volatility_span: 20          # EWMA 룩백 기간
  trend_window: 14             # 선형 회귀 윈도우
  drawdown_window: 60          # 롤링 고점 윈도우
  normalization_method: zscore # zscore | minmax

regimes:
  temperature: 1.0             # 소프트맥스 온도 (낮을수록 선명)

transitions:
  prior_strength: 10.0         # 디리클레 사전분포 집중도
  learning_rate: 0.05          # 베이지안 업데이트 속도

stabilization:
  hysteresis_threshold: 0.15   # 레짐 전환 최소 확률 차이
  min_persistence_bars: 5      # 전환 확정 전 최소 봉 수
  majority_vote_window: 10     # 롤링 투표 윈도우

risk:
  riskoff_confirmation_count: 3  # 리스크오프 확정에 필요한 스트레서 수
  overextension_decay: 0.02      # 레짐 피로 감쇠율
```

---

## 테스트

```bash
pytest tests/ -v                          # 전체 268개 테스트
pytest tests/test_phase0_features.py -v   # 특성 엔지니어링
pytest tests/test_pipeline_integration.py # 엔드투엔드
pytest tests/test_stress.py               # 수치 안정성
pytest tests/test_visualization.py        # 3D 렌더링
```

<details>
<summary><strong>모듈별 테스트 커버리지</strong></summary>

| 모듈 | 테스트 수 | 범위 |
|------|--------:|------|
| Phase 0 — 특성 엔지니어링 | 35 | 코어 파이프라인 |
| Phase 1 — 레짐 분류 | 20 | 코어 파이프라인 |
| Phase 2 — 전이 행렬 | 25 | 코어 파이프라인 |
| Phase 3 — 시간 안정화 | 30 | 코어 파이프라인 |
| Phase 4 — 리스크 | 22 | 코어 파이프라인 |
| 파이프라인 통합 | 18 | 엔드투엔드 |
| 시각화 | 16 | 2D + 3D |
| 시그널 | 12 | 탐지 |
| 스트레스 / 수치 | 20 | 엣지 케이스 |
| 캘리브레이션 + 기타 | 31 | 도구 |

</details>

---

## 프로젝트 구조

```
src/financial_dynamics/
├── pipeline.py                  # 오케스트레이터 (배치 + 스트리밍)
├── types.py                     # Regime, FeatureVector, BarState
├── config.py                    # 타입 설정 + YAML 로더
├── phase0_features/             # EWMA 변동성, 추세, 낙폭, 상관관계, 충격
├── phase1_regimes/              # 소프트맥스 센트로이드 분류
├── phase2_transitions/          # 디리클레-베이지안 마르코프 학습
├── phase3_stabilization/        # 히스테리시스, 지속성, 다수결 투표
├── phase4_risk/                 # 리스크오프 확인, 과확장
├── visualization/               # 2D/3D 위상 공간, 대시보드, 궤적
├── calibration/                 # 센트로이드 피팅, 하이퍼파라미터 튜닝
├── backtesting/                 # 롤링 윈도우 평가
├── benchmarks/                  # 베이스라인 분류기
├── forecasting/                 # k-스텝 레짐 예측
├── signals/                     # 레짐 전환 / 리스크 탐지
├── data_loader.py               # yfinance 연동
└── persistence/                 # 상태 직렬화

app.py                           # Streamlit 인터랙티브 대시보드
config/default.yaml              # 전체 튜닝 가능 파라미터
```

---

## 활용 사례

<table>
<tr>
<td width="50%">

**헤지펀드 및 프롭 데스크**
- 체계적 전략을 위한 설명 가능한 레짐 필터
- 레짐 기반 포지션 사이징 (베가/델타 스케일링)
- 리스크오프 확정 조기 경보

**퀀트 연구원**
- 모듈형, 테스트 가능한 레짐 탐지
- 학습된 전이 행렬
- 멀티 자산 백테스트

</td>
<td width="50%">

**리스크 관리**
- 스트레스 테스트를 위한 투명한 레짐 예측
- 멀티 자산 전이 시그널
- 실시간 사전 전환 경고

**핀테크 및 로보어드바이저**
- 고객 친화적 레짐 라벨
- 설명 가능한 자산배분 변경
- 자동 방어적 리밸런싱

</td>
</tr>
</table>

---

## 배포

<details>
<summary><strong>Streamlit Cloud (2분 소요)</strong></summary>

```bash
git push origin main
```
이후: [share.streamlit.io](https://share.streamlit.io) &rarr; 저장소 연결 &rarr; 배포

</details>

<details>
<summary><strong>Docker</strong></summary>

```bash
docker build -t financial-dynamics .
docker run -d -p 8501:8501 --restart unless-stopped financial-dynamics
```

</details>

<details>
<summary><strong>커스텀 도메인 (fdm.micapai.com)</strong></summary>

Porkbun DNS + Streamlit Cloud 설정에 대한 자세한 내용은 [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)를 참조하세요.

</details>

---

## 문서

| 리소스 | 설명 |
|--------|------|
| [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Streamlit Cloud, Docker, 커스텀 도메인 |
| [STREAMLIT_QUICK_START.md](../STREAMLIT_QUICK_START.md) | 로컬 대시보드 실행 가이드 |
| [config/default.yaml](../config/default.yaml) | 전체 튜닝 가능 파라미터 |
| `scripts/run_pipeline.py --help` | CLI 레퍼런스 |

---

## 기여하기

기여를 환영합니다. 주요 변경 사항은 먼저 이슈를 열어 논의해 주세요.

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
pytest tests/ -v
```

---

## 라이선스

[MIT](../LICENSE) — Jeff Milam & [Micap.AI](https://micap.ai)

---

<div align="center">

**Built by [Micap.AI](https://micap.ai)**

<sub>Python · NumPy · Pandas · SciPy · scikit-learn · Streamlit · Plotly · yfinance · 베이지안 추론 · 마르코프 체인</sub>

<br>

[![GitHub stars](https://img.shields.io/github/stars/jmiaie/financial-dynamics-model?style=social)](https://github.com/jmiaie/financial-dynamics-model)

</div>
