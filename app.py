import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from finvizfinance.quote import finvizfinance

st.set_page_config(page_title="Informe Híbrido Definitivo", page_icon="📈", layout="centered")

def calificar(pct):
    if pct >= 75: return "🟢 Excelente"
    elif pct >= 60: return "🟢 Bueno"
    elif pct >= 45: return "🟡 Neutral"
    elif pct >= 30: return "🟠 Precaución"
    else: return "🔴 Riesgoso"

# Función auxiliar para convertir valores de Finviz a números limpios
def parse_finviz_val(val_str):
    if not val_str or val_str == '-' or val_str == 'N/A':
        return None
    try:
        clean_str = val_str.replace('%', '').replace(',', '').strip()
        return float(clean_str)
    except:
        return None

st.title("📈 Informe Híbrido Definitivo")
st.markdown("**15 Indicadores Técnicos + 20 Ratios (Finviz) + Evaluación y Gestión de Riesgo**")

# --- BARRA LATERAL ---
st.sidebar.header("Parámetros")
nombre_o_ticker = st.sidebar.text_input("Activo (Ej: Tesla, AAPL, NVDA)", value="Tesla")
capital_disponible = st.sidebar.number_input("Capital Disponible ($)", value=10000, step=500)
pct_riesgo_max = st.sidebar.slider("Riesgo Máximo por Operación (%)", min_value=0.5, max_value=5.0, value=2.0) / 100.0

