import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero - Resumen Ingresos/Egresos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título y descripción
st.title("💰 Dashboard Financiero - Resumen de Ingresos y Egresos")
st.markdown("""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    <h4>📊 Análisis detallado de la evolución financiera de empresas por mes</h4>
    <p>Visualización interactiva de saldos, ingresos y egresos para cada entidad.</p>
    </div>
""", unsafe_allow_html=True)

# --- FUNCIONES DE PROCESAMIENTO ---

@st.cache_data
def cargar_datos_financieros(uploaded_file=None):
    """
    Carga y procesa los datos del archivo Excel con múltiples hojas
    """
    archivo_por_defecto = 'Resumen ingresos-egresos.xlsx'
    
    if uploaded_file is not None:
        df_dict = pd.read_excel(uploaded_file, sheet_name=None, header=None)
        st.sidebar.success("✅ Archivo cargado manualmente")
    else:
        if os.path.exists(archivo_por_defecto):
            try:
                df_dict = pd.read_excel(archivo_por_defecto, sheet_name=None, header=None)
                st.sidebar.success(f"✅ Archivo base cargado: {len(df_dict)} meses")
            except Exception as e:
                st.sidebar.error(f"❌ Error al cargar archivo: {e}")
                return None
        else:
            st.sidebar.error(f"❌ No se encontró el archivo '{archivo_por_defecto}'")
            return None
    
    # Procesar cada hoja (mes)
    datos_completos = []
    
    for mes, df in df_dict.items():
        try:
            # Limpiar y procesar el DataFrame
            df_limpio = df.iloc[4:8, 1:13].copy()  # Filas 5-8, columnas B-M (índices 1-12)
            df_limpio.columns = ['Recauchaje Insamar', 'Banco Chile_1', 'Logística', 'Sustrend', 
                                'Sustrend Laboratorios', 'Volltech', 'Dario E.I.R.L.', 
                                'Sangha Inmobiliaria', 'Banco Chile_2', 'Inversiones Sangha', 
                                'Wellnes Academy', 'Banco Santander Stgo']
            
            # Asignar índices (filas)
            df_limpio.index = ['Saldo inicial', 'Ingresos', 'Egresos', 'Saldo final']
            
            # Transformar a formato largo
            df_melted = df_limpio.T.reset_index()
            df_melted.columns = ['Empresa', 'Saldo_inicial', 'Ingresos', 'Egresos', 'Saldo_final']
            df_melted['Mes'] = mes
            
            # Limpiar valores (convertir a numérico)
            for col in ['Saldo_inicial', 'Ingresos', 'Egresos', 'Saldo_final']:
                df_melted[col] = pd.to_numeric(df_melted[col], errors='coerce')
            
            # Eliminar filas con todos NaN o empresas sin datos
            df_melted = df_melted.dropna(subset=['Saldo_inicial', 'Ingresos', 'Egresos', 'Saldo_final'], how='all')
            df_melted = df_melted[~df_melted['Empresa'].str.contains('Banco', na=False)]
            
            datos_completos.append(df_melted)
            
        except Exception as e:
            st.warning(f"Error procesando mes {mes}: {e}")
            continue
    
    if datos_completos:
        df_final = pd.concat(datos_completos, ignore_index=True)
        
        # Ordenar meses cronológicamente
        orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        df_final['Mes'] = pd.Categorical(df_final['Mes'], categories=orden_meses, ordered=True)
        df_final = df_final.sort_values(['Mes', 'Empresa'])
        
        # Calcular métricas adicionales
        df_final['Resultado_neto'] = df_final['Ingresos'] + df_final['Egresos']  # Egresos son negativos
        df_final['Variacion_saldo'] = df_final['Saldo_final'] - df_final['Saldo_inicial']
        df_final['Margen'] = (df_final['Resultado_neto'] / df_final['Ingresos'].replace(0, np.nan)) * 100
        
        return df_final
    else:
        return None

def formatear_moneda(valor):
    """Formatea valores como moneda chilena"""
    if pd.isna(valor):
        return "N/A"
    return f"${valor:,.0f}"

