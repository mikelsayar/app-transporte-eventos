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
            funcion = c2.selectbox("Función", ["Main L+R", "Outfill L+R", "Delay L+R", "Frontfill (Mono)", "Sub (Mono)", "Sub L+R"], key=f"funcion_{i}")
            modelo = c3.selectbox("Modelo", ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series", "d&b Y-Series", "d&b V10p / Y7p", "d&b SL-SUB", "d&b J-SUB"], key=f"modelo_{i}")
            
            c4, c5, _ = st.columns([1, 1, 1])
            cajas = c4.number_input("Cajas por array (o totales si Mono)", min_value=0, max_value=48, value=10, key=f"cajas_{i}")
            ap = c5.checkbox("ArrayProcessing (AP)", value=True, key=f"ap_{i}")
            
            # Nota visual si el sistema ignora el checkbox de AP
            if "GSL" in modelo or "SUB" in modelo:
                st.caption("ℹ️ *Este sistema funciona siempre a 1 caja por tiro de NLT4 (AP forzado / Activo 2 vías).*")

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
            is_pasivo = "V-Series" in mod or "Y-Series" in mod or "p" in mod or "Frontfill" in fun
            is_gsl = "GSL" in mod
            is_ksl_xsl = "KSL" in mod or "XSL" in mod

            # 1. CÁLCULO DE TIROS DE NLT4 Y LINKS
            if is_gsl or is_sub:
                tiros = cajas
                links_por_array = 0
                tiene_ap = True # Forzado visualmente
            elif is_ksl_xsl:
                if tiene_ap:
                    tiros = cajas
                    links_por_array = 0
                else:
                    tiros = math.ceil(cajas / 2)
                    links_por_array = math.floor(cajas / 2)
            elif is_pasivo:
                # 1 tiro NLT4 alimenta hasta 2 cajas pasivas
                tiros = math.ceil(cajas / 2)
                links_por_array = math.floor(cajas / 2)
            else:
                tiros = math.ceil(cajas / 2)
                links_por_array = math.floor(cajas / 2)

            # 2. Ruteo Físico (LK25 vs NLT8) y Breakouts
            lk25 = 0
            nlt8 = 0
            brk_lk = 0
            brk_nlt8_2 = 0
            brk_nlt8_4 = 0

            if is_pasivo:
                # Frontfill/V-Series: 1 NLT8 da servicio a 4 NLT4 (1 ch por NLT4)
                nlt8 = math.ceil(tiros / 4)
                brk_nlt8_4 = nlt8
            elif is_sub:
                # Subs: Atacamos con NLT8 y Breakout a 2x NLT4
                nlt8 = math.ceil(tiros / 2)
                brk_nlt8_2 = nlt8
            else:
                # PA Principal (KSL, XSL, GSL) -> LK25 (6 tiros) / NLT8 (2 tiros)
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
                "AP": "Sí" if tiene_ap else "No",
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