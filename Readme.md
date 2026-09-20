# Quant-Backtesting & ML Engine

Una plataforma integral desarrollada en Python y Streamlit para el diseño, simulación y optimización de estrategias de trading algorítmico. Esta herramienta combina el rigor del backtesting *Event-Driven* con modelos predictivos de Machine Learning, enfocándose en la eficiencia computacional y la prevención del sobreajuste (*overfitting*).

## Arquitectura y Características Principales

* **Motor de Backtesting Híbrido:** Simulación realista que incorpora fricciones de mercado (comisiones, cash management) y un análisis exhaustivo de métricas ajustadas por riesgo (Sharpe, Sortino, Max Drawdown, Calmar Proxy).
* **Optimización de Hiperparámetros (HPO) de Bajo Costo:** Integración de la librería `FLAML` utilizando el algoritmo **CFO** (*Cost-Frugal Optimization*) para encontrar combinaciones óptimas de indicadores técnicos (SMA, RSI, MACD, Estocástico, Bollinger Bands) bajo restricciones estrictas de tiempo.
* **Procesamiento Vectorizado (Rolling OLS):** Implementación de regresiones lineales rodantes (`statsmodels.regression.rolling`) altamente optimizadas para evaluar la predictibilidad de múltiples *features* de forma casi instantánea, evitando los cuellos de botella de la iteración secuencial.
* **Prevención de Data Leakage:** Pipeline de evaluación robusto que utiliza **Walk-Forward Validation** para las estrategias de cruce y `TimeSeriesSplit` para el entrenamiento de los ensambles de Machine Learning (LightGBM, XGBoost, Random Forest), garantizando una validación *Out-of-Sample* (OOS) estadísticamente válida.
* **Interfaz Reactiva y Modular:** Diseño de UI mediante Streamlit con un manejo avanzado del estado (`st.session_state`), lo que permite persistir los cálculos pesados en memoria, separar la lógica de negocio de la capa de presentación y renderizar gráficos interactivos de alta fidelidad (Plotly y Bokeh) sin recálculos innecesarios.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.9+
* **Frontend / Framework:** Streamlit
* **Finanzas & Datos:** `yfinance`, `pandas`, `numpy`, `ta` (Technical Analysis Library)
* **Backtesting:** `Backtesting.py`
* **Machine Learning & Estadística:** `scikit-learn`, `FLAML` (AutoML), `statsmodels`
* **Visualización:** `Plotly`, `Bokeh`

## ⚙️ Instalación y Configuración

1. Clona el repositorio:
   ```bash
   git clone https://github.com/wgekko/app-backtexting-avanzado.git
   cd app-backtexting-avanzado

Video Demo 



https://github.com/user-attachments/assets/caac6b0e-2fcc-41f7-8f8c-287e67ebb186



 
