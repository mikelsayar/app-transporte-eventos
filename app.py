import streamlit as st
import pandas as pd
import numpy as np
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
    st.error("⚠️ Error temporal al conectar con Google Sheets.")
else:
    st.success("☁️ Sincronizado en tiempo real con tu catálogo logístico.")

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
    return n[:10]

with col_izq:
    st.subheader("📄 Carga de Albarán")
    archivo = st.file_uploader("Arrastra el albarán técnico (PDF / Imagen)", type=["pdf", "png", "jpg", "jpeg"])
    if archivo:
        st.info(f"Albarán cargado: {archivo.name}")

    st.subheader("📋 Dotación de Material")
    if df_catalogo is not None:
        for idx, row in df_catalogo.iterrows():
            nombre = str(row.get("Descripción / Unidad Logística", f"Bulto {idx+1}"))
            codigo = str(row.get("ID / Código", f"B{idx+1}"))
            
            val_def = 5 if "KSL" in nombre and "Bumper" not in nombre else (
                3 if "SL-SUB" in nombre else (
                    2 if "Motores" in nombre else (
                        2 if "D80" in nombre else (
                            3 if "D40" in nombre else (
                                5 if "120x60" in nombre else (
                                    1 if "80x60" in nombre else (
                                        2 if "Quantum" in nombre else 0
                                    )
                                )
                            )
                        )
                    )
                )
            )
            cantidades[codigo] = st.number_input(nombre, min_value=0, value=val_def, step=1, key=f"inp_{codigo}")

# 1. HUELLAS FÍSICAS Y APILADO VERTICAL COMPARTIDO
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
            ancho_cm = int(round(parse_num(row.get("Ancho al frontal de carga (cm)", 60))))
            fondo_cm = int(round(parse_num(row.get("Fondo de calle (cm)", 80))))
            max_stack = max(1, int(parse_num(row.get("Alturas de apilado", 1))))
            
            peso_total += cant * peso_u
            
            # Todo el material modular puede rotar, excepto los KSL o subs cuyo patín dicte lo contrario
            puede_rotar = not ("ksl" in nombre.lower() and "bumper" not in nombre.lower()) and not ("sl-sub" in nombre.lower())
            
            if "quantum" in nombre.lower() or "q338" in nombre.lower():
                puede_rotar = False
                ancho_cm, fondo_cm = 165, 65

            item_info = {
                "nombre": nombre,
                "alias": obtener_alias(nombre),
                "categoria": categoria,
                "w": ancho_cm,
                "d": fondo_cm,
                "peso": peso_u,
                "max_stack": max_stack,
                "color": COLORES_CAT.get(categoria, "#495057"),
                "puede_rotar": puede_rotar
            }

            if max_stack > 1:
                key_compat = (categoria, ancho_cm, fondo_cm, max_stack)
                for _ in range(cant):
                    compat_pools[key_compat].append(item_info)
            else:
                for _ in range(cant):
                    items_individuales.append(item_info)

pool_items = []
for key, units in compat_pools.items():
    cat, w_cm, d_cm, max_stack = key
    while units:
        torre = units[:max_stack]
        units = units[max_stack:]
        counts = Counter([u["alias"] for u in torre])
        lbl_parts = [f"{cnt}x {k}" if cnt > 1 else k for k, cnt in counts.items()]
        pool_items.append({
            "name": " / ".join(lbl_parts),
            "categoria": cat,
            "w": w_cm,
            "d": d_cm,
            "color": torre[0]["color"],
            "peso": sum(u["peso"] for u in torre),
            "alt": len(torre),
            "puede_rotar": torre[0]["puede_rotar"]
        })

for it in items_individuales:
    pool_items.append({
        "name": it["alias"],
        "categoria": it["categoria"],
        "w": it["w"],
        "d": it["d"],
        "color": it["color"],
        "peso": it["peso"],
        "alt": 1,
        "puede_rotar": it["puede_rotar"]
    })

# 2. MOTOR DE EMPAQUETADO PURO "BEST-FIT SKYLINE CONTINUO" (TETRIS TOTAL)
TRUCK_W_CM = 248
ANCHO_CAMION = 2.48
LARGO_CAMION = 13.60
skyline = np.zeros(TRUCK_W_CM, dtype=float) + 3.0
placed = []

consoles = [it for it in pool_items if "q338" in it['name'].lower() or "consola" in it['name'].lower()]
pool = [it for it in pool_items if it not in consoles]

