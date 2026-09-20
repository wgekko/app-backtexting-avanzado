import os
import warnings
import datetime as dt

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from flaml import tune
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

# ============================================================
# FUNCIONES AUXILIARES Y ESTRATEGIA (Sin cambios)
# ============================================================
def SMA(values, n): return pd.Series(values).rolling(int(n)).mean().values

def safe_float(value, default=np.nan):
    try:
        value = float(value)
        return value if np.isfinite(value) else default
    except (TypeError, ValueError): return default

def get_stat(stats, key, default=np.nan):
    try: return safe_float(stats[key], default)
    except Exception: return default

class CrossHold(Strategy):
    fast = 50
    slow = 200
    hold = 126
    stop_loss = 0.0
    take_profit = 0.0

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
                order_kwargs = {}
                if self.stop_loss > 0:
                    order_kwargs["sl"] = self.data.Close[-1] * (1 - self.stop_loss)
                if self.take_profit > 0:
                    order_kwargs["tp"] = self.data.Close[-1] * (1 + self.take_profit)
                self.buy(**order_kwargs)
                self.bars_in_trade = 0

def extract_metrics(stats):
    total_return = get_stat(stats, "Return [%]")
    buy_hold_return = get_stat(stats, "Buy & Hold Return [%]")
    max_dd = get_stat(stats, "Max. Drawdown [%]")
    calmar_proxy = total_return / abs(max_dd) if (np.isfinite(total_return) and np.isfinite(max_dd) and max_dd < 0) else np.nan
    alpha_vs_bh = (total_return - buy_hold_return) if (np.isfinite(total_return) and np.isfinite(buy_hold_return)) else np.nan

    return {
        "Return [%]": total_return, "Buy & Hold Return [%]": buy_hold_return, "Alpha vs B&H [%]": alpha_vs_bh,
        "Sharpe": get_stat(stats, "Sharpe Ratio"), "Sortino": get_stat(stats, "Sortino Ratio"),
        "Max Drawdown [%]": max_dd, "Avg Drawdown [%]": get_stat(stats, "Avg. Drawdown [%]"),
        "Calmar Proxy": calmar_proxy, "Exposure [%]": get_stat(stats, "Exposure Time [%]"),
        "Win Rate [%]": get_stat(stats, "Win Rate [%]"), "Profit Factor": get_stat(stats, "Profit Factor"),
        "# Trades": get_stat(stats, "# Trades"), "Best Trade [%]": get_stat(stats, "Best Trade [%]"),
        "Worst Trade [%]": get_stat(stats, "Worst Trade [%]"), "Expectancy [%]": get_stat(stats, "Expectancy [%]"),
    }

def composite_score(stats):
    sharpe = get_stat(stats, "Sharpe Ratio", 0.0)
    sortino = get_stat(stats, "Sortino Ratio", 0.0)
    ret = get_stat(stats, "Return [%]", 0.0)
    max_dd = get_stat(stats, "Max. Drawdown [%]", 0.0)
    
    if not np.isfinite(sharpe): sharpe = 0.0
    if not np.isfinite(sortino): sortino = 0.0
    if not np.isfinite(ret): ret = 0.0
    if not np.isfinite(max_dd): max_dd = 0.0

    drawdown_penalty = abs(min(max_dd, 0.0))
    score = (0.40 * sharpe + 0.25 * sortino + 0.15 * (ret / 100.0) + 
             0.20 * ((ret / 100.0) / max(drawdown_penalty / 100.0, 0.01)) - 0.005 * drawdown_penalty)
    return float(score)

@st.cache_data(show_spinner=False)
def download_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if data.empty: return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    needed = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in needed if c not in data.columns]
    if missing: return pd.DataFrame()
    data = data[needed].copy().apply(pd.to_numeric, errors="coerce")
    data.dropna(inplace=True)
    return data

def run_backtest(data, fast, slow, hold, stop_loss, take_profit, cash, commission):
    if fast >= slow: return None
    try:
        bt = Backtest(data, CrossHold, cash=float(cash), commission=float(commission), exclusive_orders=True)
        return bt.run(fast=int(fast), slow=int(slow), hold=int(hold), stop_loss=float(stop_loss), take_profit=float(take_profit))
    except Exception: return None

def build_walk_forward_ranges(data_length, train_years=5, test_months=12):
    train_size = int(train_years * 252)
    test_size = int(test_months * 21)
    ranges = []
    start = 0
    while (start + train_size + test_size <= data_length):
        ranges.append({"train_start": start, "train_end": start + train_size, 
                       "test_start": start + train_size, "test_end": start + train_size + test_size})
        start += test_size
    return ranges

