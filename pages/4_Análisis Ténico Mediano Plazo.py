import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.utils import load_data, remove_weekend_gaps

# -----------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------
st.set_page_config(page_title="Análisis Técnico Largo Plazo", layout="wide", page_icon=":material/finance_mode:")
st.subheader(":material/finance_mode: Panel de Análisis Técnico Avanzado (Daily+)")
st.markdown("Herramientas estructurales para Swing Trading e Inversiones a Largo Plazo.")

# -----------------------------------------
# FUNCIONES DE CÁLCULO E INDICADORES
# -----------------------------------------
def calc_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    df['ATR'] = np.max(ranges, axis=1).rolling(window=period).mean()
    # Cálculo para visualización del Stop Dinámico (Largo)
    df['Stop_Loss'] = df['Close'] - (df['ATR'] * 2) 
    return df

def calc_swing_macd(df, fast_ma=10, slow_ma=20, macd_fast=12, macd_slow=26, macd_sig=9):
    df['EMA_Fast'] = df['Close'].ewm(span=fast_ma, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=slow_ma, adjust=False).mean()
    
    df['MACD'] = df['Close'].ewm(span=macd_fast, adjust=False).mean() - df['Close'].ewm(span=macd_slow, adjust=False).mean()
    df['MACD_Signal'] = df['MACD'].ewm(span=macd_sig, adjust=False).mean()
    
    df['Signal'] = 0
    df.loc[(df['EMA_Fast'] > df['EMA_Slow']) & (df['MACD'] > df['MACD_Signal']), 'Signal'] = 1
    df.loc[(df['EMA_Fast'] < df['EMA_Slow']) & (df['MACD'] < df['MACD_Signal']), 'Signal'] = -1
    df['Position'] = df['Signal'].diff()
    return df

def calc_rsi_bollinger(df, periods=14):
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=periods - 1, adjust=False).mean()
    ema_down = down.ewm(com=periods - 1, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + ema_up / ema_down))
    
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Up'] = df['BB_Mid'] + (df['BB_Std'] * 2)
    df['BB_Low'] = df['BB_Mid'] - (df['BB_Std'] * 2)
    
    # Estandarización de lógica (Estado a Posición)
    buy_cond = (df['RSI'] > 30) & (df['RSI'].shift(1) <= 30) & (df['Close'] < df['BB_Mid'])
    sell_cond = (df['RSI'] < 70) & (df['RSI'].shift(1) >= 70) & (df['Close'] > df['BB_Mid'])
    
    df['Signal'] = np.nan
    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1
    df['Signal'] = df['Signal'].ffill().fillna(0) # Mantiene el régimen
    df['Position'] = df['Signal'].diff()
    return df

def calc_golden_cross(df):
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    df['Signal'] = 0
    df.loc[df['SMA_50'] > df['SMA_200'], 'Signal'] = 1
    df.loc[df['SMA_50'] < df['SMA_200'], 'Signal'] = -1
    df['Position'] = df['Signal'].diff() # Detecta el cruce exacto
    return df

# -----------------------------------------
# BARRA LATERAL (SIDEBAR) PARA CONTROLES
# -----------------------------------------
st.sidebar.header("Parámetros del Sistema")
ticker = st.sidebar.text_input("Activo (ej. AAPL, SPY, BTC-USD, EURUSD=X)", "BTC-USD")
timeframe = st.sidebar.selectbox("Temporalidad", ["1d", "1wk", "1mo"], index=0)
period = st.sidebar.selectbox("Período Histórico", ["1y", "2y", "5y", "10y", "max"], index=2)

strategy = st.sidebar.radio(
    "Modelo de Análisis", 
    ["Inversión Institucional (SMA 50/200)", "Swing Trading (MACD + EMA)", "Extremos de Volatilidad (RSI + Bollinger)"]
)

data = load_data(ticker, timeframe, period)

if data.empty:
    st.error("No se encontraron datos. Verifica el símbolo introducido.")
