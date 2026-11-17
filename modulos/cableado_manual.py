import streamlit as st
import pandas as pd
import math

def mostrar_calculadora_manual():
    st.markdown("Añade los sistemas necesarios para tu diseño y configúralos a medida.")

    if "num_sistemas" not in st.session_state:
        st.session_state.num_sistemas = 1

    def anadir_sistema():
        st.session_state.num_sistemas += 1

    def quitar_sistema():
        if st.session_state.num_sistemas > 1:
            st.session_state.num_sistemas -= 1

    for i in range(st.session_state.num_sistemas):
        with st.expander(f"⚙️ Configuración de Sistema {i + 1}", expanded=True):
            c1, c2, c3 = st.columns(3)
            
            nombre = c1.text_input("Nombre", value=f"Sistema {i + 1}", key=f"nombre_{i}")
            
            # Añadidas las opciones de Sub Volado
            funciones_lista = ["Main L+R", "Outfill L+R", "Delay L+R", "Frontfill (Mono)", "Sub (Mono)", "Sub L+R", "Sub Volado L+R", "Sub Volado (Mono)"]
            funcion = c2.selectbox("Función", funciones_lista, key=f"funcion_{i}")
            
            # Añadido d&b KSL-SUB
            modelos_lista = ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series", "d&b Y-Series", "d&b V10p / Y7p", "d&b SL-SUB", "d&b KSL-SUB", "d&b J-SUB"]
            modelo = c3.selectbox("Modelo", modelos_lista, key=f"modelo_{i}")
            
            c4, c5, _ = st.columns([1, 1, 1])
            cajas = c4.number_input("Cajas por array (o totales si Mono)", min_value=0, max_value=48, value=10, key=f"cajas_{i}")
            ap = c5.checkbox("ArrayProcessing (AP)", value=True, key=f"ap_{i}")
            
            # Nota visual para sistemas sin links
            if "GSL" in modelo or "SUB" in modelo:
                st.caption("ℹ️ *Este sistema rutea 1 caja por tiro de NLT4 (Sin links).*")

    col_add, col_sub, _ = st.columns([1, 1, 2])
    with col_add:
        st.button("➕ Añadir Sistema", on_click=anadir_sistema)
    with col_sub:
        st.button("➖ Quitar Último", on_click=quitar_sistema)

    st.markdown("---")
    
    if st.button("Calcular Necesidades Totales", type="primary"):
        st.subheader("📋 Resumen de Material d&b")
        
        resultados = []
        
        for i in range(st.session_state.num_sistemas):
            nom = st.session_state[f"nombre_{i}"]
            fun = st.session_state[f"funcion_{i}"]
            mod = st.session_state[f"modelo_{i}"]
            cajas = st.session_state[f"cajas_{i}"]
            tiene_ap = st.session_state[f"ap_{i}"]
            
            if cajas == 0:
                continue
                
            multiplicador_arrays = 2 if "L+R" in fun else 1
            
            # Banderas de topología
            is_sub = "SUB" in mod
            is_sub_volado = "Volado" in fun and is_sub
            is_pasivo = "V-Series" in mod or "Y-Series" in mod or "p" in mod or "Frontfill" in fun
            is_gsl = "GSL" in mod
            is_ksl_xsl = ("KSL" in mod and not is_sub) or "XSL" in mod

            # 1. CÁLCULO DE TIROS DE NLT4 Y LINKS
            if is_gsl or is_sub:
                tiros = cajas
                links_por_array = 0
                tiene_ap = True # Forzamos la lógica AP matemáticamente para que no cuente links
            elif is_ksl_xsl:
                if tiene_ap:
                    tiros = cajas
                    links_por_array = 0
                else:
                    tiros = math.ceil(cajas / 2)
                    links_por_array = math.floor(cajas / 2)
            elif is_pasivo:
                tiros = math.ceil(cajas / 2)
                links_por_array = math.floor(cajas / 2)
            else:
                tiros = math.ceil(cajas / 2)
                links_por_array = math.floor(cajas / 2)

            # 2. RUTEO FÍSICO Y BREAKOUTS
            lk25 = 0
            nlt8 = 0
            brk_lk = 0
            brk_nlt8_2 = 0
            brk_nlt8_4 = 0

            if is_pasivo:
                # Frontfill/V-Series: 1 NLT8 -> Breakout/Cajetín a 4x NLT4
                nlt8 = math.ceil(tiros / 4)
                brk_nlt8_4 = nlt8
                
            elif is_sub_volado:
                # Subs Volados: Regla estricta 2-6-8
                if tiros <= 2:
                    nlt8 = 1
                    brk_nlt8_2 = 1
                elif tiros <= 6:
                    lk25 = 1
                    brk_lk = 1
                elif tiros <= 8:
                    lk25 = 1
                    brk_lk = 1
                    nlt8 = 1
                    brk_nlt8_2 = 1
                else:
                    # Fallback por si vuelas más de 8 excepcionalmente
                    lk25 = tiros // 6
                    resto = tiros % 6
                    if resto > 0:
                        if resto <= 2:
                            nlt8 = 1
                            brk_nlt8_2 = 1
                        else:
                            lk25 += 1
                    brk_lk = lk25
                    
            elif is_sub:
                # Subs de suelo estándar: NLT8 -> Breakout a 2x NLT4
                nlt8 = math.ceil(tiros / 2)
                brk_nlt8_2 = nlt8
                
            else:
                # PA Principal (KSL, XSL, GSL) -> LK25 o NLT8
                if tiros <= 4:
                    nlt8 = math.ceil(tiros / 2)
                    brk_nlt8_2 = nlt8
                else:
                    lk25 = tiros // 6
                    resto = tiros % 6
                    
                    if resto == 1 or resto == 2:
                        nlt8 = 1
                        brk_nlt8_2 = 1
                    elif resto >= 3:
                        lk25 += 1
                    
                    brk_lk = lk25

            resultados.append({
                "Sistema": f"{nom} ({mod})",
                "Cajas": cajas * multiplicador_arrays,
                "AP": "Sí" if tiene_ap and not is_sub else "No/NA",
                "LK 25": lk25 * multiplicador_arrays,
                "Brk LK->6x NLT4": brk_lk * multiplicador_arrays,
                "NLT8": nlt8 * multiplicador_arrays,
                "Brk NLT8->2x NLT4": brk_nlt8_2 * multiplicador_arrays,
                "Brk NLT8->4x NLT4": brk_nlt8_4 * multiplicador_arrays,
                "Links NLT4": links_por_array * multiplicador_arrays
            })
        
        if resultados:
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.success("📦 **TOTALES GLOBALES PARA ALMACÉN:**")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mangueras LK 25", df['LK 25'].sum())
            c2.metric("Brk LK -> 6x", df['Brk LK->6x NLT4'].sum())
            c3.metric("Mangueras NLT8", df['NLT8'].sum())
            c4.metric("Links NLT4", df['Links NLT4'].sum())
            
            c5, c6, c7, _ = st.columns(4)
            c5.metric("Brk NLT8 -> 2x", df['Brk NLT8->2x NLT4'].sum())
            c6.metric("Brk/Cajetín NLT8 -> 4x", df['Brk NLT8->4x NLT4'].sum())
        else:
            st.warning("No hay sistemas con cajas configuradas.")