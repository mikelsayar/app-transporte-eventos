import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict, Counter

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

# --- ENLACES A GOOGLE SHEETS ---
CSV_URL_CATALOGO = "https://docs.google.com/spreadsheets/d/1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c/export?format=csv&gid=101"
# 👇 SUSTITUYE ESTO POR EL GID DE TU PESTAÑA DE VEHÍCULOS
CSV_URL_VEHICULOS = "https://docs.google.com/spreadsheets/d/1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c/export?format=csv&gid=102"

def parse_num(val, default=0.0):
    if pd.isna(val) or val is None or str(val).strip() == '':
        return default
    val_str = str(val).replace(',', '.').strip()
    try:
        return float(val_str)
    except:
        return default

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df_cat = pd.read_csv(CSV_URL_CATALOGO)
    except:
        df_cat = None
        
    try:
        df_veh = pd.read_csv(CSV_URL_VEHICULOS)
    except:
        df_veh = None
        
    return df_cat, df_veh

df_catalogo, df_vehiculos = cargar_datos()

st.title("🚛 Gestor de Transporte y Estiba de Eventos")

if df_catalogo is None:
    st.error("⚠️ Error temporal al conectar con la pestaña Catálogo de Google Sheets.")
else:
    st.success("☁️ Sincronizado en tiempo real con tus catálogos logísticos.")

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

def clasificar_familia(alias, categoria):
    al = alias.lower()
    if "sl-sub" in al or "sub" in categoria.lower(): return "SUB"
    if "ksl" in al and "bumper" not in al: return "PA"
    if "motor" in al or "bumper" in al or "rigging" in categoria.lower(): return "RIG"
    if any(x in al for x in ["d80", "d40", "d90", "d25"]) or "amplif" in categoria.lower(): return "AMP"
    if "q338" in al or "control" in categoria.lower(): return "FOH"
    return "CAB"

with col_izq:
    st.subheader("🚚 Vehículo de Transporte")
    
    dic_vehiculos = {}
    if df_vehiculos is not None and not df_vehiculos.empty:
        for idx, row in df_vehiculos.iterrows():
            nombre = str(row.get("Vehículo", f"Opción {idx+1}"))
            if nombre.strip() == "" or nombre.lower() == "nan": continue
            largo = parse_num(row.get("Largo útil (m)", 13.60))
            ancho = parse_num(row.get("Ancho útil (m)", 2.48))
            peso = parse_num(row.get("Carga útil (kg)", 24000))
            dic_vehiculos[nombre] = {"largo": largo, "ancho": ancho, "peso": peso}
            
    if not dic_vehiculos:
        # Fallback de seguridad si falla la hoja o el GID no es válido aún
        dic_vehiculos = {
            "Tráiler Estándar 13.6m": {"largo": 13.60, "ancho": 2.48, "peso": 24000},
            "Rígido 18t (8.0m)": {"largo": 8.00, "ancho": 2.45, "peso": 9000},
            "Furgón Carrozado Ligero": {"largo": 4.20, "ancho": 2.10, "peso": 1000}
        }
        
    vehiculo_sel = st.selectbox("Selecciona la capacidad del vehículo:", list(dic_vehiculos.keys()))
    
    LARGO_CAMION = dic_vehiculos[vehiculo_sel]["largo"]
    ANCHO_CAMION = dic_vehiculos[vehiculo_sel]["ancho"]
    PESO_MAX = dic_vehiculos[vehiculo_sel]["peso"]
    TRUCK_W_CM = int(round(ANCHO_CAMION * 100))

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
                4 if "SL-SUB" in nombre else (
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
            alias = obtener_alias(nombre)
            fam = clasificar_familia(alias, categoria)

            if fam == "SUB":
                ancho_cm, fondo_cm = 110, 130
                puede_rotar = False
            elif fam == "PA":
                ancho_cm, fondo_cm = 60, 100
                puede_rotar = False
            elif fam == "FOH":
                ancho_cm, fondo_cm = 165, 65
                puede_rotar = True
            else:
                if (ancho_cm == 80 and fondo_cm == 60):
                    ancho_cm, fondo_cm = 60, 80
                puede_rotar = True

            item_info = {
                "nombre": nombre,
                "alias": alias,
                "familia": fam,
                "categoria": categoria,
                "w": ancho_cm,
                "d": fondo_cm,
                "peso": peso_u,
                "max_stack": max_stack,
                "color": COLORES_CAT.get(categoria, "#495057"),
                "rot": puede_rotar
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
            "cat": torre[0]["familia"],
            "w": w_cm,
            "d": d_cm,
            "color": torre[0]["color"],
            "peso": sum(u["peso"] for u in torre),
            "alt": len(torre),
            "rot": torre[0]["rot"]
        })

