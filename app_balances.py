import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Finanzas Reales", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# 1. Carga y Limpieza Crítica de Datos
df = conn.read(ttl=0)

if not df.empty:
    # Aseguramos que el ID sea entero y sin valores nulos para evitar el error de borrado
    df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
    # Filtramos filas vacías que puedan venir de la hoja
    df = df.dropna(subset=['concepto']) 

st.title("Control de Gastos e Ingresos 💰")

# --- 2. SECCIÓN DE BALANCE ---
if not df.empty:
    total_ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
    total_gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    total_deudas = df[df['tipo'] == 'Deuda']['monto'].sum()
    balance_neto = total_ingresos - total_gastos

    st.subheader("Resumen:")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    col_m1.metric("Total Ingresos", f"{total_ingresos:,.2f} €")
    col_m2.metric("Total Gastos", f"{total_gastos:,.2f} €", delta=f"-{total_gastos:,.2f} €", delta_color="inverse")
    
    color_balance = "green" if balance_neto >= 0 else "red"
    col_m3.metric("Balance Neto", f"{balance_neto:,.2f} €", delta=f"{balance_neto:,.2f} €")
    col_m4.metric("Total Deudas", f"{total_deudas:,.2f} €")

    st.markdown(f"""
        <div style="background-color: rgba(200, 200, 200, 0.1); padding: 20px; border-radius: 10px; border-left: 10px solid {color_balance};">
            <h3 style="margin:0;">Estado Actual:</h3>
            <p style="font-size: 24px; color: {color_balance}; font-weight: bold; margin:0;">{balance_neto:,.2f} €</p>
        </div>
    """, unsafe_allow_html=True)

# --- 3. VISUALIZACIÓN DE TABLAS ---
st.divider()
c_izq, c_der = st.columns(2)

with c_izq:
    st.subheader("Ingresos")
    df_ing = df[df["tipo"] == "Ingreso"].sort_values("fecha", ascending=False)
    st.dataframe(df_ing[["fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

with c_der:
    st.subheader("Gastos")
    df_gas = df[df["tipo"] == "Gasto"].sort_values("fecha", ascending=False)
    st.dataframe(df_gas[["fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

with st.expander("📄 Ver Deudas Detalladas"):
    df_deudas = df[df["tipo"] == "Deuda"].sort_values("fecha", ascending=False)
    st.dataframe(df_deudas[["fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

# --- 4. FORMULARIO DE ENTRADA ---
st.divider()
with st.expander("➕ Añadir Movimiento"):
    with st.form("form_add", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        tipo = col1.selectbox("Tipo", ["Ingreso", "Gasto", "Deuda"])
        concepto = col2.text_input("Concepto")
        monto = col3.number_input("Euros", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Guardar"):
            if concepto:
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
                st.success("¡Guardado correctamente!")
                st.rerun()
            else:
                st.error("Por favor, introduce un concepto.")

# --- 5. BORRADO SEGURO ---
if not df.empty:
    with st.expander("🗑️ Eliminar un registro"):
        # Creamos las opciones solo con filas válidas
        opciones = df.apply(lambda x: f"{int(x['id'])} | {x['fecha']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        seleccion = st.selectbox("Busca el movimiento que quieres quitar:", opciones)
        
        if st.button("Confirmar Eliminación", type="primary", use_container_width=True):
            try:
                # Extraemos el ID solo cuando se pulsa el botón
                id_a_borrar = int(seleccion.split(" | ")[0])
                df_final = df[df['id'] != id_a_borrar]
                conn.update(data=df_final)
                st.success(f"Registro {id_a_borrar} eliminado.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo eliminar: {e}")