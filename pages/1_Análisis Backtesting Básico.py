import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from flaml import tune
import streamlit.components.v1 as components
import os

from ta.trend import sma_indicator, ema_indicator, MACD
from ta.momentum import rsi, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
import statsmodels.api as sm
import plotly.express as px

st.set_page_config(page_title="Plataforma Quant Avanzada", layout="wide", page_icon=":material/finance_mode:")
st.subheader(":material/finance_mode: Plataforma Quant: Backtesting & Machine Learning con Osciladores Optimizados por CFO")

tab1, tab2 = st.tabs([":material/analytics: Crossover", ":material/bar_chart_4_bars: ML con Indicadores y Estocástico"])

# =====================================================================
# PESTAÑA 1: FLAML & BACKTESTING DE CRUCE DE MEDIAS
# =====================================================================
with tab1:
    st.markdown("### Optimización de Golden Cross usando CFO y FLAML")
    
    def SMA(values, n):
        return pd.Series(values).rolling(n).mean()

    class CrossHold(Strategy):
        fast = 50   
        slow = 200  
        hold = 126  
        
        def init(self):
            self.fast_ma = self.I(SMA, self.data.Close, self.fast)
            self.slow_ma = self.I(SMA, self.data.Close, self.slow)
            self.bars_in_trade = 0
            
        def next(self):
            if self.position:
                self.bars_in_trade += 1
                if self.bars_in_trade >= self.hold:
                    self.position.close()
                    self.bars_in_trade = 0
            else:
                if crossover(self.fast_ma, self.slow_ma):
                    self.buy()
                    self.bars_in_trade = 0

    col1_t1, col2_t1 = st.columns([1, 3])
    with col1_t1:
        ticker_1 = st.text_input("Ticker", value="AAPL", key="t1")
        start_date_1 = st.date_input("Fecha Inicio", value=pd.to_datetime("2016-01-01"), key="d1")
        hold_days = st.number_input("Días de retención", min_value=10, max_value=252, value=126)
        time_budget_1 = st.slider("Tiempo CFO Backtest (seg)", 1, 60, 10, key="b1")
        run_opt_1 = st.button("Ejecutar Optimización Backtest")
        
    with col2_t1:
        if run_opt_1:
            with st.spinner(f"Optimizando backtest para {ticker_1}..."):
                try:
                    data_1 = yf.download(ticker_1, start=start_date_1)
                    if isinstance(data_1.columns, pd.MultiIndex):
                        data_1.columns = [c[0] for c in data_1.columns]
                    data_1.dropna(inplace=True)
                    
                    bt = Backtest(data_1, CrossHold, cash=10000, commission=0.0)
                    stats_base = bt.run(fast=50, slow=200, hold=hold_days)
                    
                    def objective_bt(config):
                        f = config['fast']
                        s = f + config['gap']
                        stats = bt.run(fast=f, slow=s, hold=hold_days)
                        sharpe = stats['Sharpe Ratio']
                        return {"sharpe": sharpe if not pd.isna(sharpe) else 0.0}

                    search_space_bt = {
                        'fast': tune.randint(lower=20, upper=80),
                        'gap': tune.randint(lower=60, upper=240)
                    }
                    
                    analysis = tune.run(
                        objective_bt,
                        config=search_space_bt,
                        metric="sharpe",
                        mode="max",
                        search_alg="CFO",
                        points_to_evaluate=[{'fast': 50, 'gap': 150}],
                        time_budget_s=time_budget_1,
                        num_samples=100,
                        verbose=0
                    )
                    
                    best_f = analysis.best_config['fast']
                    best_s = best_f + analysis.best_config['gap']
                    best_sharpe = analysis.best_result['sharpe']
                    stats_opt = bt.run(fast=best_f, slow=best_s, hold=hold_days)
                    
                    # Generar HTML del gráfico
                    plot_file = "backtest_plot.html"
                    bt.plot(filename=plot_file, open_browser=False)
                    with open(plot_file, "r", encoding='utf-8') as f:
                        html_data = f.read()
                    if os.path.exists(plot_file):
                        os.remove(plot_file)

                    # Guardar en session_state para persistencia
                    st.session_state['res_t1'] = {
                        'stats_base': stats_base,
                        'best_f': best_f,
                        'best_s': best_s,
                        'best_sharpe': best_sharpe,
                        'stats_opt': stats_opt,
                        'html_data': html_data
                    }
                except Exception as e:
                    st.error(f"Error durante la ejecución del Backtest: {e}")

        # Renderizado de resultados desde session_state
        if 'res_t1' in st.session_state:
            res = st.session_state['res_t1']
            
            col1, col2, col3 = st.columns(3)
            col1.info("LÍNEA BASE (MA 50 / 200)")
            col1.metric("Retorno (%) Baseline", f"{res['stats_base']['Return [%]']:.2f}%")
            col1.metric("Sharpe Ratio Baseline", f"{res['stats_base']['Sharpe Ratio']:.3f}")
            
            col2.success("RESULTADO ÓPTIMO CFO")
            col2.metric(label="Mejores Medias", value=f"{res['best_f']} / {res['best_s']}")
            col2.metric(label="Sharpe Optimizado", value=f"{res['best_sharpe']:.3f}", delta=f"{res['best_sharpe'] - res['stats_base']['Sharpe Ratio']:.3f}")
            col2.metric(label="Retorno Optimizado", value=f"{res['stats_opt']['Return [%]']:.2f}%", delta=f"{res['stats_opt']['Return [%]'] - res['stats_base']['Return [%]']:.2f}%")

            st.markdown("---")
            st.subheader(f":material/checkbook: Reporte de la Estrategia Optimizada ({res['best_f']} / {res['best_s']})")
            st.dataframe(res['stats_opt'].to_frame(name="Valor del Indicador"), height=400)
            st.markdown("---")
            
            st.subheader("Curva de Equidad y Transacciones (Estrategia Óptima)")
            components.html(res['html_data'], height=700, scrolling=True)

