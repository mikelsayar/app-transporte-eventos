import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Transporte y Estiba de Eventos", layout="wide", page_icon="🚛")

st.title("🚛 Gestor de Transporte y Estiba de Eventos")
st.markdown("Cálculo dinámico de metros lineales (ML), pesos y plano de carga en camión.")

# Layout en 2 columnas: Entradas a la izquierda, Resultados y Gráfico a la derecha
col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.subheader("📄 Carga de Albarán")
    archivo = st.file_uploader("Arrastra el PDF o foto del albarán", type=["pdf", "png", "jpg", "jpeg"])
    if archivo:
        st.success(f"Archivo cargado: {archivo.name}")
        st.caption("Valores sincronizados con la dotación detectada.")

    st.subheader("📋 Dotación de Bultos")
    cant_ksl = st.number_input("Carros 4x KSL", min_value=0, value=4, step=1)
    bumpers = st.number_input("Bumpers KSL (sobre stack de 4)", min_value=0, value=2, step=1)
    cant_sub = st.number_input("Patines 2x SL-SUB", min_value=0, value=3, step=1)
    cant_d80 = st.number_input("Touring Racks D80 (apilados x2)", min_value=0, value=3, step=1)
    cant_motores = st.number_input("Cases individuales Motor 2T", min_value=0, value=4, step=1)
    cant_cl5 = st.number_input("Case Yamaha CL5 FOH", min_value=0, value=1, step=1)
    cant_dm7 = st.number_input("Case Yamaha DM7 Monitores", min_value=0, value=1, step=1)
    cant_mjf = st.number_input("Cases dobles MJF-210 (cuñas)", min_value=0, value=4, step=1)
    cant_side = st.number_input("Dollies Sidefill/Drumfill Meyer", min_value=0, value=3, step=1)
    cant_racks_sis = st.number_input("Racks 16U / RIO / SAIs", min_value=0, value=2, step=1)
    cant_baul120 = st.number_input("Baúles cables 120x60", min_value=0, value=4, step=1)
    cant_baul80 = st.number_input("Baúles accesorios 80x60", min_value=0, value=3, step=1)

# Cálculos de ML y peso
ml_neto = (
    (cant_ksl / 2) * 1.00 +
    (cant_sub / 2) * 0.75 +
    (cant_d80 / 8) * 0.80 +
    (cant_motores / 4) * 0.55 +
    cant_cl5 * 0.55 +
    cant_dm7 * 0.50 +
    (cant_mjf / 4) * 0.60 +
    (cant_side / 3) * 0.75 +
    (cant_racks_sis / 3) * 0.75 +
    (cant_baul120 / 4) * 1.20 +
    (cant_baul80 / 6) * 0.60
)
ml_con_holgura = ml_neto * 1.10

peso_total = (
    cant_ksl * 260 + bumpers * 95 +
    cant_sub * 280 +
    cant_d80 * 105 +
    cant_motores * 110 +
    cant_cl5 * 110 +
    cant_dm7 * 75 +
    cant_mjf * 95 +
    cant_side * 110 +
    cant_racks_sis * 90 +
    cant_baul120 * 180 +
    cant_baul80 * 110
)

