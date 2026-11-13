import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Ruteo PA Inteligente", layout="wide", page_icon="🔌")

# --- FUNCIONES DE LECTURA EASE FOCUS ---
def parse_xld(file_content):
    text = file_content.decode("utf-8")
    items = []
    current = {}
    
    for line in text.splitlines():
        line = line.strip()
        if line == ';':
            if 'Label' in current: items.append(current)
            current = {}
        elif line.startswith('"'):
            parts = line.split(',', 1)
            if len(parts) >= 2:
                current[parts[0].strip('"')] = parts[1].strip('"')
    if 'Label' in current: items.append(current)
    
    processed = []
    for it in items:
        if 'Position' in it:
            try:
                x, y, z = map(float, it['Position'].split(','))
            except:
                x, y, z = 0.0, 0.0, 0.0
        else:
            x, y, z = 0.0, 0.0, 0.0
            
        label = it.get('Label', 'Unknown')
        cat = "Otros"
        if "MAIN" in label.upper(): cat = "Main PA"
        elif "OUTFILL" in label.upper(): cat = "Outfill"
        elif "FRONTFILL" in label.upper() or "FF" in label.upper(): cat = "Frontfill"
        elif "SUB" in label.upper(): cat = "Subgraves"
        elif "DOWNFILL" in label.upper(): cat = "Downfill"

        processed.append({
            'Categoría': cat, 'Label': label,
            'X': x, 'Y': y, 'Z': z,
            'Modelo': it.get('Speaker', '')
        })
    return pd.DataFrame(processed)

