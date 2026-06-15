import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Ayuda Memoria de Proyectos", layout="wide")

st.title("📝 Bitácora y Ayuda Memoria de Proyectos")
st.caption("Conectado en vivo con Google Sheets en la Nube")

# --- CONFIGURACIÓN DE CONEXIONES ---
SHEET_ID = "1sg1NjmlqFRmY_JoGNP_n26ZUkfgxCdeuGv666j0F0G0"
URL_LEER_CSV = f"https://script.google.com/macros/s/AKfycbx-1Xirl-jO74d7EA6fwFavFQRXtZm994wN5yORJ0M_nktpghHb-ZaWdprbBLUg8mFzhQ/exec"

# ⚠️ REEMPLAZA ESTA URL POR LA QUE COPIASTE EN EL PASO 1
URL_ESCRITURA_API = "AQUÍ_PEGA_TU_URL_DE_GOOGLE_APPS_SCRIPT"

def obtener_bitacora():
    url_limpia = f"{URL_LEER_CSV}&nocache={int(datetime.now().timestamp())}"
    df = pd.read_csv(url_limpia)
    if 'id' in df.columns:
        df['id'] = df['id'].astype(str)
    return df

try:
    df_db = obtener_bitacora()
except Exception as e:
    st.error(f"Error al leer los datos de Google Sheets: {e}")
    st.stop()

lista_proyectos = ["HEXA015 - Campamento", "Portal de Documentos", "Importación Aceite de Oliva", "Proyecto Alpacas"]

tab_registro, tab_historial = st.tabs(["🆕 Registrar / Editar Observación", "📊 Historial de Anotaciones"])

with tab_registro:
    st.subheader("Formulario de Anotaciones")
    operacion = st.radio("Selecciona una acción:", ["Nueva Anotación", "Modificar Anotación Existente"], horizontal=True)
    
    if operacion == "Nueva Anotación":
        with st.form("form_nuevo"):
            col1, col2 = st.columns(2)
            with col1:
                proyecto_sel = st.selectbox("Proyecto", lista_proyectos)
                semana = st.date_input("Fecha/Semana", datetime.now())
            with col2:
                categoria = st.selectbox("Categoría/Hito", ["Progreso Técnico", "Administrativo", "Pendiente Crítico", "Reunión", "Otro"])
            
            observacion = st.text_area("Escribe aquí la anotación o ayuda memoria:")
            enviar = st.form_submit_button("Guardar Anotación")
            
            if enviar:
                if observacion.strip() == "":
                    st.error("La observación no puede estar vacía.")
                else:
                    # Crear el payload estructurado
                    payload = {
                        "id": str(int(datetime.now().timestamp())),
                        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "semana": semana.strftime("%Y-%W"),
                        "proyecto": proyecto_sel,
                        "categoria": categoria,
                        "observacion": observacion
                    }
                    
                    # Enviar petición POST directamente al Google Apps Script
                    with st.spinner("Guardando en la nube de Google..."):
                        try:
                            response = requests.post(URL_ESCRITURA_API, data=json.dumps(payload), headers={"Content-Type": "application/json"})
                            if response.status_code == 200:
                                st.success(f"¡Anotación guardada con éxito en Google Sheets para {proyecto_sel}!")
                                # Forzar recarga limpia para ver reflejado el cambio
                                st.rerun()
                            else:
                                st.error(f"Error en respuesta del servidor: {response.status_code}")
                        except Exception as err:
                            st.error(f"Error de red al intentar guardar: {err}")

    elif operacion == "Modificar Anotación Existente":
        st.info("Módulo de edición en desarrollo para sincronización directa.")

with tab_historial:
    st.subheader("📋 Historial Consultado desde Google Sheets")
    if df_db.empty or len(df_db) == 0:
        st.info("Aún no hay registros en la bitácora.")
    else:
        proyectos_filtro = st.multiselect("Filtrar por Proyecto:", lista_proyectos, default=lista_proyectos)
        df_filtrado = df_db[df_db['proyecto'].isin(proyectos_filtro)]
        
        if not df_filtrado.empty:
            columnas_vista = ['semana', 'proyecto', 'categoria', 'observacion', 'fecha_registro']
            st.dataframe(df_filtrado[columnas_vista].sort_values(by="semana", ascending=False), use_container_width=True)
        else:
            st.write("No hay registros que coincidan con los filtros.")
