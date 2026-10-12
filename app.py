import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

# Enlace de exportación limpia del Google Sheet
CSV_URL = "https://docs.google.com/spreadsheets/d/1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c/export?format=csv"

# Función para convertir números con comas o puntos decimales a float
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
    except Exception as e:
        return None

df_catalogo = cargar_catalogo()

st.title("🚛 Gestor de Transporte y Estiba de Eventos")

if df_catalogo is None:
    st.error("⚠️ Error temporal al leer Google Sheets. Reintentando...")
else:
    st.success("☁️ Sincronizado en tiempo real con tu Catálogo de Google Drive.")

col_izq, col_der = st.columns([1, 2])

cantidades = {}

# Paleta de colores por categoría
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
            
            # Valor por defecto inicial
            val_def = 4 if "KSL" in nombre else (3 if "SL-SUB" in nombre or "D80" in nombre else 0)
            cantidades[codigo] = st.number_input(nombre, min_value=0, value=val_def, step=1, key=f"inp_{codigo}")

# Cálculos dinámicos
ml_neto_total = 0.0
peso_total = 0.0
items_a_cargar = []

if df_catalogo is not None:
    for idx, row in df_catalogo.iterrows():
        codigo = str(row.get("ID / Código", f"B{idx+1}"))
        cant = cantidades.get(codigo, 0)
        
        if cant > 0:
            peso_u = parse_num(row.get("Peso Bruto por bulto (kg)", 0))
            ml_u = parse_num(row.get("ML unitarios por bulto (m)", 0))
            fondo_cm = parse_num(row.get("Fondo de calle (cm)", 100))
            bultos_ancho = max(1, int(parse_num(row.get("Bultos a lo ancho", 2))))
            alturas = max(1, int(parse_num(row.get("Alturas de apilado", 1))))
            bultos_por_calle = max(1, int(parse_num(row.get("Bultos por calle", bultos_ancho * alturas))))
            categoria = str(row.get("Categoría", "Varios"))
            nombre = str(row.get("Descripción / Unidad Logística", codigo))
            
            # Si en la hoja ML unitario estaba vacío o en 0, lo calculamos al vuelo
            if ml_u <= 0 and bultos_por_calle > 0:
                ml_u = (fondo_cm / 100.0) / bultos_por_calle
                
            peso_total += cant * peso_u
            ml_neto_total += cant * ml_u
            
            items_a_cargar.append({
                "nombre": nombre,
                "cant": cant,
                "categoria": categoria,
                "fondo_m": fondo_cm / 100.0,
                "bultos_ancho": bultos_ancho,
                "alturas": alturas,
                "bultos_por_calle": bultos_por_calle,
                "ml_totales": cant * ml_u,
                "color": COLORES_CAT.get(categoria, "#343A40")
            })

ml_con_holgura = ml_neto_total * 1.10

with col_der:
    st.subheader("📊 Resumen Logístico de Carga")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metros Lineales (+10%)", f"{ml_con_holgura:.2f} ML", f"Neto: {ml_neto_total:.2f} m")
    m2.metric("Peso Total Estimado", f"{peso_total:,.0f} kg")
    
    if ml_con_holgura <= 7.8 and peso_total <= 9000:
        vehiculo = "Rígido 18t (8.0m)"
    else:
        vehiculo = "Tráiler 13.60m"
    m3.metric("Vehículo Óptimo", vehiculo)

    ocupacion = min(100, int((ml_con_holgura / 13.60) * 100))
    m4.metric("Ocupación Tráiler", f"{ocupacion}%", f"{max(0.0, 13.60 - ml_con_holgura):.1f} m libres")

    st.subheader("📐 Esquema de Estiba en Camión")
    
    fig, ax = plt.subplots(figsize=(12, 3.4))
    truck_width = 2.45
    total_length = 13.60

    # Chasis tráiler
    ax.add_patch(patches.Rectangle((0, 0), total_length, truck_width, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    # Dibujar bultos por calles a lo largo del semirremolque
    pos_x = 0.05
    for item in items_a_cargar:
        calles_necesarias = item["cant"] / item["bultos_por_calle"]
        ancho_avance = calles_necesarias * item["fondo_m"]
        
        if ancho_avance > 0:
            rect = patches.FancyBboxPatch(
                (pos_x, 0.05), ancho_avance, truck_width - 0.10,
                boxstyle="round,pad=0.02", linewidth=1.2,
                edgecolor='#1E1E1E', facecolor=item["color"], alpha=0.85
            )
            ax.add_patch(rect)
            
            # Etiqueta en el bloque
            texto = f"{item['cant']}x {item['nombre']}\n({ancho_avance:.2f} ML)"
            ax.text(pos_x + ancho_avance/2, truck_width/2, texto,
                    color='white', ha='center', va='center', fontsize=7.5, fontweight='bold')
            
            pos_x += ancho_avance + 0.05

    # Línea de corte de fin de carga
    if ml_con_holgura > 0:
        ax.axvline(x=ml_con_holgura, color='#D6336C', linestyle='--', linewidth=2.5)
        ax.text(ml_con_holgura + 0.15, 1.22, f"FIN DE CARGA\n{ml_con_holgura:.2f} ML\n({peso_total:,.0f} kg)", 
                color='#D6336C', fontsize=8.5, fontweight='bold', va='center')

    ax.text(0.1, truck_width - 0.25, "CABECERA / FRENTE", fontsize=7.5, fontweight='bold', color='#495057')
    ax.text(total_length - 0.2, truck_width - 0.25, "PUERTAS / TRASERA", fontsize=7.5, fontweight='bold', color='#495057', ha='right')

    ax.set_xlim(-0.1, total_length + 0.2)
    ax.set_ylim(-0.1, truck_width + 0.3)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
