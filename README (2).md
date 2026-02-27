# ♻️ Analizador de Compras Ágiles - Gestión de Residuos

Dashboard interactivo desarrollado con **Streamlit** para el análisis de licitaciones públicas de gestión de residuos en Chile, con clasificación automática por tipo (peligrosos, no peligrosos y mixtas).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green.svg)
![Plotly](https://img.shields.io/badge/Plotly-5.14+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Descripción

Esta aplicación permite explorar, filtrar y visualizar datos de licitaciones públicas de gestión de residuos, proporcionando insights valiosos sobre el mercado de manejo de residuos en el sector público chileno. Los datos incluyen clasificación automática por tipo de residuo con nivel de confianza.

### 🔍 ¿Qué puedes hacer con esta herramienta?

- **Analizar** licitaciones por tipo de residuo (peligrosos, no peligrosos, mixtas)
- **Evaluar** la calidad de la clasificación con niveles de confianza
- **Comparar regiones** y su actividad en gestión de residuos
- **Identificar** principales organismos licitantes por categoría
- **Visualizar** tendencias temporales y estacionalidad
- **Filtrar** datos de forma interactiva por múltiples criterios
- **Exportar** datos filtrados para análisis externos

## ✨ Características Principales

### 🎯 Clasificación Inteligente
- **Residuos peligrosos**: Materiales que requieren manejo especial
- **Residuos no peligrosos**: Residuos domiciliarios, escombros, lodos, etc.
- **Residuos mixtos**: Licitaciones que combinan ambos tipos
- **Nivel de confianza**: Indicador de calidad de la clasificación (alta/media)

### 📊 Visualizaciones Interactivas

| Pestaña | Descripción |
|---------|-------------|
| **Visión General** | KPIs principales, distribución por tipo de residuo, evolución temporal |
| **Análisis por Tipo Residuo** | Desglose detallado por categoría con métricas específicas |
| **Análisis Regional** | Distribución geográfica y comparativas regionales |
| **Análisis por Organismo** | Ranking de licitantes y análisis de concentración |
| **Tendencia Temporal** | Patrones mensuales, estacionalidad y crecimiento interanual |
| **Datos Detallados** | Tabla interactiva con exportación a CSV |

## 🛠️ Tecnologías Utilizadas

- **[Streamlit](https://streamlit.io/)** - Framework para aplicaciones de datos
- **[Pandas](https://pandas.pydata.org/)** - Manipulación y análisis de datos
- **[Plotly](https://plotly.com/python/)** - Visualizaciones interactivas
- **[NumPy](https://numpy.org/)** - Cálculos numéricos

## 📦 Instalación

### Requisitos previos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Clona el repositorio**
```bash
git clone https://github.com/tu-usuario/analizador-residuos.git
cd analizador-residuos
