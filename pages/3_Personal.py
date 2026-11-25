import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Gestión de Personal", page_icon="👥", layout="wide")

# --- 1. BASE DE DATOS DE TÉCNICOS (ROSTER) ---
if "bbdd_tecnicos" not in st.session_state:
    st.session_state.bbdd_tecnicos = {
        "Mikel": ["FOH", "Monitores", "RF", "PA System"],
        "Ane": ["Téc. Iluminación", "Operadora LX"],
        "Jon": ["Téc. Sonido", "Escenario", "Carga"],
        "Sara": ["Téc. Pantalla", "Vídeo"],
        "Gorka": ["Rigging", "Carga"],
        "Ibai": ["FOH", "Monitores", "Téc. Sonido"]
    }

# --- 2. BASE DE DATOS DE EVENTOS ---
if "bbdd_eventos" not in st.session_state:
    st.session_state.bbdd_eventos = {
        "PROD-001 | Zetak - San Mamés": {
            "fecha": datetime.date(2026, 7, 15), 
            "recinto": "San Mamés",
            "mapa_link": "https://maps.google.com/...",
            "cliente": "Zetak",
            "contacto": "Gorka",
            "telefono": "600123456",
            "email": "gorka@zetak.com",
            "prl_contacto": "Ana",
            "prl_plataforma": "Obralia",
            "acreditaciones": "Pulseras en puerta 0",
            "toro": "Sí, 1 toro con conductor",
            "personal_cd": "4 manos carga/descarga",
            "notas": "Falta confirmar el hotel de los técnicos de luces.",
            # Memoria del personal asignado a este evento
            "personal": {"Sonido": [], "Iluminación": [], "Vídeo": [], "Rigging": []}
        }
    }

if "evento_activo" not in st.session_state:
    st.session_state.evento_activo = None

st.title("📋 Hoja de Producción y Personal")

# --- BUSCADOR Y ARCHIVO DE EVENTOS ---
st.markdown("### 🔎 Buscar y Cargar Evento")
col_busq, _ = st.columns([2, 2])
texto_busqueda = col_busq.text_input("Buscador libre (Nombre, Cliente o Recinto):", placeholder="Ej. Zetak, Bilbao, Julio...")

eventos_filtrados = []
for nombre, datos in st.session_state.bbdd_eventos.items():
    coincide = (
        texto_busqueda.lower() in nombre.lower() or 
        texto_busqueda.lower() in datos.get("cliente", "").lower() or 
        texto_busqueda.lower() in datos.get("recinto", "").lower()
    )
    if coincide:
        eventos_filtrados.append(nombre)

eventos_filtrados.sort(key=lambda x: st.session_state.bbdd_eventos[x].get("fecha", datetime.date(2000, 1, 1)))

c_select, c_btn = st.columns([3, 1])
opciones_eventos = ["+ Crear Nuevo Evento..."] + eventos_filtrados

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
    default_mapa = datos_actuales.get("mapa_link", "")
    default_cliente = datos_actuales.get("cliente", "")
    default_contacto = datos_actuales.get("contacto", "")
    default_telefono = datos_actuales.get("telefono", "")
    default_email = datos_actuales.get("email", "")
    default_prl = datos_actuales.get("prl_contacto", "")
    default_prl_plat = datos_actuales.get("prl_plataforma", "")
    default_acred = datos_actuales.get("acreditaciones", "")
    default_toro = datos_actuales.get("toro", "")
    default_personal_cd = datos_actuales.get("personal_cd", "")
    default_notas = datos_actuales.get("notas", "")
    default_personal = datos_actuales.get("personal", {"Sonido": [], "Iluminación": [], "Vídeo": [], "Rigging": []})
else:
    default_nombre = ""
    default_fecha = datetime.date.today()
    default_recinto = ""
    default_mapa = ""
    default_cliente = ""
    default_contacto = ""
    default_telefono = ""
    default_email = ""
    default_prl = ""
    default_prl_plat = ""
    default_acred = ""
    default_toro = ""
    default_personal_cd = ""
    default_notas = ""
    default_personal = {"Sonido": [], "Iluminación": [], "Vídeo": [], "Rigging": []}

# Memoria temporal para la edición del personal en la interfaz
if "edit_personal" not in st.session_state or st.session_state.get("last_event") != default_nombre:
    # Hacemos una copia para no alterar la BBDD hasta que se pulse "Guardar"
    import copy
    st.session_state.edit_personal = copy.deepcopy(default_personal)
    st.session_state.last_event = default_nombre

# --- FORMULARIO DE EDICIÓN ---
with st.expander("01 | DATOS GENERALES Y ENLACES", expanded=True):
    c1, c2, c3, c4 = st.columns([1.5, 1, 1.5, 1.5])
    num_produccion = c1.text_input("Nº Producción / Nombre Evento", value=default_nombre, placeholder="Ej. PROD-001 | Gira Verano")
    fecha_evento = c2.date_input("Fecha", value=default_fecha)
    recinto = c3.text_input("Recinto", value=default_recinto)
    mapa_link = c4.text_input("Mapa / Link", value=default_mapa)
    st.markdown("---")
    c5, c6, c7, c8 = st.columns(4)
    cliente = c5.text_input("Cliente", value=default_cliente)
    contacto = c6.text_input("Contacto", value=default_contacto)
    telefono = c7.text_input("Teléfono", value=default_telefono)
    email = c8.text_input("Email", value=default_email)
    st.markdown("---")
    col_prl, col_log = st.columns(2)
    with col_prl:
        prl_contacto = st.text_input("PRL Contacto", value=default_prl)
        prl_plataforma = st.text_input("Plataforma PRL", value=default_prl_plat)
        acreditaciones = st.text_input("Acreditaciones", value=default_acred)
    with col_log:
        toro = st.text_input("Toro / Torero", value=default_toro)
        personal_cd = st.text_input("Personal C/D", value=default_personal_cd)