# --- CARGA DE DATOS ---

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/money--v1.png", width=100)
    st.header("⚙️ Configuración")
    
    uploaded_file = st.file_uploader(
        "Cargar archivo Excel",
        type=['xlsx'],
        help="Sube el archivo 'Resumen ingresos-egresos.xlsx'",
        key="file_uploader"
    )
    
    with st.spinner('Cargando y procesando datos...'):
        df = cargar_datos_financieros(uploaded_file)
    
    if df is not None and not df.empty:
        st.success(f"✅ Datos cargados: {df['Mes'].nunique()} meses, {df['Empresa'].nunique()} empresas")
        
        # Mostrar info del dataset
        st.markdown("---")
        st.markdown("### 📊 Resumen")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Meses", df['Mes'].nunique())
        with col2:
            st.metric("Empresas", df['Empresa'].nunique())
        
        st.markdown("---")
        st.header("🔍 Filtros")
        
        # Filtros
        meses_disponibles = sorted(df['Mes'].unique())
        meses_seleccionados = st.multiselect(
            "📅 Meses",
            options=meses_disponibles,
            default=meses_disponibles,
            key="filtro_meses"
        )
        
        empresas_disponibles = sorted(df['Empresa'].unique())
        empresas_seleccionadas = st.multiselect(
            "🏢 Empresas",
            options=empresas_disponibles,
            default=empresas_disponibles,
            key="filtro_empresas"
        )
        
        # Rango de valores
        st.markdown("### 💰 Filtros de montos")
        col1, col2 = st.columns(2)
        with col1:
            min_monto = float(df['Saldo_final'].min())
            max_monto = float(df['Saldo_final'].max())
            rango_saldo = st.slider(
                "Saldo final (millones)",
                min_value=0.0,
                max_value=float(max_monto/1_000_000),
                value=(0.0, float(max_monto/1_000_000)),
                step=1.0,
                key="rango_saldo"
            )
        with col2:
            min_ingreso = float(df['Ingresos'].min())
            max_ingreso = float(df['Ingresos'].max())
            rango_ingreso = st.slider(
                "Ingresos (millones)",
                min_value=0.0,
                max_value=float(max_ingreso/1_000_000),
                value=(0.0, float(max_ingreso/1_000_000)),
                step=1.0,
                key="rango_ingreso"
            )
    else:
        st.error("❌ No se pudieron cargar los datos")
        st.stop()

# --- APLICAR FILTROS ---

df_filtrado = df.copy()

if meses_seleccionados:
    df_filtrado = df_filtrado[df_filtrado['Mes'].isin(meses_seleccionados)]
if empresas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Empresa'].isin(empresas_seleccionadas)]
if rango_saldo:
    df_filtrado = df_filtrado[
        (df_filtrado['Saldo_final'].abs() >= rango_saldo[0]*1_000_000) &
        (df_filtrado['Saldo_final'].abs() <= rango_saldo[1]*1_000_000)
    ]
if rango_ingreso:
    df_filtrado = df_filtrado[
        (df_filtrado['Ingresos'].abs() >= rango_ingreso[0]*1_000_000) &
        (df_filtrado['Ingresos'].abs() <= rango_ingreso[1]*1_000_000)
    ]

# --- MÉTRICAS PRINCIPALES ---

st.markdown("## 📈 Panel de Control Financiero")

col1, col2, col3, col4 = st.columns(4)

with col1:
    saldo_total = df_filtrado.groupby('Mes')['Saldo_final'].sum().sum()
    st.metric(
        label="💰 Saldo Total Acumulado",
        value=formatear_moneda(saldo_total),
        delta=f"Promedio: {formatear_moneda(saldo_total/df_filtrado['Mes'].nunique())}"
    )

with col2:
    ingresos_totales = df_filtrado.groupby('Mes')['Ingresos'].sum().sum()
    st.metric(
        label="📈 Ingresos Totales",
        value=formatear_moneda(ingresos_totales),
        delta=f"Promedio mes: {formatear_moneda(ingresos_totales/df_filtrado['Mes'].nunique())}"
    )