if st.sidebar.button("Analizar Activo", type="primary"):
    diccionario_seguro = {
        "bitcoin": "BTC-USD", "ethereum": "ETH-USD", "solana": "SOL-USD", "cardano": "ADA-USD",
        "apple": "AAPL", "tesla": "TSLA", "nvidia": "NVDA", "microsoft": "MSFT",
        "amazon": "AMZN", "google": "GOOGL", "meta": "META", "netflix": "NFLX",
        "oro": "GC=F", "sp500": "SPY", "bonos usa": "TLT"
    }
    
    clave = nombre_o_ticker.strip().lower()
    ticker = diccionario_seguro.get(clave, nombre_o_ticker.upper())
    
    with st.spinner(f"Analizando datos técnicos y de Finviz para {ticker}..."):
        try:
            # -------------------------------------------------------------
            # 1. OBTENCIÓN Y CÁLCULO DE DATOS TÉCNICOS (YFINANCE)
            # -------------------------------------------------------------
            activo = yf.Ticker(ticker)
            hist = activo.history(period="1y")
            
            if hist.empty or len(hist) < 60:
                st.error(f"⚠️ No se encontraron suficientes datos históricos para '{nombre_o_ticker}'. Pruebe con el ticker exacto (ej: AAPL).")
            else:
                c, h, l, v = hist['Close'], hist['High'], hist['Low'], hist['Volume']
                precio = c.iloc[-1]
                var_1m = ((precio - c.iloc[-20]) / c.iloc[-20]) * 100 if len(c) >= 20 else 0

                # Cálculo de los 15 Indicadores Técnicos
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
                
                bb_mid = c.rolling(20).mean()
                bb_std = c.rolling(20).std()
                bb_upper = (bb_mid + (bb_std * 2)).iloc[-1]
                bb_lower = (bb_mid - (bb_std * 2)).iloc[-1]
                bb_middle = bb_mid.iloc[-1]
                
                low14, high14 = l.rolling(14).min(), h.rolling(14).max()
                stoch_k_series = ((c - low14) / (high14 - low14) * 100)
                stoch_k = stoch_k_series.iloc[-1] if not stoch_k_series.empty and not pd.isna(stoch_k_series.iloc[-1]) else 50
                
                high_low, high_close, low_close = h - l, np.abs(h - c.shift()), np.abs(l - c.shift())
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = true_range.rolling(14).mean().iloc[-1]
                
                roc = ((c - c.shift(10)) / c.shift(10) * 100).iloc[-1]
                vol_medio = v.rolling(20).mean().iloc[-1] if not v.empty else 1
                vol_ratio = (v.iloc[-1] / vol_medio) if vol_medio > 0 else 1.0
                donchian_high = h.rolling(20).max().iloc[-1]
                dist_sma50 = ((precio - sma50) / sma50) * 100

                # -------------------------------------------------------------
                # 2. OBTENCIÓN DE FUNDAMENTALES DE FINVIZ
                # -------------------------------------------------------------
                es_accion = False
                fv_data = {}
                try:
                    if "-" not in ticker and "=" not in ticker:
                        stock_fv = finvizfinance(ticker)
                        fv_data = stock_fv.ticker_fundament()
                        if fv_data and 'Market Cap' in fv_data:
                            es_accion = True
                except:
                    es_accion = False

                # Extracción de los 20 ratios traducidos desde Finviz
                pe_ratio = fv_data.get('P/E', 'N/D')
                forward_pe = fv_data.get('Forward P/E', 'N/D')
                peg_ratio = fv_data.get('PEG', 'N/D')
                pb_ratio = fv_data.get('P/B', 'N/D')
                ps_ratio = fv_data.get('P/S', 'N/D')
                ev_to_ebitda = fv_data.get('EV/EBITDA', 'N/D')
                ev_to_rev = fv_data.get('P/C', 'N/D') # Alternativa de liquidez/ventas
                
                roe = fv_data.get('ROE', 'N/D')
                roa = fv_data.get('ROA', 'N/D')
                roic = fv_data.get('ROI', 'N/D')
                
                gross_margins = fv_data.get('Gross Margin', 'N/D')
                operating_margins = fv_data.get('Oper. Margin', 'N/D')
                profit_margins = fv_data.get('Profit Margin', 'N/D')
                
                debt_to_equity = fv_data.get('Debt/Eq', 'N/D')
                current_ratio = fv_data.get('Current Ratio', 'N/D')
                quick_ratio = fv_data.get('Quick Ratio', 'N/D')
                
                dividend_yield = fv_data.get('Dividend %', fv_data.get('Dividend', 'N/D'))
                payout_ratio = fv_data.get('Payout', 'N/D')
                revenue_growth = fv_data.get('Sales Q/Q', 'N/D')
                earnings_growth = fv_data.get('EPS Q/Q', 'N/D')

                # -------------------------------------------------------------
                # 3. EVALUACIÓN DE PUNTUACIONES Y FACTORES CLAVE
                # -------------------------------------------------------------
                score_tech_raw = 0
                razones_tecnicas = []
                
                if precio > sma20: score_tech_raw += 1
                if precio > sma50: score_tech_raw += 2; razones_tecnicas.append("Precio por encima de la media de 50 sesiones (Tendencia media alcista)")
                if precio > sma200: score_tech_raw += 2; razones_tecnicas.append("Estructura de largo plazo alcista (Precio > SMA200)")
                if macd_actual > signal_actual: score_tech_raw += 2; razones_tecnicas.append("Cruce y momento alcista en el MACD")
                if 30 <= rsi <= 65: score_tech_raw += 2; razones_tecnicas.append(f"RSI en zona óptima y saludable ({rsi:.1f})")
                if stoch_k < 80: score_tech_raw += 1
                if roc > 0: score_tech_raw += 1; razones_tecnicas.append("Tasa de cambio de precio positiva (ROC)")

                score_tech_pct = (score_tech_raw / 11) * 100

                score_fund_pct = 50.0
                razones_fundamentales = []

                if es_accion:
                    puntos_fund = 0
                    max_puntos_fund = 5
                    
                    pe_val = parse_finviz_val(pe_ratio)
                    roe_val = parse_finviz_val(roe)
                    cr_val = parse_finviz_val(current_ratio)
                    de_val = parse_finviz_val(debt_to_equity)
                    pm_val = parse_finviz_val(profit_margins)
                    
                    if pe_val and 0 < pe_val < 25:
                        puntos_fund += 1; razones_fundamentales.append(f"PER atractivo y razonable en Finviz ({pe_val:.2f})")
                    if roe_val and roe_val > 15:
                        puntos_fund += 1; razones_fundamentales.append(f"Alta rentabilidad para el accionista (ROE > 15%)")
                    if cr_val and cr_val > 1.2:
                        puntos_fund += 1; razones_fundamentales.append(f"Buena liquidez a corto plazo (Current Ratio > 1.2)")
                    if de_val and de_val < 1.0: # En Finviz 1.0 = 100%
                        puntos_fund += 1; razones_fundamentales.append(f"Estructura de deuda saludable (Debt/Eq < 1.0)")
                    if pm_val and pm_val > 10:
                        puntos_fund += 1; razones_fundamentales.append(f"Márgenes netos sólidos (> 10%)")
                        
                    score_fund_pct = (puntos_fund / max_puntos_fund) * 100
                else:
                    razones_fundamentales.append("Sin métricas fundamentales aplicables (Cripto / Índice / Materia Prima)")

                score_global_pct = (score_tech_pct * 0.5) + (score_fund_pct * 0.5)

                # -------------------------------------------------------------
                # 4. PRESENTACIÓN DE RESULTADOS EN LA APP MÓVIL
                # -------------------------------------------------------------
                st.subheader(f"INFORME DEFINITIVO: {nombre_o_ticker.upper()} ({ticker})")
                
                col1, col2 = st.columns(2)
                col1.metric("Precio Actual", f"${precio:,.2f}", f"{var_1m:+.2f}% (1M)")
                col2.metric("Índice Global", f"{score_global_pct:.1f}%", calificar(score_global_pct))

                st.divider()

                st.write(f"📊 **Salud Técnica:** {score_tech_pct:.1f}% -> {calificar(score_tech_pct)}")
                st.write(f"📈 **Salud Fundamental:** {score_fund_pct:.1f}% -> {calificar(score_fund_pct)}")

                st.line_chart(c.tail(120))

                # --- PESTAÑA 1: 15 TÉCNICOS DETALLADOS ---
                with st.expander("🔍 Ver los 15 Indicadores Técnicos Detallados"):
                    st.write(f"1. **RSI (14):** {rsi:.1f} {'(Sobrecompra)' if rsi>70 else ('(Sobreventa)' if rsi<30 else '(Saludable)')}")
                    st.write(f"2. **SMA Corto (20):** ${sma20:,.2f} {'(Alcista)' if precio>sma20 else '(Bajista)'}")
                    st.write(f"3. **SMA Medio (50):** ${sma50:,.2f} {'(Alcista)' if precio>sma50 else '(Bajista)'}")
                    st.write(f"4. **SMA Largo (200):** ${sma200:,.2f} {'(Alcista)' if precio>sma200 else '(Bajista)'}")
                    st.write(f"5. **MACD Line:** {macd_actual:.2f}")
                    st.write(f"6. **MACD Señal:** {signal_actual:.2f} {'(Momento Alcista)' if macd_actual>signal_actual else '(Momento Bajista)'}")
                    st.write(f"7. **Bollinger Superior:** ${bb_upper:,.2f}")
                    st.write(f"8. **Bollinger Media:** ${bb_middle:,.2f}")
                    st.write(f"9. **Bollinger Inferior (Soporte):** ${bb_lower:,.2f}")
                    st.write(f"10. **Estocástico (%K):** {stoch_k:.1f} {'(Sobrecompra)' if stoch_k>80 else ('(Sobreventa)' if stoch_k<20 else '(Neutro)')}")
                    st.write(f"11. **ATR (Volatilidad):** ${atr:.2f}")
                    st.write(f"12. **ROC (Momento 10d):** {roc:+.2f}%")
                    st.write(f"13. **Ratio de Volumen:** {vol_ratio:.2f}x {'(Alto Volumen)' if vol_ratio>1.5 else '(Normal)'}")
                    st.write(f"14. **Canal Donchian Máx (Resistencia):** ${donchian_high:,.2f}")
                    st.write(f"15. **Posición vs SMA 50:** {dist_sma50:+.2f}%")

                # --- PESTAÑA 2: 20 RATIOS FUNDAMENTALES (FINVIZ) ---
                with st.expander("📊 Ver los 20 Ratios Fundamentales (Finviz)"):
                    if es_accion:
                        st.write(f"1. **PER (Trailing P/E):** {pe_ratio}")
                        st.write(f"2. **Forward P/E:** {forward_pe}")
                        st.write(f"3. **PEG Ratio:** {peg_ratio}")
                        st.write(f"4. **Price-to-Book (P/B):** {pb_ratio}")
                        st.write(f"5. **Price-to-Sales (P/S):** {ps_ratio}")
                        st.write(f"6. **EV / EBITDA:** {ev_to_ebitda}")
                        st.write(f"7. **EV / Ventas (P/C):** {ev_to_rev}")
                        st.write(f"8. **ROE (Rentab. Capital):** {roe}")
                        st.write(f"9. **ROA (Rentab. Activos):** {roa}")
                        st.write(f"10. **ROIC (ROI):** {roic}")
                        st.write(f"11. **Margen Bruto:** {gross_margins}")
                        st.write(f"12. **Margen Operativo:** {operating_margins}")
                        st.write(f"13. **Margen Beneficio Neto:** {profit_margins}")
                        st.write(f"14. **Deuda / Capital (D/E):** {debt_to_equity}")
                        st.write(f"15. **Current Ratio (Liquidez):** {current_ratio}")
                        st.write(f"16. **Quick Ratio (Prueba Ácida):** {quick_ratio}")
                        st.write(f"17. **Dividend Yield:** {dividend_yield}")
                        st.write(f"18. **Payout Ratio:** {payout_ratio}")
                        st.write(f"19. **Crecimiento de Ingresos (Q/Q):** {revenue_growth}")
                        st.write(f"20. **Crecimiento de Beneficios (Q/Q):** {earnings_growth}")
                    else:
                        st.info("ℹ️ Activo no accionario: Ratios fundamentales omitidos (Criptomoneda / Índice / Materia Prima).")

                # --- PESTAÑA 3: FACTORES CLAVE DETECTADOS ---
                with st.expander("🔍 Factores Clave Detectados"):
                    st.markdown("**Técnicos:**")
                    for r in razones_tecnicas:
                        st.write(f"• [Técnico] {r}")
                    st.markdown("**Fundamentales:**")
                    for r in razones_fundamentales:
                        st.write(f"• [Fundamental] {r}")

                # --- PESTAÑA 4: RECOMENDACIÓN Y GESTIÓN DE RIESGO ---
                st.subheader("🛡️ Recomendación y Plan Operativo")
                
                if score_global_pct >= 70:
                    st.success("🟢 **RECOMENDACIÓN: COMPRA FUERTE (ALTA CONFLUENCIA HÍBRIDA)**\n\n• El activo demuestra solidez fundamental y un momento técnico alcista muy favorable.")
                elif score_global_pct >= 45:
                    st.warning("🟡 **RECOMENDACIÓN: MANTENER / ESPERA NEUTRAL**\n\n• Señales mixtas en el mercado. Conviene vigilar soportes o esperar confirmación.")
                else:
                    st.error("🔴 **RECOMENDACIÓN: PRECAUCIÓN / ZONA DE RIESGO**\n\n• Debilidad técnica o valoración exigente. Se aconseja prudencia.")

                stop_loss = precio - (1.5 * atr)
                take_profit = precio + (2.5 * atr)
                riesgo = precio - stop_loss
                beneficio = take_profit - precio
                ratio_rb = beneficio / riesgo if riesgo > 0 else 0

                capital_a_riesgo = capital_disponible * pct_riesgo_max
                unidades_a_comprar = capital_a_riesgo / riesgo if riesgo > 0 else 0
                inversion_total = unidades_a_comprar * precio

                st.markdown(f"""
                * 💰 **Capital Total:** ${capital_disponible:,.2f}
                * ⚠️ **Riesgo Máximo ({pct_riesgo_max*100}%):** ${capital_a_riesgo:,.2f}
                * 🎯 **Precio Entrada Sugerido:** ${precio:,.2f}
                * 🛑 **Stop Loss (Invalidación):** ${stop_loss:,.2f} (-1.5x ATR)
                * 🏁 **Take Profit (Objetivo):** ${take_profit:,.2f} (+2.5x ATR)
                * 📦 **Unidades a Comprar:** {unidades_a_comprar:,.2f} (Inversión: ${inversion_total:,.2f})
                * 📐 **Ratio Riesgo / Beneficio:** 1 : {ratio_rb:.2f} {'(Excelente > 1.5)' if ratio_rb >= 1.5 else '(Precaución)'}
                """)

        except Exception as e:
            st.error(f"⚠️ Hubo un error al procesar los datos: {e}")
