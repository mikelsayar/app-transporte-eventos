import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Calculadora de Ruteo PA", layout="wide", page_icon="🔌")

# --- CONEXIÓN A GOOGLE SHEETS ---
CSV_URL_CABLES = "https://docs.google.com/spreadsheets/d/1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c/export?format=csv&gid=237384040"

@st.cache_data(ttl=60)
def cargar_cables():
    try:
        df = pd.read_csv(CSV_URL_CABLES)
        # Limpieza básica de columnas por si hay espacios
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return None

df_cables = cargar_cables()

st.title("🔌 Motor de Cableado y Ruteo")

if df_cables is None or df_cables.empty:
    st.warning("⚠️ La pestaña de Cables está vacía o no se puede leer. Usando cálculo teórico genérico.")
else:
    st.success(f"☁️ Inventario de cables conectado ({len(df_cables)} referencias encontradas).")

# --- 1. GEOMETRÍA ---
st.subheader("📐 1. Geometría de Tiro")
col1, col2, col3 = st.columns(3)

with col1:
    h_trim = st.number_input("Altura del Bumper PA (Trim) en metros:", min_value=0.0, value=12.0, step=0.5)
with col2:
    d_rack = st.number_input("Distancia horizontal Bumper-Etapas (m):", min_value=0.0, value=10.0, step=0.5)
with col3:
    holgura = st.slider("Holgura de seguridad (peinado y caídas):", min_value=1.0, max_value=1.5, value=1.15, step=0.05, help="1.15 = 15% extra")

dist_necesaria = math.sqrt((h_trim**2) + (d_rack**2)) * holgura
st.info(f"**Tirada mínima requerida al aire:** {dist_necesaria:.2f} metros")

# --- 2. CONFIGURACIÓN DEL SISTEMA ---
st.subheader("🔊 2. Arreglo Principal y Subgraves (Por Lado)")
c1, c2 = st.columns(2)

with c1:
    st.markdown("**PA Principal**")
    sistema_pa = st.selectbox("Sistema de PA:", ["d&b audiotechnik (KSL/XSL)", "L-Acoustics (dV-DOSC)"])
    cajas_pa = st.number_input("Número de cajas PA (por lado):", min_value=0, value=12, step=1)
    if "d&b" in sistema_pa:
        modo_pa = st.radio("Modo de amplificación PA:", ["ArrayProcessing (1 canal/caja)", "Line Link (2 cajas/canal)"])
    else:
        modo_pa = st.radio("Ratio de Linkeo PA:", ["2 Cajas por canal", "3 Cajas por canal"])

with c2:
    st.markdown("**Subgraves**")
    sistema_sub = st.selectbox("Sistema de Subs:", ["d&b audiotechnik (SL-SUB)", "L-Acoustics (dV-SUB / SB218)"])
    cajas_sub = st.number_input("Número de Subgraves (por lado):", min_value=0, value=4, step=1)


st.divider()

# --- 3. MOTOR MATEMÁTICO DE RUTEO ---
st.subheader("📦 Lista de Preparación de Cableado (Por Lado)")

lista_preparacion = []
barriletes_nl8 = 0
barriletes_nl4 = 0

