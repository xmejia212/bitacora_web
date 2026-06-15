import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Ayuda Memoria de Proyectos", layout="wide")

st.title("📝 Bitácora y Ayuda Memoria de Proyectos")
st.caption("Conectado en vivo con Google Sheets en la Nube")

# 1. Establecer conexión con Google Sheets
# Streamlit leerá las credenciales automáticamente desde los "Secrets" de la plataforma
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer los datos actuales del Google Sheet
def obtener_bitacora():
    # Deshabilitamos la caché (ttl=0) para ver los cambios reflejados de inmediato al registrar/editar
    return conn.read(worksheet="Sheet1", ttl=0)

# Cargar datos iniciales
try:
    df_db = obtener_bitacora()
except Exception as e:
    st.error("Error al conectar con Google Sheets. Verifica las credenciales en Secrets.")
    st.stop()

# Lista de proyectos (Puedes cambiar o ampliar esta lista según requieras)
lista_proyectos = ["HEXA015 - Campamento", "Portal de Documentos", "Importación Aceite de Oliva", "Proyecto Alpacas"]

# Creamos las pestañas de navegación
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
            enviar = st.form_submit_button("Guardar en Google Sheets")
            
            if enviar:
                if observacion.strip() == "":
                    st.error("La observación no puede estar vacía.")
                else:
                    # Generar una nueva fila como DataFrame de Pandas
                    nuevo_registro = pd.DataFrame([{
                        "id": str(int(datetime.now().timestamp())),
                        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "semana": semana.strftime("%Y-%W"),
                        "proyecto": proyecto_sel,
                        "categoria": categoria,
                        "observacion": observacion
                    }])
                    
                    # Combinar los datos existentes con la nueva fila
                    df_actualizado = pd.concat([df_db, nuevo_registro], ignore_index=True)
                    
                    # Subir y sobreescribir la hoja de cálculo en la nube
                    conn.update(worksheet="Sheet1", data=df_actualizado)
                    st.success(f"¡Anotación guardada en la nube para {proyecto_sel}!")
                    st.rerun()

    elif operacion == "Modificar Anotación Existente":
        if df_db.empty or len(df_db) == 0:
            st.warning("No hay anotaciones registradas en el Google Sheet para modificar.")
        else:
            # Crear opciones legibles para el selectbox a partir del DataFrame
            opciones_editar = {}
            for index, fila in df_db.iterrows():
                # Evitar errores si la celda de observación viene vacía
                obs_corta = str(fila['observacion'])[:50] if pd.notna(fila['observacion']) else ""
                label = f"[{fila['semana']}] {fila['proyecto']} - {obs_corta}..."
                opciones_editar[label] = fila
            
            nota_seleccionada_texto = st.selectbox("Selecciona la nota que deseas corregir o cambiar:", list(opciones_editar.keys()))
            nota_a_editar = opciones_editar[nota_seleccionada_texto]
            
            with st.form("form_editar"):
                st.info(f"Modificando registro original con ID: {nota_a_editar['id']}")
                col1, col2 = st.columns(2)
                with col1:
                    proyecto_edit = st.selectbox("Proyecto", lista_proyectos, index=lista_proyectos.index(nota_a_editar['proyecto']) if nota_a_editar['proyecto'] in lista_proyectos else 0)
                with col2:
                    opciones_cat = ["Progreso Técnico", "Administrativo", "Pendiente Crítico", "Reunión", "Otro"]
                    cat_edit = st.selectbox("Categoría", opciones_cat, index=opciones_cat.index(nota_a_editar['categoria']) if nota_a_editar['categoria'] in opciones_cat else 0)
                
                obs_edit = st.text_area("Modificar observación:", value=nota_a_editar['observacion'])
                guardar_cambios = st.form_submit_button("Actualizar Registro en la Nube")
                
                if guardar_cambios:
                    # Modificar la fila correspondiente en el DataFrame original usando el ID único
                    # Aseguramos la comparación transformando ambos a string
                    df_db['id'] = df_db['id'].astype(str)
                    target_id = str(nota_a_editar['id'])
                    
                    if target_id in df_db['id'].values:
                        df_db.loc[df_db['id'] == target_id, 'proyecto'] = proyecto_edit
                        df_db.loc[df_db['id'] == target_id, 'categoria'] = cat_edit
                        df_db.loc[df_db['id'] == target_id, 'observacion'] = obs_edit
                        df_db.loc[df_db['id'] == target_id, 'fecha_registro'] = f"{nota_a_editar['fecha_registro']} (Modificado: {datetime.now().strftime('%m-%d %H:%M')})"
                        
                        # Guardar cambios en Google Sheets
                        conn.update(worksheet="Sheet1", data=df_db)
                        st.success("¡Registro actualizado en Google Sheets!")
                        st.rerun()
                    else:
                        st.error("No se pudo localizar el ID del registro para actualizar.")

with tab_historial:
    st.subheader("📋 Historial Completo guardado en Google Sheets")
    
    if df_db.empty or len(df_db) == 0:
        st.info("Aún no hay registros en la bitácora de Google Sheets.")
    else:
        # Filtro rápido multi-selección por proyecto
        proyectos_filtro = st.multiselect("Filtrar por Proyecto:", lista_proyectos, default=lista_proyectos)
        df_filtrado = df_db[df_db['proyecto'].isin(proyectos_filtro)]
        
        if not df_filtrado.empty:
            # Columnas visibles ordenadas
            columnas_vista = ['semana', 'proyecto', 'categoria', 'observacion', 'fecha_registro']
            # Mostrar tabla interactiva, ordenando de forma descendente por semana
            st.dataframe(df_filtrado[columnas_vista].sort_values(by="semana", ascending=False), use_container_width=True)
        else:
            st.write("No hay registros que coincidan con los filtros seleccionados.")