import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control Financiero Pro", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# 1. Carga y Limpieza de Datos
df = conn.read(ttl=0)

if not df.empty:
    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
    df = df.dropna(subset=['concepto']) 

st.title("Gestión de Finanzas Personales 💰")

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
col_tab1, col_tab2 = st.columns(2)
with col_tab1:
    st.subheader("📥 Ingresos y Cobros")
    df_inc = df[df["tipo"].isin(["Ingreso", "Cobro Préstamo"])].sort_values("fecha", ascending=False)
    st.dataframe(df_inc[["fecha", "tipo", "concepto", "monto"]], use_container_width=True, hide_index=True)
with col_tab2:
    st.subheader("📤 Gastos y Pagos")
    df_exp = df[df["tipo"].isin(["Gasto", "Pago Deuda", "Prestado"])].sort_values("fecha", ascending=False)
    st.dataframe(df_exp[["fecha", "tipo", "concepto", "monto"]], use_container_width=True, hide_index=True)

# --- 5. GESTIÓN DE DATOS (AÑADIR, EDITAR, BORRAR) ---
st.divider()
st.subheader("⚙️ Gestión de Movimientos")
tab_add, tab_edit, tab_delete = st.tabs(["➕ Añadir", "✏️ Editar", "🗑️ Eliminar"])

# TAB AÑADIR
with tab_add:
    with st.form("form_add", clear_on_submit=True):
        f1, f2, f3 = st.columns([1, 2, 1])
        tipo = f1.selectbox("Tipo", ["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"], key="add_tipo")
        
        if tipo == "Pago Deuda" and not resumen_deudas.empty:
            concepto = f2.selectbox("¿Qué deuda pagas?", resumen_deudas['concepto'].tolist())
        elif tipo == "Cobro Préstamo" and not resumen_prestamos.empty:
            concepto = f2.selectbox("¿Quién devuelve?", resumen_prestamos['concepto'].tolist())
        else:
            concepto = f2.text_input("Concepto / Persona")
            
        monto = f3.number_input("Euros", min_value=0.0, step=0.01)
        if st.form_submit_button("Guardar Nuevo"):
            nuevo_id = int(df['id'].max() + 1) if not df.empty else 1
            nueva_fila = pd.DataFrame([{"id": nuevo_id, "fecha": datetime.now().strftime("%Y-%m-%d"), "tipo": tipo, "concepto": concepto, "monto": monto}])
            conn.update(data=pd.concat([df, nueva_fila], ignore_index=True))
            st.success("Guardado")
            st.rerun()

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