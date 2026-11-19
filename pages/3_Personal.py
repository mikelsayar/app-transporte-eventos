import streamlit as st

st.set_page_config(page_title="Hoja de Producción", page_icon="📋", layout="wide")

st.title("📋 Hoja de Producción de Evento")
st.markdown("Rellena los datos para generar la orden de trabajo. Próximamente se conectará con Google Sheets.")

# --- 01 DATOS GENERALES ---
with st.expander("01 | DATOS GENERALES Y ENLACES", expanded=True):
    c1, c2, c3 = st.columns(3)
    nombre_evento = c1.text_input("Nombre del Evento (Ej. Gira Verano 2027)")
    recinto = c2.text_input("Recinto / Localización")
    mapa_link = c3.text_input("Enlace a Google Maps")
    
    c4, c5, c6 = st.columns(3)
    cliente = c4.text_input("Cliente / Productora")
    contacto_prod = c5.text_input("Contacto Producción (Nombre y Tlf)")
    contacto_prl = c6.text_input("Contacto PRL")

# --- 02 PERSONAL TÉCNICO ---
with st.expander("02 | PERSONAL TÉCNICO (Asignación)", expanded=False):
    st.info("Próximamente: Aquí irá el motor dinámico de asignación de técnicos filtrado por rol (FOH, Monitores, LX, Vídeo, etc).")
    
    # Ejemplo de cómo se verá visualmente un bloque de sonido
    st.markdown("**Departamento de Sonido**")
    col_rol, col_tec = st.columns(2)
    col_rol.selectbox("Puesto", ["FOH", "Monitores", "Escenario", "RF", "PA System"])
    col_tec.selectbox("Técnico Asignado", ["Selecciona Rol primero..."], disabled=True)
    st.button("➕ Añadir Técnico de Sonido")

# --- 03 PLANNING GENERAL ---
with st.expander("03 | PLANNING Y HORARIOS", expanded=False):
    st.info("Próximamente: Tabla dinámica para añadir filas de horarios (Carga, Montaje, Pruebas, Show).")

# --- 04 LOGÍSTICA Y VEHÍCULOS ---
with st.expander("04 | VEHÍCULOS Y LOGÍSTICA", expanded=False):
    st.info("Próximamente: Asignación de furgonetas, camiones, conductores y horas de salida/destino.")

# --- 05 ALOJAMIENTO Y COMIDAS ---
with st.expander("05 | ALOJAMIENTOS Y DIETAS", expanded=False):
    st.info("Próximamente: Gestión de hoteles, rooming list, horarios de catering y alergias.")

# --- 06 AVISOS Y PRL ---
with st.expander("06 | AVISOS Y SEGURIDAD", expanded=False):
    st.text_area("Notas internas, epis necesarios, requisitos de acreditaciones, etc.")

st.markdown("---")
if st.button("Generar Hoja en Google Sheets (Simulación)", type="primary"):
    if nombre_evento:
        st.success(f"✅ ¡Simulación completada! Se crearía una pestaña llamada '{nombre_evento}' en tu Google Sheets.")
    else:
        st.error("⚠️ Ponle al menos un nombre al evento en el bloque 01 para poder generar la hoja.")