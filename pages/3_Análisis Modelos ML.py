import streamlit as st
import yfinance as yf
import ta
import pandas as pd
import numpy as np
import datetime
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS
from sklearn.metrics import mean_absolute_error, mean_squared_error
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from flaml import AutoML

# Configuración de la página
st.set_page_config(page_title="Stock Predictor OLS & FLAML", layout="wide", page_icon=":material/finance:")
st.subheader(":material/network_intelligence: Predicción de Acciones con Indicadores Técnicos y Machine Learning")

# --- BARRA LATERAL ---
st.sidebar.header("Configuración de Datos")
ticker = st.sidebar.text_input("Ticker", value="NVDA")
start_date = st.sidebar.date_input("Fecha de Inicio", value=pd.to_datetime("2022-10-25"))
end_date = st.sidebar.date_input("Fecha de Fin", value=datetime.date.today())

st.sidebar.header("Opciones de Modelado")
modo = st.sidebar.radio("Selecciona el método de predicción:", ("1. Backtest Original Vectorizado (Rolling OLS)", "2. Optimización con FLAML (CFO)"))
window_size = st.sidebar.slider("Ventana de Entrenamiento (Días)", min_value=10, max_value=60, value=20)

# --- CARGA DE DATOS ---
@st.cache_data
def load_and_preprocess_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if df.empty: return df
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df['Previous_Close'] = df['Close'].shift(1)
    df['Close_shifted'] = df['Close'].shift(1)
    df['Open_shifted'] = df['Open'].shift(1)
    df['High_shifted'] = df['High'].shift(1)
    df['Low_shifted'] = df['Low'].shift(1)
    
    df['SMA_50'] = ta.trend.sma_indicator(df['Close_shifted'], window=50)
    df['EMA_50'] = ta.trend.ema_indicator(df['Close_shifted'], window=50)
    df['RSI'] = ta.momentum.rsi(df['Close_shifted'], window=14)
    df['MACD'] = ta.trend.macd(df['Close_shifted'], window_slow=26, window_fast=12)
    df['Signal_Line'] = ta.trend.macd_signal(df['Close_shifted'], window_slow=26, window_fast=12, window_sign=9)
    
    indicator_bb = ta.volatility.BollingerBands(close=df['Close_shifted'], window=20, window_dev=2)
    df['BB_Upper'] = indicator_bb.bollinger_hband()
    df['BB_Lower'] = indicator_bb.bollinger_lband()
    
    indicator_stoch = ta.momentum.StochasticOscillator(high=df['High_shifted'], low=df['Low_shifted'], close=df['Close_shifted'], window=14, smooth_window=3)
    df['%K'] = indicator_stoch.stoch()
    df['%D'] = indicator_stoch.stoch_signal()
    
    df['ATR'] = ta.volatility.average_true_range(high=df['High_shifted'], low=df['Low_shifted'], close=df['Close_shifted'], window=14)
    df.dropna(inplace=True)
    return df

df = load_and_preprocess_data(ticker, start_date, end_date)
if df.empty:
    st.error("No se encontraron datos para los parámetros seleccionados.")
    st.stop()

indicators = ['SMA_50', 'EMA_50', 'RSI', 'MACD', 'Signal_Line', 'BB_Upper', 'BB_Lower', '%K', '%D', 'ATR', 'Previous_Close']

# --- MODO 1: ROLLING OLS (VECTORIZADO EXTREMADAMENTE RÁPIDO) ---
if modo == "1. Backtest Original Vectorizado (Rolling OLS)":
    st.header("Modo 1: Backtest Vectorizado con Rolling OLS")
    
    if st.button("Ejecutar Backtest Rolling OLS"):
        with st.spinner("Entrenando modelos rodantes en C (Statsmodels)..."):
            accuracy_data = {'Indicador': [], 'MAE': [], 'MSE': []}
            results = {}

            # Índices de evaluación para igualar lógica original: test_index iniciaba en window_size + 1
            valid_indices = range(window_size + 1, len(df))
            
            for indicator in indicators[:-1]:
                exog = sm.add_constant(df[[indicator, 'Previous_Close']])
                endog = df['Close']
                
                # Ejecuta la regresión rodante de una sola vez sobre toda la serie temporal
                model = RollingOLS(endog, exog, window=window_size).fit()
                
                # Para predecir i+1 usando la regresión terminada en i-1 (como el código original), 
                # desplazamos los betas generados 2 períodos hacia adelante
                shifted_params = model.params.shift(2)
                
                # Multiplicación vectorial instantánea para obtener todas las predicciones
                all_preds = (exog * shifted_params).sum(axis=1)
                
                # Filtramos para el rango de backtest
                preds_filtered = all_preds.iloc[valid_indices]
                actuals_filtered = endog.iloc[valid_indices]
                dates_filtered = df.index[valid_indices]
                
                mae = mean_absolute_error(actuals_filtered, preds_filtered)
                mse = mean_squared_error(actuals_filtered, preds_filtered)
                
                results[indicator] = {'predictions': preds_filtered.values, 'actual': actuals_filtered.values, 'dates': dates_filtered}
                accuracy_data['Indicador'].append(indicator)
                accuracy_data['MAE'].append(mae)
                accuracy_data['MSE'].append(mse)
            
            # Guardamos estado 
            st.session_state['ml_modo1'] = {'accuracy_df': pd.DataFrame(accuracy_data).sort_values(by='MAE'), 'results': results}
    
    # Renderizar OLS
    if 'ml_modo1' in st.session_state:
        acc_df = st.session_state['ml_modo1']['accuracy_df']
        res = st.session_state['ml_modo1']['results']
        
        st.subheader("Métricas de Error por Indicador")
        st.dataframe(acc_df.reset_index(drop=True))
        
        best_ind = acc_df.iloc[0]['Indicador']
        st.subheader(f"Predicción vs Realidad (Mejor Indicador: {best_ind})")
        
        # fig = go.Figure()
        # fig.add_trace(go.Scatter(x=res[best_ind]['dates'], y=res[best_ind]['actual'], mode='lines', name='Precio Real'))
        # fig.add_trace(go.Scatter(x=res[best_ind]['dates'], y=res[best_ind]['predictions'], mode='lines', name=f'Pred. OLS ({best_ind})'))
        # fig.update_layout(title="Resultados del mejor modelo OLS", xaxis_title="Fecha", yaxis_title="Precio USD")
        # st.plotly_chart(fig, width='stretch')
        fig = go.Figure()
        # Precio Real en Verde Neón brillante
        fig.add_trace(go.Scatter(
            x=res[best_ind]['dates'], 
            y=res[best_ind]['actual'], 
            mode='lines', 
            name='Precio Real',
            line=dict(color='#00FFA3', width=2)
        ))
        # Predicción OLS en Magenta / Rosa vibrante
        fig.add_trace(go.Scatter(
            x=res[best_ind]['dates'], 
            y=res[best_ind]['predictions'], 
            mode='lines', 
            name=f'Pred. OLS ({best_ind})',
            line=dict(color='#FF007F', width=2)
        ))
        fig.update_layout(
            title="Resultados del mejor modelo OLS", 
            xaxis_title="Fecha", 
            yaxis_title="Precio USD",
            hovermode="x unified"
        )
        st.plotly_chart(fig, width='stretch')

