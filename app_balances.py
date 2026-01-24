import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# CSS Minimalista: Blanco, Negro y Rojo
st.markdown("""
    <style>
    /* Fondo y Texto General */
    .main { background-color: #ffffff !important; }
    h1, h2, h3, h4, p, span, label { color: #000000 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Métricas con acento rojo */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #f0f0f0;
        border-left: 5px solid #ff4b4b;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Botones Negros con Hover Rojo */
    .stButton>button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none;
        border-radius: 4px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #ff4b4b !important;
        transform: scale(1.02);
    }

    /* Tabs */
    button[data-baseweb="tab"] { color: #888888 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #ff4b4b !important; border-bottom-color: #ff4b4b !important; }
    
    /* Divisores */
    hr { border-top: 1px solid #eeeeee; }
    </style>
    """, unsafe_allow_html=True)
# Función sencilla de clasificación de conceptos usando palabras clave
def clasificador_ia_sencilla(concepto):
    concepto = concepto.lower()
    
    # Diccionario expandido de "neuronas"
    categorias = {
        "Transporte": [
            "taxi", "uber", "cabify", "bus", "metro", "gasolina", "gasolinera", "parking", "estacionamiento", 
            "renfe", "vuelo", "avión", "tren", "peaje", "taller", "reparacion", "neumaticos", "itv", "diésel", "repsol", "cepsa"
        ],
        "Alimentación": [
            "mercadona", "carrefour", "lidl", "aldi", "dia", "alcampo", "eroski", "supermercado", "hipercor",
            "comida", "restaurante", "bar", "pizzería", "glovo", "just eat", "ubereats", "café", "desayuno", 
            "cena", "burger king", "mcdonalds", "tapa", "panaderia", "carniceria"
        ],
        "Hogar": [
            "alquiler", "hipoteca", "luz", "agua", "internet", "comunidad", "ikea", "leroy merlin", 
            "ferretería", "fontanero", "electricista", "mueble", "deco", "limpieza", "detergente", 
            "gas", "calefacción", "endesa", "iberdrola"
        ],
        "Ocio y Viajes": [
            "cine", "netflix", "spotify", "gym", "gimnasio", "concierto", "teatro", "videojuegos", 
            "hotel", "airbnb", "booking", "viaje", "discoteca", "copa", "cerveza", "hbo", "disney+", 
            "playstation", "xbox", "steam"
        ],
        "Salud y Belleza": [
            "farmacia", "médico", "dentista", "hospital", "seguro", "psicologo", "fisio", 
            "peluquería", "barbería", "cosméticos", "maquillaje", "perfume", "crema"
        ],
        "Suscripciones y Digital": [
            "amazon", "prime", "apple", "icloud", "adobe", "google", "cloud", "hosting", 
            "software", "patreon", "chatgpt", "midjourney"
        ],
        "Ropa y Complementos": [
            "zara", "h&m", "nike", "adidas", "mango", "primark", "ropa", "zapatos", 
            "bolso", "moda", "tienda", "centro comercial"
        ],
        "Educación": [
            "curso", "academia", "universidad", "libro", "formacion", "master", "clases", "escuela"
        ],
        "Restaurantes": [
            "restaurante", "café", "bar", "pizzería", "glovo", "just eat", "ubereats", 
            "desayuno", "comida", "cena", "burger king", "mcdonalds", "tapa"
        ],
        "Tecnología": [
            "apple", "samsung", "xiaomi", "ordenador", "portátil", "tablet", "smartphone", 
            "televisión", "tv", "auriculares", "cargador", "gadget"
        ]
    }

    for categoria, palabras in categorias.items():
        if any(palabra in concepto for palabra in palabras):
            return categoria
            
    return "Varios"