with col3:
    egresos_totales = df_filtrado.groupby('Mes')['Egresos'].sum().sum()
    st.metric(
        label="📉 Egresos Totales",
        value=formatear_moneda(abs(egresos_totales)),
        delta=f"Promedio mes: {formatear_moneda(abs(egresos_totales)/df_filtrado['Mes'].nunique())}",
        delta_color="inverse"
    )

with col4:
    resultado_neto = ingresos_totales + egresos_totales
    st.metric(
        label="💵 Resultado Neto",
        value=formatear_moneda(resultado_neto),
        delta=f"Margen: {(resultado_neto/ingresos_totales*100):.1f}%" if ingresos_totales != 0 else "N/A"
    )

st.markdown("---")

# --- VISUALIZACIONES ---

# Crear pestañas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visión General",
    "🏢 Análisis por Empresa",
    "📅 Evolución Temporal",
    "💰 Comparativa",
    "📋 Datos Detallados"
])

with tab1:
    st.header("Visión General del Portfolio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Saldo por empresa (último mes disponible)
        ultimo_mes = df_filtrado['Mes'].max()
        df_ultimo = df_filtrado[df_filtrado['Mes'] == ultimo_mes].copy()
        
        fig_saldo = px.bar(
            df_ultimo,
            x='Empresa',
            y='Saldo_final',
            title=f'Saldo Final por Empresa - {ultimo_mes}',
            color='Saldo_final',
            color_continuous_scale='RdYlGn',
            text_auto='.2s'
        )
        fig_saldo.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_saldo, use_container_width=True, key="bar_saldo")
    
    with col2:
        # Distribución de ingresos vs egresos
        df_melt = df_filtrado.melt(
            id_vars=['Empresa', 'Mes'],
            value_vars=['Ingresos', 'Egresos'],
            var_name='Tipo',
            value_name='Monto'
        )
        df_melt['Monto_abs'] = df_melt['Monto'].abs()
        
        fig_dist = px.box(
            df_melt,
            x='Tipo',
            y='Monto_abs',
            color='Tipo',
            title='Distribución de Ingresos y Egresos',
            points='all',
            color_discrete_map={'Ingresos': '#2ecc71', 'Egresos': '#e74c3c'}
        )
        fig_dist.update_layout(yaxis_title="Monto ($)")
        st.plotly_chart(fig_dist, use_container_width=True, key="box_dist")
    
    # Top empresas por ingresos
    st.subheader("Top 5 Empresas por Ingresos")
    top_ingresos = df_filtrado.groupby('Empresa')['Ingresos'].sum().nlargest(5).reset_index()
    
    fig_top = px.bar(
        top_ingresos,
        x='Ingresos',
        y='Empresa',
        title='Empresas con mayores ingresos totales',
        orientation='h',
        color='Ingresos',
        color_continuous_scale='Viridis',
        text_auto='.2s'
    )
    st.plotly_chart(fig_top, use_container_width=True, key="bar_top")

