# 💰 Dashboard Financiero - Resumen de Ingresos y Egresos

Dashboard interactivo desarrollado con **Streamlit** para visualizar y analizar la evolución financiera de múltiples empresas, mostrando saldos, ingresos y egresos mensuales.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green.svg)
![Plotly](https://img.shields.io/badge/Plotly-5.14+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Descripción

Esta aplicación permite explorar de manera interactiva los datos financieros de un portfolio de empresas, con información detallada por mes de saldos iniciales, ingresos, egresos y saldos finales.

### 🔍 ¿Qué puedes hacer con esta herramienta?

- **Visualizar** la evolución mensual de saldos por empresa
- **Comparar** ingresos vs egresos de forma interactiva
- **Identificar** las empresas más rentables del portfolio
- **Analizar** tendencias temporales y estacionalidad
- **Filtrar** datos por mes, empresa y rangos de montos
- **Exportar** datos filtrados para análisis externos

## ✨ Características Principales

### 📊 Panel de Control
- Métricas clave: saldo total, ingresos totales, egresos totales y resultado neto
- Visualizaciones interactivas con códigos de color intuitivos
- Filtros dinámicos por múltiples criterios

### 📈 Visualizaciones por Pestañas

| Pestaña | Descripción |
|---------|-------------|
| **Visión General** | KPIs principales, distribución de saldos, top empresas |
| **Análisis por Empresa** | Desglose detallado por empresa con evolución mensual |
| **Evolución Temporal** | Tendencias mensuales y mapa de calor de saldos |
| **Comparativa** | Ranking de rentabilidad y participación por empresa |
| **Datos Detallados** | Tabla interactiva con exportación a CSV |

## 🛠️ Tecnologías Utilizadas

- **[Streamlit](https://streamlit.io/)** - Framework para aplicaciones de datos
- **[Pandas](https://pandas.pydata.org/)** - Manipulación y análisis de datos
- **[Plotly](https://plotly.com/python/)** - Visualizaciones interactivas
- **[NumPy](https://numpy.org/)** - Cálculos numéricos
- **[OpenPyXL](https://openpyxl.readthedocs.io/)** - Lectura de archivos Excel

## 📦 Instalación

### Requisitos previos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clona el repositorio**
```bash
git clone https://github.com/tu-usuario/dashboard-financiero.git
cd dashboard-financiero
