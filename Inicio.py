import streamlit as st

st.set_page_config(
    page_title="Gestión Técnica Global",
    page_icon="🎛️",
    layout="wide"
)

st.title("🎛️ Panel de Control Técnico")
st.markdown("""
Bienvenido al sistema unificado de gestión de eventos. 
Usa el **menú lateral izquierdo** para navegar entre las distintas herramientas:

* 🚚 **1. Logística:** Calculadora de estiba, pesos y cubicaje de camiones.
* 🔌 **2. Cableado:** Motor de ruteo 3D para PA y Subgraves.

*Próximamente:* Gestión de personal, cuadrantes, etc.
""")