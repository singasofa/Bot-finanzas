import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Analizador Híbrido", page_icon="📈", layout="centered")

def calificar(pct):
    if pct >= 75: return "🟢 Excelente"
    elif pct >= 60: return "🟢 Bueno"
    elif pct >= 45: return "🟡 Neutral"
    elif pct >= 30: return "🟠 Precaución"
    else: return "🔴 Riesgoso"

st.title("📈 Analizador Híbrido de Activos")
st.markdown("Evaluación técnica, fundamental y gestión de riesgo en tiempo real.")

st.sidebar.header("Parámetros")
nombre_o_ticker = st.sidebar.text_input("Activo (Ej: Tesla, Bitcoin, AAPL)", value="Tesla")
capital_disponible = st.sidebar.number_input("Capital ($)", value=10000, step=500)
pct_riesgo_max = st.sidebar.slider("Riesgo Máx (%)", min_value=0.5, max_value=5.0, value=2.0) / 100.0

if st.sidebar.button("Analizar Activo", type="primary"):
    diccionario_seguro = {
        "bitcoin": "BTC-USD", "ethereum": "ETH-USD", "solana": "SOL-USD", "cardano": "ADA-USD",
        "apple": "AAPL", "tesla": "TSLA", "nvidia": "NVDA", "microsoft": "MSFT",
        "amazon": "AMZN", "google": "GOOGL", "meta": "META", "netflix": "NFLX",
        "oro": "GC=F", "sp500": "SPY", "bonos usa": "TLT"
    }
    
    clave = nombre_o_ticker.strip().lower()
    ticker = diccionario_seguro.get(clave, nombre_o_ticker.upper())
    
    with st.spinner(f"Analizando {ticker}..."):
        try:
            activo = yf.Ticker(ticker)
            hist = activo.history(period="1y")
            
            if hist.empty or len(hist) < 60:
                st.error(f"⚠️ No hay suficientes datos para '{nombre_o_ticker}'.")
            else:
                c, h, l, v = hist['Close'], hist['High'], hist['Low'], hist['Volume']
                precio = c.iloc[-1]
                var_1m = ((precio - c.iloc[-20]) / c.iloc[-20]) * 100 if len(c) >= 20 else 0

                info = {}
                es_accion = False
                try:
                    info = activo.info
                    if 'marketCap' in info and info['marketCap'] is not None:
                        es_accion = True
                except:
                    pass

                sma20 = c.rolling(20).mean().iloc[-1]
                sma50 = c.rolling(50).mean().iloc[-1] if len(c) >= 50 else sma20
                sma200 = c.rolling(200).mean().iloc[-1] if len(c) >= 200 else sma50
                
                ema12, ema26 = c.ewm(span=12, adjust=False).mean(), c.ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                
                delta = c.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi_series = 100 - (100 / (1 + (gain / loss)))
                rsi = rsi_series.iloc[-1] if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1]) else 50
                
                high_low, high_close, low_close = h - l, np.abs(h - c.shift()), np.abs(l - c.shift())
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = true_range.rolling(14).mean().iloc[-1]
                
                score_tech_raw = 0
                if precio > sma20: score_tech_raw += 1
                if precio > sma50: score_tech_raw += 2
                if precio > sma200: score_tech_raw += 2
                if macd_line.iloc[-1] > signal_line.iloc[-1]: score_tech_raw += 2
                if 30 <= rsi <= 65: score_tech_raw += 2
                score_tech_pct = (score_tech_raw / 10) * 100

                score_fund_pct = 50.0
                if es_accion:
                    puntos_fund = 0
                    pe = info.get('trailingPE', 0)
                    roe = info.get('returnOnEquity', 0)
                    if pe and 0 < pe < 25: puntos_fund += 1
                    if roe and (roe * 100) > 15: puntos_fund += 1
                    score_fund_pct = (puntos_fund / 2) * 100

                score_global_pct = (score_tech_pct * 0.5) + (score_fund_pct * 0.5)

                st.subheader(f"Resultados: {ticker}")
                col1, col2 = st.columns(2)
                col1.metric("Precio Actual", f"${precio:,.2f}", f"{var_1m:+.2f}%")
                col2.metric("Índice Global", f"{score_global_pct:.1f}%", calificar(score_global_pct))

                st.divider()

                tab1, tab2, tab3 = st.tabs(["📊 Gráfico y Salud", "⚙️ Técnico", "🛡️ Plan de Riesgo"])

                with tab1:
                    st.write(f"• **Salud Técnica:** {score_tech_pct:.1f}% -> {calificar(score_tech_pct)}")
                    st.write(f"• **Salud Fundamental:** {score_fund_pct:.1f}% -> {calificar(score_fund_pct)}")
                    st.line_chart(c.tail(100))

                with tab2:
                    st.write(f"• **RSI (14):** {rsi:.1f}")
                    st.write(f"• **SMA 50:** ${sma50:,.2f}")
                    st.write(f"• **SMA 200:** ${sma200:,.2f}")
                    st.write(f"• **ATR (Volatilidad):** ${atr:.2f}")

                with tab3:
                    stop_loss = precio - (1.5 * atr)
                    take_profit = precio + (2.5 * atr)
                    riesgo = precio - stop_loss
                    capital_a_riesgo = capital_disponible * pct_riesgo_max
                    unidades = capital_a_riesgo / riesgo if riesgo > 0 else 0
                    inversion_total = unidades * precio

                    st.success(f"**Unidades a comprar:** {unidades:,.2f}")
                    st.info(f"**Inversión Total:** ${inversion_total:,.2f}")
                    st.write(f"🛑 **Stop Loss:** ${stop_loss:,.2f}")
                    st.write(f"🎯 **Take Profit:** ${take_profit:,.2f}")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
