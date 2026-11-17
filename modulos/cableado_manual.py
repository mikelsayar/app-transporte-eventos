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

    # Bucle que dibuja los sistemas
    for i in range(st.session_state.num_sistemas):
        with st.expander(f"⚙️ Configuración de Sistema {i + 1}", expanded=True):
            c1, c2, c3 = st.columns(3)
            
            nombre = c1.text_input("Nombre (ej. Main)", value=f"Sistema {i + 1}", key=f"nombre_{i}")
            
            # La función determina si multiplicamos x2 (L+R) o si es Mono
            funcion = c2.selectbox("Función", ["Main L+R", "Outfill L+R", "Delay L+R", "Frontfill (Mono)", "Sub (Mono)"], key=f"funcion_{i}")
            
            modelo = c3.selectbox("Modelo", ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series", "d&b SL-SUB"], key=f"modelo_{i}")
            
            c4, c5, _ = st.columns([1, 1, 1])
            cajas = c4.number_input("Cajas por array (o totales si es Mono)", min_value=0, max_value=48, value=10, key=f"cajas_{i}")
            ap = c5.checkbox("ArrayProcessing (AP)", value=True, key=f"ap_{i}")

    col_add, col_sub, _ = st.columns([1, 1, 2])
    with col_add:
        st.button("➕ Añadir Sistema", on_click=anadir_sistema)
    with col_sub:
        st.button("➖ Quitar Último", on_click=quitar_sistema)

    st.markdown("---")
    
    # Motor de Cálculo d&b
    if st.button("Calcular Necesidades Totales", type="primary"):
        st.subheader("📋 Resumen de Material")
        
        resultados = []
        
        for i in range(st.session_state.num_sistemas):
            nom = st.session_state[f"nombre_{i}"]
            fun = st.session_state[f"funcion_{i}"]
            mod = st.session_state[f"modelo_{i}"]
            cajas_por_array = st.session_state[f"cajas_{i}"]
            tiene_ap = st.session_state[f"ap_{i}"]
            
            if cajas_por_array == 0:
                continue
                
            # Determinar cantidad de arrays (2 si es L+R, 1 si es Mono)
            multiplicador_arrays = 2 if "L+R" in fun else 1
            
            # --- LÓGICA DE CANALES Y LINKS ---
            if tiene_ap:
                # 1 caja chupa los 2 canales del amplificador (No hay links)
                cajas_por_circuito = 1
                links_por_array = 0
            else:
                # 2 cajas comparten los 2 canales del amplificador (Llevan 1 link entre ellas)
                cajas_por_circuito = 2
                links_por_array = math.floor(cajas_por_array / 2)
            
            # Circuitos NLT4 físicos necesarios por array
            circuitos_nlt4_por_array = math.ceil(cajas_por_array / cajas_por_circuito)
            canales_por_array = circuitos_nlt4_por_array * 2 
            
            # --- LÓGICA DE MULTIPINES (LK vs NLT8) ---
            lks_por_array = 0
            nlt8_por_array = 0
            breakouts_lk = 0
            breakouts_nlt8 = 0
            
            # Si el array pide más de 4 canales, pasamos directamente a formato LK
            if canales_por_array > 4:
                lks_por_array = math.ceil(canales_por_array / 12)
                breakouts_lk = lks_por_array
            else:
                # Si pide 4 canales o menos, tiramos NLT8 (ej. un frontfill pequeño o 4 cajas sin AP)
                nlt8_por_array = math.ceil(canales_por_array / 4)
                breakouts_nlt8 = nlt8_por_array
            
            # Añadimos los datos a la tabla multiplicando por el número de arrays (L+R o Mono)
            resultados.append({
                "Sistema": f"{nom} ({mod})",
                "Total Cajas": cajas_por_array * multiplicador_arrays,
                "AP": "Sí" if tiene_ap else "No",
                "LK 30m": lks_por_array * multiplicador_arrays,
                "Breakout LK": breakouts_lk * multiplicador_arrays,
                "NLT8 30m": nlt8_por_array * multiplicador_arrays,
                "Breakout NLT8 a NLT4": breakouts_nlt8 * multiplicador_arrays,
                "Links NLT4 (1m)": links_por_array * multiplicador_arrays
            })
        
        # Mostrar en pantalla
        if resultados:
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Sumatorio final para el pedido a almacén
            st.success("📦 **TOTALES GLOBALES PARA ALMACÉN:**")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mangueras LK (30m)", df['LK 30m'].sum())
            c2.metric("Breakouts LK", df['Breakout LK'].sum())
            c3.metric("Mangueras NLT8", df['NLT8 30m'].sum())
            c4.metric("Links NLT4", df['Links NLT4 (1m)'].sum())
        else:
            st.warning("No hay sistemas con cajas configuradas.")