import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
import os
import pathlib

st.sidebar.markdown("### 🧾 Debug runtime")
st.sidebar.code(f"__file__ = {__file__}")
st.sidebar.code(f"cwd = {os.getcwd()}")
st.sidebar.code(f"files = {sorted([p.name for p in pathlib.Path('.').glob('*.py')])}")
st.sidebar.code(f"pages = {sorted([str(p) for p in pathlib.Path('pages').glob('*.py')]) if pathlib.Path('pages').exists() else 'NO pages/'}")
warnings.filterwarnings("ignore")
st.sidebar.code(f"RUNNING: {__file__}")


# ----------------------------
# CONFIG STREAMLIT
# ----------------------------
st.set_page_config(
    page_title="Dashboard Financiero - Resumen Ingresos/Egresos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("💰 Dashboard Financiero - Resumen de Ingresos y Egresos")
st.markdown(
    """
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    <h4>📊 Análisis detallado de la evolución financiera de empresas por mes</h4>
    <p>Visualización interactiva de saldos, ingresos y egresos para cada entidad.</p>
    </div>
""",
    unsafe_allow_html=True,
)


# ----------------------------
# HELPERS
# ----------------------------
ORDEN_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
ORDEN_MESES_SET = set(ORDEN_MESES)


def formatear_moneda(valor):
    """Formatea valores como moneda chilena."""
    try:
        if pd.isna(valor):
            return "N/A"
        return f"${float(valor):,.0f}"
    except Exception:
        return "N/A"


def _to_numeric_safe(s):
    return pd.to_numeric(s, errors="coerce")


def _safe_month_name(mes_raw):
    """
    Normaliza el nombre de hoja/mes:
    - deja solo el nombre si coincide con ORDEN_MESES
    - si no coincide, lo devuelve tal cual (pero luego lo ordenamos al final)
    """
    if mes_raw is None:
        return None
    mes = str(mes_raw).strip()
    # Capitalización simple
    mes_cap = mes[:1].upper() + mes[1:].lower() if mes else mes
    if mes_cap in ORDEN_MESES_SET:
        return mes_cap
    return mes  # lo dejamos "como venga" para no perder la hoja


# ----------------------------
# DATA LOADING
# ----------------------------
@st.cache_data(show_spinner=False)
def cargar_datos_financieros(uploaded_file=None):
    """
    Carga y procesa el Excel con múltiples hojas (meses).
    Estructura esperada:
    - valores en filas 4:8 y columnas 1:13 (según tu template)
    """
    archivo_por_defecto = "Resumen ingresos-egresos.xlsx"

    if uploaded_file is not None:
        df_dict = pd.read_excel(uploaded_file, sheet_name=None, header=None)
    else:
        if not os.path.exists(archivo_por_defecto):
            return None, f"No se encontró el archivo '{archivo_por_defecto}'"
        try:
            df_dict = pd.read_excel(archivo_por_defecto, sheet_name=None, header=None)
        except Exception as e:
            return None, f"Error al cargar archivo: {e}"

    empresas_cols = [
        "Recauchaje Insamar",
        "Banco Chile_1",
        "Logística",
        "Sustrend",
        "Sustrend Laboratorios",
        "Volltech",
        "Dario E.I.R.L.",
        "Sangha Inmobiliaria",
        "Banco Chile_2",
        "Inversiones Sangha",
        "Wellnes Academy",
        "Banco Santander Stgo",
    ]

    datos_completos = []
    warnings_mes = []

    for mes, df in df_dict.items():
        mes_norm = _safe_month_name(mes)
        try:
            # Guardas básicas: hoja suficientemente grande
            if df.shape[0] < 8 or df.shape[1] < 13:
                warnings_mes.append(f"Hoja '{mes}' no tiene el tamaño esperado; se omitió.")
                continue

            # Tu recorte original
            df_limpio = df.iloc[4:8, 1:13].copy()

            # Si por alguna razón no calza exacto, ajustamos (evita crash)
            if df_limpio.shape != (4, 12):
                # Intento de ajuste mínimo: recortar a 4x12
                df_limpio = df_limpio.iloc[:4, :12]
                if df_limpio.shape != (4, 12):
                    warnings_mes.append(f"Hoja '{mes}' no calza 4x12; se omitió.")
                    continue

            df_limpio.columns = empresas_cols
            df_limpio.index = ["Saldo inicial", "Ingresos", "Egresos", "Saldo final"]

            df_melted = df_limpio.T.reset_index()
            df_melted.columns = ["Empresa", "Saldo_inicial", "Ingresos", "Egresos", "Saldo_final"]
            df_melted["Mes"] = mes_norm

            # numéricos
            for col in ["Saldo_inicial", "Ingresos", "Egresos", "Saldo_final"]:
                df_melted[col] = _to_numeric_safe(df_melted[col])

            # limpia: quita filas completamente vacías (todas NaN)
            df_melted = df_melted.dropna(
                subset=["Saldo_inicial", "Ingresos", "Egresos", "Saldo_final"],
                how="all",
            )

            # filtra bancos (si quieres excluirlos)
            df_melted = df_melted[~df_melted["Empresa"].astype(str).str.contains("Banco", na=False)]

            datos_completos.append(df_melted)

        except Exception as e:
            warnings_mes.append(f"Error procesando hoja '{mes}': {e}")

    if not datos_completos:
        msg = "No se pudo procesar ninguna hoja."
        if warnings_mes:
            msg += " " + " | ".join(warnings_mes[:4])
        return None, msg

    df_final = pd.concat(datos_completos, ignore_index=True)

    # Normaliza Mes: categórico solo para meses "conocidos", lo demás al final
    df_final["Mes"] = df_final["Mes"].astype(str)

    # Orden: meses conocidos primero, desconocidos después (alfabético)
    conocidos = [m for m in ORDEN_MESES if m in set(df_final["Mes"])]
    desconocidos = sorted([m for m in set(df_final["Mes"]) if m not in ORDEN_MESES_SET])
    categorias = conocidos + desconocidos
    df_final["Mes"] = pd.Categorical(df_final["Mes"], categories=categorias, ordered=True)

    df_final = df_final.sort_values(["Mes", "Empresa"])

    # métricas derivadas (con guards)
    df_final["Resultado_neto"] = df_final["Ingresos"].fillna(0) + df_final["Egresos"].fillna(0)
    df_final["Variacion_saldo"] = df_final["Saldo_final"] - df_final["Saldo_inicial"]

    ingresos_safe = df_final["Ingresos"].replace(0, np.nan)
    df_final["Margen"] = (df_final["Resultado_neto"] / ingresos_safe) * 100

    df_final = df_final.replace([np.inf, -np.inf], np.nan)

    msg_ok = f"Datos cargados: {df_final['Mes'].nunique()} meses, {df_final['Empresa'].nunique()} empresas"
    if warnings_mes:
        msg_ok += f" (Avisos: {len(warnings_mes)})"
    return df_final, msg_ok


# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/money--v1.png", width=100)
    st.header("⚙️ Configuración")

    uploaded_file = st.file_uploader(
        "Cargar archivo Excel",
        type=["xlsx"],
        help="Sube el archivo 'Resumen ingresos-egresos.xlsx'",
        key="file_uploader",
    )

    with st.spinner("Cargando y procesando datos..."):
        df, msg = cargar_datos_financieros(uploaded_file)

    if df is None or df.empty:
        st.error(f"❌ No se pudieron cargar los datos. {msg}")
        st.stop()

    st.success(f"✅ {msg}")

    st.markdown("---")
    st.header("🔍 Filtros")

    # Meses disponibles (como strings)
    meses_disponibles = [str(m) for m in df["Mes"].cat.categories] if hasattr(df["Mes"], "cat") else sorted(df["Mes"].unique())
    meses_presentes = [m for m in meses_disponibles if m in set(df["Mes"].astype(str))]

    meses_seleccionados = st.multiselect(
        "📅 Meses",
        options=meses_presentes,
        default=meses_presentes,
        key="filtro_meses",
    )

    empresas_disponibles = sorted(df["Empresa"].dropna().unique().tolist())
    empresas_seleccionadas = st.multiselect(
        "🏢 Empresas",
        options=empresas_disponibles,
        default=empresas_disponibles,
        key="filtro_empresas",
    )

    st.markdown("### 💰 Filtros de montos")

    saldo_max = df["Saldo_final"].dropna().abs().max()
    ingreso_max = df["Ingresos"].dropna().abs().max()

    saldo_max_m = float(saldo_max / 1_000_000) if pd.notna(saldo_max) and saldo_max > 0 else 100.0
    ingreso_max_m = float(ingreso_max / 1_000_000) if pd.notna(ingreso_max) and ingreso_max > 0 else 100.0

    col1, col2 = st.columns(2)
    with col1:
        rango_saldo = st.slider(
            "Saldo final (millones)",
            min_value=0.0,
            max_value=saldo_max_m,
            value=(0.0, saldo_max_m),
            step=1.0,
            key="rango_saldo",
        )
    with col2:
        rango_ingreso = st.slider(
            "Ingresos (millones)",
            min_value=0.0,
            max_value=ingreso_max_m,
            value=(0.0, ingreso_max_m),
            step=1.0,
            key="rango_ingreso",
        )


# ----------------------------
# APPLY FILTERS
# ----------------------------
df_filtrado = df.copy()
df_filtrado["Mes_str"] = df_filtrado["Mes"].astype(str)

if meses_seleccionados:
    df_filtrado = df_filtrado[df_filtrado["Mes_str"].isin(meses_seleccionados)]
if empresas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado["Empresa"].isin(empresas_seleccionadas)]