# --- 0. CONFIGURACIONES INICIALES ---
st.set_page_config(page_title="Control Financiero Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# 1. Carga y Limpieza de Datos
df = conn.read(ttl=0)

if not df.empty:
    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
    # Convertimos la fecha a objeto fecha real para que los gráficos funcionen bien
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.dropna(subset=['concepto']) 

    # --- LA MAGIA PARA TUS DATOS ANTIGUOS ---
    # Esta línea recorre TODO el Excel y aplica la IA a cada fila
    df['categoria'] = df.apply(
        lambda row: clasificador_ia_sencilla(row['concepto']) if row['tipo'] == 'Gasto' else (
            "Deudas" if "Deuda" in row['tipo'] else (
                "Préstamos" if "Préstamo" in row['tipo'] or row['tipo'] == "Prestado" else "Ingresos"
            )
        ), axis=1
    )
# --- 2. CÁLCULOS LÓGICOS AVANZADOS ---
if not df.empty:
    # A. Ingresos y Gastos Estándar
    total_ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
    total_gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    # B. Lógica de Deudas (Lo que tú debes)
    deudas_orig = df[df['tipo'] == 'Deuda'].groupby('concepto')['monto'].sum().reset_index()
    deudas_orig.columns = ['concepto', 'monto_total_deuda']
    pagos_deudas = df[df['tipo'] == 'Pago Deuda'].groupby('concepto')['monto'].sum().reset_index()
    pagos_deudas.columns = ['concepto', 'monto_pagado']
    resumen_deudas = pd.merge(deudas_orig, pagos_deudas, on='concepto', how='left').fillna(0)
    resumen_deudas['pendiente'] = resumen_deudas['monto_total_deuda'] - resumen_deudas['monto_pagado']
    total_deudas_pendientes = resumen_deudas['pendiente'].sum()
    pagos_deudas_total = df[df['tipo'] == 'Pago Deuda']['monto'].sum()

    # C. Lógica de Préstamos (Lo que te deben a ti)
    prestamos_dados = df[df['tipo'] == 'Prestado'].groupby('concepto')['monto'].sum().reset_index()
    prestamos_dados.columns = ['concepto', 'monto_prestado']
    cobros_recibidos = df[df['tipo'] == 'Cobro Préstamo'].groupby('concepto')['monto'].sum().reset_index()
    cobros_recibidos.columns = ['concepto', 'monto_recuperado']
    resumen_prestamos = pd.merge(prestamos_dados, cobros_recibidos, on='concepto', how='left').fillna(0)
    resumen_prestamos['por_cobrar'] = resumen_prestamos['monto_prestado'] - resumen_prestamos['monto_recuperado']
    total_por_cobrar = resumen_prestamos['por_cobrar'].sum()
    
    prestado_total = df[df['tipo'] == 'Prestado']['monto'].sum()
    cobrado_total = df[df['tipo'] == 'Cobro Préstamo']['monto'].sum()

    # D. Definición de Saldos
    saldo_disponible = total_ingresos - total_gastos - pagos_deudas_total - prestado_total + cobrado_total
    patrimonio_total = saldo_disponible + total_por_cobrar

    # --- 3. SECCIÓN DE MÉTRICAS ---
    st.subheader("Resumen de Situación")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ingresos Totales", f"{total_ingresos:,.2f} €")
    m2.metric("Gastos Totales", f"{total_gastos:,.2f} €", delta=f"-{total_gastos:,.2f} €", delta_color="inverse")
    m3.metric("Por Cobrar", f"{total_por_cobrar:,.2f} €")
    m4.metric("Deuda Pendiente", f"{total_deudas_pendientes:,.2f} €", delta_color="inverse")

    color_banner = "green" if saldo_disponible >= 0 else "red"
    st.markdown(f"""
        <div style="background-color: rgba(200, 200, 200, 0.1); padding: 25px; border-radius: 15px; border-left: 10px solid {color_banner}; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><h4 style="margin:0; opacity: 0.8;">SALDO DISPONIBLE (EFECTIVO)</h4><p style="font-size: 32px; color: {color_banner}; font-weight: bold; margin:0;">{saldo_disponible:,.2f} €</p></div>
                <div style="text-align: right;"><h4 style="margin:0; opacity: 0.8;">PATRIMONIO TOTAL</h4><p style="font-size: 24px; color: #555; font-weight: bold; margin:0;">{patrimonio_total:,.2f} €</p></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. VISUALIZACIÓN Y TABLAS ---
st.divider()
col_tab1, col_tab2, col_tab3, col_tab4 = st.columns(4)
with col_tab1:
    st.subheader("📥 Ingresos y Cobros")
    df_inc = df[df["tipo"].isin(["Ingreso", "Cobro Préstamo"])].sort_values("fecha", ascending=False)
    st.dataframe(df_inc[["fecha", "tipo", "concepto", "monto"]], use_container_width=True, hide_index=True)
with col_tab2:
    st.subheader("📤 Gastos y Pagos")
    df_exp = df[df["tipo"].isin(["Gasto", "Pago Deuda", "Prestado"])].sort_values("fecha", ascending=False)
    st.dataframe(df_exp[["fecha", "tipo", "concepto", "monto"]], use_container_width=True, hide_index=True)

with col_tab3:
    st.subheader("📊 Resúmenes")
    if not resumen_deudas.empty:
        st.markdown("**Deudas Pendientes:**")
        st.dataframe(resumen_deudas[resumen_deudas['pendiente'] > 0][['concepto', 'monto_total_deuda', 'monto_pagado', 'pendiente']], use_container_width=True, hide_index=True)
    else:
        st.info("No hay deudas registradas")
    
    if not resumen_prestamos.empty:
        st.markdown("**Préstamos por Cobrar:**")
        st.dataframe(resumen_prestamos[resumen_prestamos['por_cobrar'] > 0][['concepto', 'monto_prestado', 'monto_recuperado', 'por_cobrar']], use_container_width=True, hide_index=True)
    else:
        st.info("No hay préstamos registrados")

#VISUALIZACIÓN:
with col_tab4:
    st.subheader("📊 Gastos por Categoría (IA)")
    df_gastos = df[df['tipo'] == 'Gasto']
    if not df_gastos.empty:
        # Agrupamos por la categoría que ha creado nuestra IA
        resumen_cat = df_gastos.groupby('categoria')['monto'].sum().sort_values(ascending=False)
        st.bar_chart(resumen_cat) # Un gráfico de barras sencillo y limpio
    else:
        st.info("Aún no hay gastos para categorizar.")
        
# --- 5. GESTIÓN DE DATOS (AÑADIR, EDITAR, BORRAR) ---
st.divider()
st.subheader("Gestión de Movimientos")
tab_add, tab_edit, tab_delete = st.tabs(["➕ Añadir", "✏️ Editar", "🗑️ Eliminar"])


# TAB AÑADIR
with tab_add:
    # IMPORTANTE: Sacamos el selector de tipo fuera del form para que la IA responda en tiempo real
    col_t1, col_t2 = st.columns([1, 3])
    with col_t1:
        tipo = st.selectbox("Tipo de Movimiento", 
                            ["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"], 
                            key="add_tipo_ia")

    with st.form("form_add_final", clear_on_submit=True):
        f_c1, f_c2 = st.columns([2, 1])
        
        # Lógica dinámica de conceptos
        if tipo == "Pago Deuda":
            lista_d = resumen_deudas[resumen_deudas['pendiente'] > 0]['concepto'].tolist()
            concepto = f_c1.selectbox("¿Qué deuda pagas?", lista_d) if lista_d else f_c1.text_input("Concepto (No hay deudas pendientes)")
        elif tipo == "Cobro Préstamo":
            lista_p = resumen_prestamos[resumen_prestamos['por_cobrar'] > 0]['concepto'].tolist()
            concepto = f_c1.selectbox("¿Quién te devuelve dinero?", lista_p) if lista_p else f_c1.text_input("Concepto (No hay préstamos pendientes)")
        else:
            concepto = f_c1.text_input("Concepto / Persona", placeholder="Ej: Taxi al aeropuerto")
            
            # --- FEEDBACK DE LA IA EN TIEMPO REAL ---
            if tipo == "Gasto" and concepto:
                cat_ia = clasificador_ia_sencilla(concepto)
                if cat_ia != "Varios":
                    st.info(f"🤖 **IA detecta:** {cat_ia}")
                else:
                    st.caption("🤖 IA: Sin categoría clara (irá a 'Varios')")

        monto = f_c2.number_input("Cantidad (€)", min_value=0.0, step=0.01)
        
        # BOTÓN DE GUARDADO
        if st.form_submit_button("Guardar Registro", use_container_width=True):
            if concepto and monto > 0:
                # 1. Determinar Categoría final
                if tipo == "Gasto":
                    categoria_final = clasificador_ia_sencilla(concepto)
                elif tipo in ["Deuda", "Pago Deuda"]:
                    categoria_final = "Deudas"
                elif tipo in ["Prestado", "Cobro Préstamo"]:
                    categoria_final = "Préstamos"
                else:
                    categoria_final = "Ingresos"

                # 2. Crear nueva fila (Asegúrate de que tu Excel tenga estas columnas)
                nuevo_id = int(df['id'].max() + 1) if not df.empty else 1
                nueva_fila = pd.DataFrame([{
                    "id": nuevo_id,
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "tipo": tipo,
                    "concepto": concepto,
                    "monto": monto,
                    "categoria": categoria_final  # <-- NUEVA COLUMNA PARA LA IA
                }])

                # 3. Actualizar Google Sheets
                df_up = pd.concat([df, nueva_fila], ignore_index=True)
                conn.update(data=df_up)
                
                st.success(f"✅ Registrado como {categoria_final}")
                st.rerun()
            else:
                st.error("Por favor, rellena el concepto y un monto mayor a 0.")
# TAB EDITAR
with tab_edit:
    if not df.empty:
        # 1. Selección del registro
        opciones_edit = df.apply(lambda x: f"{int(x['id'])} | {x['tipo']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        seleccion_edit = st.selectbox("Busca el registro que quieres modificar:", opciones_edit)
        id_edit = int(seleccion_edit.split(" | ")[0])
        
        # 2. Carga de datos actuales
        datos_actuales = df[df['id'] == id_edit].iloc[0]
        
        with st.form("form_edit"):
            fe1, fe2, fe3 = st.columns([1, 2, 1])
            nuevo_tipo = fe1.selectbox("Tipo", ["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"], 
                                      index=["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"].index(datos_actuales['tipo']))
            nuevo_concepto = fe2.text_input("Concepto", value=datos_actuales['concepto'])
            nuevo_monto = fe3.number_input("Euros", min_value=0.0, step=0.01, value=float(datos_actuales['monto']))
            
            if st.form_submit_button("Actualizar Registro"):
                df.loc[df['id'] == id_edit, ['tipo', 'concepto', 'monto']] = [nuevo_tipo, nuevo_concepto, nuevo_monto]
                conn.update(data=df)
                st.success(f"Registro {id_edit} actualizado correctamente")
                st.rerun()
    else:
        st.info("No hay datos para editar")

# TAB ELIMINAR
with tab_delete:
    if not df.empty:
        opciones_del = df.apply(lambda x: f"{int(x['id'])} | {x['tipo']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        seleccion_del = st.selectbox("Selecciona registro a eliminar:", opciones_del)
        if st.button("Eliminar Permanentemente", type="primary"):
            id_del = int(seleccion_del.split(" | ")[0])
            conn.update(data=df[df['id'] != id_del])
            st.warning(f"Registro {id_del} borrado")
            st.rerun()