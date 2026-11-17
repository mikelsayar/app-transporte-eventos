import streamlit as st
import pandas as pd

def mostrar_calculadora_manual():
    st.markdown("Configura los diferentes sistemas del diseño (Valores por lado):")
    
    # --- MAIN PA ---
    with st.expander("🔊 Main PA", expanded=True):
        c1, c2, c3 = st.columns(3)
        sistema_main = c1.selectbox("Sistema Main", ["d&b KSL", "d&b GSL", "d&b XSL", "d&b V-Series"], key="m_sys")
        cajas_main = c2.number_input("Cajas por lado", 0, 24, 10, key="m_cajas")
        lk_main = c3.selectbox("Acometida", ["10m LK", "20m LK", "30m LK", "50m LK"], key="m_lk")
        ap_main = st.checkbox("ArrayProcessing (AP) activado", value=True, key="m_ap")

    # --- OUTFILL ---
    with st.expander("🔈 Outfill / Sidefill"):
        c1, c2, c3 = st.columns(3)
        sistema_out = c1.selectbox("Sistema Outfill", ["Ninguno", "d&b V-Series", "d&b XSL", "d&b Y-Series"], key="o_sys")
        cajas_out = c2.number_input("Cajas por lado", 0, 24, 0, key="o_cajas")
        lk_out = c3.selectbox("Acometida", ["10m LK", "20m LK", "30m LK", "50m LK"], key="o_lk")
        ap_out = st.checkbox("ArrayProcessing (AP) activado", value=True, key="o_ap")

    # --- SUBWOOFERS ---
    with st.expander("🔉 Subwoofers (Volados o Suelo)"):
        c1, c2, c3 = st.columns(3)
        sistema_sub = c1.selectbox("Sistema Subs", ["Ninguno", "d&b SL-SUB", "d&b J-SUB", "d&b B22"], key="s_sys")
        cajas_sub = c2.number_input("Cajas por lado (o totales)", 0, 30, 0, key="s_cajas")
        acometida_sub = c3.selectbox("Acometida", ["Socapex 10m", "Socapex 20m", "NLT8 20m"], key="s_lk")

    # --- BOTÓN DE CALCULAR ---
    if st.button("Calcular Necesidades Totales", type="primary"):
        st.markdown("---")
        st.subheader("📋 Resumen de Material (Aproximación Base)")
        
        total_links = 0
        if cajas_main > 0: total_links += (cajas_main - 1) * 2
        if cajas_out > 0: total_links += (cajas_out - 1) * 2
        # Los subs suelen llevar un link cada 2 cajas o ir directos, lo afinaremos luego.
        
        st.success(f"📦 **LINKS NLT4 (L+R):** {total_links} unidades estimadas.")
        st.info("Próximamente: Matemática exacta para el cálculo de LKs/Breakouts en base a los canales de AP.")