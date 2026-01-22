import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Finanzas Pro | Red Edition", layout="wide", initial_sidebar_state="collapsed")

# --- DISEÑO CSS: BLANCO, NEGRO Y ROJO ---
st.markdown("""
    <style>
    /* Fondo Blanco y Texto Negro */
    .main { background-color: #ffffff !important; color: #000000 !important; }
    
    /* Forzar color de texto en todos los encabezados y párrafos */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { color: #000000 !important; font-family: 'Inter', sans-serif; }
    
    /* Métricas Minimalistas con borde rojo */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #000000;
        border-left: 8px solid #FF0000; /* El detalle en rojo */
        padding: 20px;
        border-radius: 4px;
        box-shadow: 5px 5px 0px #000000; /* Sombra sólida estilo retro/moderno */
    }
    
    /* Botones: Fondo Negro, Texto Blanco, Hover Rojo */
    .stButton>button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #000000 !important;
        border-radius: 0px !important;
        transition: 0.4s;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        background-color: #FF0000 !important;
        border-color: #FF0000 !important;
        color: #ffffff !important;
        transform: translateY(-2px);
    }
    
    /* Tabs (Pestañas) */
    button[data-baseweb="tab"] { color: #000000 !important; font-weight: bold; }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF0000 !important;
        color: #ffffff !important;
        border-radius: 4px 4px 0 0;
    }

    /* Input boxes y Selectores */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border: 1px solid #000000 !important;
        border-radius: 0px !important;
    }

    /* Barra de progreso en Rojo */
    div[data-testid="stProgress"] > div > div > div > div {
        background-color: #FF0000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN Y CARGA DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)

if not df.empty:
    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce').dt.date
    df = df.dropna(subset=['concepto'])

# --- TITULO ---
st.markdown("# FINANZAS REALES <span style='color: #FF0000;'>PRO</span>", unsafe_allow_html=True)
st.write("---")

# --- LÓGICA DE CÁLCULO ---
if not df.empty:
    # Cálculos estándar
    total_ing = df[df['tipo'] == 'Ingreso']['monto'].sum()
    total_gas = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    # Deudas (Lo que DEBO)
    deudas = df[df['tipo'] == 'Deuda'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'total'})
    pagos = df[df['tipo'] == 'Pago Deuda'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'pagado'})
    res_deudas = pd.merge(deudas, pagos, on='concepto', how='left').fillna(0)
    res_deudas['pendiente'] = res_deudas['total'] - res_deudas['pagado']
    total_debo = res_deudas['pendiente'].sum()

    # Préstamos (Lo que ME DEBEN)
    prestado = df[df['tipo'] == 'Prestado'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'total'})
    cobrado = df[df['tipo'] == 'Cobro Préstamo'].groupby('concepto')['monto'].sum().reset_index().rename(columns={'monto': 'recuperado'})
    res_prestamos = pd.merge(prestado, cobrado, on='concepto', how='left').fillna(0)
    res_prestamos['por_cobrar'] = res_prestamos['total'] - res_prestamos['recuperado']
    total_me_deben = res_prestamos['por_cobrar'].sum()

    # Saldos Finales
    saldo_real = total_ing - total_gas - df[df['tipo'] == 'Pago Deuda']['monto'].sum() - df[df['tipo'] == 'Prestado']['monto'].sum() + df[df['tipo'] == 'Cobro Préstamo']['monto'].sum()
    patrimonio = saldo_real + total_me_deben

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("DISPONIBLE (EFECTIVO)", f"{saldo_real:,.2f} €")
    m2.metric("PATRIMONIO TOTAL", f"{patrimonio:,.2f} €")
    m3.metric("PRÉSTAMOS (ACTIVOS)", f"{total_me_deben:,.2f} €")
    m4.metric("DEUDAS (PASIVOS)", f"{total_debo:,.2f} €")

    st.write("---")

    # --- DASHBOARD GRÁFICO (ROJO Y NEGRO) ---
    col_izq, col_der = st.columns([2, 1])
    
    with col_izq:
        # Gráfico de líneas con colores de la marca
        fig_line = px.line(df.sort_values('fecha'), x='fecha', y='monto', color='tipo',
                          title="FLUJO DE CAJA HISTÓRICO",
                          color_discrete_map={
                              "Ingreso": "#000000", # Negro
                              "Gasto": "#FF0000",   # Rojo
                              "Prestado": "#777777",# Gris
                              "Deuda": "#CC0000"    # Rojo Oscuro
                          }, template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)

    with col_der:
        # Donut de Gastos en escala de rojos
        df_gas = df[df['tipo'] == 'Gasto']
        if not df_gas.empty:
            fig_pie = px.pie(df_gas, values='monto', names='concepto', hole=0.7,
                            title="DISTRIBUCIÓN DE GASTOS",
                            color_discrete_sequence=['#FF0000', '#000000', '#444444', '#888888', '#CC0000'])
            st.plotly_chart(fig_pie, use_container_width=True)

# --- PANEL DE GESTIÓN ---
st.write("---")
tab_data, tab_ops = st.tabs(["📊 VER MOVIMIENTOS", "⚙️ GESTIONAR REGISTROS"])

with tab_data:
    st.dataframe(df.sort_values('fecha', ascending=False), use_container_width=True, hide_index=True)

with tab_ops:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("### AÑADIR")
        with st.form("add_f", clear_on_submit=True):
            tipo = st.selectbox("Operación", ["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"])
            conc = st.text_input("Concepto / Persona")
            mont = st.number_input("Euros (€)", min_value=0.0, step=0.01)
            if st.form_submit_button("GUARDAR"):
                if conc and mont > 0:
                    nuevo_id = int(df['id'].max() + 1) if not df.empty else 1
                    nueva_fila = pd.DataFrame([{"id": nuevo_id, "fecha": datetime.now().strftime("%Y-%m-%d"), "tipo": tipo, "concepto": conc, "monto": mont}])
                    conn.update(data=pd.concat([df, nueva_fila], ignore_index=True))
                    st.success("REGISTRADO")
                    st.rerun()

    with col_b:
        st.write("### EDITAR / BORRAR")
        if not df.empty:
            opciones = df.apply(lambda x: f"{int(x['id'])} | {x['tipo']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
            seleccion = st.selectbox("Selecciona un movimiento", opciones)
            id_sel = int(seleccion.split(" | ")[0])
            
            c1, c2 = st.columns(2)
            if c1.button("ELIMINAR REGISTRO", type="secondary", use_container_width=True):
                conn.update(data=df[df['id'] != id_sel])
                st.warning("BORRADO")
                st.rerun()
            
            st.info("Para editar, usa el formulario de 'Añadir' y borra el registro antiguo.")