def walk_forward_evaluate(data, best_params, train_years, test_months, cash, commission):
    ranges = build_walk_forward_ranges(len(data), train_years=train_years, test_months=test_months)
    rows = []
    for i, r in enumerate(ranges, start=1):
        test_data = data.iloc[r["test_start"]:r["test_end"]].copy()
        if len(test_data) < 20: continue
        stats = run_backtest(test_data, fast=best_params["fast"], slow=best_params["slow"], hold=best_params["hold"], 
                             stop_loss=best_params["stop_loss"], take_profit=best_params["take_profit"], cash=cash, commission=commission)
        if stats is None: continue
        m = extract_metrics(stats)
        rows.append({"Fold": i, "Test Start": test_data.index[0], "Test End": test_data.index[-1], "Return [%]": m["Return [%]"],
                     "Sharpe": m["Sharpe"], "Sortino": m["Sortino"], "Max Drawdown [%]": m["Max Drawdown [%]"],
                     "Win Rate [%]": m["Win Rate [%]"], "# Trades": m["# Trades"]})
    return pd.DataFrame(rows)

# ============================================================
# INTERFAZ Y SIDEBAR
# ============================================================
st.set_page_config(page_title="Quant Backtesting - CFO", page_icon=":material/analytics:", layout="wide")
st.title(":material/analytics: Plataforma Quant - CrossHold + CFO/FLAML")
st.markdown("### Estrategia base\nOptimización multivariable CFO con *Session State*.")

st.sidebar.header("Datos")
ticker = st.sidebar.text_input("Ticker", value="AAPL").upper().strip()
start_date = st.sidebar.date_input("Fecha de inicio", value=pd.to_datetime("2016-01-01"))
end_date = st.sidebar.date_input("Fecha de fin", value=dt.date.today())

st.sidebar.header("Capital y costos")
cash = st.sidebar.number_input("Capital inicial", min_value=1000.0, value=10000.0, step=1000.0)
commission = st.sidebar.number_input("Comisión", min_value=0.0, max_value=0.02, value=0.001, step=0.0001, format="%.4f")

st.sidebar.header("Rango de optimización")
min_fast = st.sidebar.slider("Fast mínimo", 5, 100, 20)
max_fast = st.sidebar.slider("Fast máximo", 20, 150, 80)
min_gap = st.sidebar.slider("Gap mínimo", 20, 100, 60)
max_gap = st.sidebar.slider("Gap máximo", 80, 300, 240)
min_hold = st.sidebar.slider("Hold mínimo", 10, 100, 30)
max_hold = st.sidebar.slider("Hold máximo", 50, 365, 252)

st.sidebar.header("Gestión de riesgo")
use_sl = st.sidebar.checkbox("Optimizar Stop Loss", value=True)
use_tp = st.sidebar.checkbox("Optimizar Take Profit", value=True)
sl_min = st.sidebar.slider("SL mínimo (%)", 1.0, 20.0, 3.0, disabled=not use_sl)
sl_max = st.sidebar.slider("SL máximo (%)", 2.0, 30.0, 15.0, disabled=not use_sl)
tp_min = st.sidebar.slider("TP mínimo (%)", 2.0, 50.0, 5.0, disabled=not use_tp)
tp_max = st.sidebar.slider("TP máximo (%)", 5.0, 100.0, 40.0, disabled=not use_tp)

st.sidebar.header("CFO")
time_budget = st.sidebar.slider("Tiempo CFO (segundos)", 5, 180, 30)
num_samples = st.sidebar.slider("Máximo de evaluaciones", 20, 500, 150)
objective_name = st.sidebar.selectbox("Objetivo CFO", ["Score ajustado por riesgo", "Sharpe", "Sortino", "Retorno"])

st.sidebar.header("Walk-Forward")
run_walk_forward = st.sidebar.checkbox("Ejecutar validación Walk-Forward", value=True)
train_years = st.sidebar.slider("Años de entrenamiento", 2, 10, 5, disabled=not run_walk_forward)
test_months = st.sidebar.slider("Meses de prueba por fold", 3, 24, 12, disabled=not run_walk_forward)

execute = st.sidebar.button("Ejecutar optimización", type="primary")

# Validaciones pre-ejecución
if execute:
    if min_fast >= max_fast or min_gap >= max_gap or min_hold >= max_hold or (use_sl and sl_min >= sl_max) or (use_tp and tp_min >= tp_max):
        st.error("Corrige los rangos de optimización antes de continuar.")
        st.stop()

