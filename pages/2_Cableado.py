import streamlit as st
from modulos.cableado_manual import mostrar_calculadora_manual
from modulos.cableado_csv import mostrar_carga_csv

st.set_page_config(page_title="Cableado de PA", page_icon="🔌", layout="wide")

st.title("🔌 Gestión de Cableado y Redes")

tab_manual, tab_archivo = st.tabs(["⚙️ Cálculo Manual (A máximos)", "📁 Cargar Archivo (ArrayCalc)"])

with tab_manual:
    mostrar_calculadora_manual()

with tab_archivo:
    mostrar_carga_csv()