import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

# Enlace de exportación limpia del Google Sheet
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

# Orden lógico de carga de proa a popa (pesos pesados primero)
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
            
            # Valor inicial por defecto para pruebas
            val_def = 4 if "KSL" in nombre else (3 if "SL-SUB" in nombre or "D80" in nombre else 0)
            cantidades[codigo] = st.number_input(nombre, min_value=0, value=val_def, step=1, key=f"inp_{codigo}")

# 1. DESGLOSE DE HUELLAS FÍSICAS DE SUELO (TENIENDO EN CUENTA APILADO)
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
            remontable_str = str(row.get("¿Remontable?", "")).lower()
            
            # Permitir rotar si es un baúl estándar o maleta cuadrada/modular
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

# 2. MOTOR DE EMPAQUETADO INTELIGENTE (OPTIMIZACIÓN DE CALLES 2D)
ANCHO_CAMION = 2.48
LARGO_CAMION = 13.60

cola_bultos = list(huellas_suelo)
# Ordenar inicialmente por prioridad de carga y profundidad
cola_bultos.sort(key=lambda x: (ORDEN_CARGA_CAT.get(x["categoria"], 10), -x["fondo"], -x["ancho"]))

bloques_dibujo = []
cur_x = 0.03

while len(cola_bultos) > 0:
    # Abrir nueva calle con el primer bulto disponible
    bulto_base = cola_bultos.pop(0)
    calle_items = [bulto_base]
    ancho_disponible = ANCHO_CAMION - bulto_base["ancho"] - 0.02
    
    # 1º: Intentar meter bultos del mismo tipo o misma profundidad
    i = 0
    while i < len(cola_bultos) and ancho_disponible >= 0.35:
        cand = cola_bultos[i]
        mismo_tipo = (cand["nombre"] == bulto_base["nombre"])
        misma_profundidad = (abs(cand["fondo"] - bulto_base["fondo"]) <= 0.05)
        
        if (mismo_tipo or misma_profundidad) and (cand["ancho"] <= ancho_disponible + 0.01):
            calle_items.append(cand)
            ancho_disponible -= (cand["ancho"] + 0.005)
            cola_bultos.pop(i)
        else:
            i += 1
            
    # 2º: Si aún sobra ancho en la calle, rastrear cualquier bulto que encaje
    i = 0
    while i < len(cola_bultos) and ancho_disponible >= 0.35:
        cand = cola_bultos[i]
        cand_w = cand["ancho"]
        cand_d = cand["fondo"]
        
        if cand_w <= ancho_disponible + 0.01:
            calle_items.append(cand)
            ancho_disponible -= (cand_w + 0.005)
            cola_bultos.pop(i)
        elif cand.get("puede_rotar", False) and (cand_d <= ancho_disponible + 0.01):
            # Rotar el bulto para que encaje
            cand_rot = dict(cand)
            cand_rot["ancho"] = cand_d
            cand_rot["fondo"] = cand_w
            calle_items.append(cand_rot)
            ancho_disponible -= (cand_d + 0.005)
            cola_bultos.pop(i)
        else:
            i += 1
            
    # Posicionar físicamente todos los bultos seleccionados en esta calle
    cur_y = 0.02
    max_fondo_calle = max(item["fondo"] for item in calle_items)
    
    for item in calle_items:
        bloques_dibujo.append({
            "x": cur_x,
            "y": cur_y,
            "w_x": item["fondo"],
            "h_y": item["ancho"],
            "nombre": item["nombre"],
            "color": item["color"],
            "peso": item["peso"],
            "alturas": item["alturas"]
        })
        cur_y += item["ancho"] + 0.005
        
    cur_x += max_fondo_calle + 0.02

ml_ocupados = cur_x if len(bloques_dibujo) > 0 else 0.0
ml_con_holgura = ml_ocupados * 1.05

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

    st.subheader("📐 Esquema de Estiba en Planta (Optimizado)")
    
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.add_patch(patches.Rectangle((0, 0), LARGO_CAMION, ANCHO_CAMION, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    for b in bloques_dibujo:
        rect = patches.FancyBboxPatch(
            (b["x"], b["y"]), b["w_x"], b["h_y"],
            boxstyle="round,pad=0.01", linewidth=1.1,
            edgecolor='#1E1E1E', facecolor=b["color"], alpha=0.88
        )
        ax.add_patch(rect)
        
        texto_apilado = f"\n({b['alturas']} alt)" if b['alturas'] > 1 else ""
        ax.text(
            b["x"] + b["w_x"]/2, b["y"] + b["h_y"]/2, 
            f"{b['nombre']}{texto_apilado}",
            color='white', ha='center', va='center', fontsize=6.3, fontweight='bold'
        )

    if ml_con_holgura > 0:
        ax.axvline(x=ml_con_holgura, color='#D6336C', linestyle='--', linewidth=2.5)
        ax.text(ml_con_holgura + 0.15, 1.24, f"FIN DE CARGA\n{ml_con_holgura:.2f} ML\n({peso_total:,.0f} kg)", 
                color='#D6336C', fontsize=8.5, fontweight='bold', va='center')

    ax.text(0.1, ANCHO_CAMION - 0.20, "◄ FRENTE / TRACTORA", fontsize=7.5, fontweight='bold', color='#495057')
    ax.text(LARGO_CAMION - 0.2, ANCHO_CAMION - 0.20, "PUERTAS / TRASERA ►", fontsize=7.5, fontweight='bold', color='#495057', ha='right')

    ax.set_xlim(-0.2, LARGO_CAMION + 0.2)
    ax.set_ylim(-0.2, ANCHO_CAMION + 0.3)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
