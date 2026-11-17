import streamlit as st
import pandas as pd

def mostrar_calculadora_manual():
    st.markdown("Añade los sistemas necesarios para tu diseño y configúralos a medida.")

    # 1. Inicializar la memoria de Streamlit para contar cuántos sistemas hay
    if "num_sistemas" not in st.session_state:
        st.session_state.num_sistemas = 1

    # 2. Funciones para sumar o restar bloques
    def anadir_sistema():
        st.session_state.num_sistemas += 1

    def quitar_sistema():
        if st.session_state.num_sistemas > 1:
            st.session_state.num_sistemas -= 1

    # 3. Bucle que dibuja tantos bloques como indique el contador
    for i in range(st.session_state.num_sistemas):
        with st.expander(f"⚙️ Configuración de Sistema {i + 1}", expanded=True):
            c1, c2, c3 = st.columns(3)
            
            # Usamos un sufijo único (_i) en los "key" para que Streamlit no mezcle los datos de diferentes bloques
            nombre = c1.text_input("Nombre (ej. Main L+R)", value=f"Sistema {i + 1}", key=f"nombre_{i}")
            funcion = c2.selectbox("Función", ["Main", "Outfill", "Frontfill", "Sub", "Delay", "Reoutfill"], key=f"funcion_{i}")
            modelo = c3.selectbox("Modelo de caja", ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series", "d&b Y-Series", "d&b SL-SUB", "d&b J-SUB", "d&b B22"], key=f"modelo_{i}")
            
            c4, c5, c6 = st.columns(3)
            cajas = c4.number_input("Cajas (Total)", min_value=0, max_value=48, value=10, key=f"cajas_{i}")
            acometida = c5.selectbox("Acometida principal", ["10m LK", "20m LK", "30m LK", "50m LK", "Socapex 10m", "Socapex 20m"], key=f"acometida_{i}")
            ap = c6.checkbox("ArrayProcessing (AP) activado", value=True, key=f"ap_{i}")

    # 4. Botonera para gestionar los bloques
    col_add, col_sub, _ = st.columns([1, 1, 2])
    with col_add:
        st.button("➕ Añadir Sistema", on_click=anadir_sistema)
    with col_sub:
        st.button("➖ Quitar Último", on_click=quitar_sistema)

    st.markdown("---")
    
    # 5. Lógica de cálculo final
    if st.button("Calcular Necesidades Totales", type="primary"):
        st.subheader("📋 Resumen de Material")
        
        total_links = 0
        resumen_lineas = []
        
        # Recorremos la memoria para leer lo que has rellenado en cada bloque
        for i in range(st.session_state.num_sistemas):
            nom = st.session_state[f"nombre_{i}"]
            fun = st.session_state[f"funcion_{i}"]
            mod = st.session_state[f"modelo_{i}"]
            caj = st.session_state[f"cajas_{i}"]
            aco = st.session_state[f"acometida_{i}"]
            tiene_ap = st.session_state[f"ap_{i}"]
            
            if caj > 0:
                # Matemática básica (a refinar)
                links = caj - 1 if "SUB" not in mod else caj // 2
                if links < 0: links = 0
                total_links += links
                
                estado_ap = "Sí" if tiene_ap else "No"
                resumen_lineas.append(f"**{nom} ({fun} - {mod}):** {caj} cajas. Lógica base -> {links} links, {aco} (AP: {estado_ap})")
        
        # Imprimimos los resultados
        for linea in resumen_lineas:
            st.write(linea)
            
        st.success(f"📦 **LINKS ESTIMADOS TOTALES (Suma de todos los bloques):** {total_links} unidades.")