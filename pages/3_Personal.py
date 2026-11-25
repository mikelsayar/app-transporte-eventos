import streamlit as st
import pandas as pd
import datetime
import copy

st.set_page_config(page_title="Gestión de Personal", page_icon="👥", layout="wide")

# --- 1. BASE DE DATOS DE TÉCNICOS (ROSTER INVISIBLE DE MOMENTO) ---
if "bbdd_tecnicos" not in st.session_state:
    st.session_state.bbdd_tecnicos = {
        "Mikel": ["FOH", "Monitores", "RF", "PA System"],
        "Ane": ["TEC ILUMINACIÓN", "Operadora LX"],
        "Jon": ["TÉC. SONIDO", "Escenario", "Carga"],
        "Sara": ["TÉC. PANTALLA", "Vídeo"],
        "Gorka": ["RIGGING", "Carga"],
        "Ibai": ["FOH", "Monitores", "TÉC. SONIDO"]
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
            "personal": {"dias": 1, "Sonido": [], "Iluminación": [], "Vídeo": [], "Rigging": []}
        }
    }

if "evento_activo" not in st.session_state:
    st.session_state.evento_activo = None

# ==========================================
# PANTALLA PRINCIPAL: HOJA DE PRODUCCIÓN
# ==========================================
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
    default_personal = datos_actuales.get("personal", {"dias": 1, "Sonido": [], "Iluminación": [], "Vídeo": [], "Rigging": []})
    if "dias" not in default_personal:
        default_personal["dias"] = 1
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
    default_personal = {"dias": 1, "Sonido": [], "Iluminación": [], "Vídeo": [], "Rigging": []}

if "edit_personal" not in st.session_state or st.session_state.get("last_event") != default_nombre:
    st.session_state.edit_personal = copy.deepcopy(default_personal)
    st.session_state.last_event = default_nombre


# --- FORMULARIO DE EDICIÓN ---

# [BLOQUE 01 INTACTO Y SELLADO]
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

