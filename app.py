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
URL_ESCRITURA_API = "https://script.google.com/macros/s/AKfycbx-1Xirl-jO74d7EA6fwFavFQRXtZm994wN5yORJ0M_nktpghHb-ZaWdprbBLUg8mFzhQ/exec"

def obtener_bitacora():
    url_limpia = f"{URL_LEER_CSV}&nocache={int(datetime.now().timestamp())}"
    df = pd.read_csv(url_limpia)
    if not df.empty:
        df['id'] = df['id'].astype(str).str.strip()
        df['proyecto'] = df['proyecto'].fillna('').astype(str)
        df['categoria'] = df['categoria'].fillna('').astype(str)
        df['observacion'] = df['observacion'].fillna('').astype(str)
        df['semana'] = df['semana'].fillna('').astype(str)
        df['fecha_registro'] = df['fecha_registro'].fillna('').astype(str)
    return df

try:
    df_db = obtener_bitacora()
except Exception as e:
    st.error(f"Error al leer los datos de Google Sheets: {e}")
    st.stop()

# Lista de proyectos de ingeniería y control de documentos
lista_proyectos = ["HEXA015 - Campamento", "Portal de Documentos"]
opciones_cat = ["Progreso Técnico", "Administrativo", "Pendiente Crítico", "Reunión", "Otro"]

# --- FUNCIÓN PARA VENTANA EMERGENTE DE EDICIÓN ---
@st.dialog("✏️ Modificar Anotación")
def ventana_editar(nota):
    st.markdown(f"**ID Registro:** `{nota['id']}` | **Creado:** *{nota['fecha_registro']}*")
    
    with st.form("form_dialog_editar"):
        p_index = lista_proyectos.index(nota['proyecto']) if nota['proyecto'] in lista_proyectos else 0
        proyecto_edit = st.selectbox("Proyecto", lista_proyectos, index=p_index)
        
        c_index = opciones_cat.index(nota['categoria']) if nota['categoria'] in opciones_cat else 0
        cat_edit = st.selectbox("Categoría/Hito", opciones_cat, index=c_index)
        
        obs_edit = st.text_area("Contenido de la observación:", value=nota['observacion'], height=150)
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            guardar = st.form_submit_button("Guardar Cambios", type="primary")
        with col_btn2:
            cancelar = st.form_submit_button("Cancelar")
            
        if guardar:
            if obs_edit.strip() == "":
                st.error("La observación no puede quedar vacía.")
            else:
                payload_edit = {
                    "accion": "editar",
                    "id": str(nota['id']),
                    "proyecto": proyecto_edit,
                    "categoria": cat_edit,
                    "observacion": obs_edit
                }
                
                with st.spinner("Sincronizando con Google Sheets..."):
                    try:
                        response = requests.post(URL_ESCRITURA_API, data=json.dumps(payload_edit), headers={"Content-Type": "application/json"})
                        res_json = json.loads(response.text)
                        if response.status_code == 200 and res_json.get("status") == "success":
                            st.success("¡Registro actualizado!")
                            st.rerun()
                        else:
                            st.error(f"Error: {res_json.get('message')}")
                    except Exception as err:
                        st.error(f"Error de red: {err}")
        if cancelar:
            st.rerun()

# --- PESTAÑAS ---
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
                    
                    with st.spinner("Guardando en la nube..."):
                        try:
                            response = requests.post(URL_ESCRITURA_API, data=json.dumps(payload), headers={"Content-Type": "application/json"})
                            if response.status_code == 200 and json.loads(response.text).get("status") == "success":
                                st.success("¡Anotación guardada con éxito!")
                                st.rerun()
                            else:
                                st.error("Error al guardar en Google Sheets.")
                        except Exception as err:
                            st.error(f"Error: {err}")

    elif operacion == "Modificar Anotación Existente":
        if df_db.empty:
            st.warning("No hay anotaciones registradas para modificar.")
        else:
            st.markdown("### 📋 Últimas 20 anotaciones registradas")
            st.caption("Haz clic en el botón 📝 Editar de cualquier fila para abrir la ventana emergente de edición.")
            
            # Tomamos las últimas 20 anotaciones ordenadas por fecha reciente
            df_ultimos = df_db.sort_values(by="fecha_registro", ascending=False).head(20).copy()
            
            # Encabezados de la tabla
            header_cols = st.columns([1, 1.5, 2, 2, 4.5])
            header_cols[0].markdown("**Acción**")
            header_cols[1].markdown("**Semana**")
            header_cols[2].markdown("**Proyecto**")
            header_cols[3].markdown("**Categoría**")
            header_cols[4].markdown("**Observación**")
            st.markdown("---")
            
            # Filas de datos
            for idx, fila in df_ultimos.iterrows():
                row_cols = st.columns([1, 1.5, 2, 2, 4.5])
                
                if row_cols[0].button("📝 Editar", key=f"btn_{fila['id']}"):
                    ventana_editar(fila)
                
                row_cols[1].write(fila['semana'])
                row_cols[2].write(fila['proyecto'])
                row_cols[3].write(fila['categoria'])
                
                texto_obs = fila['observacion']
                obs_corta = (texto_obs[:70] + '...') if len(texto_obs) > 70 else texto_obs
                row_cols[4].write(obs_corta)

with tab_historial:
    st.subheader("📋 Historial Consultado desde Google Sheets")
    if df_db.empty:
        st.info("Aún no hay registros en la bitácora.")
    else:
        proyectos_filtro = st.multiselect("Filtrar por Proyecto:", lista_proyectos, default=lista_proyectos)
        df_filtrado = df_db[df_db['proyecto'].isin(proyectos_filtro)]
        
        if not df_filtrado.empty:
            columnas_vista = ['semana', 'proyecto', 'categoria', 'observacion', 'fecha_registro']
            st.dataframe(df_filtrado[columnas_vista].sort_values(by="semana", ascending=False), use_container_width=True)
        else:
            st.write("No hay registros que coincidan con los filtros.")
