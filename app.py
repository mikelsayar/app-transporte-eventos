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
    "Amplificación": "#E8590C",
    "Control / FOH": "#2F9E44",
    "Cableado": "#495057",
    "Cableado / Accesorios": "#495057",
    "Rigging / Estructura": "#1098AD",
    "Rigging / Motores": "#F59F00",
    "Monitores": "#20C997"
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
            
            # Cantidad inicial
            val_def = 4 if "KSL" in nombre else (3 if "SL-SUB" in nombre or "D80" in nombre else 0)
            cantidades[codigo] = st.number_input(nombre, min_value=0, value=val_def, step=1, key=f"inp_{codigo}")

# 1. GENERACIÓN DE HUELLAS DE SUELO (RESPETANDO APILADOS Y MEDIDAS REALES)
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
            bultos_ancho_definidos = int(parse_num(row.get("Bultos a lo ancho", 0)))
            
            # Ancho y fondo en metros
            ancho_m = max(0.30, ancho_cm / 100.0)
            fondo_m = max(0.30, fondo_cm / 100.0)
            
            peso_total += cant * peso_u
            
            torres_completas = cant // max_stack
            sobrante = cant % max_stack
            
            for _ in range(torres_completas):
                huellas_suelo.append({
                    "nombre": nombre,
                    "ancho": ancho_m,
                    "fondo": fondo_m,
                    "bultos_ancho_max": bultos_ancho_definidos,
                    "color": COLORES_CAT.get(categoria, "#495057"),
                    "peso": peso_u * max_stack,
                    "alturas": max_stack
                })
            if sobrante > 0:
                huellas_suelo.append({
                    "nombre": nombre,
                    "ancho": ancho_m,
                    "fondo": fondo_m,
                    "bultos_ancho_max": bultos_ancho_definidos,
                    "color": COLORES_CAT.get(categoria, "#495057"),
                    "peso": peso_u * sobrante,
                    "alturas": sobrante
                })

# 2. MOTOR DE ESTIBA REAL (ANCHO EUROPEO 2.48 m)
ANCHO_CAMION = 2.48   # Semirremolque estándar europeo útil
LARGO_CAMION = 13.60

cur_x = 0.03
cur_y = 0.02
fondo_max_calle = 0.0
bloques_dibujo = []
items_en_calle = 0

for b in huellas_suelo:
    w = b["ancho"]
    d = b["fondo"]
    max_a_lo_ancho = b["bultos_ancho_max"]
    
    # Comprobar si cabe en la calle actual (por metros físicos o por cupo definido en la hoja)
    excede_ancho = (cur_y + w) > (ANCHO_CAMION + 0.005)
    excede_cupo = (max_a_lo_ancho > 0 and items_en_calle >= max_a_lo_ancho)
    
    if excede_ancho or excede_cupo:
        # Salto de calle hacia la trasera
        cur_x += fondo_max_calle + 0.02
        cur_y = 0.02
        fondo_max_calle = 0.0
        items_en_calle = 0
        
    bloques_dibujo.append({
        "x": cur_x,
        "y": cur_y,
        "w_x": d,
        "h_y": w,
        "nombre": b["nombre"],
        "color": b["color"],
        "peso": b["peso"],
        "alturas": b["alturas"]
    })
    
    cur_y += w + 0.005  # Holgura de solo 5 mm para dibujo limpio
    items_en_calle += 1
    if d > fondo_max_calle:
        fondo_max_calle = d

ml_ocupados = (cur_x + fondo_max_calle) if len(bloques_dibujo) > 0 else 0.0
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

    st.subheader("📐 Esquema de Estiba en Planta (Vista Superior)")
    
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
            color='white', ha='center', va='center', fontsize=6.5, fontweight='bold'
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
