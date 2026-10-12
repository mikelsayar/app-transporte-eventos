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
            
            # Valores por defecto iniciales
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
                    "alturas": max_stack
                })
            if sobrante > 0:
                huellas_suelo.append({
                    "nombre": nombre,
                    "categoria": categoria,
                    "ancho": ancho_m,
                    "fondo": fondo_m,
                    "color": COLORES_CAT.get(categoria, "#495057"),
                    "peso": peso_u * sobrante,
                    "alturas": sobrante
                })

# 2. MOTOR DE ESTIBA PROFESIONAL POR CALLES HOMOGÉNEAS
ANCHO_CAMION = 2.48
LARGO_CAMION = 13.60

# Agrupar por bulto exacto
grupos = defaultdict(list)
for h in huellas_suelo:
    grupos[(h['categoria'], h['nombre'], h['fondo'], h['ancho'])].append(h)

calles_completas = []
picos_sueltos = []

for key, items in grupos.items():
    cat, nombre, fondo, ancho = key
    max_a_lo_ancho = int(ANCHO_CAMION // ancho)
    
    # Extraer todas las calles completas de 4 bultos (o según su ancho)
    while len(items) >= max_a_lo_ancho:
        calle = items[:max_a_lo_ancho]
        calles_completas.append((cat, fondo, calle))
        items = items[max_a_lo_ancho:]
        
    picos_sueltos.extend(items)

# Ordenar picos por categoría y profundidad
picos_sueltos.sort(key=lambda x: (ORDEN_CARGA_CAT.get(x['categoria'], 10), -x['fondo'], -x['ancho']))

calles_mixtas = []
while picos_sueltos:
    seed = picos_sueltos.pop(0)
    calle = [seed]
    rem_w = ANCHO_CAMION - seed['ancho'] - 0.01
    
    # 1. Buscar en picos otro que tenga el mismo fondo
    i = 0
    while i < len(picos_sueltos) and rem_w >= 0.30:
        if abs(picos_sueltos[i]['fondo'] - seed['fondo']) < 0.05 and picos_sueltos[i]['ancho'] <= rem_w + 0.01:
            calle.append(picos_sueltos.pop(i))
            rem_w -= (calle[-1]['ancho'] + 0.005)
        else:
            i += 1
            
    # 2. Si aún hay hueco, añadir cualquier otro pico compatible
    i = 0
    while i < len(picos_sueltos) and rem_w >= 0.30:
        if picos_sueltos[i]['ancho'] <= rem_w + 0.01:
            calle.append(picos_sueltos.pop(i))
            rem_w -= (calle[-1]['ancho'] + 0.005)
        else:
            i += 1
            
    calles_mixtas.append((seed['categoria'], max(x['fondo'] for x in calle), calle))

# Unir todas las calles y ordenarlas por orden de carga (cabecera a trasera)
todas_las_calles = calles_completas + calles_mixtas
todas_las_calles.sort(key=lambda x: (ORDEN_CARGA_CAT.get(x[0], 10), -x[1]))

# Posicionar bloques físicamente
bloques_dibujo = []
cur_x = 0.03

for cat, fondo_calle, calle_items in todas_las_calles:
    cur_y = 0.02
    for item in calle_items:
        bloques_dibujo.append({
            'x': cur_x,
            'y': cur_y,
            'w_x': item['fondo'],
            'h_y': item['ancho'],
            'nombre': item['nombre'],
            'color': item['color'],
            'peso': item['peso'],
            'alturas': item['alturas']
        })
        cur_y += item['ancho'] + 0.005
    cur_x += fondo_calle + 0.02

ml_ocupados = cur_x if len(bloques_dibujo) > 0 else 0.0
ml_con_holgura = ml_ocupados * 1.05

# Generador de etiquetas legibles
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
        base = name[:8]
    if alturas > 1:
        return f"{base}\n({alturas} alt)"
    return base

with col_der:
    st.subheader("📊 Resumen Logístico de Carga")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metros Lineales (Fondo)", f"{ml_con_holgura:.2f} ML", f"Neto: {ml_ocupados:.2f} m")
    m2.metric("Peso Total Estimado", f"{peso_total:,.0f} kg")
    
    if ml_con_holgura <= 7.8 and peso_total <= 9000:
        vehiculo = "Rígido 18t (8.0m)"
    else:
        vehiculo = "Tráiler 13.60m"
    m3.metric("Vehículo Óptimo", vehiculo)

    ocupacion = min(100, int((ml_con_holgura / LARGO_CAMION) * 100))
    m4.metric("Ocupación Tráiler", f"{ocupacion}%", f"{max(0.0, LARGO_CAMION - ml_con_holgura):.1f} m libres")

    st.subheader("📐 Esquema de Estiba en Planta (Calles Homogéneas)")
    
    fig, ax = plt.subplots(figsize=(13, 3.8))
    ax.add_patch(patches.Rectangle((0, 0), LARGO_CAMION, ANCHO_CAMION, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    for b in bloques_dibujo:
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

    # Marcadores limpios fuera del camión
    ax.text(0.1, ANCHO_CAMION + 0.12, "FRENTE / CABECERA", fontsize=8.5, fontweight='bold', color='#1971C2')
    ax.text(LARGO_CAMION - 0.2, ANCHO_CAMION + 0.12, "PUERTAS / TRASERA", fontsize=8.5, fontweight='bold', color='#D6336C', ha='right')

    ax.set_xlim(-0.2, LARGO_CAMION + 0.2)
    ax.set_ylim(-0.2, ANCHO_CAMION + 0.4)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