# --- LÓGICA PA PRINCIPAL ---
if cajas_pa > 0:
    lista_preparacion.append("### 🔸 PA Principal")
    if "d&b" in sistema_pa:
        # Canales según AP o Link
        canales_pa = cajas_pa if "ArrayProcessing" in modo_pa else math.ceil(cajas_pa / 2.0)
        
        num_lk25 = canales_pa // 6
        resto = canales_pa % 6
        num_nlt8 = resto // 2
        num_nlt4 = resto % 2
        
        if num_lk25 > 0:
            lista_preparacion.append(f"- **{num_lk25}x Manguera LK25** de tiro (≥ {dist_necesaria:.1f}m)")
            lista_preparacion.append(f"  - *{num_lk25}x Breakout LK25 a 6xNLT4*")
        if num_nlt8 > 0:
            lista_preparacion.append(f"- **{num_nlt8}x Manguera NLT8** de tiro (≥ {dist_necesaria:.1f}m)")
            lista_preparacion.append(f"  - *{num_nlt8}x Bifurca NLT8 a 2xNLT4*")
        if num_nlt4 > 0:
            lista_preparacion.append(f"- **{num_nlt4}x Manguera NLT4** de tiro directa (≥ {dist_necesaria:.1f}m)")
            
    else: # L-Acoustics dV-DOSC
        ratio = 2 if "2 Cajas" in modo_pa else 3
        lineas_nl4 = math.ceil(cajas_pa / ratio)
        links_internos = cajas_pa - lineas_nl4
        
        # Cada NL8 alimenta 2 líneas biamplificadas de NL4
        num_nl8 = lineas_nl4 // 2
        num_nl4 = lineas_nl4 % 2
        
        if num_nl8 > 0:
            lista_preparacion.append(f"- **{num_nl8}x Manguera NL8** de tiro (≥ {dist_necesaria:.1f}m)")
            lista_preparacion.append(f"  - *{num_nl8}x Bifurca NL8 a 2xNL4*")
            barriletes_nl8 += num_nl8 # Requiere barrilete para conectar el Breakout
        if num_nl4 > 0:
            lista_preparacion.append(f"- **{num_nl4}x Manguera NL4** de tiro directa (≥ {dist_necesaria:.1f}m)")
        if links_internos > 0:
            lista_preparacion.append(f"- **{links_internos}x Latiguillo Link NL4** (1m aprox) para puenteo entre cajas.")

# --- LÓGICA SUBGRAVES ---
if cajas_sub > 0:
    lista_preparacion.append("\n### 🔹 Subgraves")
    # Asumimos que los subs están en el suelo, la distancia es d_rack directa + holgura
    dist_subs = d_rack * holgura
    if dist_subs < 5: dist_subs = 5.0 # Mínimo vital
    
    if "d&b" in sistema_sub:
        # SL-SUB: 1 cajón = 2 canales. Un NLT8 cubre 2 cajones.
        num_nlt8 = cajas_sub // 2
        num_nlt4 = cajas_sub % 2
        
        if num_nlt8 > 0:
            lista_preparacion.append(f"- **{num_nlt8}x Manguera NLT8** (Suelo: ≥ {dist_subs:.1f}m)")
            lista_preparacion.append(f"  - *{num_nlt8}x Bifurca NLT8 a 2xNLT4*")
        if num_nlt4 > 0:
            lista_preparacion.append(f"- **{num_nlt4}x Manguera NLT4** directa (Suelo: ≥ {dist_subs:.1f}m)")
            
    else: # L-Acoustics Subs
        # 1 cajón = 1 línea NL4. Un NL8 cubre 4 cajones.
        num_nl8 = cajas_sub // 4
        num_nl4 = cajas_sub % 4
        
        if num_nl8 > 0:
            lista_preparacion.append(f"- **{num_nl8}x Manguera NL8** (Suelo: ≥ {dist_subs:.1f}m)")
            lista_preparacion.append(f"  - *{num_nl8}x Breakout NL8 a 4xNL4*")
            barriletes_nl8 += num_nl8 # Requiere barrilete
        if num_nl4 > 0:
            lista_preparacion.append(f"- **{num_nl4}x Manguera NL4** directa (Suelo: ≥ {dist_subs:.1f}m)")

# --- SUMATORIO DE ADAPTADORES ---
if barriletes_nl8 > 0 or barriletes_nl4 > 0:
    lista_preparacion.append("\n### 🔗 Empalmes y Barriletes (Automáticos)")
    if barriletes_nl8 > 0:
        lista_preparacion.append(f"- **{barriletes_nl8}x Barrilete Empalme NL8** (Para enganchar las bifurcas/breakouts de L-Acoustics al tiro principal)")
    if barriletes_nl4 > 0:
        lista_preparacion.append(f"- **{barriletes_nl4}x Barrilete Empalme NL4**")

# --- RENDERIZADO DE RESULTADOS ---
for linea in lista_preparacion:
    st.markdown(linea)

# --- ESPACIO PARA EL BUSCADOR DE STOCK ---
st.divider()
st.info("💡 *El siguiente paso evolutivo de esta sección será cruzar estos requisitos (ej: 'LK25 ≥ 13.8m') con tu Excel para devolverte: '1x Manguera LK25 de 15m (Stock OK)'.*")
