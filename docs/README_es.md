<div align="center">

# Financial Dynamics Model
### Modelo de Dinámica Financiera

### Pipeline de Dinámica de Sistemas Bayesiano para Clasificación de Regímenes de Mercado

[![PyPI version](https://img.shields.io/pypi/v/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Python](https://img.shields.io/pypi/pyversions/financial-dynamics?style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0d7377.svg?style=flat-square)](../LICENSE)
[![Tests](https://img.shields.io/badge/tests-268%20passed-0d7377?style=flat-square)](#pruebas)
[![Downloads](https://img.shields.io/pypi/dm/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Coverage](https://img.shields.io/badge/coverage-98%25-0d7377?style=flat-square)](#pruebas)
[![mypy](https://img.shields.io/badge/type%20checked-mypy-0d7377?style=flat-square)](https://mypy-lang.org/)
[![Streamlit](https://img.shields.io/badge/demo-live-0d7377?style=flat-square&logo=streamlit)](https://financial-dynamics-model.streamlit.app)

**Transforma datos OHLCV sin procesar en probabilidades de régimen explicables para trading cuantitativo y gestión de riesgo.**

[Demo en vivo](https://financial-dynamics-model.streamlit.app) &nbsp;|&nbsp; [Documentación](#documentación) &nbsp;|&nbsp; [Instalación](#instalación) &nbsp;|&nbsp; [Referencia de la API](#api-de-python)

[English](../README.md) &nbsp;|&nbsp; [中文](README_zh.md) &nbsp;|&nbsp; [日本語](README_ja.md) &nbsp;|&nbsp; [한국어](README_ko.md) &nbsp;|&nbsp; **[Español](README_es.md)** &nbsp;|&nbsp; [Português](README_pt.md)

---

<table>
<tr>
<td align="center"><strong>80.6%</strong><br><sub>Precisión</sub></td>
<td align="center"><strong>268</strong><br><sub>Pruebas</sub></td>
<td align="center"><strong>5</strong><br><sub>Fases del Pipeline</sub></td>
<td align="center"><strong>4</strong><br><sub>Regímenes de Mercado</sub></td>
<td align="center"><strong>12</strong><br><sub>Capas 3D</sub></td>
</tr>
</table>

</div>

---

## ¿Por qué Financial Dynamics?

La mayoría de las herramientas de detección de regímenes son redes neuronales de tipo caja negra o reglas de umbral simplistas. Financial Dynamics se ubica en el punto óptimo: **inferencia bayesiana completamente transparente** con **ingeniería de grado de producción**.

Cada probabilidad es trazable. Cada transición es explicable. Cada señal tiene un origen matemático claro.

```
                         ┌─────────────────────────────────┐
                         │     Financial Dynamics Model     │
                         └────────────────┬────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
     ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
     │   API Python    │        │   App Streamlit  │        │ Herramientas CLI│
     │                 │        │                  │        │                 │
     │ pipeline.run()  │        │  3D Interactivo  │        │  run_pipeline   │
     │ pipeline.step() │        │  Gráficos Live   │        │  run_backtest   │
     │ pipeline.fore-  │        │  Feed de señales │        │  run_calibrate  │
     │   cast()        │        │  Pronósticos     │        │  run_benchmark  │
     └─────────────────┘        └──────────────────┘        └─────────────────┘
```

---

## Instalación

```bash
# Biblioteca principal
pip install financial-dynamics

# Con datos en tiempo real (yfinance)
pip install financial-dynamics[data]

# Dashboard completo (Streamlit + Plotly + yfinance)
pip install financial-dynamics[dashboard]

# Todo, incluyendo herramientas de desarrollo
pip install financial-dynamics[all]
```

O desde el código fuente:

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
```

---

## Inicio Rápido

### Dashboard Interactivo

```bash
streamlit run app.py
```

Cargue cualquier ticker (SPY, QQQ, AAPL, BTC-USD) y observe la clasificación de régimen en tiempo real. Los gráficos se actualizan al instante, los pronósticos se calculan automáticamente y las señales se activan conforme cambian los regímenes.

> **Pruébelo ahora:** [financial-dynamics-model.streamlit.app](https://financial-dynamics-model.streamlit.app)

### API de Python

```python
from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv

# Obtener datos y ejecutar el pipeline
df = fetch_ohlcv("SPY", period="1y", interval="1d")
pipeline = FinancialDynamicsPipeline()
results = pipeline.run(df)

# Régimen actual + confianza
current = results["risk_adjusted_regime"].iloc[-1]
confidence = results["post_prob_CALM_TREND"].iloc[-1]
print(f"Régimen: {current} ({confidence:.1%} confianza)")

# Pronóstico para las próximas 10 barras
forecast = pipeline.forecast(horizon=10)
print(f"Duración esperada: {forecast.expected_duration:.1f} barras")
print(f"Trayectoria: {' → '.join(r.name for r in forecast.most_likely_path[:5])}")
```

### CLI

```bash
python scripts/run_pipeline.py --symbol SPY --period 1y --interval 1d
python scripts/run_backtest.py --data historical.csv --labels regimes.csv --rolling
python scripts/run_calibration.py --output calibrated.yaml
python scripts/run_benchmark.py --config config/default.yaml
```

---

## Arquitectura del Pipeline

<div align="center">

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                   DATOS OHLCV SIN PROCESAR                  ║
 ╚══════════════════════════╦═══════════════════════════════════╝
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 0  │ Ingeniería de Características                    │
 │          │ 5D normalizado: vol · tendencia · drawdown ·     │
 │          │ corr · shock                                     │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 1  │ Clasificación por Centroides                     │
 │          │ P(Sᵢ|Xₜ) = exp(−‖Xₜ − Cᵢ‖ / τ) / Z             │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 2  │ Transiciones Bayesianas de Markov                │
 │          │ P_post = P_centroide × T[prev, :] / Z            │
 │          │ Prior de Dirichlet · aprendizaje en línea         │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 3  │ Estabilización Temporal                          │
 │          │ Histéresis · persistencia · voto mayoritario     │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  FASE 4  │ Condicionamiento de Riesgo                       │
 │          │ Confirmación Risk-Off · sobreextensión ·         │
 │          │ bucle de lateralización                           │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ╔══════════════════════════════════════════════════════════════╗
 ║             RÉGIMEN + CONFIANZA + PRONÓSTICO                ║
 ╚══════════════════════════════════════════════════════════════╝
```

</div>

---

## Regímenes de Mercado

<table>
<tr>
<th width="180">Régimen</th>
<th>Características</th>
<th width="60">Firma de Características</th>
<th width="140">Señal de Trading</th>
</tr>
<tr>
<td>
  <strong>Tendencia Calma</strong><br>
  <sub>Riesgo bajo, direccional</sub>
</td>
<td>Baja volatilidad, tendencia alcista sólida, drawdown mínimo, correlaciones estables</td>
<td><code>[0.1, 0.8, 0.05, 0.1, 0.1]</code></td>
<td>Acumulación larga</td>
</tr>
<tr>
<td>
  <strong>Tendencia Volátil</strong><br>
  <sub>Alta energía, direccional</sub>
</td>
<td>Alta volatilidad, momentum direccional, recuperaciones desde correcciones</td>
<td><code>[0.8, 0.7, 0.3, 0.5, 0.6]</code></td>
<td>Seguimiento de tendencia</td>
</tr>
<tr>
<td>
  <strong>Lateralización (Chop)</strong><br>
  <sub>Baja energía, sin dirección</sub>
</td>
<td>Baja volatilidad, tendencia débil, reversión a la media, rango acotado</td>
<td><code>[0.4, 0.2, 0.15, 0.3, 0.3]</code></td>
<td>Trading de rango</td>
</tr>
<tr>
<td>
  <strong>Aversión al Riesgo (Risk-Off)</strong><br>
  <sub>Riesgo elevado, defensivo</sub>
</td>
<td>Alta volatilidad, drawdowns profundos, clusters de shock, contagio de estrés</td>
<td><code>[0.9, 0.3, 0.8, 0.9, 0.9]</code></td>
<td>Cobertura / defensivo</td>
</tr>
</table>

---

## Campo de Atractores en Espacio de Fases 3D

La visualización 3D interactiva proyecta el espacio de características 5D sobre 3 componentes principales, revelando la estructura geométrica de los regímenes de mercado:

<table>
<tr>
<td width="50%">

**Capas Estructurales**
- Cuencas de atracción de régimen (envolventes convexas)
- Elipsoides de covarianza a 1.5&sigma;
- Flechas de flujo de transición de Markov
- Vectores de carga PCA (ejes de características)
- Marcadores de centroide con etiquetas

</td>
<td width="50%">

**Capas Dinámicas**
- Trayectoria codificada por velocidad (teal &rarr; rojo)
- Marcadores de cambio de régimen en puntos de transición
- Halos de distribución estacionaria
- Isosuperficie de zona de peligro por volatilidad
- Estela tipo cometa con decaimiento exponencial

</td>
</tr>
</table>

> **10 controles interactivos** — active o desactive cada capa de forma independiente. Arrastre para rotar, desplace la rueda para hacer zoom, pase el cursor para ver detalles.

---

## Configuración

Todos los parámetros en [`config/default.yaml`](../config/default.yaml):

```yaml
features:
  volatility_span: 20          # Ventana retrospectiva EWMA
  trend_window: 14             # Ventana de regresión lineal
  drawdown_window: 60          # Ventana de pico móvil
  normalization_method: zscore # zscore | minmax

regimes:
  temperature: 1.0             # Temperatura softmax (menor = más definido)

transitions:
  prior_strength: 10.0         # Concentración del prior de Dirichlet
  learning_rate: 0.05          # Velocidad de actualización bayesiana

stabilization:
  hysteresis_threshold: 0.15   # Brecha mínima de probabilidad para cambio
  min_persistence_bars: 5      # Barras antes de confirmar cambio
  majority_vote_window: 10     # Ventana de voto mayoritario

risk:
  riskoff_confirmation_count: 3  # Estresores necesarios para Risk-Off
  overextension_decay: 0.02      # Tasa de fatiga de régimen
```

---

## Pruebas

```bash
pytest tests/ -v                          # Las 268 pruebas
pytest tests/test_phase0_features.py -v   # Ingeniería de características
pytest tests/test_pipeline_integration.py # De extremo a extremo
pytest tests/test_stress.py               # Estabilidad numérica
pytest tests/test_visualization.py        # Renderizado 3D
```

<details>
<summary><strong>Cobertura de Pruebas por Módulo</strong></summary>

| Módulo | Pruebas | Cobertura |
|--------|--------:|-----------|
| Fase 0 — Características | 35 | Pipeline principal |
| Fase 1 — Regímenes | 20 | Pipeline principal |
| Fase 2 — Transiciones | 25 | Pipeline principal |
| Fase 3 — Estabilización | 30 | Pipeline principal |
| Fase 4 — Riesgo | 22 | Pipeline principal |
| Integración del Pipeline | 18 | De extremo a extremo |
| Visualización | 16 | 2D + 3D |
| Señales | 12 | Detección |
| Estrés / Numérico | 20 | Casos extremos |
| Calibración + Otros | 31 | Herramientas |

</details>

---

## Estructura del Proyecto

```
src/financial_dynamics/
├── pipeline.py                  # Orquestador (batch + streaming)
├── types.py                     # Regime, FeatureVector, BarState
├── config.py                    # Configuración tipada + cargador YAML
├── phase0_features/             # Vol EWMA, tendencia, drawdown, corr, shock
├── phase1_regimes/              # Clasificación softmax por centroides
├── phase2_transitions/          # Aprendizaje Markov bayesiano-Dirichlet
├── phase3_stabilization/        # Histéresis, persistencia, voto mayoritario
├── phase4_risk/                 # Confirmación Risk-Off, sobreextensión
├── visualization/               # Espacio de fases 2D/3D, dashboard, trayectoria
├── calibration/                 # Ajuste de centroides, optimización de hiperparámetros
├── backtesting/                 # Evaluación con ventana móvil
├── benchmarks/                  # Clasificadores de referencia
├── forecasting/                 # Pronósticos de régimen a k pasos
├── signals/                     # Detección de cambio de régimen / riesgo
├── data_loader.py               # Integración con yfinance
└── persistence/                 # Serialización de estado

app.py                           # Dashboard interactivo de Streamlit
config/default.yaml              # Todos los parámetros configurables
```

---

## Casos de Uso

<table>
<tr>
<td width="50%">

**Fondos de Cobertura y Mesas de Operaciones**
- Filtro de régimen explicable para estrategias sistemáticas
- Dimensionamiento de posiciones por régimen (escalar vega/delta)
- Alerta temprana para confirmación de Risk-Off

**Investigadores Cuantitativos**
- Detección de regímenes modular y testeable
- Matrices de transición aprendidas
- Backtesting multi-activo

</td>
<td width="50%">

**Gestión de Riesgo**
- Pronósticos de régimen transparentes para pruebas de estrés
- Señales de contagio multi-activo
- Alertas en tiempo real previas a cambios de régimen

**Fintech y Robo-Advisors**
- Etiquetas de régimen amigables para el cliente
- Cambios de asignación explicables
- Rebalanceo defensivo automatizado

</td>
</tr>
</table>

---

## Despliegue

<details>
<summary><strong>Streamlit Cloud (2 minutos)</strong></summary>

```bash
git push origin main
```
Luego: [share.streamlit.io](https://share.streamlit.io) &rarr; Conectar repositorio &rarr; Desplegar

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

Consulte [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) para la configuración de DNS en Porkbun + Streamlit Cloud.

</details>

---

## Documentación

| Recurso | Descripción |
|---------|-------------|
| [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Streamlit Cloud, Docker, dominio personalizado |
| [STREAMLIT_QUICK_START.md](../STREAMLIT_QUICK_START.md) | Ejecutar el dashboard localmente |
| [config/default.yaml](../config/default.yaml) | Todos los parámetros configurables |
| `scripts/run_pipeline.py --help` | Referencia de la CLI |

---

## Contribuciones

Las contribuciones son bienvenidas. Por favor abra un issue primero para discutir cambios significativos.

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
pytest tests/ -v
```

---

## Licencia

[MIT](../LICENSE) — Jeff Milam & [Micap.AI](https://micap.ai)

---

<div align="center">

**Desarrollado por [Micap.AI](https://micap.ai)**

<sub>Python · NumPy · Pandas · SciPy · scikit-learn · Streamlit · Plotly · yfinance · Inferencia bayesiana · Cadenas de Markov</sub>

<br>

[![GitHub stars](https://img.shields.io/github/stars/jmiaie/financial-dynamics-model?style=social)](https://github.com/jmiaie/financial-dynamics-model)

</div>
