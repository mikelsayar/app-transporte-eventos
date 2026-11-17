import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cableado de PA", page_icon="🔌")

st.title("🔌 Gestión de Cableado y Redes")
st.markdown("Calculadora de tiradas, multipines y mangueras para sistemas de PA.")

# Creamos dos pestañas para separar las lógicas
tab_manual, tab_archivo = st.tabs(["⚙️ Cálculo Manual (A máximos)", "📁 Cargar Archivo (ArrayCalc)"])

with tab_manual:
    st.subheader("Configuración del Arreglo (Main PA)")
    
    # Fila de controles
    col1, col2, col3 = st.columns(3)
    with col1:
        sistema = st.selectbox("Sistema", ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series", "d&b SL-SUB"])
    with col2:
        cajas_por_lado = st.number_input("Cajas por arreglo", min_value=1, max_value=24, value=10)
    with col3:
        distancia_lk = st.selectbox("Acometida principal (LK)", ["10m", "20m", "30m", "50m"])
        
    # Checkboxes para opciones extra que afectan al cableado
    st.markdown("**Opciones de ruteo**")
    array_processing = st.checkbox("ArrayProcessing (AP) activado", value=True)
    
    if st.button("Calcular Necesidades de Cableado"):
        st.markdown("---")
        st.markdown(f"### 📋 Listado de Material por Lado ({sistema})")
        
        # Matemática de cables (A refinar en el siguiente paso)
        links_audio = cajas_por_lado - 1
        
        # Lógica MUY básica de multipines (la mejoraremos luego para AP)
        if array_processing:
             multipin = 2 # Si hay AP, a bulto pedimos 2 LKs por ahora
             breakout = 2
        else:
             multipin = 1
             breakout = 1
        
        # Construimos una tabla de datos
        resultados = pd.DataFrame({
            "Cantidad": [links_audio, breakout, multipin],
            "Tipo de Material": [
                f"Link NLT4 (1m)", 
                "Breakout LK a NLT4", 
                f"Manguera LK ({distancia_lk})"
            ],
            "Aplicación": [
                "Puenteo entre cajas", 
                "Transición Racks D80/D40 -> LK", 
                "Tirada principal hasta el motor"
            ]
        })
        
        st.table(resultados)
        st.success(f"📦 **TOTAL PARA L+R:** {links_audio * 2}x Links NLT4, {breakout * 2}x Breakouts, {multipin * 2}x Mangueras LK {distancia_lk}.")

with tab_archivo:
    st.subheader("Cargar Export de ArrayCalc")
    st.markdown("Sube el archivo CSV exportado desde d&b ArrayCalc para leer el patch exacto.")
    
    uploaded_file = st.file_uploader("Sube tu archivo CSV de ArrayCalc", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Leemos el CSV
            df_arraycalc = pd.read_csv(uploaded_file)
            st.success("¡Archivo cargado correctamente!")
            
            # Mostramos los datos crudos por ahora para verificar
            st.markdown("**Datos extraídos del archivo:**")
            st.dataframe(df_arraycalc)
            
            # Aquí añadiremos luego la lógica para contar cajas por arreglo desde el CSV
            st.info("Próximamente: Lectura automática de links y LKs basada en las columnas del CSV.")
            
        except Exception as e:
            st.error(f"Hubo un error al procesar el archivo: {e}")