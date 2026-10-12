import streamlit as st

st.set_page_config(page_title="Transporte de Eventos", layout="wide", page_icon="🚛")

st.title("🚛 Gestor de Transporte y Estiba")
st.success("✅ Aplicación conectada y operativa")

st.subheader("📋 Material para Evento")
c1, c2 = st.columns(2)

with c1:
    cant_ksl = st.number_input("Carros 4x KSL", min_value=0, value=4)
    bumpers = st.number_input("Bumpers KSL (sobre stack)", min_value=0, value=2)
    cant_sub = st.number_input("Patines 2x SL-SUB", min_value=0, value=3)
    cant_d80 = st.number_input("Touring Racks D80 (apilados)", min_value=0, value=3)

with c2:
    cant_motores = st.number_input("Motores 2T individuales", min_value=0, value=4)
    cant_cl5 = st.number_input("Yamaha CL5 FOH", min_value=0, value=1)
    cant_dm7 = st.number_input("Yamaha DM7 Monitores", min_value=0, value=1)

# Cálculos directos de suelo y peso
ml_neto = (cant_ksl * 0.50) + (cant_sub * 0.375) + (cant_d80 * 0.10) + (cant_motores * 0.14) + 1.00
ml_con_holgura = ml_neto * 1.10
peso_total = (cant_ksl * 260) + (bumpers * 95) + (cant_sub * 280) + (cant_d80 * 105) + (cant_motores * 110) + 185

st.divider()
st.subheader("📊 Resumen Logístico de Carga")
m1, m2, m3 = st.columns(3)
m1.metric("Metros Lineales (con holgura)", f"{ml_con_holgura:.2f} ML", f"Neto: {ml_neto:.2f} m")
m2.metric("Peso Total Estimado", f"{peso_total:,.0f} kg")
m3.metric("Vehículo Recomendado", "Rígido 18t (8m útiles)" if ml_con_holgura <= 7.8 else "Tráiler 13.6m")
