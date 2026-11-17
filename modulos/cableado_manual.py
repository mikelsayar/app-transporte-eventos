import streamlit as st
import pandas as pd
import math

def mostrar_calculadora_manual():
    st.markdown("Añade los sistemas necesarios para tu diseño y configúralos a medida.")

    # 1. Memoria para los bloques dinámicos
    if "num_sistemas" not in st.session_state:
        st.session_state.num_sistemas = 1

    def anadir_sistema():
        st.session_state.num_sistemas += 1

    def quitar_sistema():
        if st.session_state.num_sistemas > 1:
            st.session_state.num_sistemas -= 1

    # 2. Construcción de la interfaz
    for i in range(st.session_state.num_sistemas):
        with st.expander(f"⚙️ Configuración de Sistema {i + 1}", expanded=True):
            c1, c2, c3 = st.columns(3)
            
            nombre = c1.text_input("Nombre", value=f"Sistema {i + 1}", key=f"nombre_{i}")
            funcion = c2.selectbox("Función", ["Main L+R", "Outfill L+R", "Delay L+R", "Frontfill (Mono)", "Sub (Mono)"], key=f"funcion_{i}")
            modelo = c3.selectbox("Modelo", ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series", "d&b SL-SUB"], key=f"modelo_{i}")
            
            c4, c5, _ = st.columns([1, 1, 1])
            cajas = c4.number_input("Cajas por array (o totales si Mono)", min_value=0, max_value=48, value=10, key=f"cajas_{i}")
            ap = c5.checkbox("ArrayProcessing (AP)", value=True, key=f"ap_{i}")

    col_add, col_sub, _ = st.columns([1, 1, 2])
    with col_add:
        st.button("➕ Añadir Sistema", on_click=anadir_sistema)
    with col_sub:
        st.button("➖ Quitar Último", on_click=quitar_sistema)

    st.markdown("---")
    
    # 3. Motor de cálculo técnico
    if st.button("Calcular Necesidades Totales", type="primary"):
        st.subheader("📋 Resumen de Material")
        
        resultados = []
        
        for i in range(st.session_state.num_sistemas):
            nom = st.session_state[f"nombre_{i}"]
            fun = st.session_state[f"funcion_{i}"]
            mod = st.session_state[f"modelo_{i}"]
            cajas = st.session_state[f"cajas_{i}"]
            tiene_ap = st.session_state[f"ap_{i}"]
            
            if cajas == 0:
                continue
                
            # Determinar L+R (x2) o Mono (x1)
            multiplicador_arrays = 2 if "L+R" in fun else 1
            
            # Lógica de canales y links de d&b
            if tiene_ap:
                cajas_por_circuito = 1
                links_por_array = 0
            else:
                cajas_por_circuito = 2
                links_por_array = math.floor(cajas / 2)
            
            circuitos = math.ceil(cajas / cajas_por_circuito)
            canales = circuitos * 2
            
            # Decisión entre Manguera LK (12ch) y NLT8 (4ch)
            lks = 0
            nlt8 = 0
            
            if canales > 4:
                lks = math.ceil(canales / 12)
            else:
                nlt8 = math.ceil(canales / 4)
            
            resultados.append({
                "Sistema": f"{nom} ({mod})",
                "Cajas Totales": cajas * multiplicador_arrays,
                "AP": "Sí" if tiene_ap else "No",
                "LK 30m": lks * multiplicador_arrays,
                "Breakout LK": lks * multiplicador_arrays,
                "NLT8 30m": nlt8 * multiplicador_arrays,
                "Breakout NLT8": nlt8 * multiplicador_arrays,
                "Links NLT4": links_por_array * multiplicador_arrays
            })
        
        # 4. Volcado de datos en pantalla
        if resultados:
            df = pd.DataFrame(resultados)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.success("📦 **TOTALES GLOBALES PARA ALMACÉN:**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mangueras LK (30m)", df['LK 30m'].sum())
            c2.metric("Breakouts LK", df['Breakout LK'].sum())
            c3.metric("Mangueras NLT8", df['NLT8 30m'].sum())
            c4.metric("Links NLT4", df['Links NLT4'].sum())
        else:
            st.warning("No hay sistemas con cajas configuradas.")