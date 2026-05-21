<div align="center">

# Financial Dynamics Model
### Modelo de Dinamica Financeira

### Pipeline de Dinamica de Sistemas Bayesiano para Classificacao de Regimes de Mercado

[![PyPI version](https://img.shields.io/pypi/v/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Python](https://img.shields.io/pypi/pyversions/financial-dynamics?style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0d7377.svg?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-268%20passed-0d7377?style=flat-square)](#testes)
[![Downloads](https://img.shields.io/pypi/dm/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Coverage](https://img.shields.io/badge/coverage-98%25-0d7377?style=flat-square)](#testes)
[![mypy](https://img.shields.io/badge/type%20checked-mypy-0d7377?style=flat-square)](https://mypy-lang.org/)
[![Streamlit](https://img.shields.io/badge/demo-live-0d7377?style=flat-square&logo=streamlit)](https://financial-dynamics-model.streamlit.app)

**Transforma dados brutos OHLCV em probabilidades de regime interpretaveis para trading quantitativo e gestao de risco.**

[Demo ao Vivo](https://financial-dynamics-model.streamlit.app) &nbsp;|&nbsp; [Documentacao](#documentacao) &nbsp;|&nbsp; [Instalacao](#instalacao) &nbsp;|&nbsp; [Referencia da API](#api-python)

[English](../README.md) &nbsp;|&nbsp; [中文](README_zh.md) &nbsp;|&nbsp; [日本語](README_ja.md) &nbsp;|&nbsp; [한국어](README_ko.md) &nbsp;|&nbsp; [Español](README_es.md) &nbsp;|&nbsp; **[Portugues](README_pt.md)**

---

<table>
<tr>
<td align="center"><strong>80.6%</strong><br><sub>Acuracia</sub></td>
<td align="center"><strong>268</strong><br><sub>Testes</sub></td>
<td align="center"><strong>5</strong><br><sub>Fases do Pipeline</sub></td>
<td align="center"><strong>4</strong><br><sub>Regimes de Mercado</sub></td>
<td align="center"><strong>12</strong><br><sub>Camadas 3D</sub></td>
</tr>
</table>

</div>

---

## Por que o Financial Dynamics?

A maioria das ferramentas de deteccao de regime sao redes neurais black-box ou regras simples de threshold. O Financial Dynamics ocupa o ponto ideal: **inferencia bayesiana totalmente transparente** com **engenharia de nivel producao**.

Cada probabilidade e rastreavel. Cada transicao e explicavel. Cada sinal tem uma origem matematica clara.

```
                         ┌─────────────────────────────────┐
                         │     Financial Dynamics Model     │
                         └────────────────┬────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
     ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
     │   API Python    │        │   App Streamlit  │        │ Ferramentas CLI │
     │                 │        │                  │        │                 │
     │ pipeline.run()  │        │  3D Interativo   │        │  run_pipeline   │
     │ pipeline.step() │        │  Graficos Live   │        │  run_backtest   │
     │ pipeline.fore-  │        │  Feed de Sinais  │        │  run_calibrate  │
     │   cast()        │        │  Previsoes       │        │  run_benchmark  │
     └─────────────────┘        └──────────────────┘        └─────────────────┘
```

---

## Instalacao

```bash
# Biblioteca principal
pip install financial-dynamics

# Com dados ao vivo (yfinance)
pip install financial-dynamics[data]

# Dashboard completo (Streamlit + Plotly + yfinance)
pip install financial-dynamics[dashboard]

# Tudo incluindo ferramentas de desenvolvimento
pip install financial-dynamics[all]
```

Ou a partir do codigo-fonte:

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
```

---

## Inicio Rapido

### Dashboard Interativo

```bash
streamlit run app.py
```

Carregue qualquer ticker (SPY, QQQ, AAPL, BTC-USD) e acompanhe a classificacao de regime em tempo real. Os graficos atualizam instantaneamente, as previsoes sao calculadas automaticamente e os sinais disparam conforme os regimes mudam.

> **Experimente agora:** [financial-dynamics-model.streamlit.app](https://financial-dynamics-model.streamlit.app)

### API Python

```python
from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv

# Buscar dados e executar o pipeline
df = fetch_ohlcv("SPY", period="1y", interval="1d")
pipeline = FinancialDynamicsPipeline()
results = pipeline.run(df)

# Regime atual + confianca
current = results["risk_adjusted_regime"].iloc[-1]
confidence = results["post_prob_CALM_TREND"].iloc[-1]
print(f"Regime: {current} ({confidence:.1%} de confianca)")

# Prever os proximos 10 periodos
forecast = pipeline.forecast(horizon=10)
print(f"Duracao esperada: {forecast.expected_duration:.1f} periodos")
print(f"Caminho: {' → '.join(r.name for r in forecast.most_likely_path[:5])}")
```

### CLI

```bash
python scripts/run_pipeline.py --symbol SPY --period 1y --interval 1d
python scripts/run_backtest.py --data historical.csv --labels regimes.csv --rolling
python scripts/run_calibration.py --output calibrated.yaml
python scripts/run_benchmark.py --config config/default.yaml
```

---

## Arquitetura do Pipeline

<div align="center">

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                   DADOS BRUTOS OHLCV                        ║
 ╚══════════════════════════╦═══════════════════════════════════╝
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 0  │ Engenharia de Features                           │
 │          │ 5D normalizado: vol · tendencia · drawdown · corr · choque │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 1  │ Classificacao por Centroides                     │
 │          │ P(Sᵢ|Xₜ) = exp(−‖Xₜ − Cᵢ‖ / τ) / Z             │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 2  │ Transicoes Bayesianas de Markov                  │
 │          │ P_post = P_centroide × T[prev, :] / Z            │
 │          │ Prior de Dirichlet · aprendizado online           │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 3  │ Estabilizacao Temporal                           │
 │          │ Histerese · persistencia · voto majoritario       │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 4  │ Condicionamento de Risco                         │
 │          │ Confirmacao Risk-Off · sobreextensao · ciclo chop │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ╔══════════════════════════════════════════════════════════════╗
 ║             REGIME + CONFIANCA + PREVISAO                    ║
 ╚══════════════════════════════════════════════════════════════╝
```

</div>

---

## Regimes de Mercado

<table>
<tr>
<th width="180">Regime</th>
<th>Caracteristicas</th>
<th width="60">Assinatura de Features</th>
<th width="140">Sinal de Trading</th>
</tr>
<tr>
<td>
  <strong>Tendencia Calma</strong><br>
  <sub>Baixo risco, direcional</sub>
</td>
<td>Baixa volatilidade, tendencia de alta forte, drawdown minimo, correlacoes estaveis</td>
<td><code>[0.1, 0.8, 0.05, 0.1, 0.1]</code></td>
<td>Acumulacao comprada</td>
</tr>
<tr>
<td>
  <strong>Tendencia Volatil</strong><br>
  <sub>Alta energia, direcional</sub>
</td>
<td>Alta volatilidade, momentum direcional, recuperacoes apos quedas</td>
<td><code>[0.8, 0.7, 0.3, 0.5, 0.6]</code></td>
<td>Seguidor de tendencia</td>
</tr>
<tr>
<td>
  <strong>Lateralizacao (Chop)</strong><br>
  <sub>Baixa energia, sem direcao</sub>
</td>
<td>Baixa volatilidade, tendencia fraca, reversao a media, movimento em faixa</td>
<td><code>[0.4, 0.2, 0.15, 0.3, 0.3]</code></td>
<td>Trading de faixa</td>
</tr>
<tr>
<td>
  <strong>Risk-Off (Aversao ao Risco)</strong><br>
  <sub>Alto risco, defensivo</sub>
</td>
<td>Alta volatilidade, drawdowns profundos, clusters de choque, contagio de estresse</td>
<td><code>[0.9, 0.3, 0.8, 0.9, 0.9]</code></td>
<td>Hedge / defensivo</td>
</tr>
</table>

---

## Campo de Atratores no Espaco de Fase 3D

A visualizacao 3D interativa projeta o espaco de features 5D em 3 componentes principais, revelando a estrutura geometrica dos regimes de mercado:

<table>
<tr>
<td width="50%">

**Camadas Estruturais**
- Bacias de atracao de regime (envoltoria convexa)
- Elipsoides de covariancia 1.5&sigma;
- Setas de fluxo de transicao de Markov
- Vetores de carga PCA (eixos de features)
- Marcadores de centroide com rotulos

</td>
<td width="50%">

**Camadas Dinamicas**
- Trajetoria codificada por velocidade (teal &rarr; vermelho)
- Marcadores de mudanca de regime nos pontos de transicao
- Halos de distribuicao estacionaria
- Isosuperficie de zona de perigo de volatilidade
- Rastro tipo cometa com decaimento exponencial

</td>
</tr>
</table>

> **10 controles interativos** — ative/desative cada camada independentemente. Arraste para rotacionar, scroll para zoom, passe o mouse para detalhes.

---

## Configuracao

Todos os parametros em [`config/default.yaml`](../config/default.yaml):

```yaml
features:
  volatility_span: 20          # Lookback EWMA
  trend_window: 14             # Janela de regressao linear
  drawdown_window: 60          # Janela de pico movel
  normalization_method: zscore # zscore | minmax

regimes:
  temperature: 1.0             # Temperatura softmax (menor = mais nitido)

transitions:
  prior_strength: 10.0         # Concentracao do prior de Dirichlet
  learning_rate: 0.05          # Velocidade de atualizacao bayesiana

stabilization:
  hysteresis_threshold: 0.15   # Gap minimo de probabilidade para mudar
  min_persistence_bars: 5      # Periodos antes de confirmar mudanca
  majority_vote_window: 10     # Janela de votacao movel

risk:
  riskoff_confirmation_count: 3  # Estressores necessarios para Risk-Off
  overextension_decay: 0.02      # Taxa de fadiga de regime
```

---

## Testes

```bash
pytest tests/ -v                          # Todos os 268 testes
pytest tests/test_phase0_features.py -v   # Engenharia de features
pytest tests/test_pipeline_integration.py # Ponta a ponta
pytest tests/test_stress.py               # Estabilidade numerica
pytest tests/test_visualization.py        # Renderizacao 3D
```

<details>
<summary><strong>Cobertura de Testes por Modulo</strong></summary>

| Modulo | Testes | Cobertura |
|--------|-------:|-----------|
| Fase 0 — Features | 35 | Pipeline principal |
| Fase 1 — Regimes | 20 | Pipeline principal |
| Fase 2 — Transicoes | 25 | Pipeline principal |
| Fase 3 — Estabilizacao | 30 | Pipeline principal |
| Fase 4 — Risco | 22 | Pipeline principal |
| Integracao do Pipeline | 18 | Ponta a ponta |
| Visualizacao | 16 | 2D + 3D |
| Sinais | 12 | Deteccao |
| Estresse / Numerico | 20 | Casos limite |
| Calibracao + Outros | 31 | Ferramentas |

</details>

---

## Estrutura do Projeto

```
src/financial_dynamics/
├── pipeline.py                  # Orquestrador (batch + streaming)
├── types.py                     # Regime, FeatureVector, BarState
├── config.py                    # Config tipada + carregador YAML
├── phase0_features/             # Vol EWMA, tendencia, drawdown, corr, choque
├── phase1_regimes/              # Classificacao softmax por centroides
├── phase2_transitions/          # Aprendizado bayesiano-Dirichlet de Markov
├── phase3_stabilization/        # Histerese, persistencia, voto majoritario
├── phase4_risk/                 # Confirmacao Risk-Off, sobreextensao
├── visualization/               # Espaco de fase 2D/3D, dashboard, trajetoria
├── calibration/                 # Ajuste de centroides, tuning de hiperparametros
├── backtesting/                 # Avaliacao com janela movel
├── benchmarks/                  # Classificadores de referencia
├── forecasting/                 # Previsoes de regime k-passos
├── signals/                     # Deteccao de mudanca de regime / risco
├── data_loader.py               # Integracao com yfinance
└── persistence/                 # Serializacao de estado

app.py                           # Dashboard interativo Streamlit
config/default.yaml              # Todos os parametros ajustaveis
```

---

## Casos de Uso

<table>
<tr>
<td width="50%">

**Fundos de Hedge e Mesas Proprietarias**
- Filtro de regime explicavel para estrategias sistematicas
- Dimensionamento de posicao por regime (escalar vega/delta)
- Alerta antecipado para confirmacao de Risk-Off

**Pesquisadores Quantitativos**
- Deteccao de regime modular e testavel
- Matrizes de transicao aprendidas
- Backtesting multi-ativo

</td>
<td width="50%">

**Gestao de Risco**
- Previsoes de regime transparentes para testes de estresse
- Sinais de contagio multi-ativo
- Alertas em tempo real pre-mudanca de regime

**Fintech e Robo-Advisors**
- Rotulos de regime compreensiveis para o cliente
- Mudancas de alocacao explicaveis
- Rebalanceamento defensivo automatizado

</td>
</tr>
</table>

---

## Deploy

<details>
<summary><strong>Streamlit Cloud (2 minutos)</strong></summary>

```bash
git push origin main
```
Em seguida: [share.streamlit.io](https://share.streamlit.io) &rarr; Conectar repositorio &rarr; Deploy

</details>

<details>
<summary><strong>Docker</strong></summary>

```bash
docker build -t financial-dynamics .
docker run -d -p 8501:8501 --restart unless-stopped financial-dynamics
```

</details>

<details>
<summary><strong>Dominio Personalizado (fdm.micapai.com)</strong></summary>

Consulte [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) para configuracao de DNS Porkbun + Streamlit Cloud.

</details>

---

## Documentacao

| Recurso | Descricao |
|---------|-----------|
| [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Streamlit Cloud, Docker, dominio personalizado |
| [STREAMLIT_QUICK_START.md](../STREAMLIT_QUICK_START.md) | Executar o dashboard localmente |
| [config/default.yaml](../config/default.yaml) | Todos os parametros ajustaveis |
| `scripts/run_pipeline.py --help` | Referencia da CLI |

---

## Contribuindo

Contribuicoes sao bem-vindas. Por favor, abra uma issue primeiro para discutir mudancas significativas.

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
pytest tests/ -v
```

---

## Licenca

[MIT](../LICENSE) — Jeff Milam & [Micap.AI](https://micap.ai)

---

<div align="center">

**Desenvolvido por [Micap.AI](https://micap.ai)**

<sub>Python · NumPy · Pandas · SciPy · scikit-learn · Streamlit · Plotly · yfinance · Inferencia Bayesiana · Cadeias de Markov</sub>

<br>

[![GitHub stars](https://img.shields.io/github/stars/jmiaie/financial-dynamics-model?style=social)](https://github.com/jmiaie/financial-dynamics-model)

</div>