# Rangos sobre valores absolutos (como venías haciendo)
if rango_saldo:
    df_filtrado = df_filtrado[
        (df_filtrado["Saldo_final"].fillna(0).abs() >= rango_saldo[0] * 1_000_000)
        & (df_filtrado["Saldo_final"].fillna(0).abs() <= rango_saldo[1] * 1_000_000)
    ]
if rango_ingreso:
    df_filtrado = df_filtrado[
        (df_filtrado["Ingresos"].fillna(0).abs() >= rango_ingreso[0] * 1_000_000)
        & (df_filtrado["Ingresos"].fillna(0).abs() <= rango_ingreso[1] * 1_000_000)
    ]

if df_filtrado.empty:
    st.warning("⚠️ No hay datos que cumplan con los filtros seleccionados.")
    st.stop()


# ----------------------------
# KPIs
# ----------------------------
st.markdown("## 📈 Panel de Control Financiero")
col1, col2, col3, col4 = st.columns(4)

n_meses = max(int(df_filtrado["Mes_str"].nunique()), 1)

with col1:
    saldo_total = df_filtrado.groupby("Mes_str")["Saldo_final"].sum().sum()
    st.metric(
        label="💰 Saldo Total Acumulado",
        value=formatear_moneda(saldo_total),
        delta=f"Promedio: {formatear_moneda(saldo_total / n_meses)}",
    )

