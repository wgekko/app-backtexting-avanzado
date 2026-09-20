import streamlit as st
import yfinance as yf
import pandas as pd

@st.cache_data
def load_data(ticker, timeframe, period):
    """Descarga datos de yfinance y corrige el formato MultiIndex."""
    df = yf.download(ticker, period=period, interval=timeframe)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df

def remove_weekend_gaps(fig, df):
    """Elimina los espacios en blanco del eje X para días sin cotización."""
    idx_dates = df.index.strftime('%Y-%m-%d').tolist()
    all_dates = pd.date_range(start=df.index[0], end=df.index[-1]).strftime('%Y-%m-%d').tolist()
    missing_dates = list(set(all_dates) - set(idx_dates))
    fig.update_xaxes(rangebreaks=[dict(values=missing_dates)])
    return fig