# ============================================================
# BLOQUE DE EJECUCIÓN (Lógica pesada guardada en Estado)
# ============================================================
if execute:
    with st.spinner(f"Optimizando arquitectura completa para {ticker}..."):
        data = download_data(ticker, start_date, end_date)
        if data.empty or len(data) < max(300, max_gap + max_fast + 20):
            st.error("No hay suficientes datos. Revisa el ticker o amplía el rango.")
            st.stop()

        # Baseline
        baseline_params = {"fast": 50, "slow": 200, "hold": 126, "stop_loss": 0.0, "take_profit": 0.0}
        stats_baseline = run_backtest(data, cash=cash, commission=commission, **baseline_params)
        baseline_metrics = extract_metrics(stats_baseline)

        # Función objetivo CFO
        def objective(config):
            fast = int(config["fast"])
            slow = fast + int(config["gap"])
            hold = int(config["hold"])
            stop_loss = float(config["stop_loss"]) / 100.0 if use_sl else 0.0
            take_profit = float(config["take_profit"]) / 100.0 if use_tp else 0.0

            if slow <= fast: return {"objective": -1e6}
            stats = run_backtest(data=data, fast=fast, slow=slow, hold=hold, stop_loss=stop_loss, take_profit=take_profit, cash=cash, commission=commission)
            
            if stats is None: return {"objective": -1e6}
            trades = get_stat(stats, "# Trades", 0)
            if not np.isfinite(trades) or trades < 3: return {"objective": -1e6}
            
            sharpe, sortino, ret = get_stat(stats, "Sharpe Ratio", 0.0), get_stat(stats, "Sortino Ratio", 0.0), get_stat(stats, "Return [%]", 0.0)
            
            if objective_name == "Sharpe": score = sharpe if np.isfinite(sharpe) else -1e6
            elif objective_name == "Sortino": score = sortino if np.isfinite(sortino) else -1e6
            elif objective_name == "Retorno": score = ret if np.isfinite(ret) else -1e6
            else: 
                score = composite_score(stats)
                if not np.isfinite(score): score = -1e6

            return {"objective": float(score), "sharpe": float(sharpe if np.isfinite(sharpe) else 0.0), "return": float(ret if np.isfinite(ret) else 0.0)}

        search_space = {
            "fast": tune.randint(lower=min_fast, upper=max_fast + 1),
            "gap": tune.randint(lower=min_gap, upper=max_gap + 1),
            "hold": tune.randint(lower=min_hold, upper=max_hold + 1),
            "stop_loss": tune.uniform(lower=float(sl_min), upper=float(sl_max)) if use_sl else tune.choice([0.0]),
            "take_profit": tune.uniform(lower=float(tp_min), upper=float(tp_max)) if use_tp else tune.choice([0.0])
        }

        points = [{"fast": 50, "gap": 150, "hold": 126, "stop_loss": float((sl_min + sl_max) / 2 if use_sl else 0.0), "take_profit": float((tp_min + tp_max) / 2 if use_tp else 0.0)}]

        analysis = tune.run(objective, config=search_space, metric="objective", mode="max", search_alg="CFO", points_to_evaluate=points, time_budget_s=time_budget, num_samples=num_samples, verbose=0)
        best = analysis.best_config
        
        best_params = {
            "fast": int(best["fast"]), "slow": int(best["fast"]) + int(best["gap"]), "hold": int(best["hold"]),
            "stop_loss": float(best["stop_loss"]) / 100.0 if use_sl else 0.0, "take_profit": float(best["take_profit"]) / 100.0 if use_tp else 0.0
        }
        
        stats_opt = run_backtest(data, cash=cash, commission=commission, **best_params)
        opt_metrics = extract_metrics(stats_opt)
        best_objective = safe_float(analysis.best_result.get("objective", np.nan))

        # Heatmap
        heat_rows = []
        for f in sorted(set([max(min_fast, best_params["fast"]-20), best_params["fast"], min(max_fast, best_params["fast"]+20)])):
            for gap in sorted(set([max(min_gap, int(best["gap"])-20), int(best["gap"]), min(max_gap, int(best["gap"])+20)])):
                s = f + gap
                heat_stats = run_backtest(data=data, fast=f, slow=s, hold=best_params["hold"], stop_loss=best_params["stop_loss"], take_profit=best_params["take_profit"], cash=cash, commission=commission)
                if heat_stats is not None:
                    heat_rows.append({"Fast": f, "Gap": gap, "Score": composite_score(heat_stats), "Sharpe": get_stat(heat_stats, "Sharpe Ratio")})
        heat_df = pd.DataFrame(heat_rows)

        # Walk-Forward
        wf_df = walk_forward_evaluate(data, best_params, train_years, test_months, cash, commission) if run_walk_forward else pd.DataFrame()

        # HTML Bokeh Plot
        html_data = ""
        try:
            bt_final = Backtest(data, CrossHold, cash=float(cash), commission=float(commission), exclusive_orders=True)
            bt_final.run(**best_params)
            plot_file = "backtest_plot_cfo.html"
            bt_final.plot(filename=plot_file, open_browser=False)
            with open(plot_file, "r", encoding="utf-8") as f:
                html_data = f.read()
            if os.path.exists(plot_file): os.remove(plot_file)
        except Exception as e:
            st.warning(f"Error generando gráfico de Bokeh: {e}")

        # Curva Comparativa Equity
        eq_df = pd.DataFrame()
        try:
            eq_df = pd.DataFrame({
                "Estrategia CFO": pd.Series(stats_opt["_equity_curve"]["Equity"]).values,
                "Buy & Hold": pd.Series(stats_opt["_equity_curve"]["Buy & Hold"]).values
            }, index=data.index[-len(pd.Series(stats_opt["_equity_curve"]["Equity"])):])
        except Exception: pass

        # Guardar todo en Session State
        st.session_state['f2_data'] = {
            'data_len': len(data), 'current_price': float(data["Close"].iloc[-1]), 'dates': (data.index[0].date(), data.index[-1].date()),
            'total_bh': (data["Close"].iloc[-1] / data["Close"].iloc[0] - 1) * 100,
            'baseline_metrics': baseline_metrics, 'best_params': best_params, 'opt_metrics': opt_metrics,
            'best_objective': best_objective, 'heat_df': heat_df, 'wf_df': wf_df, 'html_data': html_data, 'eq_df': eq_df
        }