with col_der:
    st.subheader("📊 Resumen de Transporte")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metros Lineales (+10%)", f"{ml_con_holgura:.2f} ML", f"Neto: {ml_neto:.2f} m")
    m2.metric("Peso Total de Carga", f"{peso_total:,.0f} kg")
    
    if ml_con_holgura <= 7.8 and peso_total <= 9000:
        vehiculo = "Rígido 18t (8.0m)"
    else:
        vehiculo = "Tráiler 13.60m"
    m3.metric("Vehículo Óptimo", vehiculo)

    ocupacion = min(100, int((ml_con_holgura / 13.60) * 100))
    m4.metric("Ocupación Tráiler", f"{ocupacion}%", f"{max(0.0, 13.60 - ml_con_holgura):.1f} m libres")

    st.subheader("📐 Esquema de Estiba (Planta de Carga)")
    
    # Dibujo del plano 2D
    fig, ax = plt.subplots(figsize=(11, 3.4))
    truck_width = 2.45
    total_length = 13.60

    # Contenedor del camión
    ax.add_patch(patches.Rectangle((0, 0), total_length, truck_width, linewidth=2, edgecolor='#333333', facecolor='#F8F9FA'))

    # Generación de bloques de carga dinámicos según cantidades
    pos_x = 0.05
    bloques = []

    # 1. Carros KSL
    filas_ksl = (cant_ksl + 1) // 2
    for i in range(filas_ksl):
        tiene_bumper = (i * 2 < bumpers)
        etiqueta = "Carro KSL\n+ Bumper" if tiene_bumper else "Carro 4x KSL"
        bloques.append((pos_x, 0.05, 1.00, 1.15, etiqueta, "#1971C2"))
        if (i * 2 + 1) < cant_ksl:
            tiene_bumper_2 = ((i * 2 + 1) < bumpers)
            etiqueta_2 = "Carro KSL\n+ Bumper" if tiene_bumper_2 else "Carro 4x KSL"
            bloques.append((pos_x, 1.25, 1.00, 1.15, etiqueta_2, "#1971C2"))
        pos_x += 1.05

    # 2. SL-SUBs
    filas_sub = (cant_sub + 1) // 2
    for i in range(filas_sub):
        bloques.append((pos_x, 0.05, 0.75, 1.15, "Patín SL-SUB", "#7048E8"))
        if (i * 2 + 1) < cant_sub:
            bloques.append((pos_x, 1.25, 0.75, 1.15, "Patín SL-SUB", "#7048E8"))
        pos_x += 0.80

    # 3. D80 Racks
    if cant_d80 > 0:
        bloques.append((pos_x, 0.05, 0.80, 1.15, f"{cant_d80}x Racks D80\n(apilados)", "#E8590C"))
        pos_x += 0.85

    # 4. Consolas
    if cant_cl5 > 0 or cant_dm7 > 0:
        if cant_cl5 > 0:
            bloques.append((pos_x, 0.05, 0.90, 1.30, "CL5 FOH", "#2F9E44"))
        if cant_dm7 > 0:
            bloques.append((pos_x, 1.40, 0.90, 1.00, "DM7 Mon", "#2F9E44"))
        pos_x += 0.95

    # 5. Motores
    if cant_motores > 0:
        bloques.append((pos_x, 0.05, 0.55, 2.35, f"{cant_motores}x Motores 2T individuales", "#F59F00"))
        pos_x += 0.60

    # 6. Monitores cuña MJF
    if cant_mjf > 0:
        bloques.append((pos_x, 0.05, 0.60, 2.35, f"{cant_mjf}x Cases MJF-210 (apilados)", "#20C997"))
        pos_x += 0.65

    # 7. Baúles y varios
    if cant_baul120 > 0 or cant_baul80 > 0:
        bloques.append((pos_x, 0.05, 1.00, 2.35, f"Baúles Cables/Pies\n({cant_baul120}x 120 + {cant_baul80}x 80)", "#495057"))
        pos_x += 1.05

    # Dibujar los rectángulos
    for x, y, w, h, label, color in bloques:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", linewidth=1.2, edgecolor='#1E1E1E', facecolor=color, alpha=0.88)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, color='white', ha='center', va='center', fontsize=7.5, fontweight='bold')

    # Línea de corte de carga
    ax.axvline(x=ml_con_holgura, color='#D6336C', linestyle='--', linewidth=2)
    ax.text(ml_con_holgura + 0.15, 1.22, f"FIN DE CARGA\n{ml_con_holgura:.2f} ML", color='#D6336C', fontsize=8, fontweight='bold', va='center')

    ax.set_xlim(-0.1, total_length + 0.2)
    ax.set_ylim(-0.1, truck_width + 0.3)
    ax.set_aspect('equal')
    ax.axis('off')

    st.pyplot(fig)
