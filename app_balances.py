import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Finanzas Reales", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar datos (Sin caché para ver cambios al instante)
df = conn.read(ttl=0)

# Asegurar tipos de datos
if not df.empty:
    df['monto'] = pd.to_numeric(df['monto'], errors='coerce')
    df['id'] = pd.to_numeric(df['id'], errors='coerce')

st.title("Control de Gastos e Ingresos")
# --- CÁLCULOS DE BALANCE ---
if not df.empty:
    total_ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
    total_gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    total_deudas = df[df['tipo'] == 'Deuda']['monto'].sum()
    balance_neto = total_ingresos - total_gastos

    # --- SECCIÓN DE BALANCE (DISEÑO) ---
    st.subheader("Resumen: ")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    col_m1.metric("Total Ingresos", f"{total_ingresos:.2f} €")
    col_m2.metric("Total Gastos", f"{total_gastos:.2f} €", delta=f"-{total_gastos:.2f} €", delta_color="inverse")
    
    # El balance cambia de color automáticamente con st.metric
    # Opcional: Usamos Markdown para un control total del color del título
    color_balance = "green" if balance_neto >= 0 else "red"
    col_m3.metric("Balance Neto", f"{balance_neto:.2f} €", delta=f"{balance_neto:.2f} €")
    col_m4.metric("Total Deudas", f"{total_deudas:.2f} €")

    st.markdown(f"""
        <div style="background-color: rgba(200, 200, 200, 0.1); padding: 20px; border-radius: 10px; border-left: 10px solid {color_balance};">
            <h3 style="margin:0;">Estado Actual:</h3>
            <p style="font-size: 24px; color: {color_balance}; font-weight: bold; margin:0;">{balance_neto:.2f} €</p>
        </div>
    """, unsafe_allow_html=True)

# --- TABLAS SEPARADAS CON MEJOR ESTILO ---
st.divider()
c_izq, c_der = st.columns(2)

with c_izq:
    st.subheader("Ingresos")
    df_ing = df[df["tipo"] == "Ingreso"].sort_values("fecha", ascending=False)
    # Cambiamos st.table por st.dataframe para que se vea más moderno y tenga scroll si crece mucho
    st.dataframe(df_ing[["fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

with c_der:
    st.subheader("Gastos")
    df_gas = df[df["tipo"] == "Gasto"].sort_values("fecha", ascending=False)
    st.dataframe(df_gas[["fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

with st.expander("📄 Deudas"):
    df_deudas = df[df["tipo"] == "Deuda"].sort_values("fecha", ascending=False)
    st.dataframe(df_deudas[["fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

# --- FORMULARIO ---
with st.expander("Añadir Movimiento"):
    with st.form("form_add", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        tipo = col1.selectbox("Tipo", ["Ingreso", "Gasto","Deuda"])
        concepto = col2.text_input("Concepto")
        monto = col3.number_input("Euros", min_value=0.0)
        
        if st.form_submit_button("Guardar"):
            nuevo_id = int(df['id'].max() + 1) if not df.empty else 1
            nueva_fila = pd.DataFrame([{
                "id": nuevo_id,
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "tipo": tipo,
                "concepto": concepto,
                "monto": monto
            }])
            df = pd.concat([df, nueva_fila], ignore_index=True)
            conn.update(data=df)
            st.success("¡Guardado en Google Sheets!")
            st.rerun()

# --- BORRADO ---
st.divider()
if not df.empty:
    with st.expander("🗑️ Eliminar un registro"):
        # Creamos una lista de opciones que el humano sí entienda
        opciones = df.apply(lambda x: f"{x['id']} | {x['fecha']} - {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        
        seleccion = st.selectbox("Busca el movimiento que quieres quitar:", opciones)
        
        # Extraemos el ID de la cadena seleccionada
        id_a_borrar = int(seleccion.split(" | ")[0])
        
        if st.button("Confirmar Eliminación", type="primary", use_container_width=True):
            df_final = df[df['id'] != id_a_borrar]
            conn.update(data=df_final)
            st.success("Registro eliminado con éxito")
            st.rerun()
