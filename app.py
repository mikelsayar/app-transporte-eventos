import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
            
            val_def = 2 if "KSL" in nombre and "Bumper" not in nombre else (7 if "D80" in nombre else (8 if "120x60" in nombre else 0))
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
            
            # Permitir rotar si es baúl modular
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

# 2. MOTOR DE ESTIBA EN 4 CARRILES (60 CM) + ESPECIALES AL FINAL
ANCHO_CAMION = 2.48
LARGO_CAMION = 13.60

track_y = [0.02, 0.625, 1.23, 1.835]
track_x = [0.03, 0.03, 0.03, 0.03]

items_60 = []
items_120 = []
items_special = []

for h in huellas_suelo:
    w = h['ancho']
    d = h['fondo']
    if 0.55 <= w <= 0.65:
        items_60.append(h)
    elif h.get('puede_rotar', False) and (0.55 <= d <= 0.65):
        h_rot = dict(h)
        h_rot['ancho'] = d
        h_rot['fondo'] = w
        items_60.append(h_rot)
    elif 1.10 <= w <= 1.35:
        items_120.append(h)
    elif h.get('puede_rotar', False) and (1.10 <= d <= 1.35):
        h_rot = dict(h)
        h_rot['ancho'] = d
        h_rot['fondo'] = w
        items_120.append(h_rot)
    else:
        items_special.append(h)

placed = []

# Cargar modulares de 60 cm ordenados por prioridad de peso (cabecera a trasera)
items_60.sort(key=lambda x: (ORDEN_CARGA_CAT.get(x['categoria'], 10), -x['fondo'], x['nombre']))

while items_60:
    curr = items_60.pop(0)
    best_track = track_x.index(min(track_x))
    x = track_x[best_track]
    y = track_y[best_track]
    placed.append({
        'x': x, 'y': y, 'w_x': curr['fondo'], 'h_y': curr['ancho'],
        'nombre': curr['nombre'], 'color': curr['color'], 'peso': curr['peso'], 'alturas': curr['alturas']
    })
    track_x[best_track] += curr['fondo'] + 0.015

# Cargar bultos de 120 cm (ocupan 2 carriles)
for curr in items_120:
    max_01 = max(track_x[0], track_x[1])
    max_23 = max(track_x[2], track_x[3])
    if max_01 <= max_23:
        x = max_01
        y = track_y[0]
        track_x[0] = x + curr['fondo'] + 0.015
        track_x[1] = x + curr['fondo'] + 0.015
    else:
        x = max_23
        y = track_y[2]
        track_x[2] = x + curr['fondo'] + 0.015
        track_x[3] = x + curr['fondo'] + 0.015
    placed.append({
        'x': x, 'y': y, 'w_x': curr['fondo'], 'h_y': curr['ancho'],
        'nombre': curr['nombre'], 'color': curr['color'], 'peso': curr['peso'], 'alturas': curr['alturas']
    })

# Cargar bultos no estándar al final (hacia las puertas)
cur_end_x = max(track_x) if placed else 0.03
cur_y = 0.02
calle_fondo = 0.0
for curr in items_special:
    w = curr['ancho']
    d = curr['fondo']
    if cur_y + w > ANCHO_CAMION + 0.01:
        cur_end_x += calle_fondo + 0.02
        cur_y = 0.02
        calle_fondo = 0.0
    placed.append({
        'x': cur_end_x, 'y': cur_y, 'w_x': d, 'h_y': w,
        'nombre': curr['nombre'], 'color': curr['color'], 'peso': curr['peso'], 'alturas': curr['alturas']
    })
    cur_y += w + 0.01
    if d > calle_fondo:
        calle_fondo = d

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

    st.subheader("📐 Esquema de Estiba en Planta (4 Carriles Touring)")
    
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
