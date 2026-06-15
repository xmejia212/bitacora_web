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
URL_LEER_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# ⚠️ REEMPLAZA ESTA URL POR TU URL REAL DE GOOGLE APPS SCRIPT
URL_ESCRITURA_API = "https://script.google.com/macros/s/AKfycbx-1Xirl-jO74d7EA6fwFavFQRXtZm994wN5yORJ0M_nktpghHb-ZaWdprbBLUg8mFzhQ/exec"

def obtener_bitacora():
    url_limpia = f"{URL_LEER_CSV}&nocache={int(datetime.now().timestamp())}"
    df = pd.read_csv(url_limpia)
    # Limpieza básica para asegurar consistencia de tipos
    if not df.empty:
        df['id'] = df['id'].astype(str).str.strip()
        df['proyecto'] = df['proyecto'].fillna('').astype(str)
        df['categoria'] = df['categoria'].fillna('').astype(str)
        df['observacion'] = df['observacion'].fillna('').astype(str)
    return df

try:
    df_db = obtener_bitacora()
except Exception as e:
    st.error(f"Error al leer los datos de Google Sheets: {e}")
    st.stop()

lista_proyectos = ["HEXA015 - Campamento", "Portal de Documentos", "Importación Aceite de Oliva", "Proyecto Alpacas"]
opciones_cat = ["Progreso Técnico", "Administrativo", "Pendiente Crítico", "Reunión", "Otro"]

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
                categoria = st.selectbox("Categoría/Hito", opciones_cat)
            
            observacion = st.text_area("Escribe aquí la anotación o ayuda memoria:")
            enviar = st.form_submit_button("Guardar Anotación")
            
            if enviar:
                if observacion.strip() == "":
                    st.error("La observación no puede estar vacía.")
                else:
                    payload = {
                        "accion": "crear",
                        "id": str(int(datetime.now().timestamp())),
                        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "semana": semana.strftime("%Y-%W"),
                        "proyecto": proyecto_sel,
                        "categoria": categoria,
                        "observacion": observacion
                    }
                    
                    with st.spinner("Guardando nueva anotación en la nube..."):
                        try:
                            response = requests.post(URL_ESCRITURA_API, data=json.dumps(payload), headers={"Content-Type": "application/json"})
                            if response.status_code == 200 and json.loads(response.text).get("status") == "success":
                                st.success(f"¡Anotación guardada con éxito en Google Sheets!")
                                st.rerun()
                            else:
                                st.error("Error al guardar en el archivo de Google.")
                        except Exception as err:
                            st.error(f"Error de conexión: {err}")

    elif operacion == "Modificar Anotación Existente":
        if df_db.empty or len(df_db) == 0:
            st.warning("No hay anotaciones registradas en el Google Sheet para modificar.")
        else:
            # Crear un diccionario amigable mapeando un texto descriptivo a la fila real
            opciones_editar = {}
            for index, fila in df_db.iterrows():
                obs_corta = fila['observacion'][:45] if len(fila['observacion']) > 45 else fila['observacion']
                label = f"[{fila['semana']}] {fila['proyecto']} | {fila['categoria']} -> ({obs_corta}...)"
                opciones_editar[label] = fila
            
            seleccion = st.selectbox("Selecciona la nota que deseas corregir o cambiar:", list(opciones_editar.keys()))
            nota_a_editar = opciones_editar[seleccion]
            
            # Formulario de edición con los datos cargados de la nota seleccionada
            with st.form("form_editar"):
                st.markdown(f"**Editando Registro ID:** `{nota_a_editar['id']}` | **Fecha original:** *{nota_a_editar['fecha_registro']}*")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Pre-seleccionar el proyecto original
                    p_index = lista_proyectos.index(nota_a_editar['proyecto']) if nota_a_editar['proyecto'] in lista_proyectos else 0
                    proyecto_edit = st.selectbox("Proyecto", lista_proyectos, index=p_index)
                with col2:
                    # Pre-seleccionar la categoría original
                    c_index = opciones_cat.index(nota_a_editar['categoria']) if nota_a_editar['categoria'] in opciones_cat else 0
                    cat_edit = st.selectbox("Categoría/Hito", opciones_cat, index=c_index)
                
                obs_edit = st.text_area("Modificar el contenido de la observación:", value=nota_a_editar['observacion'])
                guardar_cambios = st.form_submit_button("Actualizar Anotación")
                
                if guardar_cambios:
                    if obs_edit.strip() == "":
                        st.error("La observación no puede quedar vacía.")
                    else:
                        payload_edit = {
                            "accion": "editar",
                            "id": str(nota_a_editar['id']),
                            "proyecto": proyecto_edit,
                            "categoria": cat_edit,
                            "observacion": obs_edit
                        }
                        
                        with st.spinner("Sincronizando corrección en Google Sheets..."):
                            try:
                                response = requests.post(URL_ESCRITURA_API, data=json.dumps(payload_edit), headers={"Content-Type": "application/json"})
                                res_json = json.loads(response.text)
                                if response.status_code == 200 and res_json.get("status") == "success":
                                    st.success("¡Anotación actualizada correctamente en la base de datos!")
                                    st.rerun()
                                else:
                                    st.error(f"Error devuelto por el servidor: {res_json.get('message')}")
                            except Exception as err:
                                st.error(f"Error de red: {err}")

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
