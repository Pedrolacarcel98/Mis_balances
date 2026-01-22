import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Finanzas Pro | SaaS Edition", layout="wide", initial_sidebar_state="collapsed")

# --- DISEÑO CSS PERSONALIZADO ---
st.markdown("""
    <style>
    /* Fondo general */
    .main { background-color: #f8f9fa; }
    
    /* Estilo de las métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    /* Estilo de los tabs y contenedores */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    /* Botones principales */
    .stButton>button {
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN Y DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

if not df.empty:
    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
    df['fecha'] = pd.to_datetime(df['fecha']).dt.date
    df = df.dropna(subset=['concepto'])

# --- HEADER PROFESIONAL ---
st.title("Finanzas Reales 💎")
st.caption("Dashboard de control patrimonial de nivel profesional")
st.write("---")

# --- 2. CÁLCULOS LÓGICOS ---
if not df.empty:
    # A. Ingresos y Gastos
    total_ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
    total_gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    # B. Lógica de Deudas (Lo que DEBO)
    deudas_orig = df[df['tipo'] == 'Deuda'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'monto_deuda'})
    pagos_deudas = df[df['tipo'] == 'Pago Deuda'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'monto_pagado'})
    resumen_deudas = pd.merge(deudas_orig, pagos_deudas, on='concepto', how='left').fillna(0)
    resumen_deudas['pendiente'] = resumen_deudas['monto_deuda'] - resumen_deudas['monto_pagado']
    
    total_deudas_pendientes = resumen_deudas['pendiente'].sum()
    total_pagos_realizados = df[df['tipo'] == 'Pago Deuda']['monto'].sum()

    # C. Lógica de Préstamos (Lo que ME DEBEN)
    prestamos_dados = df[df['tipo'] == 'Prestado'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'monto_prestado'})
    cobros_recibidos = df[df['tipo'] == 'Cobro Préstamo'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'monto_cobrado'})
    resumen_prestamos = pd.merge(prestamos_dados, cobros_recibidos, on='concepto', how='left').fillna(0)
    resumen_prestamos['por_cobrar'] = resumen_prestamos['monto_prestado'] - resumen_prestamos['monto_cobrado']
    
    total_por_cobrar = resumen_prestamos['por_cobrar'].sum()
    total_prestado = df[df['tipo'] == 'Prestado']['monto'].sum()
    total_cobrado = df[df['tipo'] == 'Cobro Préstamo']['monto'].sum()

    # D. Definición de Saldos
    # Saldo Disponible = Dinero real en mano
    saldo_disponible = total_ingresos - total_gastos - total_pagos_realizados - total_prestado + total_cobrado
    # Patrimonio Total = Efectivo + Dinero que te deben (tus activos)
    patrimonio_total = saldo_disponible + total_por_cobrar

    # --- 3. DASHBOARD DE MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Saldo Disponible", f"{saldo_disponible:,.2f} €", help="Dinero real en tu cuenta")
    m2.metric("Patrimonio Neto", f"{patrimonio_total:,.2f} €", help="Tu valor total (Efectivo + Préstamos)")
    m3.metric("Por Cobrar", f"{total_por_cobrar:,.2f} €", delta="Mis Activos")
    m4.metric("Deuda Pendiente", f"{total_deudas_pendientes:,.2f} €", delta=f"-{total_deudas_pendientes:,.2f}", delta_color="inverse")

    # --- 4. VISUALIZACIÓN GRÁFICA ---
    st.write("### 📊 Análisis de Situación")
    col_g1, col_g2 = st.columns([2, 1])

    with col_g1:
        # Gráfico de líneas (Tendencia)
        df_sorted = df.sort_values('fecha')
        fig_line = px.line(df_sorted, x='fecha', y='monto', color='tipo', 
                          title="Histórico de Movimientos",
                          color_discrete_map={"Ingreso": "#2ecc71", "Gasto": "#e74c3c", "Prestado": "#3498db", "Deuda": "#f1c40f"},
                          template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)

    with col_g2:
        # Gráfico Donut (Distribución de Gastos)
        df_gastos_pie = df[df['tipo'] == 'Gasto']
        if not df_gastos_pie.empty:
            fig_pie = px.pie(df_gastos_pie, values='monto', names='concepto', 
                            title="Distribución de Gastos", hole=0.5,
                            color_discrete_sequence=px.colors.sequential.Tealgrn)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay gastos registrados para analizar.")

# --- 5. GESTIÓN DE MOVIMIENTOS ---
st.write("---")
st.subheader("⚙️ Gestión y Operaciones")
tab_view, tab_add, tab_edit, tab_delete = st.tabs(["📄 Ver Datos", "➕ Añadir", "✏️ Editar", "🗑️ Borrar"])

with tab_view:
    cv1, cv2 = st.columns(2)
    with cv1:
        st.write("**Entradas (Ingresos y Cobros)**")
        st.dataframe(df[df['tipo'].isin(['Ingreso', 'Cobro Préstamo'])].sort_values('fecha', ascending=False), use_container_width=True, hide_index=True)
    with cv2:
        st.write("**Salidas (Gastos, Deudas y Préstamos)**")
        st.dataframe(df[df['tipo'].isin(['Gasto', 'Pago Deuda', 'Prestado'])].sort_values('fecha', ascending=False), use_container_width=True, hide_index=True)

with tab_add:
    with st.form("form_add", clear_on_submit=True):
        f1, f2, f3 = st.columns([1, 2, 1])
        tipo_add = f1.selectbox("Tipo", ["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"])
        
        # Selección dinámica para facilitar la entrada
        if tipo_add == "Pago Deuda" and not resumen_deudas.empty:
            concepto_add = f2.selectbox("Acreedor", resumen_deudas['concepto'].tolist())
        elif tipo_add == "Cobro Préstamo" and not resumen_prestamos.empty:
            concepto_add = f2.selectbox("Deudor", resumen_prestamos['concepto'].tolist())
        else:
            concepto_add = f2.text_input("Concepto / Nombre")
            
        monto_add = f3.number_input("Cantidad (€)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Registrar Movimiento"):
            nuevo_id = int(df['id'].max() + 1) if not df.empty else 1
            nueva_fila = pd.DataFrame([{
                "id": nuevo_id, "fecha": datetime.now().strftime("%Y-%m-%d"),
                "tipo": tipo_add, "concepto": concepto_add, "monto": monto_add
            }])
            conn.update(data=pd.concat([df, nueva_fila], ignore_index=True))
            st.success("¡Registro añadido!")
            st.rerun()

with tab_edit:
    if not df.empty:
        opciones_edit = df.apply(lambda x: f"{int(x['id'])} | {x['tipo']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        seleccion_edit = st.selectbox("Selecciona registro a editar", opciones_edit)
        id_edit = int(seleccion_edit.split(" | ")[0])
        datos_prev = df[df['id'] == id_edit].iloc[0]
        
        with st.form("form_edit"):
            fe1, fe2, fe3 = st.columns([1, 2, 1])
            tipo_ed = fe1.selectbox("Nuevo Tipo", ["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"], 
                                   index=["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"].index(datos_prev['tipo']))
            conc_ed = fe2.text_input("Nuevo Concepto", value=datos_prev['concepto'])
            mont_ed = fe3.number_input("Nuevo Monto", value=float(datos_prev['monto']), step=0.01)
            
            if st.form_submit_button("Actualizar"):
                df.loc[df['id'] == id_edit, ['tipo', 'concepto', 'monto']] = [tipo_ed, conc_ed, mont_ed]
                conn.update(data=df)
                st.success("Cambios guardados")
                st.rerun()

with tab_delete:
    if not df.empty:
        opciones_del = df.apply(lambda x: f"{int(x['id'])} | {x['tipo']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        seleccion_del = st.selectbox("Selecciona registro a eliminar", opciones_del)
        if st.button("Confirmar Borrado", type="primary"):
            id_del = int(seleccion_del.split(" | ")[0])
            conn.update(data=df[df['id'] != id_del])
            st.warning("Registro eliminado")
            st.rerun()