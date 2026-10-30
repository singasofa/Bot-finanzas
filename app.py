import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

try:
    from finvizfinance.quote import finvizfinance
    FINVIZ_DISPONIBLE = True
except ImportError:
    FINVIZ_DISPONIBLE = False

st.set_page_config(page_title="Informe Híbrido Wall Street Pro", page_icon="📈", layout="centered")

def calificar(pct):
    if pct >= 75: return "🟢 Excelente"
    elif pct >= 60: return "🟢 Bueno"
    elif pct >= 45: return "🟡 Neutral"
    elif pct >= 30: return "🟠 Precaución"
    else: return "🔴 Riesgoso"

def parse_finviz_val(val_str):
    if not val_str or val_str == '-' or val_str == 'N/A':
        return None
    try:
        clean_str = str(val_str).replace('%', '').replace(',', '').strip()
        return float(clean_str)
    except:
        return None

st.title("📈 Informe Híbrido Wall Street Pro")
st.markdown("**Análisis Técnico Avanzado + Fundamentales Adaptados + Gestión de Riesgo Profesional**")

# --- BARRA LATERAL ---
st.sidebar.header("Parámetros de Búsqueda")
nombre_o_ticker = st.sidebar.text_input("Activo (Ej: Tesla, BTC-USD, SPY, QQQ)", value="Tesla")
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
    
    with st.spinner(f"Analizando mercados globales y conectando datos para {ticker}..."):
        try:
            activo = yf.Ticker(ticker)
            hist = activo.history(period="1y")
            
            if hist.empty or len(hist) < 60:
                st.error(f"⚠️ No se encontraron suficientes datos históricos para '{nombre_o_ticker}'. Pruebe con el ticker exacto (ej: AAPL, SPY, BTC-USD).")
            else:
                c, h, l, v = hist['Close'], hist['High'], hist['Low'], hist['Volume']
                precio = c.iloc[-1]
                var_1m = ((precio - c.iloc[-20]) / c.iloc[-20]) * 100 if len(c) >= 20 else 0

                # --- METADATOS Y TIPO DE ACTIVO ---
                info_yf = activo.info if hasattr(activo, 'info') else {}
                quote_type = info_yf.get('quoteType', 'EQUITY').upper()
                
                es_accion = (quote_type == 'EQUITY')
                es_etf = (quote_type == 'ETF')
                es_crypto = (quote_type == 'CRYPTOCURRENCY')

                # --- INDICADORES TÉCNICOS ---
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

                # ADX
                plus_dm = h.diff()
                minus_dm = l.diff()
                plus_dm = np.where((plus_dm > 0) & (plus_dm > minus_dm), plus_dm, 0.0)
                minus_dm = np.where((minus_dm > 0) & (minus_dm > plus_dm), minus_dm, 0.0)
                tr14 = true_range.rolling(14).sum()
                plus_di = 100 * (pd.Series(plus_dm).rolling(14).sum() / tr14)
                minus_di = 100 * (pd.Series(minus_dm).rolling(14).sum() / tr14)
                dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)
                adx = dx.rolling(14).mean().iloc[-1]
                adx = adx if not pd.isna(adx) else 25.0

                # OBV
                obv = (np.sign(c.diff()) * v).fillna(0).cumsum().iloc[-1]

                # --- FUNDAMENTALES Y ANALISTAS (ROBUSTO) ---
                fv_data = {}
                short_float = info_yf.get('shortPercentOfFloat', 'N/D')
                if short_float != 'N/D' and isinstance(short_float, float):
                    short_float = f"{short_float*100:.2f}%"
                
                insider_trading = info_yf.get('heldPercentInsiders', 'N/D')
                if insider_trading != 'N/D' and isinstance(insider_trading, float):
                    insider_trading = f"{insider_trading*100:.2f}%"

                # Extracción robusta de analistas desde info_yf
                recomendacion_analistas = info_yf.get('recommendationKey', info_yf.get('recommendationMean', 'N/D'))
                if isinstance(recomendacion_analistas, str) and recomendacion_analistas != 'N/D':
                    recomendacion_analistas = recomendacion_analistas.upper()
                elif isinstance(recomendacion_analistas, (int, float)):
                    recomendacion_analistas = f"Media: {recomendacion_analistas:.1f} (1=Buy, 5=Sell)"

                analistas_target = info_yf.get('targetMeanPrice', info_yf.get('targetHighPrice', info_yf.get('targetMedianPrice', 'N/D')))

                if es_accion and FINVIZ_DISPONIBLE:
                    try:
                        if "-" not in ticker and "=" not in ticker:
                            stock_fv = finvizfinance(ticker)
                            fv_data = stock_fv.ticker_fundament()
                            if recomendacion_analistas == 'N/D':
                                recomendacion_analistas = fv_data.get('Recom', 'N/D')
                    except:
                        pass

                pe_ratio = fv_data.get('P/E', info_yf.get('trailingPE', 'N/D'))
                forward_pe = fv_data.get('Forward P/E', info_yf.get('forwardPE', 'N/D'))
                peg_ratio = fv_data.get('PEG', info_yf.get('pegRatio', 'N/D'))
                pb_ratio = fv_data.get('P/B', info_yf.get('priceToBook', 'N/D'))
                roe = fv_data.get('ROE', 'N/D')
                profit_margins = fv_data.get('Profit Margin', 'N/D')
                debt_to_equity = fv_data.get('Debt/Eq', 'N/D')
                
                dividend_yield = fv_data.get('Dividend %', info_yf.get('dividendYield', 'N/D'))
                if isinstance(dividend_yield, float):
                    dividend_yield = f"{dividend_yield*100:.2f}%"

                etf_expense_ratio = info_yf.get('expenseRatio', 'N/D')
                if isinstance(etf_expense_ratio, float):
                    etf_expense_ratio = f"{etf_expense_ratio*100:.2f}%"
                etf_aum = info_yf.get('totalAssets', 'N/D')
                if isinstance(etf_aum, (int, float)):
                    etf_aum = f"${etf_aum:,.0f}"

                # --- PUNTUACIONES ---
                score_tech_raw = 0
                if precio > sma20: score_tech_raw += 1
                if precio > sma50: score_tech_raw += 2
                if precio > sma200: score_tech_raw += 2
                if macd_actual > signal_actual: score_tech_raw += 2
                if 30 <= rsi <= 65: score_tech_raw += 2
                if stoch_k < 80: score_tech_raw += 1
                if roc > 0: score_tech_raw += 1
                if adx > 25: score_tech_raw += 1

                score_tech_pct = (score_tech_raw / 12) * 100

                score_fund_pct = 50.0
                if es_accion:
                    puntos_fund = 0
                    pe_val = parse_finviz_val(pe_ratio)
                    if pe_val and 0 < pe_val < 30: puntos_fund += 1
                    if rsi <= 70: puntos_fund += 1
                    score_fund_pct = (puntos_fund / 2) * 100
                elif es_etf:
                    score_fund_pct = 75.0
                elif es_crypto:
                    score_fund_pct = 60.0

                score_global_pct = (score_tech_pct * 0.6) + (score_fund_pct * 0.4)

                # --- INTERFAZ VISUAL ---
                tipo_etiqueta = "Acción" if es_accion else ("ETF" if es_etf else ("Criptomoneda" if es_crypto else "Activo Global"))
                st.subheader(f"INFORME WALL STREET: {nombre_o_ticker.upper()} ({ticker}) — [{tipo_etiqueta}]")
                
                col1, col2 = st.columns(2)
                col1.metric("Precio Actual", f"${precio:,.2f}", f"{var_1m:+.2f}% (1M)")
                col2.metric("Índice Global", f"{score_global_pct:.1f}%", calificar(score_global_pct))

                st.divider()

                st.write(f"📊 **Salud Técnica:** {score_tech_pct:.1f}% -> {calificar(score_tech_pct)}")
                st.write(f"📈 **Salud Fundamental / Estructural:** {score_fund_pct:.1f}% -> {calificar(score_fund_pct)}")

                st.line_chart(c.tail(120))

                # --- EXPANDERS ---
                with st.expander("🎯 Consenso de Analistas y Datos de Mercado"):
                    target_str = f"${analistas_target:,.2f}" if isinstance(analistas_target, (int, float)) else "No disponible para este activo"
                    st.write(f"• **Precio Objetivo Medio (Analistas):** {target_str}")
                    st.write(f"• **Recomendación de Mercado:** {recomendacion_analistas}")
                    if es_accion:
                        st.write(f"• **Interés de Cortos (Short Float):** {short_float}")
                        st.write(f"• **Propiedad de Directivos (Insiders):** {insider_trading}")
                    if es_etf:
                        st.write(f"• **Ratio de Gastos (Expense Ratio):** {etf_expense_ratio}")
                        st.write(f"• **Patrimonio Bajo Gestión (AUM):** {etf_aum}")

                with st.expander("🔍 Ver los 17 Indicadores Técnicos Detallados"):
                    st.write(f"1. **RSI (14):** {rsi:.1f} {'(Sobrecompra)' if rsi>70 else ('(Sobreventa)' if rsi<30 else '(Saludable)')}")
                    st.write(f"2. **ADX (Fuerza de Tendencia):** {adx:.1f} {'(Tendencia Fuerte)' if adx>25 else '(Mercado Lateral)'}")
                    st.write(f"3. **SMA Corto (20):** ${sma20:,.2f}")
                    st.write(f"4. **SMA Medio (50):** ${sma50:,.2f}")
                    st.write(f"5. **SMA Largo (200):** ${sma200:,.2f}")
                    st.write(f"6. **MACD Line:** {macd_actual:.2f}")
                    st.write(f"7. **MACD Señal:** {signal_actual:.2f}")
                    st.write(f"8. **Bollinger Superior:** ${bb_upper:,.2f}")
                    st.write(f"9. **Bollinger Media:** ${bb_middle:,.2f}")
                    st.write(f"10. **Bollinger Inferior (Soporte):** ${bb_lower:,.2f}")
                    st.write(f"11. **Estocástico (%K):** {stoch_k:.1f}")
                    st.write(f"12. **ATR (Volatilidad):** ${atr:.2f}")
                    st.write(f"13. **ROC (Momento 10d):** {roc:+.2f}%")
                    st.write(f"14. **Ratio de Volumen:** {vol_ratio:.2f}x")
                    st.write(f"15. **Canal Donchian Máx (Resistencia):** ${donchian_high:,.2f}")
                    st.write(f"16. **Posición vs SMA 50:** {dist_sma50:+.2f}%")
                    st.write(f"17. **OBV (Flujo de Volumen):** {obv:,.0f}")

                with st.expander("📊 Ver Ratios Fundamentales / Estructurales"):
                    if es_accion:
                        st.write(f"1. **PER (Trailing P/E):** {pe_ratio}")
                        st.write(f"2. **Forward P/E:** {forward_pe}")
                        st.write(f"3. **PEG Ratio:** {peg_ratio}")
                        st.write(f"4. **Price-to-Book (P/B):** {pb_ratio}")
                        st.write(f"5. **ROE (Rentab. Capital):** {roe}")
                        st.write(f"6. **Margen Neto:** {profit_margins}")
                        st.write(f"7. **Deuda / Capital (D/E):** {debt_to_equity}")
                        st.write(f"8. **Dividend Yield:** {dividend_yield}")
                    elif es_etf:
                        st.write(f"• **Expense Ratio:** {etf_expense_ratio}")
                        st.write(f"• **AUM:** {etf_aum}")
                        st.write(f"• **Dividend Yield:** {dividend_yield}")
                    else:
                        st.info("ℹ️ Activo alternativo / Criptomoneda: Se priorizan métricas técnicas y de momento.")

                # --- EXTRACCIÓN ROBUSTA DE NOTICIAS ---
                noticias_list = []
                try:
                    raw_news = activo.news
                    if raw_news:
                        for n in raw_news:
                            # Manejar estructura estándar o anidada en 'content' de yfinance
                            if isinstance(n, dict):
                                title = n.get('title') or (n.get('content', {}) and n.get('content', {}).get('title'))
                                link = n.get('link') or (n.get('content', {}) and n.get('content', {}).get('clickThroughUrl', {}).get('url'))
                                if title:
                                    noticias_list.append((title, link))
                except:
                    pass

                # --- HISTÓRICO Y MÁXIMOS DE 52 SEMANAS ---
                max_52w = h.max() if not h.empty else precio
                min_52w = l.min() if not l.empty else precio
                dist_max_52w = ((precio - max_52w) / max_52w) * 100

                # --- VEREDICTO Y PLAN DE GESTIÓN DE RIESGO ---
                st.subheader("🎯 Veredicto de Compra, Histórico y Pronóstico")
                
                stop_loss = precio - (1.5 * atr)
                take_profit = precio + (2.5 * atr)
                riesgo = precio - stop_loss
                beneficio = take_profit - precio
                ratio_rb = beneficio / riesgo if riesgo > 0 else 0

                capital_a_riesgo = capital_disponible * pct_riesgo_max
                unidades_a_comprar = capital_a_riesgo / riesgo if riesgo > 0 else 0
                inversion_total = unidades_a_comprar * precio

                if score_global_pct >= 65 and rsi <= 70 and ratio_rb >= 1.5:
                    veredicto_titulo = "🟢 SÍ: BUEN MOMENTO PARA COMPRA FUERTE"
                    veredicto_color = "success"
                    explicacion_veredicto = f"El activo cuenta con alta confluencia técnica, RSI saludable ({rsi:.1f}) y ratio riesgo/beneficio óptimo (1:{ratio_rb:.2f}). Está a un {dist_max_52w:+.2f}% de su máximo anual (${max_52w:,.2f})."
                elif score_global_pct >= 50 and rsi < 40:
                    veredicto_titulo = "🟡 ESPERAR / COMPRA EN SOPORTE"
                    veredicto_color = "warning"
                    explicacion_veredicto = f"Estructura sólida pero con RSI bajo ({rsi:.1f}), cerca de soportes y alejado del máximo anual (${max_52w:,.2f}). Vigila rebotes."
                elif rsi > 75:
                    veredicto_titulo = "🟠 PRECAUCIÓN: SOBRECOMPRADO (NO COMPRAR AÚN)"
                    veredicto_color = "warning"
                    explicacion_veredicto = f"RSI muy elevado ({rsi:.1f}) y cerca del máximo de 52 semanas (${max_52w:,.2f}). Riesgo de corrección a corto plazo."
                else:
                    veredicto_titulo = "🔴 NO COMPRAR: ZONA DE RIESGO"
                    veredicto_color = "error"
                    explicacion_veredicto = f"Las señales técnicas actuales no acompañan de forma idónea. Distancia al máximo anual: {dist_max_52w:+.2f}%."

                if veredicto_color == "success":
                    st.success(f"### {veredicto_titulo}\n\n{explicacion_veredicto}")
                elif veredicto_color == "warning":
                    st.warning(f"### {veredicto_titulo}\n\n{explicacion_veredicto}")
                else:
                    st.error(f"### {veredicto_titulo}\n\n{explicacion_veredicto}")

                with st.expander("📈 Balance Comparativo (Meses y Años Atrás) y Máximos"):
                    st.markdown(f"""
                    * **Precio Actual:** `${precio:,.2f}`
                    * **Máximo de las Últimas 52 Semanas (1 Año):** `${max_52w:,.2f}` (`{dist_max_52w:.2f}%` desde el precio actual)
                    * **Mínimo de las Últimas 52 Semanas:** `${min_52w:,.2f}`
                    * **Variación a 1 Mes:** `{var_1m:+.2f}%`
                    """)
                    if len(c) >= 252:
                        precio_1ano_atras = c.iloc[-252]
                        var_1ano = ((precio - precio_1ano_atras) / precio_1ano_atras) * 100
                        st.markdown(f"* **Variación Interanual (vs 1 año atrás):** `{var_1ano:+.2f}%` (Precio hace un año: `${precio_1ano_atras:,.2f}`)")

                with st.expander("📰 Noticias Recientes y Pronóstico (Corto y Largo Plazo)"):
                    st.markdown("**Últimos titulares de mercado detectados:**")
                    if noticias_list:
                        for title, link in noticias_list[:6]:
                            if link:
                                st.markdown(f"- [{title}]({link})")
                            else:
                                st.markdown(f"- {title}")
                    else:
                        st.info("ℹ️ No hay titulares indexados en este momento para este ticker específico. Puedes consultarlos directamente en su panel oficial:")
                    
                    st.markdown(f"👉 [Ver noticias y gráficos en vivo de {ticker} en Finviz](https://finviz.com/quote.ashx?t={ticker})")
                    
                    st.markdown("---")
                    st.markdown("""
                    * **Pronóstico a Corto Plazo:** Condicionado por el volumen institucional y el RSI. Si el RSI está en zona neutra/saludable, el impulso se mantiene; si supera 70-75, el escenario apunta a consolidación.
                    * **Pronóstico a Largo Plazo:** Depende de la SMA de 200 sesiones. Si cotiza holgadamente por encima, la perspectiva estructural de fondo se mantiene alcista.
                    """)

                st.markdown("---")
                st.markdown("### 🛡️ Plan de Posición y Riesgo")
                st.markdown(f"""
                * 💰 **Capital Total Asignado:** `${capital_disponible:,.2f}`
                * ⚠️ **Riesgo Máximo Permitido ({pct_riesgo_max*100}%):** `${capital_a_riesgo:,.2f}`
                * 🎯 **Precio de Entrada Sugerido:** `${precio:,.2f}`
                * 🛑 **Stop Loss (Límite de Pérdida):** `${stop_loss:,.2f}` (-1.5x ATR)
                * 🏁 **Take Profit (Objetivo de Ganancia):** `${take_profit:,.2f}` (+2.5x ATR)
                * 📦 **Unidades a Comprar:** **{unidades_a_comprar:,.2f}** (Inversión total: **`${inversion_total:,.2f}`**)
                * 📐 **Ratio Riesgo / Beneficio:** **1 : {ratio_rb:.2f}** {'(Excelente > 1.5)' if ratio_rb >= 1.5 else '(Precaución < 1.5)'}
                """)

        except Exception as e:
            st.error(f"⚠️ Hubo un error al procesar los datos: {e}")
