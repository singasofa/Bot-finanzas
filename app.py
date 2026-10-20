import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from finvizfinance.quote import finvizfinance

st.set_page_config(page_title="Analizador Híbrido Pro (Finviz)", page_icon="📈", layout="centered")

def calificar(pct):
    if pct >= 75: return "🟢 Excelente"
    elif pct >= 60: return "🟢 Bueno"
    elif pct >= 45: return "🟡 Neutral"
    elif pct >= 30: return "🟠 Precaución"
    else: return "🔴 Riesgoso"

st.title("📈 Analizador Híbrido con Finviz")
st.markdown("Datos técnicos en tiempo real + Fundamentales extraídos de Finviz")

# --- BARRA LATERAL ---
st.sidebar.header("Parámetros")
nombre_o_ticker = st.sidebar.text_input("Activo (Ej: TSLA, AAPL, NVDA)", value="TSLA")
capital_disponible = st.sidebar.number_input("Capital Disponible ($)", value=10000, step=500)
pct_riesgo_max = st.sidebar.slider("Riesgo Máximo por Operación (%)", min_value=0.5, max_value=5.0, value=2.0) / 100.0

if st.sidebar.button("Analizar Activo", type="primary"):
    # Limpiamos el ticker (Finviz y Yahoo usan símbolos directos como TSLA, AAPL, BTC-USD)
    diccionario_seguro = {
        "bitcoin": "BTC-USD", "ethereum": "ETH-USD", "solana": "SOL-USD", "cardano": "ADA-USD",
        "apple": "AAPL", "tesla": "TSLA", "nvidia": "NVDA", "microsoft": "MSFT",
        "amazon": "AMZN", "google": "GOOGL", "meta": "META", "netflix": "NFLX",
        "oro": "GC=F", "sp500": "SPY", "bonos usa": "TLT"
    }
    
    clave = nombre_o_ticker.strip().lower()
    ticker = diccionario_seguro.get(clave, nombre_o_ticker.upper())
    
    with st.spinner(f"Consultando mercados y Finviz para {ticker}..."):
        try:
            # 1. Datos técnicos con yfinance
            activo = yf.Ticker(ticker)
            hist = activo.history(period="1y")
            
            if hist.empty or len(hist) < 60:
                st.error(f"⚠️ No hay suficientes datos históricos para '{nombre_o_ticker}'.")
            else:
                c, h, l, v = hist['Close'], hist['High'], hist['Low'], hist['Volume']
                precio = c.iloc[-1]
                var_1m = ((precio - c.iloc[-20]) / c.iloc[-20]) * 100 if len(c) >= 20 else 0

                # Indicadores técnicos esenciales
                sma20 = c.rolling(20).mean().iloc[-1]
                sma50 = c.rolling(50).mean().iloc[-1] if len(c) >= 50 else sma20
                sma200 = c.rolling(200).mean().iloc[-1] if len(c) >= 200 else sma50
                
                ema12, ema26 = c.ewm(span=12, adjust=False).mean(), c.ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_actual, signal_actual = macd_line.iloc[-1], signal_line.iloc[-1]
                
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
                if macd_actual > signal_actual: score_tech_raw += 2
                if 30 <= rsi <= 65: score_tech_raw += 2
                score_tech_pct = (score_tech_raw / 10) * 100

                # 2. Extracción de Fundamentales desde Finviz (si es una acción normal tipo TSLA, AAPL, etc.)
                es_accion = "-" in ticker or "=" in ticker == False # Filtramos criptos o futuros
                fundamentales_finviz = {}
                
                try:
                    # Intentamos extraer datos de Finviz solo si parece una acción (sin guiones raros)
                    if "-" not in ticker and "=" not in ticker:
                        stock_finviz = finvizfinance(ticker)
                        fundamentales_finviz = stock_finviz.ticker_fundament()
                        es_accion = True
                except:
                    es_accion = False

                score_fund_pct = 50.0
                if es_accion and fundamentales_finviz:
                    # Evaluamos métricas rápidas desde Finviz
                    puntos_fund = 0
                    try:
                        pe_val = float(fundamentales_finviz.get('P/E', 0) or 0)
                        if 0 < pe_val < 25: puntos_fund += 1
                    except: pass
                    score_fund_pct = (puntos_fund / 1) * 100 if puntos_fund > 0 else 50.0

                score_global_pct = (score_tech_pct * 0.5) + (score_fund_pct * 0.5)

                # --- INTERFAZ VISUAL EN LA APP MÓVIL ---
                st.subheader(f"Resultados para: {ticker}")
                
                col1, col2 = st.columns(2)
                col1.metric("Precio Actual", f"${precio:,.2f}", f"{var_1m:+.2f}%")
                col2.metric("Índice Global", f"{score_global_pct:.1f}%", calificar(score_global_pct))

                st.divider()

                # Gráfico interactivo limpio
                st.line_chart(c.tail(120))

                # --- PANEL FUNDAMENTAL ESTILO FINVIZ ---
                with st.expander("📊 Panel Fundamental (Directo de Finviz)", expanded=True):
                    if es_accion and fundamentales_finviz:
                        # Mostramos los datos clave en columnas o lista organizada
                        st.write(f"• **P/E (PER):** {fundamentales_finviz.get('P/E', 'N/D')}")
                        st.write(f"• **Forward P/E:** {fundamentales_finviz.get('Forward P/E', 'N/D')}")
                        st.write(f"• **PEG:** {fundamentales_finviz.get('PEG', 'N/D')}")
                        st.write(f"• **EPS (ttm):** {fundamentales_finviz.get('EPS (ttm)', 'N/D')}")
                        st.write(f"• **Dividend Yield:** {fundamentales_finviz.get('Dividend', 'N/D')}")
                        st.write(f"• **Profit Margin:** {fundamentales_finviz.get('Profit Margin', 'N/D')}")
                        st.write(f"• **ROE:** {fundamentales_finviz.get('ROE', 'N/D')}")
                        st.write(f"• **ROA:** {fundamentales_finviz.get('ROA', 'N/D')}")
                        st.write(f"• **Deuda / Capital (Debt/Eq):** {fundamentales_finviz.get('Debt/Eq', 'N/D')}")
                        st.write(f"• **Recomendación (Analistas):** {fundamentales_finviz.get('Recom', 'N/D')}")
                    else:
                        st.info("ℹ️ Los ratios de Finviz aplican principalmente para acciones bursátiles (ej: TSLA, AAPL, MSFT).")

                # --- PLAN DE GESTIÓN DE RIESGO ---
                with st.expander("🛡️ Plan de Riesgo y Operativa"):
                    stop_loss = precio - (1.5 * atr)
                    take_profit = precio + (2.5 * atr)
                    riesgo = precio - stop_loss
                    beneficio = take_profit - precio
                    ratio_rb = beneficio / riesgo if riesgo > 0 else 0

                    capital_a_riesgo = capital_disponible * pct_riesgo_max
                    unidades_a_comprar = capital_a_riesgo / riesgo if riesgo > 0 else 0
                    inversion_total = unidades_a_comprar * precio

                    st.write(f"🛑 **Stop Loss:** ${stop_loss:,.2f}")
                    st.write(f"🎯 **Take Profit:** ${take_profit:,.2f}")
                    st.success(f"📦 **Unidades a Comprar:** {unidades_a_comprar:,.2f}")
                    st.info(f"💵 **Inversión Total:** ${inversion_total:,.2f} (Ratio R/B: 1:{ratio_rb:.2f})")

        except Exception as e:
            st.error(f"⚠️ Ocurrió un error al conectar con Finviz o procesar el activo: {e}")