while pool:
    min_x = np.min(skyline)
    
    valleys = []
    in_v = False
    v_s = 0
    for i in range(TRUCK_W_CM):
        if abs(skyline[i] - min_x) <= 2.0:
            if not in_v:
                in_v = True
                v_s = i
        else:
            if in_v:
                valleys.append((v_s, i - v_s))
                in_v = False
    if in_v:
        valleys.append((v_s, TRUCK_W_CM - v_s))
        
    valleys.sort(key=lambda v: -v[1])
    target_v_start, target_v_len = valleys[0]
    
    best_cand_idx = None
    best_cand_w = None
    best_cand_d = None
    best_cand_score = -float('inf')
    best_cand_y = None
    best_cand_x = None
    
    for idx, item in enumerate(pool):
        orientations = [(item['w'], item['d'])]
        if item.get('puede_rotar', True) and item['w'] != item['d']:
            orientations.append((item['d'], item['w']))
            
        for (w_cm, d_cm) in orientations:
            if w_cm <= target_v_len:
                width_fill_ratio = w_cm / target_v_len
                area = w_cm * d_cm
                score = (width_fill_ratio * 1000) + area
                
                if score > best_cand_score:
                    best_cand_score = score
                    best_cand_idx = idx
                    best_cand_w = w_cm
                    best_cand_d = d_cm
                    best_cand_y = target_v_start
                    best_cand_x = np.max(skyline[best_cand_y : best_cand_y + best_cand_w])
                    
    if best_cand_idx is not None:
        it = pool.pop(best_cand_idx)
        placed.append({
            'name': it['name'], 'color': it['color'], 'alt': it.get('alt', 1),
            'x': best_cand_x / 100.0, 'y': best_cand_y / 100.0,
            'w_x': best_cand_d / 100.0, 'h_y': best_cand_w / 100.0
        })
        skyline[best_cand_y : best_cand_y + best_cand_w] = best_cand_x + best_cand_d + 1.5
    else:
        min_new_x = float('inf')
        fallback_idx = None
        f_y, f_w, f_d, f_x = None, None, None, None
        
        for idx, item in enumerate(pool):
            orientations = [(item['w'], item['d'])]
            if item.get('puede_rotar', True) and item['w'] != item['d']:
                orientations.append((item['d'], item['w']))
                
            for (w_cm, d_cm) in orientations:
                if w_cm > TRUCK_W_CM: continue
                for y_cand in range(0, TRUCK_W_CM - w_cm + 1, 5):
                    cur_x = np.max(skyline[y_cand : y_cand + w_cm])
                    new_x = cur_x + d_cm
                    
                    if new_x < min_new_x - 0.5:
                        min_new_x = new_x
                        fallback_idx = idx
                        f_y, f_w, f_d, f_x = y_cand, w_cm, d_cm, cur_x
                    elif abs(new_x - min_new_x) <= 0.5:
                        if (w_cm * d_cm) > (f_w * f_d if f_w else 0):
                            fallback_idx = idx
                            f_y, f_w, f_d, f_x = y_cand, w_cm, d_cm, cur_x
                            
        if fallback_idx is not None:
            it = pool.pop(fallback_idx)
            placed.append({
                'name': it['name'], 'color': it['color'], 'alt': it.get('alt', 1),
                'x': f_x / 100.0, 'y': f_y / 100.0,
                'w_x': f_d / 100.0, 'h_y': f_w / 100.0
            })
            skyline[f_y : f_y + f_w] = f_x + f_d + 1.5
        else:
            break

for c in consoles:
    cur_c_x = np.max(skyline[0 : c['w']])
    placed.append({
        'name': c['name'], 'color': c['color'], 'alt': c.get('alt', 1),
        'x': cur_c_x / 100.0, 'y': 0.02,
        'w_x': c['d'] / 100.0, 'h_y': c['w'] / 100.0
    })
    skyline[0 : c['w']] = cur_c_x + c['d'] + 1.5

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

    st.subheader("📐 Esquema de Estiba en Planta (Contacto Directo Optimizado)")
    
    fig, ax = plt.subplots(figsize=(13, 3.8))
    ax.add_patch(patches.Rectangle((0, 0), LARGO_CAMION, ANCHO_CAMION, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    for b in placed:
        rect = patches.FancyBboxPatch(
            (b["x"], b["y"]), b["w_x"], b["h_y"],
            boxstyle="round,pad=0.01", linewidth=1.1,
            edgecolor='#1E1E1E', facecolor=b["color"], alpha=0.90
        )
        ax.add_patch(rect)
        
        texto_alt = f"\n({b['alt']} alt)" if b['alt'] > 1 and "alt" not in b['name'] else ""
        ax.text(
            b["x"] + b["w_x"]/2, b["y"] + b["h_y"]/2, 
            f"{b['name']}{texto_alt}", color='white', ha='center', va='center', fontsize=6.8, fontweight='bold'
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
