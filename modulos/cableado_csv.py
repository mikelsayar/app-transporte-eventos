import streamlit as st
import pandas as pd

def mostrar_carga_csv():
    st.subheader("Cargar Export de ArrayCalc")
    st.markdown("Sube el archivo CSV exportado desde d&b ArrayCalc para leer el patch exacto.")
    
    uploaded_file = st.file_uploader("Sube tu archivo CSV de ArrayCalc", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df_arraycalc = pd.read_csv(uploaded_file)
            st.success("¡Archivo cargado correctamente!")
            st.dataframe(df_arraycalc)
            st.info("Próximamente: Lectura automática de links y LKs basada en las columnas del CSV.")
        except Exception as e:
            st.error(f"Hubo un error al procesar el archivo: {e}")