# --- MODO 2: FLAML (CON TIME SERIES SPLIT Y STATE) ---
else:
    st.header("Modo 2: Optimización General con FLAML (CFO)")
    time_budget = st.slider("Tiempo máximo de optimización (segundos)", 5, 60, 15)
    
    if st.button("Iniciar Optimización CFO"):
        with st.spinner("Optimizando modelo, hiperparámetros e indicadores cruzados..."):
            features = indicators
            X = df[features]
            y = df['Close'].squeeze()
            
            split_idx = int(len(df) * 0.8)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            automl = AutoML()
            settings = {
                "time_budget": time_budget,
                "metric": 'mae',
                "task": 'regression',
                "hpo_method": 'cfo',
                "estimator_list": ['lgbm', 'xgboost', 'rf', 'extra_tree'],
                "eval_method": "cv",
                "split_type": "time", # Prevención de Leakage forzando pliegues temporales
                "n_splits": 5,
                "verbose": 0
            }
            
            try:
                automl.fit(X_train=X_train, y_train=y_train, **settings)
                predictions = automl.predict(X_test)
                
                st.session_state['ml_modo2'] = {
                    'best_est': automl.best_estimator,
                    'mae': mean_absolute_error(y_test, predictions),
                    'mse': mean_squared_error(y_test, predictions),
                    'dates': df.index[split_idx:],
                    'actuals': y_test,
                    'preds': predictions,
                    'importances': pd.Series(automl.model.estimator.feature_importances_, index=features).sort_values(ascending=False)
                }
            except Exception as e:
                st.error(f"Fallo durante la optimización de FLAML: {e}")
                
    # Renderizar FLAML
    if 'ml_modo2' in st.session_state:
        r = st.session_state['ml_modo2']
        st.success(f"Optimización completada. Mejor modelo encontrado: **{r['best_est']}**")
        
        col1, col2 = st.columns(2)
        col1.metric("Mean Absolute Error (MAE)", f"{r['mae']:.4f}")
        col2.metric("Mean Squared Error (MSE)", f"{r['mse']:.4f}")
        
        st.subheader("Predicciones del Modelo vs Realidad (Set de Prueba OOS)")
        # fig2 = go.Figure()
        # fig2.add_trace(go.Scatter(x=r['dates'], y=r['actuals'], mode='lines', name='Precio Real'))
        # fig2.add_trace(go.Scatter(x=r['dates'], y=r['preds'], mode='lines', name='Predicción FLAML (CFO)'))
        # st.plotly_chart(fig2, width='stretch')
        fig2 = go.Figure()
        # Precio Real en Verde Neón brillante
        fig2.add_trace(go.Scatter(
            x=r['dates'], 
            y=r['actuals'], 
            mode='lines', 
            name='Precio Real',
            line=dict(color='#00FFA3', width=2)
        ))
        # Predicción FLAML en Azul Cyan / Celeste brillante
        fig2.add_trace(go.Scatter(
            x=r['dates'], 
            y=r['preds'], 
            mode='lines', 
            name='Predicción FLAML (CFO)',
            line=dict(color='#00E5FF', width=2)
        ))
        fig2.update_layout(
            title="Predicciones del Modelo vs Realidad (Set de Prueba OOS)",
            xaxis_title="Fecha",
            yaxis_title="Precio USD",
            hovermode="x unified"
        )
        st.plotly_chart(fig2, width='stretch')

        st.subheader("Importancia de los Indicadores (Feature Importance)")
        st.bar_chart(r['importances'])