def calcular_distancia_3d(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

# --- INTERFAZ ---
st.title("🔌 Motor de Cableado 3D a Almacén")

archivo_xld = st.file_uploader("Sube tu archivo .xld de EASE Focus o ArrayCalc", type=['xld', 'csv', 'txt'])

if archivo_xld:
    df_cajas = parse_xld(archivo_xld.getvalue())
    st.success(f"¡Diseño cargado! Detectados {len(df_cajas)} puntos de anclaje/cajas.")

    # 1. POSICIÓN DE LOS RACKS
    st.subheader("1. Ubicación de los Racks de Etapas")
    col_l, col_r, col_h = st.columns(3)
    with col_l:
        rack_l_x = st.number_input("X (Rack L):", value=-8.0, step=1.0)
        rack_l_y = st.number_input("Y (Rack L):", value=2.0, step=1.0)
    with col_r:
        rack_r_x = st.number_input("X (Rack R):", value=8.0, step=1.0)
        rack_r_y = st.number_input("Y (Rack R):", value=2.0, step=1.0)
    with col_h:
        holgura = st.slider("Holgura de seguridad", 1.0, 1.5, 1.15)

    st.divider()

    # 2. CONFIGURACIÓN INDEPENDIENTE POR ARREGLO
    st.subheader("2. Configuración por Zonas")
    categorias_detectadas = df_cajas['Categoría'].unique()
    
    # Diccionario para guardar lo que configuras en cada zona para usarlo luego en el cálculo
    config_zonas = [] 
    
    for cat in categorias_detectadas:
        st.markdown(f"### 🔸 Zona: {cat}")
        elementos_zona = df_cajas[df_cajas['Categoría'] == cat]
        
        c1, c2, c3 = st.columns([1, 1, 1.5])
        
        with c1:
            marca = st.selectbox(f"Marca {cat}:", ["d&b audiotechnik", "L-Acoustics"], key=f"marca_{cat}")
            cajas_por_arreglo = st.number_input(f"Cajas por arreglo:", min_value=1, value=8, step=1, key=f"cajas_{cat}")
            
        with c2:
            if cat == "Frontfill":
                modo = st.radio(f"Linkeo:", ["Directo a Rack", "Link a Pares"], key=f"modo_{cat}")
            elif cat == "Subgraves":
                modo = st.radio(f"Modo:", ["1 Canal / Caja", "2 Canales (Biamplificado)"], key=f"modo_{cat}")
            else:
                modo = st.radio(f"Modo Amp:", ["ArrayProcessing", "Line Link (2/ch)"], key=f"modo_{cat}")
                
        with c3:
            st.markdown("**Distancias de Tiro:**")
            tiros = []
            for idx, row in elementos_zona.iterrows():
                dist_l = calcular_distancia_3d(row['X'], row['Y'], row['Z'], rack_l_x, rack_l_y, 0.0)
                dist_r = calcular_distancia_3d(row['X'], row['Y'], row['Z'], rack_r_x, rack_r_y, 0.0)
                
                if dist_l <= dist_r:
                    tiros.append({"label": row['Label'], "rack": "L", "dist": dist_l * holgura})
                    st.write(f"- {row['Label']} ➔ Rack **L** ({dist_l*holgura:.1f}m)")
                else:
                    tiros.append({"label": row['Label'], "rack": "R", "dist": dist_r * holgura})
                    st.write(f"- {row['Label']} ➔ Rack **R** ({dist_r*holgura:.1f}m)")
                    
            config_zonas.append({
                "categoria": cat, "marca": marca, "modo": modo, 
                "cajas_por_arreglo": cajas_por_arreglo, "tiros": tiros
            })
        st.write("---")

    # 3. BOTÓN Y MOTOR MATEMÁTICO
    if st.button("🧮 Generar Listado de Cableado", type="primary", use_container_width=True):
        st.subheader("📦 Lista de Preparación a Almacén")
        
        barriletes_nl8 = 0
        barriletes_nl4 = 0
        
        for zona in config_zonas:
            st.markdown(f"#### 🔹 {zona['categoria']} ({zona['marca']})")
            
            for tiro in zona['tiros']:
                cajas = zona['cajas_por_arreglo']
                dist = tiro['dist']
                lista_cables = []
                
                # --- LOGICA D&B ---
                if zona['marca'] == "d&b audiotechnik":
                    if zona['categoria'] == "Subgraves":
                        canales = cajas * 2 if "2 Canales" in zona['modo'] else cajas
                    elif zona['categoria'] == "Frontfill":
                        canales = math.ceil(cajas / 2.0) if "Pares" in zona['modo'] else cajas
                    else:
                        canales = cajas if "ArrayProcessing" in zona['modo'] else math.ceil(cajas / 2.0)

                    num_lk25 = canales // 6
                    resto = canales % 6
                    num_nlt8 = resto // 2
                    num_nlt4 = resto % 2
                    
                    if num_lk25 > 0: lista_cables.append(f"**{num_lk25}x Manguera LK25** de tiro (≥ {dist:.1f}m) + *{num_lk25}x Breakout LK25 a 6xNLT4*")
                    if num_nlt8 > 0: lista_cables.append(f"**{num_nlt8}x Manguera NLT8** de tiro (≥ {dist:.1f}m) + *{num_nlt8}x Bifurca NLT8 a 2xNLT4*")
                    if num_nlt4 > 0: lista_cables.append(f"**{num_nlt4}x Manguera NLT4** de tiro directa (≥ {dist:.1f}m)")

                # --- LOGICA L-ACOUSTICS ---
                else:
                    if zona['categoria'] == "Subgraves":
                        canales = cajas * 2 if "2 Canales" in zona['modo'] else cajas
                        num_nl8 = canales // 4
                        num_nl4 = canales % 4
                        if num_nl8 > 0: 
                            lista_cables.append(f"**{num_nl8}x Manguera NL8** (≥ {dist:.1f}m) + *{num_nl8}x Breakout NL8 a 4xNL4*")
                            barriletes_nl8 += num_nl8
                    else:
                        ratio = 2 if "Line Link" in zona['modo'] or "Pares" in zona['modo'] else 1
                        lineas_nl4 = math.ceil(cajas / ratio)
                        links = cajas - lineas_nl4
                        
                        num_nl8 = lineas_nl4 // 2
                        num_nl4 = lineas_nl4 % 2
                        
                        if num_nl8 > 0: 
                            lista_cables.append(f"**{num_nl8}x Manguera NL8** (≥ {dist:.1f}m) + *{num_nl8}x Bifurca NL8 a 2xNL4*")
                            barriletes_nl8 += num_nl8
                        if num_nl4 > 0: lista_cables.append(f"**{num_nl4}x Manguera NL4** de tiro directa (≥ {dist:.1f}m)")
                        if links > 0: lista_cables.append(f"**{links}x Latiguillo NL4 (1m)** para links.")
                
                # Imprimir el resultado para este tiro específico
                st.write(f"**[Rack {tiro['rack']} ➔ {tiro['label']}]**")
                for c in lista_cables:
                    st.write(f"- {c}")
                    
        # Sumatorio final de barriletes
        if barriletes_nl8 > 0 or barriletes_nl4 > 0:
            st.markdown("#### 🔗 Adaptadores Automáticos Requeridos")
            if barriletes_nl8 > 0: st.write(f"- **{barriletes_nl8}x Barrilete Empalme NL8** (Para ecosistema L-Acoustics)")
            if barriletes_nl4 > 0: st.write(f"- **{barriletes_nl4}x Barrilete Empalme NL4**")
else:
    st.info("👆 Sube un archivo para comenzar.")