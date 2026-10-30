# --- BUSCAR MÁXIMO DE 52 SEMANAS / HISTÓRICO ---
                max_52w = h.max() if not h.empty else precio
                min_52w = l.min() if not l.empty else precio
                dist_max_52w = ((precio - max_52w) / max_52w) * 100

                # Obtener noticias recientes desde yfinance si están disponibles
                noticias_recientes = activo.news if hasattr(activo, 'news') and activo.news else []
                titulares_noticias = [n.get('title', '') for n in noticias_recientes[:5]] if noticias_recientes else []

                # --- VEREDICTO INTELIGENTE AMPLIADO Y GESTIÓN DE RIESGO ---
                st.subheader("🎯 Veredicto de Compra, Histórico y Pronóstico")
                
                stop_loss = precio - (1.5 * atr)
                take_profit = precio + (2.5 * atr)
                riesgo = precio - stop_loss
                beneficio = take_profit - precio
                ratio_rb = beneficio / riesgo if riesgo > 0 else 0

                capital_a_riesgo = capital_disponible * pct_riesgo_max
                unidades_a_comprar = capital_a_riesgo / riesgo if riesgo > 0 else 0
                inversion_total = unidades_a_comprar * precio

                # Lógica de Timing mejorada con contexto histórico
                if score_global_pct >= 65 and rsi <= 70 and ratio_rb >= 1.5:
                    veredicto_titulo = "🟢 SÍ: BUEN MOMENTO PARA COMPRA FUERTE"
                    veredicto_color = "success"
                    explicacion_veredicto = f"El activo muestra alta confluencia técnica, RSI saludable ({rsi:.1f}) y un ratio riesgo/beneficio óptimo (1:{ratio_rb:.2f}). Se encuentra a un {dist_max_52w:+.2f}% de su máximo anual (${max_52w:,.2f}), lo que indica fortaleza sin estar excesivamente estirado."
                elif score_global_pct >= 50 and rsi < 40:
                    veredicto_titulo = "🟡 ESPERAR / COMPRA EN SOPORTE"
                    veredicto_color = "warning"
                    explicacion_veredicto = f"El activo cuenta con fundamentales sólidos pero cotiza con un RSI bajo ({rsi:.1f}), alejado de su máximo de 52 semanas (${max_52w:,.2f}). Vigila posibles rebotes en soporte antes de entrar."
                elif rsi > 75:
                    veredicto_titulo = "🟠 PRECAUCIÓN: SOBRECOMPRADO (NO COMPRAR AÚN)"
                    veredicto_color = "warning"
                    explicacion_veredicto = f"El RSI está muy elevado ({rsi:.1f}) y el precio está probando zonas cercanas a su máximo de 52 semanas (${max_52w:,.2f}). Existe riesgo de corrección a corto plazo por sobrecompra."
                else:
                    veredicto_titulo = "🔴 NO COMPRAR: ZONA DE RIESGO"
                    veredicto_color = "error"
                    explicacion_veredicto = f"Las señales técnicas no acompañan. El precio está un {dist_max_52w:+.2f}% respecto a su máximo anual (${max_52w:,.2f}) bajo un contexto de baja confluencia."

                if veredicto_color == "success":
                    st.success(f"### {veredicto_titulo}\n\n{explicacion_veredicto}")
                elif veredicto_color == "warning":
                    st.warning(f"### {veredicto_titulo}\n\n{explicacion_veredicto}")
                else:
                    st.error(f"### {veredicto_titulo}\n\n{explicacion_veredicto}")

                # --- ANÁLISIS DE BALANCE HISTÓRICO Y NOTICIAS ---
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

                with st.expander("📰 Pronóstico a Corto/Largo Plazo basado en Noticias Recientes"):
                    st.markdown("**Últimos titulares detectados en el mercado (Tendencia de Noticias):**")
                    if titulares_noticias:
                        for titular in titulares_noticias:
                            st.markdown(f"- {titular}")
                    else:
                        st.info("No se han indexado titulares recientes de forma automática para este ticker, se recomienda revisar el enlace directo a Finviz.")
                    
                    st.markdown("---")
                    st.markdown("""
                    * **Pronóstico a Corto Plazo:** Condicionado por el flujo de volumen institucional reciente, la volatilidad (ATR) y el posicionamiento del RSI. Si el RSI está en zona neutral/saludable, el impulso se mantiene; si supera 70-75, el escenario a corto plazo apunta a consolidación o retroceso lateral.
                    * **Pronóstico a Largo Plazo:** Depende de la estructura de medias móviles (SMA de 200 sesiones). Si el activo cotiza holgadamente por encima de la SMA de 200, la perspectiva estructural de fondo se mantiene alcista a pesar del ruido macroeconómico trimestral.
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