# --- BLOQUE 02: PERSONAL TÉCNICO ---
with st.expander("02 | PERSONAL TÉCNICO (Asignación)", expanded=True):
    st.markdown("Asigna los perfiles necesarios para cada departamento. Los técnicos se filtrarán según sus aptitudes.")
    
    # Definimos los roles posibles por departamento
    roles_por_dpto = {
        "Sonido": ["FOH", "Monitores", "PA System", "RF", "Escenario", "Téc. Sonido"],
        "Iluminación": ["Operadora LX", "Téc. Iluminación"],
        "Vídeo": ["Téc. Pantalla", "Vídeo"],
        "Rigging": ["Rigging"]
    }
    
    tab_so, tab_lx, tab_vid, tab_rig = st.tabs(["🔊 Sonido", "💡 Iluminación", "📺 Vídeo", "⛓️ Rigging"])
    
    def mostrar_dpto(nombre_dpto, tab):
        with tab:
            # Mostramos los asignados actualmente
            if st.session_state.edit_personal[nombre_dpto]:
                for idx, asignacion in enumerate(st.session_state.edit_personal[nombre_dpto]):
                    col_rol, col_nom, col_del = st.columns([2, 2, 1])
                    col_rol.markdown(f"**{asignacion['rol']}**")
                    col_nom.markdown(f"👤 {asignacion['nombre']}")
                    if col_del.button("❌ Quitar", key=f"del_{nombre_dpto}_{idx}"):
                        st.session_state.edit_personal[nombre_dpto].pop(idx)
                        st.rerun()
                st.markdown("---")
            
            # Selector para añadir nuevos
            c_rol, c_tec, c_btn_add = st.columns([2, 2, 1])
            rol_elegido = c_rol.selectbox("Rol", roles_por_dpto[nombre_dpto], key=f"rol_{nombre_dpto}")
            
            # Filtrar el Roster: ¿Quién tiene esta etiqueta en sus habilidades?
            candidatos = [nom for nom, aptitudes in st.session_state.bbdd_tecnicos.items() if rol_elegido in aptitudes]
            
            if not candidatos:
                tec_elegido = c_tec.selectbox("Técnico", ["Ningún técnico con este rol"], disabled=True, key=f"tec_{nombre_dpto}")
                c_btn_add.button("Añadir", disabled=True, key=f"add_{nombre_dpto}")
            else:
                tec_elegido = c_tec.selectbox("Técnico", candidatos, key=f"tec_{nombre_dpto}")
                if c_btn_add.button("➕ Añadir", key=f"add_{nombre_dpto}"):
                    st.session_state.edit_personal[nombre_dpto].append({"rol": rol_elegido, "nombre": tec_elegido})
                    st.rerun()

    mostrar_dpto("Sonido", tab_so)
    mostrar_dpto("Iluminación", tab_lx)
    mostrar_dpto("Vídeo", tab_vid)
    mostrar_dpto("Rigging", tab_rig)

with st.expander("03 | PLANNING Y HORARIOS", expanded=False):
    st.info("Próximamente: Tabla dinámica para horarios.")

with st.expander("04 | VEHÍCULOS Y LOGÍSTICA", expanded=False):
    st.info("Próximamente: Asignación de vehículos.")

with st.expander("05 | ALOJAMIENTOS Y DIETAS", expanded=False):
    st.info("Próximamente: Gestión de hoteles.")

with st.expander("06 | AVISOS Y SEGURIDAD", expanded=False):
    notas = st.text_area("Notas internas", value=default_notas)

# --- BOTÓN DE GUARDAR / ACTUALIZAR ---
st.markdown("---")
if st.button("💾 Guardar / Actualizar Evento", type="primary"):
    if not num_produccion:
        st.error("⚠️ El evento debe tener un 'Nº Producción / Nombre' para poder guardarlo.")
    else:
        st.session_state.bbdd_eventos[num_produccion] = {
            "fecha": fecha_evento,
            "recinto": recinto,
            "mapa_link": mapa_link,
            "cliente": cliente,
            "contacto": contacto,
            "telefono": telefono,
            "email": email,
            "prl_contacto": prl_contacto,
            "prl_plataforma": prl_plataforma,
            "acreditaciones": acreditaciones,
            "toro": toro,
            "personal_cd": personal_cd,
            "notas": notas,
            # Guardamos la plantilla de personal al pulsar el botón final
            "personal": st.session_state.edit_personal
        }
        st.session_state.evento_activo = num_produccion
        st.success(f"✅ Evento '{num_produccion}' actualizado en la base de datos.")
        st.rerun()