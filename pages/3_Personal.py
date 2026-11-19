import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestión de Personal", page_icon="👥", layout="wide")

# 1. INICIALIZAR LA BASE DE DATOS SIMULADA EN MEMORIA
if "bbdd_eventos" not in st.session_state:
    st.session_state.bbdd_eventos = {
        "Concierto 5 de Marzo": {
            "recinto": "San Mamés", 
            "cliente": "Zetak", 
            "notas": "Falta confirmar el hotel de los técnicos de luces."
        }
    }

if "evento_activo" not in st.session_state:
    st.session_state.evento_activo = None

st.title("📋 Hoja de Producción y Personal")

# --- GESTOR DE EVENTOS (CARGAR / NUEVO) ---
st.markdown("### 📂 Archivo de Eventos")
c_select, c_btn = st.columns([3, 1])

opciones_eventos = ["+ Crear Nuevo Evento..."] + list(st.session_state.bbdd_eventos.keys())
evento_seleccionado = c_select.selectbox("Selecciona un evento para editar o crea uno nuevo:", opciones_eventos)

if evento_seleccionado == "+ Crear Nuevo Evento...":
    st.session_state.evento_activo = None
else:
    st.session_state.evento_activo = evento_seleccionado

st.markdown("---")

# --- VARIABLES DEL FORMULARIO ---
if st.session_state.evento_activo:
    datos_actuales = st.session_state.bbdd_eventos[st.session_state.evento_activo]
    default_nombre = st.session_state.evento_activo
    default_recinto = datos_actuales.get("recinto", "")
    default_cliente = datos_actuales.get("cliente", "")
    default_notas = datos_actuales.get("notas", "")
else:
    default_nombre = ""
    default_recinto = ""
    default_cliente = ""
    default_notas = ""

# --- FORMULARIO DE EDICIÓN ---
with st.expander("01 | DATOS GENERALES Y ENLACES", expanded=True):
    c1, c2, c3 = st.columns(3)
    nombre_evento = c1.text_input("Nombre del Evento", value=default_nombre)
    recinto = c2.text_input("Recinto / Localización", value=default_recinto)
    mapa_link = c3.text_input("Enlace a Google Maps")
    
    c4, c5, c6 = st.columns(3)
    cliente = c4.text_input("Cliente / Productora", value=default_cliente)
    contacto_prod = c5.text_input("Contacto Producción (Nombre y Tlf)")
    contacto_prl = c6.text_input("Contacto PRL")

with st.expander("02 | PERSONAL TÉCNICO (Asignación)", expanded=False):
    st.info("Próximamente: Motor dinámico de asignación de técnicos filtrado por rol (FOH, Monitores, LX, Vídeo...).")

with st.expander("03 | PLANNING Y HORARIOS", expanded=False):
    st.info("Próximamente: Tabla dinámica para añadir filas de horarios (Carga, Montaje, Pruebas, Show).")

with st.expander("04 | VEHÍCULOS Y LOGÍSTICA", expanded=False):
    st.info("Próximamente: Asignación de furgonetas, camiones, conductores y horas de salida/destino.")

with st.expander("05 | ALOJAMIENTOS Y DIETAS", expanded=False):
    st.info("Próximamente: Gestión de hoteles, rooming list, horarios de catering y alergias.")

with st.expander("06 | AVISOS Y SEGURIDAD", expanded=False):
    notas = st.text_area("Notas internas, epis necesarios, acreditaciones, etc.", value=default_notas)

# --- BOTÓN DE GUARDAR / ACTUALIZAR ---
st.markdown("---")
if st.button("💾 Guardar Evento en Base de Datos", type="primary"):
    if not nombre_evento:
        st.error("⚠️ El evento debe tener un nombre para poder guardarlo.")
    else:
        st.session_state.bbdd_eventos[nombre_evento] = {
            "recinto": recinto,
            "cliente": cliente,
            "notas": notas
        }
        st.success(f"✅ Evento '{nombre_evento}' guardado en la memoria de la aplicación.")
        st.rerun()