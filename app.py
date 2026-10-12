import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

CSV_URL = "https://docs.google.com/spreadsheets/d/1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c/export?format=csv"

def parse_num(val, default=0.0):
    if pd.isna(val) or val is None or str(val).strip() == '':
        return default
    val_str = str(val).replace(',', '.').strip()
    try:
        return float(val_str)
    except:
        return default

@st.cache_data(ttl=60)
def cargar_catalogo():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except:
        return None

df_catalogo = cargar_catalogo()

st.title("🚛 Gestor de Transporte y Estiba de Eventos")

if df_catalogo is None:
    st.error("⚠️ Error temporal al leer Google Sheets. Reintentando...")
else:
    st.success("☁️ Sincronizado en tiempo real con tu Catálogo de Google Drive.")

col_izq, col_der = st.columns([1, 2])
cantidades = {}

COLORES_CAT = {
    "PA / Cajas": "#1971C2",
    "Subgraves": "#7048E8",
    "Rigging / Motores": "#F59F00",
    "Rigging / Estructura": "#1098AD",
    "Amplificación": "#E8590C",
    "Control / FOH": "#2F9E44",
    "Monitores": "#20C997",
    "Cableado": "#495057",
    "Cableado / Accesorios": "#495057",
    "Varios": "#6C757D"
}

# Prioridad física de carga (de cabecera a trasera)
ORDEN_CARGA_CAT = {
    "PA / Cajas": 1,
    "Subgraves": 2,
    "Rigging / Motores": 3,
    "Rigging / Estructura": 4,
    "Amplificación": 5,
    "Control / FOH": 6,
    "Monitores": 7,
    "Cableado": 8,
    "Cableado / Accesorios": 9,
    "Varios": 10
}

with col_izq:
    st.subheader("📄 Carga de Albarán")
    archivo = st.file_uploader("Arrastra el PDF o foto del albarán", type=["pdf", "png", "jpg", "jpeg"])
    if archivo:
        st.info(f"Albarán recibido: {archivo.name}")

    st.subheader("📋 Dotación de Material")
    if df_catalogo is not None:
        for idx, row in df_catalogo.iterrows():
            nombre = str(row.get("Descripción / Unidad Logística", f"Bulto {idx+1}"))
            codigo = str(row.get("ID / Código", f"B{idx+1}"))
            
            val_def = 4 if "KSL" in nombre and "Bumper" not in nombre else (2 if "SL-SUB" in nombre else (9 if "D80" in nombre else (8 if "120x60" in nombre else 0)))
            cantidades[codigo] = st.number_input(nombre, min_value=0, value=val_def, step=1, key=f"inp_{codigo}")

# 1. GENERACIÓN DE HUELLAS FÍSICAS DE SUELO (APILADOS)
huellas_suelo = []
peso_total = 0.0

if df_catalogo is not None:
    for idx, row in df_catalogo.iterrows():
        codigo = str(row.get("ID / Código", f"B{idx+1}"))
        cant = cantidades.get(codigo, 0)
        
        if cant > 0:
            nombre = str(row.get("Descripción / Unidad Logística", codigo))
            categoria = str(row.get("Categoría", "Varios"))
            peso_u = parse_num(row.get("Peso Bruto por bulto (kg)", 0))
            ancho_cm = parse_num(row.get("Ancho al frontal de carga (cm)", 60))
            fondo_cm = parse_num(row.get("Fondo de calle (cm)", 80))
            max_stack = max(1, int(parse_num(row.get("Alturas de apilado", 1))))
            
            puede_rotar = ("baúl" in nombre.lower()) or ("baul" in nombre.lower()) or ("cables" in nombre.lower())
            
            ancho_m = max(0.30, ancho_cm / 100.0)
            fondo_m = max(0.30, fondo_cm / 100.0)
            
            peso_total += cant * peso_u
            
            torres_completas = cant // max_stack
            sobrante = cant % max_stack
            
            for _ in range(torres_completas):
                huellas_suelo.append({
                    "nombre": nombre,
                    "categoria": categoria,
                    "ancho": ancho_m,
                    "fondo": fondo_m,
                    "color": COLORES_CAT.get(categoria, "#495057"),
                    "peso": peso_u * max_stack,
                    "alturas": max_stack,
                    "puede_rotar": puede_rotar
                })
            if sobrante > 0:
                huellas_suelo.append({
                    "nombre": nombre,
                    "categoria": categoria,
                    "ancho": ancho_m,
                    "fondo": fondo_m,
                    "color": COLORES_CAT.get(categoria, "#495057"),
                    "peso": peso_u * sobrante,
                    "alturas": sobrante,
                    "puede_rotar": puede_rotar
                })

# 2. MOTOR DE ESTIBA PROFESIONAL: LÍNEAS COMPLETAS + PICOS AL FINAL
ANCHO_CAMION = 2.48
LARGO_CAMION = 13.60

groups = defaultdict(list)
for it in huellas_suelo:
    groups[(it['categoria'], it['nombre'], it['ancho'], it['fondo'])].append(it)

lineas_completas = []
picos = []

