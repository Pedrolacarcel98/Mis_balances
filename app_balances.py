import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuración de conexión con caché para evitar errores de hilos
@st.cache_resource
def get_connection():
    return sqlite3.connect('finanzas.db', check_same_thread=False)

conn = get_connection()
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS registros (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, tipo TEXT, concepto TEXT, monto REAL)')
conn.commit()

st.set_page_config(page_title="Mis Finanzas", page_icon="💰", layout="wide")
st.title("Mi Gestor de Gastos Pro")

# --- SECCIÓN: ENTRADA DE DATOS ---
with st.expander("➕ Añadir Nuevo Registro"):
    with st.form("formulario_registro", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        tipo = col1.selectbox("Tipo", ["Ingreso", "Gasto"])
        concepto = col2.text_input("Concepto")
        monto = col3.number_input("Importe (€)", min_value=0.0, step=0.01)
        
        if st.form_submit_button("Guardar"):
            if concepto:
                fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute('INSERT INTO registros (fecha, tipo, concepto, monto) VALUES (?,?,?,?)', 
                          (fecha_hoy, tipo, concepto, monto))
                conn.commit()
                st.success("¡Registro guardado!")
                st.rerun()
            else:
                st.warning("Escribe un concepto.")

# --- SECCIÓN: VISUALIZACIÓN ---
df = pd.read_sql_query("SELECT * FROM registros", conn)

if not df.empty:
    # Cálculo de métricas
    ingresos_totales = df[df['tipo'] == 'Ingreso']['monto'].sum()
    gastos_totales = df[df['tipo'] == 'Gasto']['monto'].sum()
    balance = ingresos_totales - gastos_totales
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Ingresos", f"{ingresos_totales:.2f}€")
    m2.metric("Total Gastos", f"{gastos_totales:.2f}€", delta_color="inverse")
    m3.metric("Balance Neto", f"{balance:.2f}€")

    st.divider()

    # --- TABLAS SEPARADAS ---
    col_ing, col_gas = st.columns(2)

    with col_ing:
        st.subheader("📥 Ingresos")
        df_ing = df[df['tipo'] == 'Ingreso'].sort_values(by="id", ascending=False)
        st.dataframe(df_ing[["fecha", "concepto", "monto"]], use_container_width=True)

    with col_gas:
        st.subheader("📤 Gastos")
        df_gas = df[df['tipo'] == 'Gasto'].sort_values(by="id", ascending=False)
        st.dataframe(df_gas[["fecha", "concepto", "monto"]], use_container_width=True)

    # --- SECCIÓN: BORRADO ---
    st.divider()
    with st.expander("🗑️ Gestionar / Borrar Entradas"):
        registro_a_borrar = st.selectbox("Selecciona registro para eliminar", 
                                         df['id'].astype(str) + " - " + df['concepto'])
        id_borrar = registro_a_borrar.split(" - ")[0]
        
        if st.button("Eliminar permanentemente", type="primary"):
            c.execute('DELETE FROM registros WHERE id = ?', (id_borrar,))
            conn.commit()
            st.warning(f"Registro {id_borrar} eliminado.")
            st.rerun()
else:
    st.info("Aún no hay movimientos registrados.")