with tab2:
    st.header("Análisis Detallado por Empresa")
    
    # Selector de empresa
    empresa_seleccionada = st.selectbox(
        "Selecciona una empresa",
        options=df_filtrado['Empresa'].unique(),
        key="select_empresa"
    )
    
    df_empresa = df_filtrado[df_filtrado['Empresa'] == empresa_seleccionada].copy()
    
    if not df_empresa.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Saldo actual", formatear_moneda(df_empresa['Saldo_final'].iloc[-1]))
        with col2:
            st.metric("Ingresos totales", formatear_moneda(df_empresa['Ingresos'].sum()))
        with col3:
            st.metric("Egresos totales", formatear_moneda(abs(df_empresa['Egresos'].sum())))
        with col4:
            st.metric("Resultado neto", formatear_moneda(df_empresa['Resultado_neto'].sum()))
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Evolución mensual
            fig_evol = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_evol.add_trace(
                go.Bar(x=df_empresa['Mes'], y=df_empresa['Ingresos'], name="Ingresos", marker_color='#2ecc71'),
                secondary_y=False
            )
            fig_evol.add_trace(
                go.Bar(x=df_empresa['Mes'], y=df_empresa['Egresos'], name="Egresos", marker_color='#e74c3c'),
                secondary_y=False
            )
            fig_evol.add_trace(
                go.Scatter(x=df_empresa['Mes'], y=df_empresa['Saldo_final'], 
                          name="Saldo final", line=dict(color='#3498db', width=3)),
                secondary_y=True
            )
            
            fig_evol.update_layout(
                title=f'Evolución mensual - {empresa_seleccionada}',
                hovermode='x unified'
            )
            fig_evol.update_xaxes(title_text="Mes")
            fig_evol.update_yaxes(title_text="Ingresos/Egresos ($)", secondary_y=False)
            fig_evol.update_yaxes(title_text="Saldo final ($)", secondary_y=True)
            
            st.plotly_chart(fig_evol, use_container_width=True, key="line_evol_empresa")
        
        with col2:
            # Composición
            total_ingresos = df_empresa['Ingresos'].sum()
            total_egresos = abs(df_empresa['Egresos'].sum())
            
            fig_pie = px.pie(
                values=[total_ingresos, total_egresos],
                names=['Ingresos', 'Egresos'],
                title=f'Composición - {empresa_seleccionada}',
                color_discrete_map={'Ingresos': '#2ecc71', 'Egresos': '#e74c3c'},
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True, key="pie_empresa")
        
        # Tabla de datos mensuales
        st.subheader("Datos mensuales")
        df_display = df_empresa[['Mes', 'Saldo_inicial', 'Ingresos', 'Egresos', 'Saldo_final', 'Resultado_neto']].copy()
        for col in ['Saldo_inicial', 'Ingresos', 'Egresos', 'Saldo_final', 'Resultado_neto']:
            df_display[col] = df_display[col].apply(formatear_moneda)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

