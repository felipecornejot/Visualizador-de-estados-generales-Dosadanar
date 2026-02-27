import streamlit as st

# Configuración de la página - PRIMERO SIEMPRE
st.set_page_config(
    page_title="Analizador de Compras Ágiles - Residuos",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verificar imports
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError as e:
    st.error(f"""
    ❌ **Error de importación: {e}**
    
    Por favor, verifica que todas las dependencias estén instaladas.
    """)
    st.stop()

import pandas as pd
import numpy as np
import re
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

# Título y descripción principal
st.title("♻️ Analizador de Compras Ágiles - Gestión de Residuos")
st.markdown("""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    <h4>📊 Dashboard interactivo para el análisis de licitaciones públicas de gestión de residuos (peligrosos, no peligrosos y mixtas)</h4>
    <p>Esta aplicación permite explorar en detalle las licitaciones adjudicadas con clasificación automática por tipo de residuo.</p>
    </div>
""", unsafe_allow_html=True)

# --- FUNCIONES DE PROCESAMIENTO ---

@st.cache_data
def cargar_y_procesar_datos(uploaded_file=None):
    """
    Carga y procesa los datos del archivo CSV
    """
    # Nombre del archivo por defecto
    archivo_por_defecto = 'ComprasAgiles_filtrado_residuos_clasificado_peligrosos_no_peligrosos_mixtas.csv'
    
    if uploaded_file is not None:
        # Caso 1: Usuario subió un archivo
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
        st.sidebar.success("✅ Archivo cargado manualmente")
        
    else:
        # Caso 2: Intentar cargar archivo por defecto del repositorio
        if os.path.exists(archivo_por_defecto):
            try:
                df = pd.read_csv(archivo_por_defecto, sep=';', encoding='utf-8')
                st.sidebar.success(f"✅ Archivo base cargado: {len(df)} licitaciones")
            except Exception as e:
                st.sidebar.error(f"❌ Error al cargar archivo por defecto: {e}")
                df = pd.DataFrame()
        else:
            st.sidebar.error(f"""
            ❌ No se encontró el archivo '{archivo_por_defecto}'
            
            Por favor, asegúrate de que el archivo existe en el repositorio.
            """)
            df = pd.DataFrame()
    
    # Si no hay datos, mostrar advertencia
    if df.empty:
        st.warning("⚠️ No hay datos para procesar. Por favor, sube un archivo CSV válido.")
        return df
    
    # Limpieza y procesamiento
    df['FechaPublicacion'] = pd.to_datetime(df['FechaPublicacion'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df['Año'] = df['FechaPublicacion'].dt.year
    df['Mes'] = df['FechaPublicacion'].dt.month
    df['MesNombre'] = df['FechaPublicacion'].dt.month_name().str[:3]
    df['Trimestre'] = df['FechaPublicacion'].dt.quarter
    df['Año-Mes'] = df['FechaPublicacion'].dt.to_period('M').astype(str)
    
    # Extraer región
    df['Region'] = df['Organismo'].apply(extraer_region)
    
    # Procesar montos
    df['Monto_Numérico_CLP'] = df['MontoLicitacion'].apply(extraer_monto_numerico)
    df['Monto_CLP_Millones'] = df['Monto_Numérico_CLP'] / 1_000_000
    df['Monto_UTM_Estimado'] = df['MontoLicitacion'].apply(extraer_utm)
    
    # Clasificar tamaño de licitación
    df['Tamaño_Licitacion'] = pd.cut(
        df['Monto_CLP_Millones'],
        bins=[0, 10, 50, 200, float('inf')],
        labels=['Pequeña (< 10M)', 'Mediana (10-50M)', 'Grande (50-200M)', 'Megaproyecto (> 200M)']
    )
    
    return df

def extraer_region(organismo):
    """Extrae la región del nombre del organismo"""
    organismo_str = str(organismo).upper()
    
    regiones = {
        'Metropolitana': ['METROPOLITANA', 'SANTIAGO', 'MAIPU', 'SAN RAMON', 'RENCA', 'PROVIDENCIA', 
                         'LAS CONDES', 'NUNOA', 'LA CISTERNA', 'VITACURA', 'LO ESPEJO', 'CERRO NAVIA',
                         'CONCHALI', 'MACUL', 'LA REINA', 'PEÑAFLOR', 'EL MONTE', 'PAINE', 'PEDRO AGUIRRE CERDA',
                         'SAN BERNARDO', 'EL BOSQUE'],
        'Valparaíso': ['VALPARAISO', 'SAN FELIPE', 'VIÑA DEL MAR', 'QUILPUE', 'CARTAGENA', 'SAN ANTONIO',
                      'LOS ANDES', 'QUILLOTA', 'ZAPALLAR', 'NOGALES', 'LA LIGUA', 'PUCHUNCAVI', 'QUINTERO',
                      'SAN ESTEBAN', 'CALLE LARGA', 'QUINTA DE TILCOCO', 'LIMACHE', 'SANTA MARIA', 'CONCON',
                      'OLMUE', 'EL QUISCO', 'EL TABO'],
        'Biobío': ['BIO BIO', 'CONCEPCIÓN', 'TALCAHUANO', 'LOS ANGELES', 'CHIGUAYANTE', 'SAN PEDRO DE LA PAZ',
                  'CORONEL', 'LOTA', 'CURANILAHUE', 'MULCHEN', 'NACIMIENTO', 'YUNGAY', 'CABRERO', 'PENCO'],
        'La Araucanía': ['ARAUCANIA', 'TEMUCO', 'ANGOL', 'VICTORIA', 'LAUTARO', 'NUEVA IMPERIAL', 'VILCUN',
                        'CUNCO', 'GORBEA', 'CURACAUTIN', 'LUMACO', 'CHOLCHOL', 'TEODORO SCHMIDT', 'MELIPEUCO'],
        'Los Lagos': ['LOS LAGOS', 'PUERTO MONTT', 'OSORNO', 'CASTRO', 'ANCUD', 'PUERTO VARAS', 'LLANQUIHUE',
                      'PALENA', 'CHILOE', 'CALBUCO', 'MAULLIN', 'QUEMCHI'],
        'Magallanes': ['MAGALLANES', 'PUNTA ARENAS', 'PORVENIR', 'PUERTO NATALES', 'PORVENIR', 'RIO VERDE'],
        'Coquimbo': ['COQUIMBO', 'LA SERENA', 'OVALLE', 'ILLAPEL', 'COMBARBALA', 'ANDACOLLO'],
        'Aysén': ['AYSEN', 'COYHAIQUE', 'PUERTO AYSEN', 'COCHRANE', 'CISNES'],
        "O'Higgins": ['OHIGGINS', 'RANCAGUA', 'SAN FERNANDO', 'SAN VICENTE', 'PICHIDEGUA', 'LAS CABRAS',
                      'PEUMO', 'COLTAUCO', 'DOÑIHUE', 'CODEGUA', 'MOSTAZAL', 'OLIVAR'],
        'Maule': ['MAULE', 'CURICO', 'TALCA', 'LINARES', 'CAUQUENES', 'CONSTITUCION', 'PARRAL', 'SAN JAVIER',
                  'MOLINA', 'SAGRADA FAMILIA', 'PELARCO', 'TENO', 'CAUQUENES'],
        'Ñuble': ['ÑUBLE', 'CHILLAN', 'SAN CARLOS', 'BULNES', 'COBQUECURA', 'QUIRIHUE', 'COIHUECO'],
        'Arica y Parinacota': ['ARICA', 'PARINACOTA'],
        'Tarapacá': ['TARAPACA', 'IQUIQUE', 'ALTO HOSPICIO', 'POZO ALMONTE'],
        'Los Ríos': ['LOS RIOS', 'VALDIVIA', 'LA UNION', 'RIO BUENO', 'PANGUIPULLI'],
        'Atacama': ['ATACAMA', 'COPIAPO', 'VALLENAR', 'HUASCO', 'ALTO DEL CARMEN'],
        'Antofagasta': ['ANTOFAGASTA', 'CALAMA', 'TOCOPILLA', 'MARIA ELENA', 'OLLAGUE', 'SIERRA GORDA', 'TALTAL']
    }
    
    for region, keywords in regiones.items():
        if any(keyword in organismo_str for keyword in keywords):
            return region
    
    return 'Otra / Nacional'

def extraer_monto_numerico(monto_str):
    """Extrae un valor numérico del campo MontoLicitacion"""
    if pd.isna(monto_str) or monto_str in ['', 'nan']:
        return np.nan
    
    monto_str = str(monto_str).replace('.', '').replace(',', '').strip()
    
    # Si es un número puro
    if monto_str.isdigit():
        try:
            return float(monto_str)
        except:
            return np.nan
    
    # Si tiene UTM
    if 'UTM' in monto_str.upper():
        numeros = re.findall(r'[\d.]+', monto_str)
        if numeros:
            try:
                valor_utm = float(numeros[0].replace('.', ''))
                if len(numeros) > 1:
                    valor_utm2 = float(numeros[1].replace('.', ''))
                    valor_utm = (valor_utm + valor_utm2) / 2
                return valor_utm * 60000
            except:
                return np.nan
    
    # Si tiene UF
    if 'UF' in monto_str.upper():
        numeros = re.findall(r'[\d.]+', monto_str)
        if numeros:
            try:
                valor_uf = float(numeros[0].replace('.', ''))
                return valor_uf * 38000  # Valor UF aproximado
            except:
                return np.nan
    
    return np.nan

def extraer_utm(monto_str):
    """Extrae el valor en UTM si está presente"""
    monto_str = str(monto_str)
    if 'UTM' in monto_str.upper():
        numeros = re.findall(r'[\d.]+', monto_str)
        if numeros:
            try:
                if len(numeros) > 1:
                    return f"{numeros[0]}-{numeros[1]} UTM"
                return f"{numeros[0]} UTM"
            except:
                return np.nan
    return np.nan

# --- CARGA DE DATOS ---

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/recycle-sign.png", width=100)
    st.header("⚙️ Configuración")
    
    uploaded_file = st.file_uploader(
        "Cargar archivo CSV de licitaciones",
        type=['csv'],
        help="Sube el archivo CSV con los datos de licitaciones. Si no subes ninguno, se usará el archivo base del repositorio.",
        key="file_uploader"
    )
    
    # Cargar datos
    with st.spinner('Cargando y procesando datos...'):
        df = cargar_y_procesar_datos(uploaded_file)
    
    if not df.empty:
        st.success(f"✅ Datos cargados: {len(df)} licitaciones")
        
        # Mostrar info del dataset
        st.markdown("---")
        st.markdown("### 📊 Resumen del Dataset")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Años", f"{df['Año'].min()} - {df['Año'].max()}")
        with col2:
            st.metric("Regiones", df['Region'].nunique())
        
        st.markdown("---")
        st.header("🔍 Filtros")
        
        # Filtros interactivos
        años_disponibles = sorted(df['Año'].dropna().unique())
        años_seleccionados = st.multiselect(
            "Años",
            options=años_disponibles,
            default=años_disponibles if años_disponibles else [],
            key="filtro_anos"
        )
        
        regiones_disponibles = sorted(df['Region'].dropna().unique())
        regiones_seleccionadas = st.multiselect(
            "Regiones",
            options=regiones_disponibles,
            default=regiones_disponibles if regiones_disponibles else [],
            key="filtro_regiones"
        )
        
        # Filtro por categoría de residuo
        categorias_residuo = sorted(df['CategoriaResiduo'].dropna().unique())
        categorias_seleccionadas = st.multiselect(
            "🗑️ Tipo de Residuo",
            options=categorias_residuo,
            default=categorias_residuo if categorias_residuo else [],
            key="filtro_categoria"
        )
        
        # Filtro por nivel de confianza
        confianza_disponible = sorted(df['ConfianzaClasificacion'].dropna().unique())
        confianza_seleccionada = st.multiselect(
            "🎯 Nivel de Confianza",
            options=confianza_disponible,
            default=confianza_disponible if confianza_disponible else [],
            key="filtro_confianza"
        )
        
        # Filtro de búsqueda por texto
        busqueda = st.text_input("🔎 Buscar en nombre u organismo", "", key="busqueda_texto")
        
        # Botón para aplicar filtros
        aplicar_filtros = st.button("🔄 Aplicar Filtros", type="primary", key="boton_filtros")
    else:
        st.error("❌ No se pudieron cargar los datos")

# --- APLICAR FILTROS ---

if not df.empty:
    df_filtrado = df.copy()

    if años_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Año'].isin(años_seleccionados)]
    if regiones_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado['Region'].isin(regiones_seleccionadas)]
    if categorias_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado['CategoriaResiduo'].isin(categorias_seleccionadas)]
    if confianza_seleccionada:
        df_filtrado = df_filtrado[df_filtrado['ConfianzaClasificacion'].isin(confianza_seleccionada)]
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado['NombreLicitacion'].str.contains(busqueda, case=False, na=False) |
            df_filtrado['Organismo'].str.contains(busqueda, case=False, na=False)
        ]

    # --- MÉTRICAS PRINCIPALES ---

    st.markdown("## 📈 Panel de Control")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_licitaciones = len(df_filtrado)
        st.metric(
            label="📋 Total Licitaciones",
            value=f"{total_licitaciones:,}",
            delta=f"{len(df_filtrado)/len(df)*100:.1f}% del total"
        )

    with col2:
        monto_total = df_filtrado['Monto_CLP_Millones'].sum()
        st.metric(
            label="💰 Monto Total (MM CLP)",
            value=f"${monto_total:,.0f}M" if not pd.isna(monto_total) else "N/A",
            delta="Suma de montos disponibles"
        )

    with col3:
        monto_promedio = df_filtrado['Monto_CLP_Millones'].mean()
        st.metric(
            label="📊 Monto Promedio (MM CLP)",
            value=f"${monto_promedio:,.1f}M" if not pd.isna(monto_promedio) else "N/A",
            delta="Por licitación"
        )

    with col4:
        organizaciones_unicas = df_filtrado['Organismo'].nunique()
        st.metric(
            label="🏢 Organizaciones",
            value=f"{organizaciones_unicas:,}",
            delta="Organismos distintos"
        )

    st.markdown("---")

    # --- VISUALIZACIONES PRINCIPALES ---

    # Crear pestañas para organizar el contenido
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Visión General",
        "🗑️ Análisis por Tipo Residuo",
        "🗺️ Análisis Regional",
        "🏛️ Análisis por Organismo",
        "📅 Tendencia Temporal",
        "📋 Datos Detallados"
    ])

    with tab1:
        st.header("Visión General del Mercado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución por tipo de residuo
            if not df_filtrado.empty and 'CategoriaResiduo' in df_filtrado.columns:
                residuo_counts = df_filtrado['CategoriaResiduo'].value_counts().reset_index()
                residuo_counts.columns = ['CategoriaResiduo', 'count']
                
                # Colores personalizados
                color_map = {
                    'peligrosos': '#e74c3c',
                    'no peligrosos': '#2ecc71',
                    'mixtas': '#f39c12'
                }
                
                fig_residuos = px.pie(
                    residuo_counts,
                    values='count',
                    names='CategoriaResiduo',
                    title='Distribución por Tipo de Residuo',
                    hole=0.4,
                    color='CategoriaResiduo',
                    color_discrete_map=color_map
                )
                fig_residuos.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_residuos, use_container_width=True, key="pie_residuos")
            else:
                st.info("No hay datos suficientes para mostrar el gráfico")
        
        with col2:
            # Nivel de confianza de la clasificación
            if not df_filtrado.empty and 'ConfianzaClasificacion' in df_filtrado.columns:
                confianza_counts = df_filtrado['ConfianzaClasificacion'].value_counts().reset_index()
                confianza_counts.columns = ['ConfianzaClasificacion', 'count']
                
                fig_confianza = px.bar(
                    confianza_counts,
                    x='ConfianzaClasificacion',
                    y='count',
                    title='Nivel de Confianza en Clasificación',
                    color='ConfianzaClasificacion',
                    color_discrete_map={'alta': '#2ecc71', 'media (inferencia)': '#f39c12'}
                )
                st.plotly_chart(fig_confianza, use_container_width=True, key="bar_confianza")
            else:
                st.info("No hay datos suficientes para mostrar el gráfico")
        
        # Evolución anual por tipo de residuo
        if not df_filtrado.empty and 'Año' in df_filtrado.columns:
            evolucion_tipo = df_filtrado.groupby(['Año', 'CategoriaResiduo']).size().reset_index(name='Cantidad')
            
            fig_evolucion_tipo = px.line(
                evolucion_tipo,
                x='Año',
                y='Cantidad',
                color='CategoriaResiduo',
                title='Evolución por Tipo de Residuo',
                markers=True,
                color_discrete_map={'peligrosos': '#e74c3c', 'no peligrosos': '#2ecc71', 'mixtas': '#f39c12'}
            )
            st.plotly_chart(fig_evolucion_tipo, use_container_width=True, key="line_evolucion_tipo")

    with tab2:
        st.header("Análisis Detallado por Tipo de Residuo")
        
        if not df_filtrado.empty and 'CategoriaResiduo' in df_filtrado.columns:
            # Selector de tipo de residuo
            tipo_analisis = st.selectbox(
                "Selecciona tipo de residuo para análisis detallado",
                options=['Todos'] + sorted(df_filtrado['CategoriaResiduo'].unique()),
                key="select_tipo_analisis"
            )
            
            df_tipo = df_filtrado if tipo_analisis == 'Todos' else df_filtrado[df_filtrado['CategoriaResiduo'] == tipo_analisis]
            
            if not df_tipo.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Licitaciones", len(df_tipo))
                with col2:
                    monto_tipo = df_tipo['Monto_CLP_Millones'].sum()
                    st.metric("Monto Total (MM CLP)", f"${monto_tipo:,.0f}M" if not pd.isna(monto_tipo) else "N/A")
                with col3:
                    if tipo_analisis != 'Todos':
                        confianza_pct = (df_tipo['ConfianzaClasificacion'] == 'alta').mean() * 100
                        st.metric("Clasificaciones con confianza alta", f"{confianza_pct:.1f}%")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Top organismos por tipo de residuo
                    top_organismos_tipo = df_tipo['Organismo'].value_counts().head(10)
                    if not top_organismos_tipo.empty:
                        fig_top_tipo = px.bar(
                            x=top_organismos_tipo.values,
                            y=top_organismos_tipo.index,
                            title=f'Top 10 Organismos - {tipo_analisis}',
                            orientation='h',
                            color=top_organismos_tipo.values,
                            color_continuous_scale='Viridis'
                        )
                        fig_top_tipo.update_layout(xaxis_title="Cantidad de Licitaciones", yaxis_title="")
                        st.plotly_chart(fig_top_tipo, use_container_width=True, key="bar_top_tipo")
                
                with col2:
                    # Distribución por tamaño de licitación
                    tamaño_counts = df_tipo['Tamaño_Licitacion'].value_counts().reset_index()
                    tamaño_counts.columns = ['Tamaño', 'count']
                    
                    fig_tamaño = px.pie(
                        tamaño_counts,
                        values='count',
                        names='Tamaño',
                        title=f'Distribución por Tamaño - {tipo_analisis}',
                        hole=0.3
                    )
                    st.plotly_chart(fig_tamaño, use_container_width=True, key="pie_tamaño")
                
                # Distribución regional para este tipo de residuo
                region_tipo = df_tipo['Region'].value_counts().reset_index()
                region_tipo.columns = ['Region', 'Cantidad']
                
                fig_region_tipo = px.bar(
                    region_tipo.head(15),
                    x='Cantidad',
                    y='Region',
                    title=f'Distribución Regional - {tipo_analisis}',
                    orientation='h',
                    color='Cantidad',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_region_tipo, use_container_width=True, key="bar_region_tipo")
        else:
            st.info("No hay datos suficientes para el análisis por tipo de residuo")

    with tab3:
        st.header("Análisis Regional Detallado")
        
        if not df_filtrado.empty and 'Region' in df_filtrado.columns and len(df_filtrado['Region'].unique()) > 0:
            # Selector de región para análisis detallado
            region_analisis = st.selectbox(
                "Selecciona una región para análisis detallado",
                options=['Todas'] + sorted(df_filtrado['Region'].unique()),
                key="select_region_analisis"
            )
            
            df_region = df_filtrado if region_analisis == 'Todas' else df_filtrado[df_filtrado['Region'] == region_analisis]
            
            if not df_region.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Licitaciones", len(df_region))
                with col2:
                    monto_region = df_region['Monto_CLP_Millones'].sum()
                    st.metric("Monto Total (MM CLP)", f"${monto_region:,.0f}M" if not pd.isna(monto_region) else "N/A")
                with col3:
                    st.metric("Organismos", df_region['Organismo'].nunique())
                with col4:
                    residuo_pred = df_region['CategoriaResiduo'].mode()[0] if not df_region['CategoriaResiduo'].empty else "N/A"
                    st.metric("Tipo residuo predominante", residuo_pred)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Distribución por tipo de residuo en la región
                    residuo_region = df_region['CategoriaResiduo'].value_counts().reset_index()
                    residuo_region.columns = ['CategoriaResiduo', 'Cantidad']
                    
                    fig_residuo_region = px.pie(
                        residuo_region,
                        values='Cantidad',
                        names='CategoriaResiduo',
                        title=f'Tipos de Residuo en {region_analisis}',
                        hole=0.3,
                        color='CategoriaResiduo',
                        color_discrete_map={'peligrosos': '#e74c3c', 'no peligrosos': '#2ecc71', 'mixtas': '#f39c12'}
                    )
                    st.plotly_chart(fig_residuo_region, use_container_width=True, key="pie_residuo_region")
                
                with col2:
                    # Top organismos en la región
                    top_organismos_region = df_region['Organismo'].value_counts().head(8)
                    if not top_organismos_region.empty:
                        fig_top_region = px.bar(
                            x=top_organismos_region.values,
                            y=top_organismos_region.index,
                            title=f'Top 8 Organismos en {region_analisis}',
                            orientation='h',
                            color=top_organismos_region.values,
                            color_continuous_scale='Viridis'
                        )
                        fig_top_region.update_layout(xaxis_title="Cantidad", yaxis_title="")
                        st.plotly_chart(fig_top_region, use_container_width=True, key="bar_top_region")
                
                # Evolución en la región
                evolucion_region = df_region.groupby(['Año', 'CategoriaResiduo']).size().reset_index(name='Cantidad')
                if not evolucion_region.empty:
                    fig_evol_region = px.line(
                        evolucion_region,
                        x='Año',
                        y='Cantidad',
                        color='CategoriaResiduo',
                        title=f'Evolución en {region_analisis} por Tipo de Residuo',
                        markers=True,
                        color_discrete_map={'peligrosos': '#e74c3c', 'no peligrosos': '#2ecc71', 'mixtas': '#f39c12'}
                    )
                    st.plotly_chart(fig_evol_region, use_container_width=True, key="line_evol_region")
        else:
            st.info("No hay datos suficientes para el análisis regional")

    with tab4:
        st.header("Análisis por Organismo")
        
        if not df_filtrado.empty:
            # Top organismos general
            st.subheader("Top 20 Organismos Licitantes")
            
            top_20 = df_filtrado.groupby('Organismo').agg({
                'IDLicitacion': 'count',
                'Monto_CLP_Millones': 'sum'
            }).round(2).rename(columns={'IDLicitacion': 'Cantidad', 'Monto_CLP_Millones': 'Monto_Total_MM'})
            
            # Agregar tipo de residuo más común
            top_residuo = df_filtrado.groupby('Organismo')['CategoriaResiduo'].agg(lambda x: x.mode()[0] if not x.mode().empty else 'N/A')
            top_20 = top_20.join(top_residuo)
            
            top_20 = top_20.sort_values('Cantidad', ascending=False).head(20).reset_index()
            
            if not top_20.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig_top = px.bar(
                        top_20,
                        x='Cantidad',
                        y='Organismo',
                        title='Top 20 - Por Cantidad de Licitaciones',
                        orientation='h',
                        color='Monto_Total_MM',
                        color_continuous_scale='Viridis',
                        text='Cantidad'
                    )
                    fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_top, use_container_width=True, key="bar_top_organismos")
                
                with col2:
                    # Tabla resumen
                    st.dataframe(
                        top_20[['Organismo', 'Cantidad', 'Monto_Total_MM', 'CategoriaResiduo']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Monto_Total_MM": st.column_config.NumberColumn(
                                "Monto Total (MM CLP)",
                                format="$ %.0fM"
                            ),
                            "CategoriaResiduo": st.column_config.TextColumn(
                                "Tipo Principal"
                            )
                        },
                        key="tabla_top_organismos"
                    )
                
                # Gráfico de burbujas: Cantidad vs Monto
                fig_burbujas = px.scatter(
                    top_20,
                    x='Cantidad',
                    y='Monto_Total_MM',
                    size='Monto_Total_MM',
                    color='CategoriaResiduo',
                    hover_name='Organismo',
                    title='Relación Cantidad vs Monto por Organismo',
                    labels={'Cantidad': 'Número de Licitaciones', 'Monto_Total_MM': 'Monto Total (MM CLP)'},
                    color_discrete_map={'peligrosos': '#e74c3c', 'no peligrosos': '#2ecc71', 'mixtas': '#f39c12'}
                )
                st.plotly_chart(fig_burbujas, use_container_width=True, key="scatter_burbujas")
        else:
            st.info("No hay datos suficientes para el análisis por organismo")

    with tab5:
        st.header("Análisis de Tendencia Temporal")
        
        if not df_filtrado.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Vista por mes
                tendencia_mensual = df_filtrado.groupby(df_filtrado['FechaPublicacion'].dt.to_period('M')).size().reset_index(name='Cantidad')
                if not tendencia_mensual.empty:
                    tendencia_mensual['Fecha'] = tendencia_mensual['FechaPublicacion'].astype(str)
                    
                    fig_mensual = px.line(
                        tendencia_mensual,
                        x='Fecha',
                        y='Cantidad',
                        title='Tendencia Mensual de Licitaciones',
                        markers=True
                    )
                    fig_mensual.update_xaxes(title_text="Mes-Año", tickangle=45)
                    fig_mensual.update_yaxes(title_text="Cantidad")
                    st.plotly_chart(fig_mensual, use_container_width=True, key="line_tendencia_mensual")
            
            with col2:
                # Distribución por trimestre
                trimestres = df_filtrado.groupby(['Año', 'Trimestre']).size().reset_index(name='Cantidad')
                if not trimestres.empty:
                    trimestres['Año-Trim'] = trimestres['Año'].astype(str) + '-T' + trimestres['Trimestre'].astype(str)
                    
                    fig_trimestral = px.bar(
                        trimestres,
                        x='Año-Trim',
                        y='Cantidad',
                        title='Licitaciones por Trimestre',
                        color='Año',
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig_trimestral.update_xaxes(title_text="Año-Trimestre", tickangle=45)
                    fig_trimestral.update_yaxes(title_text="Cantidad")
                    st.plotly_chart(fig_trimestral, use_container_width=True, key="bar_trimestral")
            
            # Análisis de estacionalidad por tipo de residuo
            st.subheader("Patrón Estacional por Tipo de Residuo")
            
            estacionalidad = df_filtrado.groupby(['MesNombre', 'CategoriaResiduo']).size().reset_index(name='Cantidad')
            meses_orden = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            if not estacionalidad.empty:
                fig_estacional = px.bar(
                    estacionalidad,
                    x='MesNombre',
                    y='Cantidad',
                    color='CategoriaResiduo',
                    title='Distribución Mensual por Tipo de Residuo',
                    barmode='group',
                    category_orders={"MesNombre": meses_orden},
                    color_discrete_map={'peligrosos': '#e74c3c', 'no peligrosos': '#2ecc71', 'mixtas': '#f39c12'}
                )
                fig_estacional.update_layout(xaxis_title="Mes", yaxis_title="Cantidad")
                st.plotly_chart(fig_estacional, use_container_width=True, key="bar_estacional")
            
            # Análisis YoY (Year over Year)
            st.subheader("Crecimiento Interanual por Tipo de Residuo")
            
            yoy = df_filtrado.groupby(['Año', 'CategoriaResiduo']).size().reset_index(name='Cantidad')
            
            if not yoy.empty:
                fig_yoy = px.line(
                    yoy,
                    x='Año',
                    y='Cantidad',
                    color='CategoriaResiduo',
                    title='Crecimiento Interanual por Tipo de Residuo',
                    markers=True,
                    color_discrete_map={'peligrosos': '#e74c3c', 'no peligrosos': '#2ecc71', 'mixtas': '#f39c12'}
                )
                st.plotly_chart(fig_yoy, use_container_width=True, key="line_yoy")
            else:
                st.info("No hay datos suficientes para el análisis de crecimiento interanual")
        else:
            st.info("No hay datos suficientes para el análisis temporal")

    with tab6:
        st.header("Datos Detallados")
        
        if not df_filtrado.empty:
            # Selector de columnas a mostrar
            columnas_disponibles = ['IDLicitacion', 'NombreLicitacion', 'Tipo', 'Estado', 'FechaPublicacion',
                                   'Organismo', 'Region', 'CategoriaResiduo', 'ConfianzaClasificacion',
                                   'MontoLicitacion', 'Monto_CLP_Millones', 'Tamaño_Licitacion']
            
            columnas_mostrar = st.multiselect(
                "Selecciona columnas a mostrar",
                options=columnas_disponibles,
                default=['IDLicitacion', 'NombreLicitacion', 'Organismo', 'Region', 
                        'CategoriaResiduo', 'FechaPublicacion', 'MontoLicitacion'],
                key="select_columnas"
            )
            
            if columnas_mostrar:
                df_display = df_filtrado[columnas_mostrar].copy()
                
                # Formatear fecha para mejor visualización
                if 'FechaPublicacion' in df_display.columns:
                    df_display['FechaPublicacion'] = df_display['FechaPublicacion'].dt.strftime('%d/%m/%Y')
                
                # Mostrar tabla con formato mejorado
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Monto_CLP_Millones": st.column_config.NumberColumn(
                            "Monto (MM CLP)",
                            format="$ %.2fM"
                        ),
                        "MontoLicitacion": st.column_config.TextColumn(
                            "Monto Original"
                        ),
                        "CategoriaResiduo": st.column_config.TextColumn(
                            "Tipo Residuo"
                        )
                    },
                    key="dataframe_detallado"
                )
                
                # Estadísticas y descargas
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Total registros:** {len(df_display)}")
                    if not df_filtrado['FechaPublicacion'].empty:
                        fecha_min = df_filtrado['FechaPublicacion'].min().strftime('%d/%m/%Y')
                        fecha_max = df_filtrado['FechaPublicacion'].max().strftime('%d/%m/%Y')
                        st.info(f"**Rango de fechas:** {fecha_min} a {fecha_max}")
                    
                    # Resumen por tipo de residuo
                    resumen = df_filtrado['CategoriaResiduo'].value_counts()
                    st.info(f"**Distribución:** {', '.join([f'{k}: {v}' for k, v in resumen.items()])}")
                
                with col2:
                    # Botón de descarga
                    csv = df_display.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Descargar datos como CSV",
                        data=csv,
                        file_name=f"licitaciones_residuos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        type="primary",
                        key="download_button"
                    )
            else:
                st.warning("Selecciona al menos una columna para mostrar")
        else:
            st.info("No hay datos para mostrar")

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 10px;'>
            <p>♻️ Analizador de Compras Ágiles - Gestión de Residuos | Desarrollado con Streamlit y Python</p>
            <p style='font-size: 0.8em;'>Clasificación automática por tipo de residuo con nivel de confianza</p>
        </div>
    """, unsafe_allow_html=True)

else:
    st.warning("👆 Por favor, sube un archivo CSV válido usando el botón en la barra lateral izquierda.")
