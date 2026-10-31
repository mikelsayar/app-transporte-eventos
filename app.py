import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict, Counter

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

def obtener_alias(n):
    nl = n.lower()
    if "ksl" in nl and "bumper" not in nl: return "KSL"
    if "sl-sub" in nl: return "SL-SUB"
    if "d80" in nl: return "D80"
    if "d40" in nl: return "D40"
    if "d90" in nl: return "D90"
    if "d25" in nl: return "D25"
    if "120" in nl or ("cables" in nl and "baúl" in nl): return "Baúl 120"
    if "80" in nl: return "Baúl 80"
    if "quantum" in nl or "digico" in nl: return "Q338"
    if "bumper" in nl: return "Bumper"
    if "motor" in nl: return "Motores"
    return n[:7]

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
            
            val_def = 5 if "KSL" in nombre and "Bumper" not in nombre else (3 if "SL-SUB" in nombre else (0 if "Bumper" in nombre else (2 if "Motores" in nombre else (3 if "D80" in nombre else (2 if "D40" in nombre else (5 if "120x60" in nombre else (1 if "80x60" in nombre else (2 if "Quantum" in nombre else 0))))))))
            cantidades[codigo] = st.number_input(nombre, min_value=0, value=val_def, step=1, key=f"inp_{codigo}")

# 1. HUELLAS Y APILADO VERTICAL
peso_total = 0.0
compat_pools = defaultdict(list)
items_individuales = []

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
            
            ancho_m = round(max(0.30, ancho_cm / 100.0), 2)
            fondo_m = round(max(0.30, fondo_cm / 100.0), 2)
            peso_total += cant * peso_u
            
            puede_rotar = ("baúl" in nombre.lower()) or ("baul" in nombre.lower()) or ("cables" in nombre.lower())

            item_info = {
                "nombre": nombre,
                "alias": obtener_alias(nombre),
                "categoria": categoria,
                "ancho": ancho_m,
                "fondo": fondo_m,
                "peso": peso_u,
                "max_stack": max_stack,
                "color": COLORES_CAT.get(categoria, "#495057"),
                "puede_rotar": puede_rotar
            }

            if max_stack > 1:
                key_compat = (categoria, ancho_m, fondo_m, max_stack)
                for _ in range(cant):
                    compat_pools[key_compat].append(item_info)
            else:
                for _ in range(cant):
                    items_individuales.append(item_info)

huellas_suelo = []

for key, units in compat_pools.items():
    cat, ancho_m, fondo_m, max_stack = key
    while units:
        torre = units[:max_stack]
        units = units[max_stack:]
        counts = Counter([u["alias"] for u in torre])
        lbl_parts = [f"{cnt}x {k}" if cnt > 1 else k for k, cnt in counts.items()]
        huellas_suelo.append({
            "nombre": " / ".join(lbl_parts),
            "categoria": cat,
            "ancho": ancho_m,
            "fondo": fondo_m,
            "color": torre[0]["color"],
            "peso": sum(u["peso"] for u in torre),
            "alturas": len(torre),
            "puede_rotar": torre[0]["puede_rotar"]
        })

for it in items_individuales:
    huellas_suelo.append({
        "nombre": it["alias"],
        "categoria": it["categoria"],
        "ancho": it["ancho"],
        "fondo": it["fondo"],
        "color": it["color"],
        "peso": it["peso"],
        "alturas": 1,
        "puede_rotar": it["puede_rotar"]
    })

# 2. MOTOR DE ESTIBA COMPACTA CONTINUA (COMPENSACIÓN DE PICOS)
ANCHO_CAMION = 2.48
LARGO_CAMION = 13.60

for h in huellas_suelo:
    if h.get("puede_rotar", False):
        if 0.55 <= h["fondo"] <= 0.65 and not (0.55 <= h["ancho"] <= 0.65):
            h["ancho"], h["fondo"] = h["fondo"], h["ancho"]

bultos_60 = [h for h in huellas_suelo if 0.50 <= h['ancho'] <= 0.65]
bultos_110 = [h for h in huellas_suelo if 1.00 <= h['ancho'] <= 1.35]
bultos_especiales = [h for h in huellas_suelo if h not in bultos_60 and h not in bultos_110]

placed = []
cur_x = 0.03

# Cabecera: Líneas homogéneas de 4 KSL
ksl_puros = [b for b in bultos_60 if "KSL" in b['nombre']]
otros_60 = [b for b in bultos_60 if "KSL" not in b['nombre']]

while len(ksl_puros) >= 4:
    cuarteto = ksl_puros[:4]
    ksl_puros = ksl_puros[4:]
    cur_y = 0.02
    for b in cuarteto:
        placed.append({'x': cur_x, 'y': cur_y, 'w_x': b['fondo'], 'h_y': b['ancho'], 'nombre': b['nombre'], 'color': b['color'], 'peso': b['peso'], 'alturas': b['alturas']})
        cur_y += b['ancho'] + 0.01
    cur_x += 1.00 + 0.02

