import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

# Enlace de exportación CSV de la pestaña 'Catálogo de Bultos' de tu Google Sheet
SHEET_ID = "1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c"
SHEET_NAME = "Catálogo%20de%20Bultos"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=60)  # Recarga datos del Sheet automáticamente cada 60 segundos
def cargar_catalogo():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except Exception as e:
        return None

df_catalogo = cargar_catalogo()

st.title("🚛 Gestor de Transporte y Estiba de Eventos")

if df_catalogo is None:
    st.error("⚠️ No se pudo conectar con el Catálogo en Google Sheets. Revisa que el enlace tenga permiso de lectura público.")
else:
    st.success("☁️ Sincronizado en tiempo real con tu Catálogo de Google Drive.")

# Distribución en dos columnas
col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.subheader("📄 Carga de Albarán")
    archivo = st.file_uploader("Arrastra el PDF o foto del albarán", type=["pdf", "png", "jpg", "jpeg"])
    if archivo:
        st.info(f"Albarán recibido: {archivo.name}")

    st.subheader("📋 Dotación de Material")
    
    cantidades = {}
    if df_catalogo is not None:
        # Generar un selector dinámico para cada bulto definido en tu Google Sheet
        for idx, row in df_catalogo.iterrows():
            nombre = str(row.get("Descripción / Unidad Logística", f"Bulto {idx+1}"))
            codigo = str(row.get("ID / Código", f"B{idx+1}"))
            
            # Valor por defecto inicial para pruebas
            val_def = 4 if "KSL" in nombre else (3 if "SL-SUB" in nombre or "D80" in nombre else 0)
            cantidades[codigo] = st.number_input(f"{nombre}", min_value=0, value=val_def, step=1, key=codigo)

# Cálculos dinámicos basados exclusivamente en las columnas del Google Sheet
ml_neto_total = 0.0
peso_total = 0.0

if df_catalogo is not None:
    for idx, row in df_catalogo.iterrows():
        codigo = str(row.get("ID / Código", f"B{idx+1}"))
        cant = cantidades.get(codigo, 0)
        
        if cant > 0:
            # Leer valores técnicos del Sheet
            peso_u = float(row.get("Peso Bruto por bulto (kg)", 0))
            ml_u = float(row.get("ML unitarios por bulto (m)", 0))
            
            peso_total += cant * peso_u
            ml_neto_total += cant * ml_u

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
    
    # Renderizado del tráiler a escala
    fig, ax = plt.subplots(figsize=(11, 3.2))
    truck_width = 2.45
    total_length = 13.60

    # Contorno del semirremolque
    ax.add_patch(patches.Rectangle((0, 0), total_length, truck_width, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    # Dibujar indicador de carga visual
    if ml_con_holgura > 0:
        ax.add_patch(patches.Rectangle((0, 0), min(total_length, ml_con_holgura), truck_width, facecolor='#1971C2', alpha=0.15))
        ax.axvline(x=ml_con_holgura, color='#D6336C', linestyle='--', linewidth=2.5)
        ax.text(ml_con_holgura + 0.15, 1.22, f"FIN DE CARGA\n{ml_con_holgura:.2f} ML\n({peso_total:,.0f} kg)", 
                color='#D6336C', fontsize=8.5, fontweight='bold', va='center')

    # Marcadores de orientación
    ax.text(0.1, truck_width - 0.25, "CABECERA / FRENTE", fontsize=7.5, fontweight='bold', color='#495057')
    ax.text(total_length - 0.2, truck_width - 0.25, "PUERTAS / TRASERA", fontsize=7.5, fontweight='bold', color='#495057', ha='right')

    ax.set_xlim(-0.1, total_length + 0.2)
    ax.set_ylim(-0.1, truck_width + 0.3)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
