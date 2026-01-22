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

st.title("Gestión de Finanzas Personales")

# --- 2. CÁLCULOS LÓGICOS AVANZADOS ---
if not df.empty:
    # A. Ingresos y Gastos Estándar
    total_ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
    total_gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    # B. Lógica de Deudas (Lo que tú debes)
    deudas_orig = df[df['tipo'] == 'Deuda'].groupby('concepto')['monto'].sum().reset_index()
    pagos_deudas = df[df['tipo'] == 'Pago Deuda'].groupby('concepto')['monto'].sum().reset_index()
    resumen_deudas = pd.merge(deudas_orig, pagos_deudas, on='concepto', how='left').fillna(0)
    resumen_deudas['pendiente'] = resumen_deudas['monto']_x - resumen_deudas['monto']_y
    total_deudas_pendientes = resumen_deudas['pendiente'].sum()
    pagos_deudas_total = df[df['tipo'] == 'Pago Deuda']['monto'].sum()

    # C. Lógica de Préstamos (Lo que te deben a ti)
    prestamos_dados = df[df['tipo'] == 'Prestado'].groupby('concepto')['monto'].sum().reset_index()
    cobros_recibidos = df[df['tipo'] == 'Cobro Préstamo'].groupby('concepto')['monto'].sum().reset_index()
    resumen_prestamos = pd.merge(prestamos_dados, cobros_recibidos, on='concepto', how='left').fillna(0)
    resumen_prestamos['por_cobrar'] = resumen_prestamos['monto']_x - resumen_prestamos['monto']_y
    total_por_cobrar = resumen_prestamos['por_cobrar'].sum()
    
    prestado_total = df[df['tipo'] == 'Prestado']['monto'].sum()
    cobrado_total = df[df['tipo'] == 'Cobro Préstamo']['monto'].sum()

    # D. Definición de Saldos
    # El Saldo Disponible es el efectivo real que tienes ahora
    saldo_disponible = total_ingresos - total_gastos - pagos_deudas_total - prestado_total + cobrado_total
    
    # El Patrimonio Neto incluye el efectivo + lo que te deben (pues sigue siendo tu dinero)
    patrimonio_total = saldo_disponible + total_por_cobrar

    # --- 3. SECCIÓN DE MÉTRICAS ---
    st.subheader("Resumen de Situación")
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric("Ingresos Totales", f"{total_ingresos:,.2f} €")
    m2.metric("Gastos Totales", f"{total_gastos:,.2f} €", delta=f"-{total_gastos:,.2f} €", delta_color="inverse")
    m3.metric("Por Cobrar (Mis Préstamos)", f"{total_por_cobrar:,.2f} €", delta="Dinero fuera")
    m4.metric("Deuda Pendiente", f"{total_deudas_pendientes:,.2f} €", delta="Por pagar", delta_color="inverse")

    # Cuadro de Saldo Actual Principal
    color_banner = "green" if saldo_disponible >= 0 else "red"
    st.markdown(f"""
        <div style="background-color: rgba(200, 200, 200, 0.1); padding: 25px; border-radius: 15px; border-left: 10px solid {color_banner}; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin:0; opacity: 0.8;">SALDO DISPONIBLE (EFECTIVO)</h4>
                    <p style="font-size: 32px; color: {color_banner}; font-weight: bold; margin:0;">{saldo_disponible:,.2f} €</p>
                </div>
                <div style="text-align: right;">
                    <h4 style="margin:0; opacity: 0.8;">PATRIMONIO TOTAL</h4>
                    <p style="font-size: 24px; color: #555; font-weight: bold; margin:0;">{patrimonio_total:,.2f} €</p>
                    <small>Disponible + Préstamos realizados</small>
                </div>
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

# SECCIONES DE CONTROL DE DEUDAS Y PRÉSTAMOS
st.write("### 🔍 Control de Saldos Pendientes")
c_p1, c_p2 = st.columns(2)

with c_p1:
    with st.expander("Deudas"):
        if not resumen_deudas.empty:
            st.dataframe(
                resumen_deudas[resumen_deudas['pendiente'] > 0],
                column_config={"concepto": "Acreedor", "pendiente": st.column_config.NumberColumn("Queda por Pagar", format="%.2f €")},
                use_container_width=True, hide_index=True
            )

with c_p2:
    with st.expander("Préstamos Otorgados"):
        if not resumen_prestamos.empty:
            st.dataframe(
                resumen_prestamos[resumen_prestamos['por_cobrar'] > 0],
                column_config={"concepto": "Persona/Concepto", "por_cobrar": st.column_config.NumberColumn("Me debe", format="%.2f €")},
                use_container_width=True, hide_index=True
            )

# --- 5. FORMULARIO DE ENTRADA MEJORADO ---
st.divider()
with st.expander("Añadir Nuevo Movimiento"):
    with st.form("form_add", clear_on_submit=True):
        f1, f2, f3 = st.columns([1, 2, 1])
        
        tipo = f1.selectbox("Tipo de Operación", 
                           ["Ingreso", "Gasto", "Deuda", "Pago Deuda", "Prestado", "Cobro Préstamo"])
        
        # Lógica de autocompletado para facilitar la vida
        if tipo == "Pago Deuda" and not resumen_deudas.empty:
            concepto = f2.selectbox("¿Qué deuda pagas?", resumen_deudas['concepto'].tolist())
        elif tipo == "Cobro Préstamo" and not resumen_prestamos.empty:
            concepto = f2.selectbox("¿Quién te devuelve dinero?", resumen_prestamos['concepto'].tolist())
        else:
            concepto = f2.text_input("Concepto o Nombre de Persona")
            
        monto = f3.number_input("Cantidad (€)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Registrar Movimiento"):
            if concepto and monto > 0:
                nuevo_id = int(df['id'].max() + 1) if not df.empty else 1
                nueva_fila = pd.DataFrame([{
                    "id": nuevo_id,
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "tipo": tipo,
                    "concepto": concepto,
                    "monto": monto
                }])
                df_up = pd.concat([df, nueva_fila], ignore_index=True)
                conn.update(data=df_up)
                st.success("¡Movimiento registrado con éxito!")
                st.rerun()
            else:
                st.error("Revisa que el concepto no esté vacío y el monto sea mayor a 0.")

# --- 6. BORRADO DE REGISTROS ---
with st.expander("🗑️ Gestionar / Eliminar historial"):
    if not df.empty:
        opciones = df.apply(lambda x: f"{int(x['id'])} | {x['fecha']} | {x['tipo']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        seleccion = st.selectbox("Selecciona registro a eliminar:", opciones)
        
        if st.button("Confirmar Borrado", type="primary"):
            id_a_borrar = int(seleccion.split(" | ")[0])
            df_final = df[df['id'] != id_a_borrar]
            conn.update(data=df_final)
            st.warning(f"Registro {id_a_borrar} eliminado.")
            st.rerun()