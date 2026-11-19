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

st.title("👥 Gestión de Personal y Producción")

# --- GESTOR DE EVENTOS (CARGAR / NUEVO) ---
st.markdown("### 📂 Archivo de Eventos")
c_select, c_btn = st.columns([3, 1])

# Selector para elegir un evento guardado o crear uno nuevo
opciones_eventos = ["+ Crear Nuevo Evento..."] + list(st.session_state.bbdd_eventos.keys())
evento_seleccionado = c_select.selectbox("Selecciona un evento para editar o crea uno nuevo:", opciones_eventos)

if evento_seleccionado == "+ Crear Nuevo Evento...":
    st.session_state.evento_activo = None
else:
    st.session_state.evento_activo = evento_seleccionado

st.markdown("---")

# --- VARIABLES DEL FORMULARIO ---
# Si hay un evento cargado, rellenamos las variables con sus datos. Si es nuevo, en blanco.
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
st.markdown("### 📝 Hoja de Producción")

with st.expander("01 | DATOS GENERALES", expanded=True):
    c1, c2, c3 = st.columns(3)
    nombre_evento = c1.text_input("Nombre del Evento (Ej. Concierto 5 de Marzo)", value=default_nombre)
    recinto = c2.text_input("Recinto / Localización", value=default_recinto)
    cliente = c3.text_input("Cliente / Productora", value=default_cliente)

with st.expander("02 | PERSONAL TÉCNICO", expanded=False):
    st.info("Aquí enlazaremos la BBDD de técnicos (Sheets) para asignar FOH, Monitores, LX...")

with st.expander("06 | AVISOS Y NOTAS INTERNAS", expanded=False):
    notas = st.text_area("Notas pendientes", value=default_notas)

# --- BOTÓN DE GUARDAR / ACTUALIZAR ---
st.markdown("---")
if st.button("💾 Guardar Evento en Base de Datos", type="primary"):
    if not nombre_evento:
        st.error("⚠️ El evento debe tener un nombre para poder guardarlo.")
    else:
        # Guardamos la info escrita en el formulario dentro de nuestra BBDD
        st.session_state.bbdd_eventos[nombre_evento] = {
            "recinto": recinto,
            "cliente": cliente,
            "notas": notas
        }
        st.success(f"✅ Evento '{nombre_evento}' guardado correctamente. (En el futuro, esto se enviará a Google Sheets).")
        st.rerun() # Recarga la página para que el selector de arriba se actualice