for it in items_individuales:
    pool_items.append({
        "name": it["alias"],
        "cat": it["familia"],
        "w": it["w"],
        "d": it["d"],
        "color": it["color"],
        "peso": it["peso"],
        "alt": 1,
        "rot": it["rot"]
    })

# 2. MOTOR SKYLINE PARAMETRIZADO AL ANCHO DEL VEHÍCULO
def ejecutar_skyline(items_entrada, orden_familias, truck_w_cm, permitir_rotar_60=False, consolas_longitudinales=False):
    skyline = np.zeros(truck_w_cm, dtype=float) + 3.0
    placed = []
    pool = []
    for it in items_entrada:
        copia = dict(it)
        if copia["cat"] == "FOH":
            copia["w"], copia["d"] = (65, 165) if consolas_longitudinales else (165, 65)
            copia["rot"] = False
        pool.append(copia)

    pool.sort(key=lambda it: (orden_familias.get(it["cat"], 9), -it["d"], -it["w"]))

    while pool:
        min_w_pool = min(
            min(it["w"], it["d"]) if (it.get("rot", False) and (permitir_rotar_60 or it["w"] != 60) and it["cat"] != "FOH") else it["w"]
            for it in pool
        )

        while True:
            min_x = np.min(skyline)
            valleys = []
            in_v = False
            v_s = 0
            for i in range(truck_w_cm):
                if skyline[i] <= min_x + 1.5:
                    if not in_v:
                        in_v = True
                        v_s = i
                else:
                    if in_v:
                        valleys.append((v_s, i - v_s))
                        in_v = False
            if in_v:
                valleys.append((v_s, truck_w_cm - v_s))

            valleys.sort(key=lambda v: (-v[1], v[0]))
            v_start, v_len = valleys[0]

            if v_len < min_w_pool:
                left_x = skyline[v_start - 1] if v_start > 0 else float("inf")
                right_x = skyline[v_start + v_len] if (v_start + v_len) < truck_w_cm else float("inf")
                raise_to = min(left_x, right_x)
                if raise_to == float("inf") or raise_to <= min_x:
                    raise_to = min_x + 5.0
                skyline[v_start : v_start + v_len] = raise_to
            else:
                break

        best_idx = None
        best_w, best_d, best_y, best_x = None, None, None, None
        best_score = -float("inf")

        for idx, it in enumerate(pool):
            can_rot = it.get("rot", False)
            if it["w"] == 60 and not permitir_rotar_60:
                can_rot = False

            orientations = [(it["w"], it["d"])]
            if can_rot and it["w"] != it["d"]:
                orientations.append((it["d"], it["w"]))

            for (w_cm, d_cm) in orientations:
                if w_cm <= v_len:
                    rem = v_len - w_cm
                    queue_prio = (len(pool) - idx) * 300

                    if rem >= min_w_pool or rem <= 28:
                        mod_bonus = 2000 - (rem * 10 if rem < min_w_pool else 0)
                    else:
                        mod_bonus = -5000

                    cand_y = v_start
                    cand_x = np.max(skyline[cand_y : cand_y + w_cm])
                    new_front = cand_x + d_cm + 1.5

                    level_bonus = 0
                    if cand_y > 0 and abs(skyline[cand_y - 1] - new_front) <= 4.0:
                        level_bonus = 1500

                    orig_bonus = 400 if w_cm == it["w"] else 0

                    score = queue_prio + mod_bonus + level_bonus + orig_bonus
                    if score > best_score:
                        best_score = score
                        best_idx = idx
                        best_w, best_d, best_y, best_x = w_cm, d_cm, cand_y, cand_x

        if best_idx is None:
            left_x = skyline[v_start - 1] if v_start > 0 else float("inf")
            right_x = skyline[v_start + v_len] if (v_start + v_len) < truck_w_cm else float("inf")
            raise_to = min(left_x, right_x)
            if raise_to == float("inf") or raise_to <= min_x:
                raise_to = min_x + 5.0
            skyline[v_start : v_start + v_len] = raise_to
            continue

        it = pool.pop(best_idx)
        placed.append({
            "name": it["name"],
            "color": it["color"],
            "alt": it["alt"],
            "x": best_x / 100.0,
            "y": best_y / 100.0,
            "w_x": best_d / 100.0,
            "h_y": best_w / 100.0,
        })
        skyline[best_y : best_y + best_w] = best_x + best_d + 1.5

    total_ml = max([p["x"] + p["w_x"] for p in placed]) if placed else 0.0
    return placed, total_ml