with col2:
    ingresos_totales = df_filtrado.groupby("Mes_str")["Ingresos"].sum().sum()
    st.metric(
        label="📈 Ingresos Totales",
        value=formatear_moneda(ingresos_totales),
        delta=f"Promedio mes: {formatear_moneda(ingresos_totales / n_meses)}",
    )

with col3:
    egresos_totales = df_filtrado.groupby("Mes_str")["Egresos"].sum().sum()
    st.metric(
        label="📉 Egresos Totales",
        value=formatear_moneda(abs(egresos_totales)),
        delta=f"Promedio mes: {formatear_moneda(abs(egresos_totales) / n_meses)}",
        delta_color="inverse",
    )

with col4:
    resultado_neto = ingresos_totales + egresos_totales
    margen = (resultado_neto / ingresos_totales * 100) if ingresos_totales not in [0, None] and not pd.isna(ingresos_totales) else None
    st.metric(
        label="💵 Resultado Neto",
        value=formatear_moneda(resultado_neto),
        delta=f"Margen: {margen:.1f}%" if margen is not None else "N/A",
    )

st.markdown("---")


# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Visión General", "🏢 Análisis por Empresa", "📅 Evolución Temporal", "💰 Comparativa", "📋 Datos Detallados"]
)


# ----------------------------
# TAB 1
# ----------------------------
with tab1:
    st.header("Visión General del Portfolio")

    colA, colB = st.columns(2)

    with colA:
        # Último mes (según orden categórico)
        ultimo_mes = df_filtrado["Mes_str"].iloc[-1] if len(df_filtrado) else None
        if ultimo_mes is None:
            st.info("No hay datos.")
        else:
            df_ultimo = df_filtrado[df_filtrado["Mes_str"] == ultimo_mes].copy()
            df_ultimo = df_ultimo.dropna(subset=["Saldo_final"])
            if not df_ultimo.empty and df_ultimo["Saldo_final"].notna().any():
                fig_saldo = px.bar(
                    df_ultimo,
                    x="Empresa",
                    y="Saldo_final",
                    title=f"Saldo Final por Empresa - {ultimo_mes}",
                    color="Saldo_final",
                    color_continuous_scale="RdYlGn",
                    text_auto=".2s",
                )
                fig_saldo.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_saldo, use_container_width=True, key="bar_saldo")
            else:
                st.info("No hay datos para el último mes.")

    with colB:
        df_melt = df_filtrado.melt(
            id_vars=["Empresa", "Mes_str"],
            value_vars=["Ingresos", "Egresos"],
            var_name="Tipo",
            value_name="Monto",
        )
        df_melt["Monto_abs"] = df_melt["Monto"].abs()
        df_melt = df_melt.dropna(subset=["Monto_abs"])

        if not df_melt.empty:
            fig_dist = px.box(
                df_melt,
                x="Tipo",
                y="Monto_abs",
                color="Tipo",
                title="Distribución de Ingresos y Egresos",
                points="all",
                color_discrete_map={"Ingresos": "#2ecc71", "Egresos": "#e74c3c"},
            )
            fig_dist.update_layout(yaxis_title="Monto ($)")
            st.plotly_chart(fig_dist, use_container_width=True, key="box_dist")
        else:
            st.info("No hay datos suficientes.")

    st.subheader("Top 5 Empresas por Ingresos")
    top_ingresos = (
        df_filtrado.groupby("Empresa")["Ingresos"].sum().replace([np.inf, -np.inf], np.nan).dropna().nlargest(5).reset_index()
    )

    if not top_ingresos.empty and top_ingresos["Ingresos"].sum() > 0:
        fig_top = px.bar(
            top_ingresos,
            x="Ingresos",
            y="Empresa",
            title="Empresas con mayores ingresos totales",
            orientation="h",
            color="Ingresos",
            color_continuous_scale="Viridis",
            text_auto=".2s",
        )
        st.plotly_chart(fig_top, use_container_width=True, key="bar_top")
    else:
        st.info("No hay datos suficientes.")


