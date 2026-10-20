import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Analizador Financiero Híbrido", page_icon="📈", layout="centered")

def calificar(pct):
    if pct >= 75: return "🟢 Excelente"
    elif pct >= 60: return "🟢 Bueno"
    elif pct >= 45: return "🟡 Neutral"
    elif pct >= 30: return "🟠 Precaución"
    else: return "🔴 Riesgoso"

st.title("📈 Analizador Híbrido Definitivo")
st.markdown("Informe completo: 15 Técnicos + 20 Fundamentales + Gestión de Riesgo")

# --- BARRA LATERAL ---
st.sidebar.header("Parámetros")
nombre_o_ticker = st.sidebar.text_input("Activo (Ej: Tesla, Bitcoin, AAPL)", value="Tesla")
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
    
    with st.spinner(f"Analizando {ticker}... Por favor espera."):
        try:
            activo = yf.Ticker(ticker)
            hist = activo.history(period="1y")
            
            if hist.empty or len(hist) < 60:
                st.error(f"⚠️ No hay suficientes datos históricos para '{nombre_o_ticker}'.")
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

                # Ratios fundamentales
                pe_ratio = info.get('trailingPE', None) if es_accion else None
                forward_pe = info.get('forwardPE', None) if es_accion else None
                peg_ratio = info.get('pegRatio', None) if es_accion else None
                pb_ratio = info.get('priceToBook', None) if es_accion else None
                ps_ratio = info.get('priceToSalesTrailing12Months', None) if es_accion else None
                ev_to_ebitda = info.get('enterpriseToEbitda', None) if es_accion else None
                ev_to_rev = info.get('enterpriseValueToRevenue', None) if es_accion else None
                
                roe = info.get('returnOnEquity', None) if es_accion else None
                roa = info.get('returnOnAssets', None) if es_accion else None
                roic = info.get('returnOnCapitalEmployed', None) if es_accion else info.get('roic', None)
                
                profit_margins = info.get('profitMargins', None) if es_accion else None
                operating_margins = info.get('operatingMargins', None) if es_accion else None
                gross_margins = info.get('grossMargins', None) if es_accion else None
                
                debt_to_equity = info.get('debtToEquity', None) if es_accion else None
                current_ratio = info.get('currentRatio', None) if es_accion else None
                quick_ratio = info.get('quickRatio', None) if es_accion else None
                
                dividend_yield = info.get('dividendYield', None) if es_accion else None
                payout_ratio = info.get('payoutRatio', None) if es_accion else None
                revenue_growth = info.get('revenueGrowth', None) if es_accion else None
                earnings_growth = info.get('earningsGrowth', None) if es_accion else None

                # Indicadores técnicos
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

                # Puntuaciones
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
                    if pe_ratio and 0 < pe_ratio < 25: puntos_fund += 1; razones_fundamentales.append(f"PER atractivo y razonable ({pe_ratio:.2f})")
                    if roe and (roe * 100) > 15: puntos_fund += 1; razones_fundamentales.append(f"Alta rentabilidad para el accionista (ROE > 15%)")
                    if current_ratio and current_ratio > 1.2: puntos_fund += 1; razones_fundamentales.append(f"Buena liquidez a corto plazo (Current Ratio > 1.2)")
                    if debt_to_equity and debt_to_equity < 100: puntos_fund += 1; razones_fundamentales.append(f"Estructura de deuda saludable (D/E < 100)")
                    if profit_margins and (profit_margins * 100) > 10: puntos_fund += 1; razones_fundamentales.append(f"Márgenes netos sólidos (> 10%)")
                    score_fund_pct = (puntos_fund / max_puntos_fund) * 100
                else:
                    razones_fundamentales.append("Sin métricas fundamentales aplicables (Cripto/Índice/Materia Prima)")

                score_global_pct = (score_tech_pct * 0.5) + (score_fund_pct * 0.5)

                # --- INTERFAZ VISUAL ---
                st.subheader(f"Informe de: {ticker}")
                
                col1, col2 = st.columns(2)
                col1.metric("Precio Actual", f"${precio:,.2f}", f"{var_1m:+.2f}%")
                col2.metric("Índice Global", f"{score_global_pct:.1f}%", calificar(score_global_pct))

                st.divider()

                # Recomendación principal
                if score_global_pct >= 70:
                    st.success("🟢 **RECOMENDACIÓN: COMPRA FUERTE (ALTA CONFLUENCIA HÍBRIDA)**\n\n• El activo demuestra solidez fundamental y un momento técnico alcista muy favorable.")
                elif score_global_pct >= 45:
                    st.warning("🟡 **RECOMENDACIÓN: MANTENER / ESPERA NEUTRAL**\n\n• Señales mixtas en el mercado. Conviene vigilar soportes o esperar confirmación.")
                else:
                    st.error("🔴 **RECOMENDACIÓN: PRECAUCIÓN / ZONA DE RIESGO**\n\n• Debilidad técnica o valoración exigente. Se aconseja prudencia.")

                # Gráfico interactivo
                st.line_chart(c.tail(150))

                # --- EXPANSOR 1: 15 INDICADORES TÉCNICOS ---
                with st.expander("📊 Ver los 15 Indicadores Técnicos Detallados"):
                    st.write(f"1. **RSI (14):** {rsi:.1f} {'(Sobrecompra)' if rsi>70 else ('(Sobreventa)' if rsi<30 else '(Saludable)')}")
                    st.write(f"2. **SMA Corto (20):** ${sma20:,.2f} {'(Alcista)' if precio>sma20 else '(Bajista)'}")
                    st.write(f"3. **SMA Medio (50):** ${sma50:,.2f} {'(Alcista)' if precio>sma50 else '(Bajista)'}")
                    st.write(f"4. **SMA Largo (200):** ${sma200:,.2f} {'(Alcista)' if precio>sma200 else '(Bajista)'}")
                    st.write(f"5. **MACD Line:** {macd_actual:.2f}")
                    st.write(f"6. **MACD Señal:** {signal_actual:.2f} {'(Momento Alcista)' if macd_actual>signal_actual else '(Momento Bajista)'}")
                    st.write(f"7. **Bollinger Superior:** ${bb_upper:,.2f}")
                    st.write(f"8. **Bollinger Media:** ${bb_middle:,.2f}")
                    st.write(f"9. **Bollinger Inferior:** ${bb_lower:,.2f} (Soporte)")
                    st.write(f"10. **Estocástico (%K):** {stoch_k:.1f} {'(Sobrecompra)' if stoch_k>80 else ('(Sobreventa)' if stoch_k<20 else '(Neutro)')}")
                    st.write(f"11. **ATR (Volatilidad):** ${atr:.2f}")
                    st.write(f"12. **ROC (Momento 10d):** {roc:+.2f}%")
                    st.write(f"13. **Ratio de Volumen:** {vol_ratio:.2f}x {'(Alto Volumen)' if vol_ratio>1.5 else '(Normal)'}")
                    st.write(f"14. **Canal Donchian Máx:** ${donchian_high:,.2f} (Resistencia)")
                    st.write(f"15. **Posición vs SMA 50:** {dist_sma50:+.2f}%")

                # --- EXPANSOR 2: 20 RATIOS FUNDAMENTALES ---
                with st.expander("📈 Ver los 20 Ratios Fundamentales"):
                    if es_accion:
                        st.write(f"1. **PER (Trailing P/E):** {pe_ratio:.2f}" if pe_ratio else "1. **PER:** N/D")
                        st.write(f"2. **Forward P/E:** {forward_pe:.2f}" if forward_pe else "2. **Forward P/E:** N/D")
                        st.write(f"3. **PEG Ratio:** {peg_ratio:.2f}" if peg_ratio else "3. **PEG Ratio:** N/D")
                        st.write(f"4. **Price-to-Book (P/B):** {pb_ratio:.2f}" if pb_ratio else "4. **Price-to-Book:** N/D")
                        st.write(f"5. **Price-to-Sales (P/S):** {ps_ratio:.2f}" if ps_ratio else "5. **Price-to-Sales:** N/D")
                        st.write(f"6. **EV / EBITDA:** {ev_to_ebitda:.2f}" if ev_to_ebitda else "6. **EV / EBITDA:** N/D")
                        st.write(f"7. **EV / Ventas (EV/Rev):** {ev_to_rev:.2f}" if ev_to_rev else "7. **EV / Rev:** N/D")
                        st.write(f"8. **ROE:** {roe*100:.2f}%" if roe else "8. **ROE:** N/D")
                        st.write(f"9. **ROA:** {roa*100:.2f}%" if roa else "9. **ROA:** N/D")
                        st.write(f"10. **ROIC:** {roic*100:.2f}%" if roic else "10. **ROIC:** N/D")
                        st.write(f"11. **Margen Bruto:** {gross_margins*100:.2f}%" if gross_margins else "11. **Margen Bruto:** N/D")
                        st.write(f"12. **Margen Operativo:** {operating_margins*100:.2f}%" if operating_margins else "12. **Margen Op.:** N/D")
                        st.write(f"13. **Margen Neto:** {profit_margins*100:.2f}%" if profit_margins else "13. **Margen Neto:** N/D")
                        st.write(f"14. **Deuda / Capital (D/E):** {debt_to_equity:.2f}" if debt_to_equity else "14. **D/E:** N/D")
                        st.write(f"15. **Current Ratio:** {current_ratio:.2f}" if current_ratio else "15. **Current Ratio:** N/D")
                        st.write(f"16. **Quick Ratio:** {quick_ratio:.2f}" if quick_ratio else "16. **Quick Ratio:** N/D")
                        st.write(f"17. **Dividend Yield:** {dividend_yield*100:.2f}%" if dividend_yield else "17. **Dividend Yield:** 0.00%")
                        st.write(f"18. **Payout Ratio:** {payout_ratio*100:.2f}%" if payout_ratio else "18. **Payout Ratio:** N/D")
                        st.write(f"19. **Crecimiento Ingresos:** {revenue_growth*100:+.2f}%" if revenue_growth else "19. **Crecimiento Ingresos:** N/D")
                        st.write(f"20. **Crecimiento Beneficios:** {earnings_growth*100:+.2f}%" if earnings_growth else "20. **Crecimiento Beneficios:** N/D")
                    else:
                        st.info("ℹ️ Activo no accionario: Ratios fundamentales omitidos (Criptomoneda / Índice / Materia Prima).")

                # --- EXPANSOR 3: FACTORES CLAVE Y RAZONES ---
                with st.expander("🔍 Factores Clave Detectados"):
                    st.markdown("**Técnicos:**")
                    for r in razones_tecnicas:
                        st.write(f"• {r}")
                    st.markdown("**Fundamentales:**")
                    for r in razones_fundamentales:
                        st.write(f"• {r}")

                # --- PLAN OPERATIVO Y GESTIÓN DE RIESGO ---
                st.subheader("🛡️ Plan Operativo y Riesgo")
                stop_loss = precio - (1.5 * atr)
                take_profit = precio + (2.5 * atr)
                riesgo = precio - stop_loss
                beneficio = take_profit - precio
                ratio_rb = beneficio / riesgo if riesgo > 0 else 0

                capital_a_riesgo = capital_disponible * pct_riesgo_max
                unidades_a_comprar = capital_a_riesgo / riesgo if riesgo > 0 else 0
                inversion_total = unidades_a_comprar * precio

                col_p1, col_p2 = st.columns(2)
                col_p1.metric("Stop Loss", f"${stop_loss:,.2f}")
                col_p2.metric("Take Profit", f"${take_profit:,.2f}")

                st.info(f"""
                * 📦 **Unidades a Comprar:** {unidades_a_comprar:,.2f}
                * 💵 **Inversión Total Estimada:** ${inversion_total:,.2f}
                * 📐 **Ratio Riesgo / Beneficio:** 1 : {ratio_rb:.2f}
                """)

        except Exception as e:
            st.error(f"⚠️ Hubo un error al procesar los datos: {e}")