with col_der:
    modo_estiba = st.radio(
        "🎯 Estrategia de ubicación de Subgraves (SL-SUB) y optimización:",
        [
            "Automático (Mínimos Metros Lineales)",
            "SL-SUB al Fondo Interior (Cabecera)",
            "SL-SUB al Final (Puertas / Trasera)"
        ],
        horizontal=True
    )

    candidatos = []
    if modo_estiba == "SL-SUB al Fondo Interior (Cabecera)":
        candidatos.append(ejecutar_skyline(pool_items, {"SUB": 1, "RIG": 2, "PA": 3, "AMP": 4, "FOH": 5, "CAB": 6}, TRUCK_W_CM, False, False))
        candidatos.append(ejecutar_skyline(pool_items, {"SUB": 1, "RIG": 2, "PA": 3, "AMP": 4, "CAB": 5, "FOH": 6}, TRUCK_W_CM, False, True))
    elif modo_estiba == "SL-SUB al Final (Puertas / Trasera)":
        candidatos.append(ejecutar_skyline(pool_items, {"PA": 1, "AMP": 2, "CAB": 3, "RIG": 4, "FOH": 5, "SUB": 6}, TRUCK_W_CM, False, True))
        candidatos.append(ejecutar_skyline(pool_items, {"PA": 1, "AMP": 2, "CAB": 3, "RIG": 4, "SUB": 5, "FOH": 6}, TRUCK_W_CM, False, False))
    else:
        ordenes = [
            ({"SUB": 1, "RIG": 2, "PA": 3, "AMP": 4, "FOH": 5, "CAB": 6}, False, False),
            ({"PA": 1, "AMP": 2, "CAB": 3, "RIG": 4, "FOH": 5, "SUB": 6}, False, True),
            ({"PA": 1, "AMP": 2, "CAB": 3, "RIG": 4, "SUB": 5, "FOH": 6}, False, False),
            ({"RIG": 1, "PA": 2, "AMP": 3, "CAB": 4, "FOH": 5, "SUB": 6}, False, True),
        ]
        for ord_map, r60, lcon in ordenes:
            candidatos.append(ejecutar_skyline(pool_items, ord_map, TRUCK_W_CM, r60, lcon))

    placed, total_ml = min(candidatos, key=lambda x: x[1]) if candidatos else ([], 0.0)
    ml_con_holgura = total_ml * 1.05

    st.subheader("📊 Resumen Logístico de Carga")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metros Lineales", f"{ml_con_holgura:.2f} ML", f"Neto: {total_ml:.2f} m")
    
    # Alerta visual si se excede el peso de la ficha del vehículo
    if peso_total > PESO_MAX:
        m2.error(f"⚠️ {peso_total:,.0f} kg")
        m2.metric("Peso Total Estimado", f"{peso_total:,.0f} kg", f"Exceso: +{peso_total - PESO_MAX:,.0f} kg", delta_color="inverse")
    else:
        m2.metric("Peso Total Estimado", f"{peso_total:,.0f} kg", f"Libres: {PESO_MAX - peso_total:,.0f} kg", delta_color="normal")
        
    m3.metric("Vehículo Seleccionado", vehiculo_sel)

    # Alerta visual si sobresale de la longitud del vehículo
    ocupacion = int((ml_con_holgura / LARGO_CAMION) * 100)
    if ml_con_holgura > LARGO_CAMION:
        m4.metric(f"Ocupación ({LARGO_CAMION}m)", f"{ocupacion}%", f"¡Sobran {ml_con_holgura - LARGO_CAMION:.1f} m!", delta_color="inverse")
    else:
        m4.metric(f"Ocupación ({LARGO_CAMION}m)", f"{ocupacion}%", f"Libres: {LARGO_CAMION - ml_con_holgura:.1f} m", delta_color="normal")

    st.subheader("📐 Esquema de Estiba en Planta")
    
    fig, ax = plt.subplots(figsize=(13, 3.8))
    # Dibuja la caja del camión físicamente
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

    # Línea sólida roja marcando las puertas físicas del vehículo
    ax.axvline(x=LARGO_CAMION, color='red', linestyle='-', linewidth=3)
    ax.text(LARGO_CAMION - 0.15, ANCHO_CAMION + 0.12, "PUERTAS REALES", fontsize=8.5, fontweight='bold', color='red', ha='right')

    # Línea punteada que muestra hasta dónde llega la carga real
    if ml_con_holgura > 0:
        color_fin = 'green' if ml_con_holgura <= LARGO_CAMION else 'red'
        ax.axvline(x=ml_con_holgura, color=color_fin, linestyle='--', linewidth=2.5)
        ax.text(ml_con_holgura + 0.15, 1.24, f"FIN DE CARGA\n{ml_con_holgura:.2f} ML", 
                color=color_fin, fontsize=8.5, fontweight='bold', va='center')

    ax.text(0.1, ANCHO_CAMION + 0.12, "FRENTE / CABECERA", fontsize=8.5, fontweight='bold', color='#1971C2')
    
    # Ajuste dinámico de los límites de la gráfica para que no se corte si la carga sobresale del camión
    limite_x = max(LARGO_CAMION, ml_con_holgura)
    ax.set_xlim(-0.2, limite_x + 1.0)
    ax.set_ylim(-0.2, ANCHO_CAMION + 0.4)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