else:
    data = calc_atr(data.copy())

    if strategy == "Swing Trading (MACD + EMA)":
        df = calc_swing_macd(data)
    elif strategy == "Extremos de Volatilidad (RSI + Bollinger)":
        df = calc_rsi_bollinger(data)
    elif strategy == "Inversión Institucional (SMA 50/200)":
        df = calc_golden_cross(data)

    buy_signals = df[df['Position'] > 0]
    sell_signals = df[df['Position'] < 0]

    # -----------------------------------------
    # MÉTRICAS DE RIESGO Y PRECIO ACTUAL
    # -----------------------------------------
    last_close = df['Close'].iloc[-1]
    last_atr = df['ATR'].iloc[-1]
    price_change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
    pct_change = (price_change / df['Close'].iloc[-2]) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Precio Actual", f"${last_close:.2f}", f"{pct_change:.2f}%")
    col2.metric("ATR (Riesgo/Volatilidad Diario)", f"${last_atr:.2f}", "Rango promedio de mov.")
    col3.metric("Recomendación Stop Loss (2x ATR)", f"${last_close - (last_atr*2):.2f}", "Basado en volatilidad")
    col4.metric("Última Señal de Sistema", "COMPRA" if df['Signal'].iloc[-1] > 0 else "VENTA" if df['Signal'].iloc[-1] < 0 else "NEUTRAL")

    # -----------------------------------------
    # GRAFICACIÓN CON PLOTLY
    # -----------------------------------------
    st.markdown("---")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])

    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'), row=1, col=1)
    
    # Traza para visualizar el Stop Loss Dinámico (2x ATR)
    fig.add_trace(go.Scatter(x=df.index, y=df['Stop_Loss'], line=dict(color='rgba(255, 100, 100, 0.5)', dash='dot', width=1.5), name='Stop Loss (2x ATR)'), row=1, col=1)

    fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Low'] * 0.95, mode='markers', marker=dict(symbol='triangle-up', size=16, color='lime', line=dict(width=2, color='darkgreen')), name='Señal COMPRA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['High'] * 1.05, mode='markers', marker=dict(symbol='triangle-down', size=16, color='red', line=dict(width=2, color='darkred')), name='Señal VENTA'), row=1, col=1)

    if strategy == "Swing Trading (MACD + EMA)":
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_Fast'], line=dict(color='cyan', width=2), name='EMA Rápida'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_Slow'], line=dict(color='magenta', width=2), name='EMA Lenta'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='cyan'), name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='magenta'), name='MACD Señal'), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD'] - df['MACD_Signal'], marker_color='gray', name='Histograma'), row=2, col=1)

    elif strategy == "Extremos de Volatilidad (RSI + Bollinger)":
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Up'], line=dict(color='rgba(200, 200, 200, 0.4)', dash='dash'), name='Bollinger Superior'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='rgba(200, 200, 200, 0.4)', dash='dash'), name='Bollinger Inferior', fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Mid'], line=dict(color='orange', width=1), name='Bollinger Media'), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)

    elif strategy == "Inversión Institucional (SMA 50/200)":
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='yellow', width=2), name='SMA 50'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='white', width=3), name='SMA 200'), row=1, col=1)
        
        vol_colors = np.where(df['Close'] >= df['Open'], 'rgba(0,255,0,0.5)', 'rgba(255,0,0,0.5)')
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=vol_colors, name='Volumen'), row=2, col=1)

    fig = remove_weekend_gaps(fig, df)

    fig.update_layout(height=750, xaxis_rangeslider_visible=False, template='plotly_dark', margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    # Se respeta el argumento especificado
    st.plotly_chart(fig, width='stretch')

    st.subheader("Datos Cuantitativos Recientes")
    st.dataframe(df[['Open', 'High', 'Low', 'Close', 'Volume', 'ATR', 'Signal']].tail(10).sort_index(ascending=False), width='stretch')