for key, item_group in groups.items():
    cat, nombre, ancho, fondo = key
    max_a_lo_ancho = int(ANCHO_CAMION // ancho)
    
    # Extraer bloques que completan líneas enteras de pared a pared
    while len(item_group) >= max_a_lo_ancho and max_a_lo_ancho > 0:
        lineas_completas.append((cat, fondo, item_group[:max_a_lo_ancho]))
        item_group = item_group[max_a_lo_ancho:]
    picos.extend(item_group)

# Ordenar las líneas completas por prioridad de carga (PA -> Subs -> D80 -> Cables)
lineas_completas.sort(key=lambda x: (ORDEN_CARGA_CAT.get(x[0], 10), -x[1]))

placed = []
cur_x = 0.03

# Colocar primero las líneas completas
for cat, fondo_linea, line_items in lineas_completas:
    cur_y = 0.02
    for it in line_items:
        placed.append({
            'x': cur_x, 'y': cur_y, 'w_x': it['fondo'], 'h_y': it['ancho'],
            'nombre': it['nombre'], 'color': it['color'], 'alturas': it['alturas']
        })
        cur_y += it['ancho'] + 0.005
    cur_x += fondo_linea + 0.02

# Colocar los bultos impares / picos al final
picos.sort(key=lambda x: (ORDEN_CARGA_CAT.get(x['categoria'], 10), -x['fondo'], -x['ancho']))

while picos:
    seed = picos.pop(0)
    calle = [seed]
    rem_w = ANCHO_CAMION - seed['ancho'] - 0.01
    
    i = 0
    while i < len(picos) and rem_w >= 0.35:
        if picos[i]['ancho'] <= rem_w + 0.01:
            calle.append(picos.pop(i))
            rem_w -= (calle[-1]['ancho'] + 0.005)
        elif picos[i].get('puede_rotar', False) and (picos[i]['fondo'] <= rem_w + 0.01):
            rot = dict(picos.pop(i))
            rot['ancho'], rot['fondo'] = rot['fondo'], rot['ancho']
            calle.append(rot)
            rem_w -= (rot['ancho'] + 0.005)
        else:
            i += 1
            
    cur_y = 0.02
    max_f = max(it['fondo'] for it in calle)
    for it in calle:
        placed.append({
            'x': cur_x, 'y': cur_y, 'w_x': it['fondo'], 'h_y': it['ancho'],
            'nombre': it['nombre'], 'color': it['color'], 'alturas': it['alturas']
        })
        cur_y += it['ancho'] + 0.005
    cur_x += max_f + 0.02

total_ml = max([p['x'] + p['w_x'] for p in placed]) if placed else 0.0
ml_con_holgura = total_ml * 1.05

def alias_corto(name, alturas):
    n = name.lower()
    if "ksl" in n and "bumper" not in n:
        base = "KSL"
    elif "sl-sub" in n:
        base = "SL-SUB"
    elif "d80" in n:
        base = "D80"
    elif "d40" in n:
        base = "D40"
    elif "120" in n or ("cables" in n and "baúl" in n):
        base = "Baúl 120"
    elif "80" in n:
        base = "Baúl 80"
    elif "quantum" in n or "digico" in n:
        base = "Q338"
    elif "bumper" in n:
        base = "Bumper"
    elif "motor" in n:
        base = "Motores"
    else:
        base = name[:9]
    if alturas > 1:
        return f"{base}\n({alturas} alt)"
    return base

with col_der:
    st.subheader("📊 Resumen Logístico de Carga")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metros Lineales (Fondo)", f"{ml_con_holgura:.2f} ML", f"Neto: {total_ml:.2f} m")
    m2.metric("Peso Total Estimado", f"{peso_total:,.0f} kg")
    
    if ml_con_holgura <= 7.8 and peso_total <= 9000:
        vehiculo = "Rígido 18t (8.0m)"
    else:
        vehiculo = "Tráiler 13.60m"
    m3.metric("Vehículo Óptimo", vehiculo)

    ocupacion = min(100, int((ml_con_holgura / LARGO_CAMION) * 100))
    m4.metric("Ocupación Tráiler", f"{ocupacion}%", f"{max(0.0, LARGO_CAMION - ml_con_holgura):.1f} m libres")

    st.subheader("📐 Esquema de Estiba en Planta")
    
    fig, ax = plt.subplots(figsize=(13, 3.8))
    ax.add_patch(patches.Rectangle((0, 0), LARGO_CAMION, ANCHO_CAMION, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    for b in placed:
        rect = patches.FancyBboxPatch(
            (b["x"], b["y"]), b["w_x"], b["h_y"],
            boxstyle="round,pad=0.01", linewidth=1.1,
            edgecolor='#1E1E1E', facecolor=b["color"], alpha=0.90
        )
        ax.add_patch(rect)
        
        lbl = alias_corto(b["nombre"], b["alturas"])
        ax.text(
            b["x"] + b["w_x"]/2, b["y"] + b["h_y"]/2, 
            lbl, color='white', ha='center', va='center', fontsize=7.5, fontweight='bold'
        )

    if ml_con_holgura > 0:
        ax.axvline(x=ml_con_holgura, color='#D6336C', linestyle='--', linewidth=2.5)
        ax.text(ml_con_holgura + 0.15, 1.24, f"FIN DE CARGA\n{ml_con_holgura:.2f} ML", 
                color='#D6336C', fontsize=8.5, fontweight='bold', va='center')

    ax.text(0.1, ANCHO_CAMION + 0.12, "FRENTE / CABECERA", fontsize=8.5, fontweight='bold', color='#1971C2')
    ax.text(LARGO_CAMION - 0.2, ANCHO_CAMION + 0.12, "PUERTAS / TRASERA", fontsize=8.5, fontweight='bold', color='#D6336C', ha='right')

    ax.set_xlim(-0.2, LARGO_CAMION + 0.2)
    ax.set_ylim(-0.2, ANCHO_CAMION + 0.4)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
