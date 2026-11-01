import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict, Counter

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

# --- ENLACES A GOOGLE SHEETS ---
CSV_URL_CATALOGO = "https://docs.google.com/spreadsheets/d/1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c/export?format=csv"
# 👇 MANTÉN AQUÍ EL GID REAL DE TU PESTAÑA DE VEHÍCULOS
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

# --- 0. INICIALIZACIÓN DE ESTADO DINÁMICO (SESSION STATE) ---
if "cantidades" not in st.session_state:
    st.session_state.cantidades = {}
    if df_catalogo is not None:
        for idx, row in df_catalogo.iterrows():
            cod = str(row.get("ID / Código", f"B{idx+1}"))
            st.session_state.cantidades[cod] = 0

def limpiar_carga():
    for k in st.session_state.cantidades.keys():
        st.session_state.cantidades[k] = 0

def cargar_demo():
    limpiar_carga()
    if df_catalogo is not None:
        for idx, row in df_catalogo.iterrows():
            nombre = str(row.get("Descripción / Unidad Logística", ""))
            cod = str(row.get("ID / Código", f"B{idx+1}"))
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
            st.session_state.cantidades[cod] = val_def

def actualizar_cantidad(codigo):
    st.session_state.cantidades[codigo] = st.session_state[f"inp_{codigo}"]

col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.subheader("🚚 Vehículo de Transporte")
    
    dic_vehiculos = {}
    if df_vehiculos is not None and not df_vehiculos.empty:
        cols = df_vehiculos.columns
        for idx, row in df_vehiculos.iterrows():
            nombre = str(row[cols[0]])
            if nombre.strip() == "" or nombre.lower() == "nan": continue
            largo = parse_num(row[cols[1]] if len(cols) > 1 else None, 13.60)
            ancho = parse_num(row[cols[2]] if len(cols) > 2 else None, 2.48)
            peso = parse_num(row[cols[5]] if len(cols) > 5 else None, 24000)
            dic_vehiculos[nombre] = {"largo": largo, "ancho": ancho, "peso": peso}
            
    if not dic_vehiculos:
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
        st.info(f"Albarán preparado: {archivo.name} (Procesamiento automático en desarrollo)")

    c1, c2 = st.columns(2)
    if c1.button("🗑️ Nuevo Evento / Limpiar"):
        limpiar_carga()
        st.rerun()
    if c2.button("🧪 Cargar Demo"):
        cargar_demo()
        st.rerun()

    st.subheader("📋 Dotación Activa")
    elementos_activos = False
    
    if df_catalogo is not None:
        for idx, row in df_catalogo.iterrows():
            codigo = str(row.get("ID / Código", f"B{idx+1}"))
            val_actual = st.session_state.cantidades.get(codigo, 0)
            
            if val_actual > 0:
                elementos_activos = True
                nombre = str(row.get("Descripción / Unidad Logística", codigo))
                st.number_input(
                    nombre, 
                    min_value=0, 
                    value=val_actual, 
                    step=1, 
                    key=f"inp_{codigo}",
                    on_change=actualizar_cantidad,
                    args=(codigo,)
                )
                
    if not elementos_activos:
        st.info("Camión vacío. Añade material manualmente o carga la demo.")

    # --- SECCIÓN AÑADIR MATERIAL EXTRA (DOBLE DESPLEGABLE) ---
    st.subheader("➕ Añadir Material Extra")
    if df_catalogo is not None and "Categoría" in df_catalogo.columns:
        categorias_unicas = df_catalogo["Categoría"].dropna().unique().tolist()
        categorias_unicas.sort()
        
        cat_sel = st.selectbox("1. Filtra por Familia:", categorias_unicas)
        df_filtrado = df_catalogo[df_catalogo["Categoría"] == cat_sel]
        
        opciones_cat = {}
        for idx, row in df_filtrado.iterrows():
            cod = str(row.get("ID / Código", f"B{idx+1}"))
            nom = str(row.get("Descripción / Unidad Logística", cod))
            opciones_cat[f"{nom} ({cod})"] = cod
            
        articulo_sel = st.selectbox("2. Selecciona el Bulto:", list(opciones_cat.keys()))
        cant_extra = st.number_input("Cantidad a añadir:", min_value=1, value=1, step=1, key="cant_extra")
        
        if st.button("Añadir al camión"):
            cod_sel = opciones_cat[articulo_sel]
            st.session_state.cantidades[cod_sel] += cant_extra
            st.rerun()

# 1. HUELLAS FÍSICAS Y APILADO VERTICAL COMPARTIDO
peso_total = 0.0
compat_pools = defaultdict(list)
items_individuales = []

if df_catalogo is not None:
    for idx, row in df_catalogo.iterrows():
        codigo = str(row.get("ID / Código", f"B{idx+1}"))
        cant = st.session_state.cantidades.get(codigo, 0)
        
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

            # Consolas a medida exacta (transversales)
            if fam == "FOH":
                ancho_cm, fondo_cm = 165, 65
                puede_rotar = False
            # Subgraves (no rotan)
            elif fam == "SUB":
                ancho_cm, fondo_cm = 110, 130
                puede_rotar = False
            # Cajas PA (no rotan en carro)
            elif fam == "PA":
                ancho_cm, fondo_cm = 60, 100
                puede_rotar = False
            # Racks, motores y baúles modulares (giran 360)
            else:
                if (ancho_cm == 80 and fondo_cm == 60):
                    ancho_cm, fondo_cm = 60, 80
                puede_rotar = True

            item_info = {
                "nombre": nombre,
                "alias": alias,
                "familia": fam,
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
        "alt": 1,
        "rot": it["rot"]
    })

# 2. MOTOR SKYLINE ESTRUCTURADO (EVITA ZIG-ZAGS DE CONSOLAS)
def ejecutar_skyline(items_entrada, orden_familias):
    skyline = np.zeros(TRUCK_W_CM, dtype=float) + 3.0
    placed = []
    pool = [dict(it) for it in items_entrada]
    # Ordenación estricta: Agrupa las familias en bloque para no fragmentar paredes
    pool.sort(key=lambda it: (orden_familias.get(it["cat"], 9), -it["w"], -it["d"]))

    while pool:
        # Calcular pieza más pequeña disponible para saber si un hueco es inservible
        min_w_pool = min(
            min(it["w"], it["d"]) if it.get("rot", False) else it["w"]
            for it in pool
        )

        while True:
            min_x = np.min(skyline)
            valleys = []
            in_v = False
            v_s = 0
            for i in range(TRUCK_W_CM):
                if skyline[i] <= min_x + 1.5:
                    if not in_v:
                        in_v = True
                        v_s = i
                else:
                    if in_v:
                        valleys.append((v_s, i - v_s))
                        in_v = False
            if in_v:
                valleys.append((v_s, TRUCK_W_CM - v_s))

            valleys.sort(key=lambda v: (-v[1], v[0]))
            v_start, v_len = valleys[0]

            # Si el valle es más estrecho que la pieza más pequeña, se sella y nivela
            if v_len < min_w_pool:
                left_x = skyline[v_start - 1] if v_start > 0 else float("inf")
                right_x = skyline[v_start + v_len] if (v_start + v_len) < TRUCK_W_CM else float("inf")
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
            right_x = skyline[v_start + v_len] if (v_start + v_len) < TRUCK_W_CM else float("inf")
            raise_to = min(left_x, right_x)
            if raise_to == float("inf") or raise_to <= min_x:
                raise_to = min_x + 5.0
            skyline[v_start : v_start + v_len] = raise_to
            continue