with tab3:
    st.header("Evolución Temporal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Evolución del saldo total
        saldo_mensual = df_filtrado.groupby('Mes')['Saldo_final'].sum().reset_index()
        
        fig_saldo_mensual = px.line(
            saldo_mensual,
            x='Mes',
            y='Saldo_final',
            title='Evolución del Saldo Total',
            markers=True,
            line_shape='spline'
        )
        fig_saldo_mensual.update_traces(line=dict(color='#3498db', width=3))
        fig_saldo_mensual.update_layout(yaxis_title="Saldo total ($)")
        st.plotly_chart(fig_saldo_mensual, use_container_width=True, key="line_saldo_mensual")
    
    with col2:
        # Ingresos vs Egresos por mes
        flujo_mensual = df_filtrado.groupby('Mes').agg({
            'Ingresos': 'sum',
            'Egresos': 'sum'
        }).reset_index()
        
        fig_flujo = go.Figure()
        fig_flujo.add_trace(go.Bar(x=flujo_mensual['Mes'], y=flujo_mensual['Ingresos'], 
                                   name='Ingresos', marker_color='#2ecc71'))
        fig_flujo.add_trace(go.Bar(x=flujo_mensual['Mes'], y=flujo_mensual['Egresos'], 
                                   name='Egresos', marker_color='#e74c3c'))
        
        fig_flujo.update_layout(
            title='Ingresos vs Egresos por Mes',
            barmode='group',
            yaxis_title="Monto ($)"
        )
        st.plotly_chart(fig_flujo, use_container_width=True, key="bar_flujo")
    
    # Heatmap de saldos por empresa y mes
    st.subheader("Mapa de Calor - Saldos por Empresa y Mes")
    
    pivot_saldos = df_filtrado.pivot_table(
        values='Saldo_final',
        index='Empresa',
        columns='Mes',
        aggfunc='first'
    ).fillna(0)
    
    fig_heatmap = px.imshow(
        pivot_saldos,
        title='Saldos (millones de pesos)',
        color_continuous_scale='RdYlGn',
        aspect='auto',
        text_auto='.0f'
    )
    fig_heatmap.update_layout(xaxis_title="Mes", yaxis_title="Empresa")
    st.plotly_chart(fig_heatmap, use_container_width=True, key="heatmap_saldos")

with tab4:
    st.header("Análisis Comparativo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ranking de rentabilidad
        rentabilidad = df_filtrado.groupby('Empresa').agg({
            'Resultado_neto': 'sum',
            'Ingresos': 'sum'
        }).reset_index()
        rentabilidad['Margen'] = (rentabilidad['Resultado_neto'] / rentabilidad['Ingresos'] * 100).round(1)
        rentabilidad = rentabilidad.sort_values('Resultado_neto', ascending=False)
        
        fig_rent = px.bar(
            rentabilidad.head(10),
            x='Resultado_neto',
            y='Empresa',
            title='Ranking de Rentabilidad (Resultado Neto)',
            orientation='h',
            color='Margen',
            color_continuous_scale='RdYlGn',
            text_auto='.2s'
        )
        fig_rent.update_layout(xaxis_title="Resultado neto ($)")
        st.plotly_chart(fig_rent, use_container_width=True, key="bar_rentabilidad")
    
    with col2:
        # Participación por empresa
        participacion = df_filtrado.groupby('Empresa')['Ingresos'].sum().sort_values(ascending=False)
        
        fig_part = px.pie(
            values=participacion.values,
            names=participacion.index,
            title='Participación en Ingresos Totales',
            hole=0.4
        )
        fig_part.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_part, use_container_width=True, key="pie_participacion")
    
    # Gráfico de burbujas
    st.subheader("Relación Ingresos vs Egresos por Empresa")
    
    resumen_empresas = df_filtrado.groupby('Empresa').agg({
        'Ingresos': 'sum',
        'Egresos': 'sum',
        'Resultado_neto': 'sum'
    }).reset_index()
    resumen_empresas['Egresos_abs'] = resumen_empresas['Egresos'].abs()
    
    fig_bubble = px.scatter(
        resumen_empresas,
        x='Ingresos',
        y='Egresos_abs',
        size='Resultado_neto',
        color='Resultado_neto',
        hover_name='Empresa',
        title='Ingresos vs Egresos por Empresa',
        labels={'Ingresos': 'Ingresos totales ($)', 'Egresos_abs': 'Egresos totales ($)'},
        color_continuous_scale='RdYlGn',
        size_max=60
    )
    fig_bubble.add_shape(
        type='line',
        x0=0, y0=0,
        x1=resumen_empresas['Ingresos'].max(),
        y1=resumen_empresas['Ingresos'].max(),
        line=dict(color='gray', width=1, dash='dash')
    )
    st.plotly_chart(fig_bubble, use_container_width=True, key="scatter_bubble")

with tab5:
    st.header("Datos Detallados")
    
    if not df_filtrado.empty:
        # Selector de columnas
        columnas_disponibles = ['Mes', 'Empresa', 'Saldo_inicial', 'Ingresos', 'Egresos', 
                                'Saldo_final', 'Resultado_neto', 'Variacion_saldo', 'Margen']
        
        columnas_mostrar = st.multiselect(
            "Selecciona columnas a mostrar",
            options=columnas_disponibles,
            default=['Mes', 'Empresa', 'Ingresos', 'Egresos', 'Saldo_final', 'Resultado_neto'],
            key="select_columnas"
        )
        
        if columnas_mostrar:
            df_display = df_filtrado[columnas_mostrar].copy()
            
            # Formatear números
            for col in ['Saldo_inicial', 'Ingresos', 'Egresos', 'Saldo_final', 'Resultado_neto', 'Variacion_saldo']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(formatear_moneda)
            
            if 'Margen' in df_display.columns:
                df_display['Margen'] = df_display['Margen'].round(1).astype(str) + '%'
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                key="dataframe_detallado"
            )
            
            # Estadísticas y descarga
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Total registros:** {len(df_display)}")
                st.info(f"**Meses:** {df_filtrado['Mes'].nunique()}")
                st.info(f"**Empresas:** {df_filtrado['Empresa'].nunique()}")
            
            with col2:
                # Botón de descarga
                csv = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Descargar datos completos como CSV",
                    data=csv,
                    file_name=f"datos_financieros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    type="primary",
                    key="download_button"
                )
    else:
        st.info("No hay datos para mostrar")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 10px;'>
        <p>💰 Dashboard Financiero - Resumen de Ingresos y Egresos | Desarrollado con Streamlit y Python</p>
        <p style='font-size: 0.8em;'>Datos actualizados al {}</p>
    </div>
""".format(datetime.now().strftime('%d/%m/%Y')), unsafe_allow_html=True)
