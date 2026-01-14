import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Gestor Finanzas Pro", layout="wide")

# 1. Conexión con Google Sheets (Usa los Secrets configurados en la nube)
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar datos frescos
def load_data():
    return conn.read(ttl=0) # ttl=0 asegura que no use caché antigua

df = load_data()

st.title("💰 Mis Cuentas Mensuales")

# 2. Formulario para añadir registros
with st.expander("➕ Añadir Movimiento", expanded=False):
    with st.form("nuevo_registro", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        tipo = col1.selectbox("Categoría", ["Ingreso", "Gasto"])
        concepto = col2.text_input("Concepto", placeholder="Ej: Supermercado, Nómina...")
        monto = col3.number_input("Cantidad (€)", min_value=0.0, step=0.1)
        
        if st.form_submit_button("Guardar Registro"):
            if concepto and monto > 0:
                # Crear el nuevo registro
                nuevo = pd.DataFrame([{
                    "id": int(df['id'].max() + 1) if not df.empty else 1,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "tipo": tipo,
                    "concepto": concepto,
                    "monto": monto
                }])
                # Actualizar Google Sheets
                df_actualizado = pd.concat([df, nuevo], ignore_index=True)
                conn.update(data=df_actualizado)
                st.success("¡Guardado en la nube!")
                st.rerun()
            else:
                st.error("Rellena todos los campos.")

# 3. Visualización en Tablas Separadas
if not df.empty:
    # Resumen visual
    ing = df[df['tipo'] == 'Ingreso']['monto'].sum()
    gas = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos Totales", f"{ing:.2f}€")
    c2.metric("Gastos Totales", f"{gas:.2f}€", delta=f"-{gas:.2f}€", delta_color="inverse")
    c3.metric("Balance Neto", f"{ing - gas:.2f}€")

    st.divider()

    # Tablas separadas por columnas
    col_ing, col_gas = st.columns(2)
    
    with col_ing:
        st.subheader("📥 Ingresos")
        df_ing = df[df['tipo'] == 'Ingreso'].sort_values("fecha", ascending=False)
        st.dataframe(df_ing[["id", "fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

    with col_gas:
        st.subheader("📤 Gastos")
        df_gas = df[df['tipo'] == 'Gasto'].sort_values("fecha", ascending=False)
        st.dataframe(df_gas[["id", "fecha", "concepto", "monto"]], use_container_width=True, hide_index=True)

    # 4. Función de Borrado
    st.divider()
    with st.expander("🗑️ Zona de Borrado"):
        # Creamos una lista de opciones descriptivas para el selectbox
        opciones = df.apply(lambda x: f"ID {x['id']}: {x['concepto']} ({x['monto']}€)", axis=1).tolist()
        seleccion = st.selectbox("Elige el registro a eliminar:", opciones)
        
        if st.button("Eliminar permanentemente", type="primary"):
            id_borrar = int(seleccion.split(":")[0].replace("ID ", ""))
            df_final = df[df['id'] != id_borrar]
            conn.update(data=df_final)
            st.warning("Registro eliminado.")
            st.rerun()
else:
    st.info("Aún no hay datos. Añade tu primer movimiento arriba.")