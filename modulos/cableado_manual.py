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
            funciones_lista = ["Main L+R", "Outfill L+R", "Delay L+R", "Frontfill (Mono)", "Sub (Mono)", "Sub L+R", "Sub Volado L+R", "Sub Volado (Mono)"]
            funcion = c2.selectbox("Función", funciones_lista, key=f"funcion_{i}")
            
            modelos_lista = ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series", "d&b Y-Series", "d&b V10p / Y7p", "d&b SL-SUB", "d&b KSL-SUB", "d&b XSL-SUB", "d&b J-SUB"]
            modelo = c3.selectbox("Modelo", modelos_lista, key=f"modelo_{i}")
            
            c4, c5, c6 = st.columns(3)
            cajas = c4.number_input("Cajas Tops (o Totales si Mono)", min_value=0, max_value=48, value=10, key=f"cajas_{i}")
            
            if modelo in ["d&b KSL", "d&b XSL"]:
                cajas_sub = c5.number_input(f"Subs volados ({modelo}-SUB)", min_value=0, max_value=12, value=0, key=f"cajassub_{i}")
                ap = c6.checkbox("ArrayProcessing (AP)", value=True, key=f"ap_{i}")
            else:
                ap = c5.checkbox("ArrayProcessing (AP)", value=True, key=f"ap_{i}")
            
            if "GSL" in modelo or "SL-SUB" in modelo or "KSL-SUB" in modelo or "J-SUB" in modelo:
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
            nom = st.session_state.get(f"nombre_{i}", f"Sistema {i+1}")
            fun = st.session_state.get(f"funcion_{i}", "Main L+R")
            mod = st.session_state.get(f"modelo_{i}", "d&b KSL")
            cajas = st.session_state.get(f"cajas_{i}", 0)
            tiene_ap = st.session_state.get(f"ap_{i}", True)
            
            cajas_sub = st.session_state.get(f"cajassub_{i}", 0) if mod in ["d&b KSL", "d&b XSL"] else 0
            
            if cajas == 0 and cajas_sub == 0:
                continue
                
            multiplicador_arrays = 2 if "L+R" in fun else 1
            
            is_sub = "SUB" in mod
            is_sub_volado_puro = "Volado" in fun and is_sub
            is_pasivo = "V-Series" in mod or "Y-Series" in mod or "p" in mod or "Frontfill" in fun
            is_gsl = "GSL" in mod
            is_ksl_xsl = ("KSL" in mod and not is_sub) or ("XSL" in mod and not is_sub)
            
            is_sub_linkeable = "XSL-SUB" in mod
            is_sub_no_linkeable = is_sub and not is_sub_linkeable

            # 1. CÁLCULO DE ETAPAS (D80/D40) POR CANALES
            ch_por_caja_top = 0
            if is_gsl or is_sub_no_linkeable:
                ch_por_caja_top = 2
            elif is_ksl_xsl:
                ch_por_caja_top = 2 if tiene_ap else 1
            elif is_sub_linkeable:
                ch_por_caja_top = 1
            elif is_pasivo:
                ch_por_caja_top = 0.5
                
            canales_tops = math.ceil(cajas * ch_por_caja_top)
            
            canales_subs_mixtos = 0
            if mod == "d&b XSL" and cajas_sub > 0:
                canales_subs_mixtos = math.ceil(cajas_sub * 1)
            elif mod == "d&b KSL" and cajas_sub > 0:
                canales_subs_mixtos = cajas_sub * 2
                
            canales_totales_array = canales_tops + canales_subs_mixtos
            
            etapas_por_array = math.ceil(canales_totales_array / 4)
            etapas_totales_sistema = etapas_por_array * multiplicador_arrays

            # 2. CÁLCULO DE TIROS DE NLT4 Y LINKS
            tiros_tops = 0
            links_por_array = 0
            
            if is_gsl or is_sub_no_linkeable:
                tiros_tops = cajas
                links_por_array = 0
            elif is_ksl_xsl:
                if tiene_ap:
                    tiros_tops = cajas
                    links_por_array = 0
                else:
                    tiros_tops = math.ceil(cajas / 2)
                    links_por_array = math.floor(cajas / 2)
            elif is_sub_linkeable or is_pasivo:
                tiros_tops = math.ceil(cajas / 2)
                links_por_array = math.floor(cajas / 2)
            else:
                tiros_tops = math.ceil(cajas / 2)
                links_por_array = math.floor(cajas / 2)

            tiros_subs_mixtos = 0
            if mod == "d&b XSL" and cajas_sub > 0:
                tiros_subs_mixtos = math.ceil(cajas_sub / 2)
                links_por_array += math.floor(cajas_sub / 2)
            elif mod == "d&b KSL" and cajas_sub > 0:
                tiros_subs_mixtos = cajas_sub
            
            tiros_totales = tiros_tops + tiros_subs_mixtos

            # 3. RUTEO FÍSICO Y BREAKOUTS
            lk25 = 0
            nlt8 = 0
            brk_lk = 0
            brk_nlt8_2 = 0
            brk_nlt8_4 = 0

            if is_pasivo:
                nlt8 = math.ceil(tiros_totales / 4)
                brk_nlt8_4 = nlt8
            elif is_sub_volado_puro:
                if tiros_totales <= 2:
                    nlt8 = 1
                    brk_nlt8_2 = 1
                elif tiros_totales <= 6:
                    lk25 = 1
                    brk_lk = 1
                elif tiros_totales <= 8:
                    lk25 = 1
                    brk_lk = 1
                    nlt8 = 1
                    brk_nlt8_2 = 1
                else:
                    lk25 = tiros_totales // 6
                    resto = tiros_totales % 6
                    if resto > 0:
                        if resto <= 2:
                            nlt8 += 1
                            brk_nlt8_2 += 1
                        else:
                            lk25 += 1
                    brk_lk = lk25
            elif is_sub:
                nlt8 = math.ceil(tiros_totales / 2)
                brk_nlt8_2 = nlt8
            else:
                if tiros_totales <= 4:
                    nlt8 = math.ceil(tiros_totales / 2)
                    brk_nlt8_2 = nlt8
                else:
                    lk25 = tiros_totales // 6
                    resto = tiros_totales % 6
                    
                    if resto == 1 or resto == 2:
                        nlt8 = 1
                        brk_nlt8_2 = 1
                    elif resto >= 3:
                        lk25 += 1
                    
                    brk_lk = lk25

            cajas_str = f"{cajas * multiplicador_arrays}"
            if cajas_sub > 0:
                cajas_str = f"{cajas_sub * multiplicador_arrays} Subs + {cajas * multiplicador_arrays} Tops"

            resultados.append({
                "Sistema": f"{nom} ({mod})",
                "Cajas": cajas_str,
                "Etapas (D80/D40)": etapas_totales_sistema,
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
            
            total_etapas = df['Etapas (D80/D40)'].sum()
            st.metric("🔌 ETAPAS TOTALES (D80/D40)", f"{total_etapas} unidades", f"Equivale a {math.ceil(total_etapas / 3)} Touring Racks (3x)")
            st.markdown("---")
            
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