resto_60 = ksl_puros + otros_60
resto_60.sort(key=lambda x: -x['fondo'])

# Parejas completas de bultos anchos (SL-SUB, Motores)
bultos_110.sort(key=lambda x: -x['fondo'])
while len(bultos_110) >= 2:
    pareja = [bultos_110.pop(0), bultos_110.pop(0)]
    max_d = max(pareja[0]['fondo'], pareja[1]['fondo'])
    placed.append({'x': cur_x, 'y': 0.02, 'w_x': pareja[0]['fondo'], 'h_y': pareja[0]['ancho'], 'nombre': pareja[0]['nombre'], 'color': pareja[0]['color'], 'peso': pareja[0]['peso'], 'alturas': pareja[0]['alturas']})
    placed.append({'x': cur_x, 'y': 1.24, 'w_x': pareja[1]['fondo'], 'h_y': pareja[1]['ancho'], 'nombre': pareja[1]['nombre'], 'color': pareja[1]['color'], 'peso': pareja[1]['peso'], 'alturas': pareja[1]['alturas']})
    cur_x += max_d + 0.02

# Bulto ancho desparejado: se completa la calle con dos bultos de 60 cm al lado
if len(bultos_110) == 1:
    odd_double = bultos_110.pop(0)
    placed.append({'x': cur_x, 'y': 0.02, 'w_x': odd_double['fondo'], 'h_y': odd_double['ancho'], 'nombre': odd_double['nombre'], 'color': odd_double['color'], 'peso': odd_double['peso'], 'alturas': odd_double['alturas']})
    
    cur_y_side = 1.24
    depths_in_row = [odd_double['fondo']]
    for _ in range(min(2, len(resto_60))):
        it60 = resto_60.pop(0)
        placed.append({'x': cur_x, 'y': cur_y_side, 'w_x': it60['fondo'], 'h_y': it60['ancho'], 'nombre': it60['nombre'], 'color': it60['color'], 'peso': it60['peso'], 'alturas': it60['alturas']})
        depths_in_row.append(it60['fondo'])
        cur_y_side += it60['ancho'] + 0.01
        
    cur_x += max(depths_in_row) + 0.02

# Líneas completas de 4 unidades de 60 cm
while len(resto_60) >= 4 and (len(resto_60) > len(bultos_especiales) or len(bultos_especiales) == 0):
    fila_4 = [resto_60.pop(0) for _ in range(4)]
    max_d = max(item['fondo'] for item in fila_4)
    cur_y = 0.02
    for b in fila_4:
        placed.append({'x': cur_x, 'y': cur_y, 'w_x': b['fondo'], 'h_y': b['ancho'], 'nombre': b['nombre'], 'color': b['color'], 'peso': b['peso'], 'alturas': b['alturas']})
        cur_y += b['ancho'] + 0.01
    cur_x += max_d + 0.02

# Consolas Q338 en trasera con material de 60 cm acoplado al lateral
for esp in bultos_especiales:
    placed.append({'x': cur_x, 'y': 0.02, 'w_x': esp['fondo'], 'h_y': esp['ancho'], 'nombre': esp['nombre'], 'color': esp['color'], 'peso': esp['peso'], 'alturas': esp['alturas']})
    if resto_60:
        acompanante = resto_60.pop(0)
        placed.append({'x': cur_x, 'y': 1.70, 'w_x': acompanante['fondo'], 'h_y': acompanante['ancho'], 'nombre': acompanante['nombre'], 'color': acompanante['color'], 'peso': acompanante['peso'], 'alturas': acompanante['alturas']})
        cur_x += max(esp['fondo'], acompanante['fondo']) + 0.02
    else:
        cur_x += esp['fondo'] + 0.02

while resto_60:
    b = resto_60.pop(0)
    placed.append({'x': cur_x, 'y': 0.02, 'w_x': b['fondo'], 'h_y': b['ancho'], 'nombre': b['nombre'], 'color': b['color'], 'peso': b['peso'], 'alturas': b['alturas']})
    cur_x += b['fondo'] + 0.02

total_ml = max([p['x'] + p['w_x'] for p in placed]) if placed else 0.0
ml_con_holgura = total_ml * 1.05

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
        
        texto_alt = f"\n({b['alturas']} alt)" if b['alturas'] > 1 and "alt" not in b['nombre'] else ""
        ax.text(
            b["x"] + b["w_x"]/2, b["y"] + b["h_y"]/2, 
            f"{b['nombre']}{texto_alt}", color='white', ha='center', va='center', fontsize=7.2, fontweight='bold'
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
