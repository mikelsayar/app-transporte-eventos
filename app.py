import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

# Enlace de exportación CSV limpio y directo (no sensible a tildes)
CSV_URL = "https://docs.google.com/spreadsheets/d/1N0Lj_zBfrLAdGmhsCwFnUQnOhFE9Ih6eoMdWMB5qV4c/export?format=csv"

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
            
            # Valor por defecto inicial para ver datos en pantalla
            val_def = 4 if "KSL" in nombre else (3 if "SL-SUB" in nombre or "D80" in nombre else 0)
            cantidades[codigo] = st.number_input(nombre, min_value=0, value=val_def, step=1, key=f"inp_{codigo}")

# Cálculos dinámicos basados en la hoja de cálculo
ml_neto_total = 0.0
peso_total = 0.0

if df_catalogo is not None:
    for idx, row in df_catalogo.iterrows():
        codigo = str(row.get("ID / Código", f"B{idx+1}"))
        cant = cantidades.get(codigo, 0)
        
        if cant > 0:
            try:
                peso_u = float(row.get("Peso Bruto por bulto (kg)", 0))
            except:
                peso_u = 0.0
            try:
                ml_u = float(row.get("ML unitarios por bulto (m)", 0))
            except:
                ml_u = 0.0
                
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
    
    fig, ax = plt.subplots(figsize=(11, 3.2))
    truck_width = 2.45
    total_length = 13.60

    ax.add_patch(patches.Rectangle((0, 0), total_length, truck_width, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    if ml_con_holgura > 0:
        ancho_carga = min(total_length, ml_con_holgura)
        ax.add_patch(patches.Rectangle((0, 0), ancho_carga, truck_width, facecolor='#1971C2', alpha=0.25))
        ax.axvline(x=ancho_carga, color='#D6336C', linestyle='--', linewidth=2.5)
        ax.text(ancho_carga + 0.15, 1.22, f"FIN DE CARGA\n{ml_con_holgura:.2f} ML\n({peso_total:,.0f} kg)", 
                color='#D6336C', fontsize=8.5, fontweight='bold', va='center')

    ax.text(0.1, truck_width - 0.25, "CABECERA / FRENTE", fontsize=7.5, fontweight='bold', color='#495057')
    ax.text(total_length - 0.2, truck_width - 0.25, "PUERTAS / TRASERA", fontsize=7.5, fontweight='bold', color='#495057', ha='right')

    ax.set_xlim(-0.1, total_length + 0.2)
    ax.set_ylim(-0.1, truck_width + 0.3)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