# ----------------------------
# TAB 2
# ----------------------------
with tab2:
    st.header("Análisis Detallado por Empresa")

    empresa_seleccionada = st.selectbox(
        "Selecciona una empresa",
        options=sorted(df_filtrado["Empresa"].dropna().unique().tolist()),
        key="select_empresa",
    )

    df_empresa = df_filtrado[df_filtrado["Empresa"] == empresa_seleccionada].copy()
    df_empresa = df_empresa.sort_values("Mes_str")

    # No mates la empresa por NaN: solo limpia en lo mínimo para charts
    if df_empresa.empty:
        st.info(f"No hay datos disponibles para {empresa_seleccionada}")
    else:
        col1, col2, col3, col4 = st.columns(4)

        ultimo_saldo = df_empresa["Saldo_final"].dropna().iloc[-1] if df_empresa["Saldo_final"].dropna().shape[0] else 0
        with col1:
            st.metric("Saldo actual", formatear_moneda(ultimo_saldo))
        with col2:
            st.metric("Ingresos totales", formatear_moneda(df_empresa["Ingresos"].sum()))
        with col3:
            st.metric("Egresos totales", formatear_moneda(abs(df_empresa["Egresos"].sum())))
        with col4:
            st.metric("Resultado neto", formatear_moneda(df_empresa["Resultado_neto"].sum()))

        colL, colR = st.columns(2)

        with colL:
            fig_evol = make_subplots(specs=[[{"secondary_y": True}]])
            fig_evol.add_trace(
                go.Bar(x=df_empresa["Mes_str"], y=df_empresa["Ingresos"].fillna(0), name="Ingresos", marker_color="#2ecc71"),
                secondary_y=False,
            )
            fig_evol.add_trace(
                go.Bar(x=df_empresa["Mes_str"], y=df_empresa["Egresos"].fillna(0), name="Egresos", marker_color="#e74c3c"),
                secondary_y=False,
            )
            fig_evol.add_trace(
                go.Scatter(
                    x=df_empresa["Mes_str"],
                    y=df_empresa["Saldo_final"].fillna(0),
                    name="Saldo final",
                    line=dict(color="#3498db", width=3),
                ),
                secondary_y=True,
            )
            fig_evol.update_layout(
                title=f"Evolución mensual - {empresa_seleccionada}",
                hovermode="x unified",
            )
            fig_evol.update_xaxes(title_text="Mes")
            fig_evol.update_yaxes(title_text="Ingresos/Egresos ($)", secondary_y=False)
            fig_evol.update_yaxes(title_text="Saldo final ($)", secondary_y=True)
            st.plotly_chart(fig_evol, use_container_width=True, key=f"line_evol_empresa_{empresa_seleccionada}")

        with colR:
            total_ingresos = float(df_empresa["Ingresos"].sum()) if not pd.isna(df_empresa["Ingresos"].sum()) else 0.0
            total_egresos = float(abs(df_empresa["Egresos"].sum())) if not pd.isna(df_empresa["Egresos"].sum()) else 0.0
            if total_ingresos > 0 or total_egresos > 0:
                fig_pie = px.pie(
                    values=[total_ingresos, total_egresos],
                    names=["Ingresos", "Egresos"],
                    title=f"Composición - {empresa_seleccionada}",
                    color_discrete_map={"Ingresos": "#2ecc71", "Egresos": "#e74c3c"},
                    hole=0.4,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_empresa_{empresa_seleccionada}")
            else:
                st.info("Sin datos de ingresos/egresos.")

        st.subheader("Datos mensuales")
        df_display = df_empresa[["Mes_str", "Saldo_inicial", "Ingresos", "Egresos", "Saldo_final", "Resultado_neto"]].copy()
        df_display.rename(columns={"Mes_str": "Mes"}, inplace=True)
        for col in ["Saldo_inicial", "Ingresos", "Egresos", "Saldo_final", "Resultado_neto"]:
            df_display[col] = df_display[col].apply(formatear_moneda)
        st.dataframe(df_display, use_container_width=True, hide_index=True)


# ----------------------------
# TAB 3
# ----------------------------
with tab3:
    st.header("Evolución Temporal")

    colA, colB = st.columns(2)

    with colA:
        saldo_mensual = df_filtrado.groupby("Mes_str")["Saldo_final"].sum().reset_index().dropna()
        if not saldo_mensual.empty:
            fig_saldo_mensual = px.line(
                saldo_mensual,
                x="Mes_str",
                y="Saldo_final",
                title="Evolución del Saldo Total",
                markers=True,
                line_shape="spline",
            )
            fig_saldo_mensual.update_traces(line=dict(color="#3498db", width=3))
            fig_saldo_mensual.update_layout(xaxis_title="Mes", yaxis_title="Saldo total ($)")
            st.plotly_chart(fig_saldo_mensual, use_container_width=True, key="line_saldo_mensual")
        else:
            st.info("No hay datos suficientes.")

    with colB:
        flujo_mensual = (
            df_filtrado.groupby("Mes_str")[["Ingresos", "Egresos"]].sum().reset_index().replace([np.inf, -np.inf], np.nan).dropna()
        )
        if not flujo_mensual.empty:
            fig_flujo = go.Figure()
            fig_flujo.add_trace(go.Bar(x=flujo_mensual["Mes_str"], y=flujo_mensual["Ingresos"], name="Ingresos", marker_color="#2ecc71"))
            fig_flujo.add_trace(go.Bar(x=flujo_mensual["Mes_str"], y=flujo_mensual["Egresos"], name="Egresos", marker_color="#e74c3c"))
            fig_flujo.update_layout(
                title="Ingresos vs Egresos por Mes",
                barmode="group",
                xaxis_title="Mes",
                yaxis_title="Monto ($)",
            )
            st.plotly_chart(fig_flujo, use_container_width=True, key="bar_flujo")
        else:
            st.info("No hay datos suficientes.")

    st.subheader("Mapa de Calor - Saldos por Empresa y Mes")

    pivot_saldos = (
        df_filtrado.pivot_table(values="Saldo_final", index="Empresa", columns="Mes_str", aggfunc="first")
        .fillna(0)
    )

    if not pivot_saldos.empty:
        fig_heatmap = px.imshow(
            pivot_saldos,
            title="Saldos (pesos)",
            color_continuous_scale="RdYlGn",
            aspect="auto",
            text_auto=".0f",
        )
        fig_heatmap.update_layout(xaxis_title="Mes", yaxis_title="Empresa")
        st.plotly_chart(fig_heatmap, use_container_width=True, key="heatmap_saldos")
    else:
        st.info("No hay datos suficientes para el mapa de calor.")


# ----------------------------
# TAB 4  (AQUÍ VA LA CORRECCIÓN DEL ERROR)
# ----------------------------
with tab4:
    st.header("Análisis Comparativo")

    colA, colB = st.columns(2)

    with colA:
        rentabilidad = (
            df_filtrado.groupby("Empresa")
            .agg({"Resultado_neto": "sum", "Ingresos": "sum"})
            .reset_index()
            .replace([np.inf, -np.inf], np.nan)
            .dropna(subset=["Resultado_neto", "Ingresos"], how="all")
        )
        rentabilidad["Margen"] = (rentabilidad["Resultado_neto"] / rentabilidad["Ingresos"].replace(0, np.nan) * 100).round(1)
        rentabilidad = rentabilidad.sort_values("Resultado_neto", ascending=False)

        if not rentabilidad.empty and rentabilidad["Resultado_neto"].abs().sum() > 0:
            fig_rent = px.bar(
                rentabilidad.head(10),
                x="Resultado_neto",
                y="Empresa",
                title="Ranking de Rentabilidad (Resultado Neto)",
                orientation="h",
                color="Margen",
                color_continuous_scale="RdYlGn",
                text_auto=".2s",
            )
            fig_rent.update_layout(xaxis_title="Resultado neto ($)")
            st.plotly_chart(fig_rent, use_container_width=True, key="bar_rentabilidad")
        else:
            st.info("No hay datos de rentabilidad.")

    with colB:
        participacion = df_filtrado.groupby("Empresa")["Ingresos"].sum().replace([np.inf, -np.inf], np.nan).dropna()
        participacion = participacion[participacion > 0]

        if not participacion.empty and participacion.sum() > 0:
            fig_part = px.pie(
                values=participacion.values,
                names=participacion.index,
                title="Participación en Ingresos Totales",
                hole=0.4,
            )
            fig_part.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_part, use_container_width=True, key="pie_participacion")
        else:
            st.info("No hay datos de participación.")

    st.subheader("Comparación Ingresos vs Egresos por Empresa")

    try:
        resumen_empresas = (
            df_filtrado.groupby("Empresa")
            .agg({"Ingresos": "sum", "Egresos": "sum"})
            .reset_index()
            .replace([np.inf, -np.inf], np.nan)
            .dropna(subset=["Ingresos", "Egresos"], how="all")
        )

        # Normaliza
        resumen_empresas["Ingresos"] = pd.to_numeric(resumen_empresas["Ingresos"], errors="coerce").fillna(0)
        resumen_empresas["Egresos"] = pd.to_numeric(resumen_empresas["Egresos"], errors="coerce").fillna(0)
        resumen_empresas["Egresos_abs"] = resumen_empresas["Egresos"].abs()

        # ✅ SOLO UNA VEZ (sin duplicado)
        resumen_empresas = resumen_empresas[resumen_empresas["Ingresos"] > 0]

        # -------------------------
        # BLINDAJE DEFINITIVO (para burbujas o cualquier uso posterior)
        # -------------------------
        resumen_empresas = resumen_empresas.replace([np.inf, -np.inf], np.nan)
        resumen_empresas["Size"] = resumen_empresas["Ingresos"].abs()
        resumen_empresas["Size"] = resumen_empresas["Size"].fillna(0)
        resumen_empresas.loc[resumen_empresas["Size"] <= 0, "Size"] = 1

        cap = resumen_empresas["Size"].quantile(0.95) if len(resumen_empresas) else 1
        if pd.notna(cap) and cap > 0:
            resumen_empresas["Size"] = resumen_empresas["Size"].clip(upper=cap)

        if resumen_empresas.empty:
            st.info("No hay suficientes datos para la comparativa.")
        else:
            # Barras (robusto)
            fig_comparativa = go.Figure()
            fig_comparativa.add_trace(go.Bar(
                x=resumen_empresas["Empresa"], y=resumen_empresas["Ingresos"],
                name="Ingresos", marker_color="#2ecc71"
            ))
            fig_comparativa.add_trace(go.Bar(
                x=resumen_empresas["Empresa"], y=resumen_empresas["Egresos_abs"],
                name="Egresos", marker_color="#e74c3c"
            ))
            fig_comparativa.update_layout(
                title="Ingresos vs Egresos por Empresa",
                xaxis_title="Empresa",
                yaxis_title="Monto ($)",
                barmode="group",
                hovermode="x unified",
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_comparativa, use_container_width=True, key="bar_comparativa_final")

            # (Opcional) Burbuja a prueba de NaN/inf/negativos
            with st.expander("Ver burbujas (Ingresos vs Egresos)"):
                fig_bubble = px.scatter(
                    resumen_empresas,
                    x="Ingresos",
                    y="Egresos_abs",
                    size="Size",
                    hover_name="Empresa",
                    size_max=60,
                    title="Burbujas: Ingresos vs Egresos (tamaño ~ Ingresos)",
                )
                st.plotly_chart(fig_bubble, use_container_width=True, key="bubble_safe")

            with st.expander("Ver datos detallados"):
                st.dataframe(resumen_empresas[["Empresa", "Ingresos", "Egresos", "Egresos_abs"]], use_container_width=True)

    except Exception as e:
        st.warning(f"Error al generar comparativa: {e}")
        st.dataframe(df_filtrado.groupby("Empresa")[["Ingresos", "Egresos"]].sum().reset_index(), use_container_width=True)

