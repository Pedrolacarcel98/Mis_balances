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

st.title("📊 Control de Gastos Persistente")

# --- FORMULARIO ---
with st.expander("Añadir Movimiento"):
    with st.form("form_add", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        tipo = col1.selectbox("Tipo", ["Ingreso", "Gasto"])
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

# --- TABLAS SEPARADAS ---
st.divider()
c_izq, c_der = st.columns(2)

with c_izq:
    st.subheader("📥 Ingresos")
    df_ing = df[df["tipo"] == "Ingreso"]
    st.table(df_ing[["id", "fecha", "concepto", "monto"]])

with c_der:
    st.subheader("📤 Gastos")
    df_gas = df[df["tipo"] == "Gasto"]
    st.table(df_gas[["id", "fecha", "concepto", "monto"]])

# --- BORRADO ---
st.divider()
if not df.empty:
    with st.expander("🗑️ Borrar Datos"):
        id_borrar = st.number_input("ID a eliminar", min_value=1, step=1)
        if st.button("Eliminar"):
            df = df[df['id'] != id_borrar]
            conn.update(data=df)
            st.warning(f"ID {id_borrar} borrado.")
            st.rerun()