# --- BLOQUE 02: PERSONAL TÉCNICO ORDENADO POR DÍAS ---
with st.expander("02 | PERSONAL TÉCNICO (Entradas y Salidas)", expanded=True):
    
    col_dias, _ = st.columns([1, 3])
    num_dias = col_dias.number_input("📅 Días de Producción", min_value=1, max_value=15, value=st.session_state.edit_personal.get("dias", 1))
    st.session_state.edit_personal["dias"] = num_dias
    
    st.markdown("---")
    
    roles_por_dpto = {
        "Rigging": ["RIGGING"],
        "Iluminación": ["TEC ILUMINACIÓN", "Operadora LX"],
        "Sonido": ["TÉC. SONIDO", "FOH", "Monitores", "RF", "PA System", "Escenario"],
        "Vídeo": ["TÉC. PANTALLA", "Vídeo"]
    }
    
    fases_evento = ["RIGGING", "MONTAJE", "SHOW", "SHOW + DESMONTAJE", "TURNO 1", "DOBLE TURNO", "TODO EL EVENTO"]
    
    # Creamos las pestañas por DÍAS en lugar de por departamentos
    nombres_pestañas = [f"📅 DÍA {d}" for d in range(1, num_dias + 1)]
    pestañas_dias = st.tabs(nombres_pestañas)
    
    # Iteramos día a día
    for dia_idx, tab_dia in enumerate(pestañas_dias, start=1):
        with tab_dia:
            # Orden de entrada lógico: Rigging -> Luces -> Sonido -> Vídeo
            for dpto, icono in [("Rigging", "⛓️"), ("Iluminación", "💡"), ("Sonido", "🔊"), ("Vídeo", "📺")]:
                st.markdown(f"#### {icono} {dpto}")
                
                # Filtramos los puestos creados para este departamento y en este día
                vacantes_este_dia = [v for v in st.session_state.edit_personal.get(dpto, []) if v.get("dia", 1) == dia_idx]
                
                if vacantes_este_dia:
                    # Nueva estructura de columnas incluyendo los NO DISPONIBLES
                    c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1.5, 1.5, 0.7, 0.4])
                    c1.caption("FASE / ENTRADA")
                    c2.caption("ROL")
                    c3.caption("TÉCNICO ASIGNADO")
                    c4.caption("❌ NO PUEDEN")
                    c5.caption("CONFIRM")
                
                for idx, vacante in enumerate(st.session_state.edit_personal.get(dpto, [])):
                    if vacante.get("dia", 1) == dia_idx:
                        c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1.5, 1.5, 0.7, 0.4])
                        
                        # 1. Fase
                        fase_idx = fases_evento.index(vacante.get("fase", "MONTAJE")) if vacante.get("fase") in fases_evento else 1
                        vacante["fase"] = c1.selectbox("Fase", fases_evento, index=fase_idx, key=f"fase_{dpto}_{idx}", label_visibility="collapsed")
                        
                        # 2. Rol
                        rol_idx = roles_por_dpto[dpto].index(vacante["rol"]) if vacante["rol"] in roles_por_dpto[dpto] else 0
                        vacante["rol"] = c2.selectbox("Rol", roles_por_dpto[dpto], index=rol_idx, key=f"rol_{dpto}_{idx}", label_visibility="collapsed")
                        
                        # 3. Asignado
                        candidatos = [nom for nom, aptitudes in st.session_state.bbdd_tecnicos.items() if vacante["rol"] in aptitudes]
                        opciones_tec = ["--- Sin asignar ---"] + candidatos
                        
                        tec_actual = vacante.get("nombre", "--- Sin asignar ---")
                        if tec_actual not in opciones_tec:
                            tec_actual = "--- Sin asignar ---"
                        tec_idx = opciones_tec.index(tec_actual)
                        
                        vacante["nombre"] = c3.selectbox("Asignado", opciones_tec, index=tec_idx, key=f"tec_{dpto}_{idx}", label_visibility="collapsed")
                        
                        # 4. Los descartados (No pueden)
                        # Recuperamos la lista de técnicos descartados (si los hay)
                        rechazados_prev = vacante.get("no_pueden", [])
                        # Filtramos por si alguien fue borrado de la BBDD general
                        rechazados_prev = [r for r in rechazados_prev if r in candidatos]
                        
                        vacante["no_pueden"] = c4.multiselect(
                            "No pueden", 
                            candidatos, 
                            default=rechazados_prev, 
                            key=f"nopueden_{dpto}_{idx}", 
                            label_visibility="collapsed"
                        )
                        
                        # 5. Confirmado
                        vacante["confirmado"] = c5.checkbox("Sí", value=vacante.get("confirmado", False), key=f"conf_{dpto}_{idx}")
                        
                        # 6. Borrar fila
                        if c6.button("❌", key=f"del_{dpto}_{idx}"):
                            st.session_state.edit_personal[dpto].pop(idx)
                            st.rerun()
                
                # Botón para añadir un hueco en ese departamento y ese día en concreto
                if st.button(f"➕ Añadir Puesto a {dpto}", key=f"add_{dpto}_d{dia_idx}"):
                    if dpto not in st.session_state.edit_personal:
                        st.session_state.edit_personal[dpto] = []
                    
                    st.session_state.edit_personal[dpto].append({
                        "dia": dia_idx,
                        "fase": "MONTAJE",
                        "rol": roles_por_dpto[dpto][0],
                        "nombre": "--- Sin asignar ---",
                        "no_pueden": [],
                        "confirmado": False
                    })
                    st.rerun()
                    
                st.markdown("---")

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
            "personal": st.session_state.edit_personal
        }
        st.session_state.evento_activo = num_produccion
        st.success(f"✅ Evento '{num_produccion}' actualizado en la base de datos.")
        st.rerun()