# ============================================================
# BLOQUE DE RENDERIZADO (Se dibuja desde el Estado)
# ============================================================
if 'f2_data' in st.session_state:
    res = st.session_state['f2_data']
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precio actual", f"${res['current_price']:,.2f}")
    c2.metric("Observaciones", f"{res['data_len']:,}")
    c3.metric("Buy & Hold", f"{res['total_bh']:.2f}%")
    c4.metric("Período", f"{res['dates'][0]} → {res['dates'][1]}")

    st.subheader("1. Baseline - Golden Cross 50/200")
    b1, b2, b3, b4, b5, b6 = st.columns(6)
    b1.metric("Return", f"{res['baseline_metrics']['Return [%]']:.2f}%")
    b2.metric("Sharpe", f"{res['baseline_metrics']['Sharpe']:.3f}")
    b3.metric("Sortino", f"{res['baseline_metrics']['Sortino']:.3f}")
    b4.metric("Max DD", f"{res['baseline_metrics']['Max Drawdown [%]']:.2f}%")
    b5.metric("Win Rate", f"{res['baseline_metrics']['Win Rate [%]']:.2f}%")
    b6.metric("Trades", f"{res['baseline_metrics']['# Trades']:.0f}")

    st.subheader("2. Optimización CFO & 3. Comparación")
    comparison = pd.DataFrame({"Baseline 50/200": res['baseline_metrics'], "CFO Optimized": res['opt_metrics']})
    st.dataframe(comparison.round(4), width="stretch")

    st.info(f"Objetivo CFO seleccionado: **{objective_name}** | Score: **{res['best_objective']:.4f}**")

    if not res['heat_df'].empty:
        st.subheader("4. Sensibilidad de Fast vs Gap")
        heatmap_df = res['heat_df'].pivot(index="Fast", columns="Gap", values="Sharpe")
        fig_heat = px.imshow(heatmap_df, text_auto=".2f", aspect="auto", title="Sharpe alrededor del óptimo")
        st.plotly_chart(fig_heat, width="stretch")

    if not res['wf_df'].empty:
        st.subheader("5. Validación Walk-Forward")
        wf_display = res['wf_df'].copy()
        wf_display["Test Start"] = wf_display["Test Start"].astype(str)
        wf_display["Test End"] = wf_display["Test End"].astype(str)
        st.dataframe(wf_display.round(4), width="stretch")

    if res['html_data']:
        st.subheader(f"6. Curva de Equity - CFO ({res['best_params']['fast']}/{res['best_params']['slow']})")
        components.html(res['html_data'], height=750, scrolling=True)

    if not res['eq_df'].empty:
        st.subheader("7. Benchmark: Estrategia vs Buy & Hold")
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(x=res['eq_df'].index, y=res['eq_df']["Estrategia CFO"], name="Estrategia CFO", mode="lines"))
        fig_eq.add_trace(go.Scatter(x=res['eq_df'].index, y=res['eq_df']["Buy & Hold"], name="Buy & Hold", mode="lines"))
        fig_eq.update_layout(title="Evolución del capital", hovermode="x unified")
        st.plotly_chart(fig_eq, width="stretch")

elif not execute:
    st.info("Configura los parámetros y pulsa **Ejecutar optimización** para comenzar.")