# ----------------------------
# TAB 5
# ----------------------------
with tab5:
    st.header("Datos Detallados")

    columnas_disponibles = [
        "Mes_str",
        "Empresa",
        "Saldo_inicial",
        "Ingresos",
        "Egresos",
        "Saldo_final",
        "Resultado_neto",
        "Variacion_saldo",
        "Margen",
    ]

    columnas_mostrar = st.multiselect(
        "Selecciona columnas a mostrar",
        options=columnas_disponibles,
        default=["Mes_str", "Empresa", "Ingresos", "Egresos", "Saldo_final", "Resultado_neto"],
        key="select_columnas",
    )

    if columnas_mostrar:
        df_display = df_filtrado[columnas_mostrar].copy()
        df_display.rename(columns={"Mes_str": "Mes"}, inplace=True)

        for col in ["Saldo_inicial", "Ingresos", "Egresos", "Saldo_final", "Resultado_neto", "Variacion_saldo"]:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(formatear_moneda)

        if "Margen" in df_display.columns:
            df_display["Margen"] = df_display["Margen"].round(1).astype(str) + "%"

        st.dataframe(df_display, use_container_width=True, hide_index=True, key="dataframe_detallado")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Total registros:** {len(df_display)}")
            st.info(f"**Meses:** {df_filtrado['Mes_str'].nunique()}")
            st.info(f"**Empresas:** {df_filtrado['Empresa'].nunique()}")

        with col2:
            csv = df_filtrado.drop(columns=["Mes_str"]).to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Descargar datos completos como CSV",
                data=csv,
                file_name=f"datos_financieros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary",
                key="download_button",
            )
    else:
        st.info("Selecciona al menos una columna.")


# ----------------------------
# FOOTER
# ----------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 10px;'>
        <p>💰 Dashboard Financiero - Resumen de Ingresos y Egresos | Desarrollado con Streamlit y Python</p>
        <p style='font-size: 0.8em;'>Datos actualizados al {}</p>
    </div>
""".format(datetime.now().strftime("%d/%m/%Y")),
    unsafe_allow_html=True,
)
