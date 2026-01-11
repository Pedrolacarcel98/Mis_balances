import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Configuración de la Base de Datos
conn = sqlite3.connect('finanzas.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS registros (id INTEGER PRIMARY KEY, fecha TEXT, tipo TEXT, concepto TEXT, monto REAL)')
conn.commit()

# 2. Interfaz de Usuario
st.set_page_config(page_title="Mis Finanzas", page_icon="💰")
st.title("💰 Mi Gestor de Gastos")

# Formulario de entrada
with st.expander("➕ Añadir Nuevo Registro", expanded=True):
    tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
    concepto = st.text_input("Concepto")
    monto = st.number_input("Importe", min_value=0.0, step=0.01)
    
    if st.button("Guardar"):
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute('INSERT INTO registros (fecha, tipo, concepto, monto) VALUES (?,?,?,?)', 
                  (fecha_hoy, tipo, concepto, monto))
        conn.commit()
        st.success("¡Guardado correctamente!")

# 3. Visualización y Cálculos
df = pd.read_sql_query("SELECT * FROM registros", conn)

if not df.empty:
    ingresos = df[df['tipo'] == 'Ingreso']['monto'].sum()
    gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    balance = ingresos - gastos
    
    # Colores según el balance (Tu idea anterior)
    color = "green" if balance >= 0 else "red"
    st.markdown(f"### Balance Actual: <span style='color:{color}'>{balance:.2f}€</span>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("Últimos movimientos")
    st.dataframe(df.sort_values(by="id", ascending=False), use_container_width=True)