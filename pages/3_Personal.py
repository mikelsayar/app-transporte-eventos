import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Gestión de Personal", page_icon="👥", layout="wide")

# 1. INICIALIZAR LA BASE DE DATOS SIMULADA (Ahora con fechas)
if "bbdd_eventos" not in st.session_state:
    st.session_state.bbdd_eventos = {
        "Zetak - San Mamés": {
            "fecha": datetime.date(2026, 7, 15), 
            "recinto": "San Mamés", 
            "cliente": "Zetak", 
            "notas": "Falta confirmar el hotel de los técnicos de luces."
        },
        "Gira Verano - Guggenheim": {
            "fecha": datetime.date(2026, 8, 15), 
            "recinto": "Guggenheim Atrium", 
            "cliente": "Museo Guggenheim", 
            "notas": "PA reducida por acústica del recinto."
        }
    }

if "evento_activo" not in st.session_state:
    st.session_state.evento_activo = None

st.title("📋 Hoja de Producción y Personal")

# --- BUSCADOR Y ARCHIVO DE EVENTOS ---
st.markdown("### 🔎 Buscar y Cargar Evento")
col_busq, _ = st.columns([2, 2])
texto_busqueda = col_busq.text_input("Buscador libre (Nombre, Cliente o Recinto):", placeholder="Ej. Zetak, Bilbao, Julio...")

# Lógica de filtrado en tiempo real
eventos_filtrados = []
for nombre, datos in st.session_state.bbdd_eventos.items():
    # Comprobamos si el texto introducido coincide con algún dato del evento
    coincide = (
        texto_busqueda.lower() in nombre.lower() or 
        texto_busqueda.lower() in datos.get("cliente", "").lower() or 
        texto_busqueda.lower() in datos.get("recinto", "").lower()
    )
    if coincide:
        eventos_filtrados.append(nombre)

# Ordenar los resultados cronológicamente por la fecha del evento
eventos_filtrados.sort(key=lambda x: st.session_state.bbdd_eventos[x].get("fecha", datetime.date(2000, 1, 1)))

# Selector final
c_select, c_btn = st.columns([3, 1])
opciones_eventos = ["+ Crear Nuevo Evento..."] + eventos_filtrados

# Mantener seleccionado el evento en el que estamos trabajando
idx_seleccion = 0
if st.session_state.evento_activo in opciones_eventos:
    idx_seleccion = opciones_eventos.index(st.session_state.evento_activo)

evento_seleccionado = c_select.selectbox("Resultados de búsqueda:", opciones_eventos, index=idx_seleccion)

if evento_seleccionado == "+ Crear Nuevo Evento...":
    st.session_state.evento_activo = None
else:
    st.session_state.evento_activo = evento_seleccionado

st.markdown("---")

# --- VARIABLES DEL FORMULARIO ---
if st.session_state.evento_activo:
    datos_actuales = st.session_state.bbdd_eventos[st.session_state.evento_activo]
    default_nombre = st.session_state.evento_activo
    default_fecha = datos_actuales.get("fecha", datetime.date.today())
    default_recinto = datos_actuales.get("recinto", "")
    default_cliente = datos_actuales.get("cliente", "")
    default_notas = datos_actuales.get("notas", "")
else:
    default_nombre = ""
    default_fecha = datetime.date.today()
    default_recinto = ""
    default_cliente = ""
    default_notas = ""

# --- FORMULARIO DE EDICIÓN ---
with st.expander("01 | DATOS GENERALES Y ENLACES", expanded=True):
    c1, c2, c3 = st.columns([2, 1, 2])
    nombre_evento = c1.text_input("Nombre del Evento (Identificador único)", value=default_nombre)
    fecha_evento = c2.date_input("Fecha Principal", value=default_fecha)
    recinto = c3.text_input("Recinto / Localización", value=default_recinto)
    
    c4, c5, c6 = st.columns(3)
    cliente = c4.text_input("Cliente / Productora", value=default_cliente)
    contacto_prod = c5.text_input("Contacto Producción (Nombre y Tlf)")
    mapa_link = c6.text_input("Enlace a Google Maps")

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
if st.button("💾 Guardar / Actualizar Evento", type="primary"):
    if not nombre_evento:
        st.error("⚠️ El evento debe tener un nombre para poder guardarlo.")
    else:
        st.session_state.bbdd_eventos[nombre_evento] = {
            "fecha": fecha_evento,
            "recinto": recinto,
            "cliente": cliente,
            "notas": notas
        }
        # Forzamos que la app recuerde que seguimos editando este evento
        st.session_state.evento_activo = nombre_evento
        st.success(f"✅ Evento '{nombre_evento}' actualizado en la base de datos.")
        st.rerun()