# =====================================================================
# PESTAÑA 2: ML + CFO + ESTOCÁSTICO
# =====================================================================
with tab2:
    st.markdown("### Optimización de SMA, RSI y Estocástico con CFO para Machine Learning")
    
    col1_t2, col2_t2 = st.columns([1, 3])
    with col1_t2:
        ticker_2 = st.text_input("Ticker", value="NVDA", key="t2")
        start_date_2 = st.date_input("Fecha Inicio", value=pd.to_datetime("2022-01-01"), key="d2")
        window_size = st.number_input("Ventana de Entrenamiento OLS", min_value=5, max_value=60, value=20)
        time_budget_2 = st.slider("Tiempo CFO ML (seg)", 5, 60, 15, key="b2")
        run_opt_2 = st.button("Optimizar Indicadores y Estocástico")

    with col2_t2:
        if run_opt_2:
            with st.spinner(f"Optimizando periodos para {ticker_2} con CFO..."):
                try:
                    data_2 = yf.download(ticker_2, start=start_date_2)
                    if isinstance(data_2.columns, pd.MultiIndex):
                        data_2.columns = [c[0] for c in data_2.columns]
                    
                    target_close = data_2['Close'].copy()
                    data_shifted = data_2.shift(1)
                    
                    def ml_objective(config):
                        sma_p = int(config['sma_period'])
                        rsi_p = int(config['rsi_period'])
                        stoch_p = int(config['stoch_period'])
                        
                        df_calc = data_shifted.copy()
                        df_calc['SMA'] = sma_indicator(df_calc['Close'], window=sma_p)
                        df_calc['RSI'] = rsi(df_calc['Close'], window=rsi_p)
                        
                        stoch = StochasticOscillator(
                            high=df_calc['High'], low=df_calc['Low'], close=df_calc['Close'], window=stoch_p
                        )
                        df_calc['STOCH'] = stoch.stoch()
                        
                        df = pd.concat([target_close.rename("Target_Close"), df_calc], axis=1).dropna()
                        if len(df) <= window_size: return {"mae": 999.0}
                            
                        errors = []
                        step_size = max(1, (len(df) - window_size) // 30)
                        for i in range(0, len(df) - window_size, step_size):
                            train_data = df.iloc[i : i + window_size]
                            test_data = df.iloc[i + window_size : i + window_size + 1]
                            
                            actual = test_data['Target_Close'].values[0]
                            X_train = sm.add_constant(train_data['SMA'])
                            y_train = train_data['Target_Close']
                            
                            try:
                                model = sm.OLS(y_train, X_train).fit()
                                X_test = sm.add_constant(test_data['SMA'], has_constant='add')
                                if len(X_test.columns) == 1: X_test.insert(0, 'const', 1.0)
                                pred = model.predict(X_test).values[0]
                                errors.append(abs(actual - pred))
                            except (ValueError, sm.tools.sm_exceptions.PerfectCollinearity):
                                errors.append(999.0)
                                
                        return {"mae": np.mean(errors)}

                    search_space_ml = {
                        'sma_period': tune.randint(lower=5, upper=50),
                        'rsi_period': tune.randint(lower=5, upper=50),
                        'stoch_period': tune.randint(lower=5, upper=50)
                    }
                    
                    analysis_ml = tune.run(
                        ml_objective, config=search_space_ml, metric="mae", mode="min", search_alg="CFO",
                        points_to_evaluate=[{'sma_period': 14, 'rsi_period': 14, 'stoch_period': 14}],
                        time_budget_s=time_budget_2, num_samples=50, verbose=0
                    )
                    
                    best_sma = int(analysis_ml.best_config['sma_period'])
                    best_rsi = int(analysis_ml.best_config['rsi_period'])
                    best_stoch = int(analysis_ml.best_config['stoch_period'])
                    best_mae = analysis_ml.best_result['mae']
                    
                    df_final = data_shifted.copy()
                    df_final['SMA_Opt'] = sma_indicator(df_final['Close'], window=best_sma)
                    df_final['RSI_Opt'] = rsi(df_final['Close'], window=best_rsi)
                    
                    stoch_final = StochasticOscillator(high=df_final['High'], low=df_final['Low'], close=df_final['Close'], window=best_stoch)
                    df_final['STOCH_Opt'] = stoch_final.stoch()
                    
                    df_final = pd.concat([target_close.rename("Target_Close"), df_final], axis=1).dropna()
                    
                    results = []
                    for i in range(len(df_final) - window_size):
                        train_data = df_final.iloc[i : i + window_size]
                        test_data = df_final.iloc[i + window_size : i + window_size + 1]
                        actual = test_data['Target_Close'].values[0]
                        date = test_data.index[0]
                        
                        for feat in ['Close', 'SMA_Opt', 'RSI_Opt', 'STOCH_Opt']:
                            X_tr = sm.add_constant(train_data[feat])
                            y_tr = train_data['Target_Close']
                            mod = sm.OLS(y_tr, X_tr).fit()
                            
                            X_te = sm.add_constant(test_data[feat], has_constant='add')
                            if len(X_te.columns) == 1: X_te.insert(0, 'const', 1.0)
                            pr = mod.predict(X_te).values[0]
                            
                            results.append({'Date': date, 'Feature': feat, 'Absolute_Error': abs(actual - pr)})
                    
                    # Persistir resultados ML
                    st.session_state['res_t2'] = {
                        'best_sma': best_sma, 'best_rsi': best_rsi, 'best_stoch': best_stoch,
                        'best_mae': best_mae, 'results_df': pd.DataFrame(results), 'ticker': ticker_2
                    }
                except Exception as e:
                    st.error(f"Error en Optimización ML: {e}")

        # Renderizar resultados de ML
        if 'res_t2' in st.session_state:
            r2 = st.session_state['res_t2']
            st.success("¡Optimización completada exitosamente!")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("SMA Óptimo", r2['best_sma'])
            col_m2.metric("RSI Óptimo", r2['best_rsi'])
            col_m3.metric("Estocástico Óptimo", r2['best_stoch'])
            col_m4.metric("MAE Mínimo", f"${r2['best_mae']:.2f}")
            
            # st.subheader("Evolución del Error con Indicadores y Estocástico Optimizados")
            # fig = px.line(r2['results_df'], x='Date', y='Absolute_Error', color='Feature', 
            #               title=f"Error Absoluto con Parámetros CFO ({r2['ticker']})")
            # st.plotly_chart(fig, width='stretch')
            st.subheader("Evolución del Error con Indicadores y Estocástico Optimizados")
            
            # Definir un mapa de colores de alto contraste para el fondo oscuro
            colores_personalizados = {
                'Close': '#FF4B4B',      # Rojo vibrante
                'SMA_Opt': '#00FFFF',    # Cyan brillante
                'RSI_Opt': '#7EE8FA',    # Azul claro / Celeste
                'STOCH_Opt': '#39FF14'   # Verde Neón
            }
            
            fig = px.line(
                r2['results_df'], 
                x='Date', 
                y='Absolute_Error', 
                color='Feature',
                color_discrete_map=colores_personalizados,
                title=f"Error Absoluto con Parámetros CFO ({r2['ticker']})"
            )
            
            # Opcional: mejorar el diseño general del gráfico para mayor claridad
            fig.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Error Absoluto",
                legend_title="Indicador",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, width='stretch')