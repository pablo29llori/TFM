# TFM — Análisis del rendimiento y la valoración salarial de futbolistas mediante integración de datos y modelos de aprendizaje automático

> Trabajo Fin de Máster en Big Data
> **Autor:** [Tu nombre]
> **Tutor:** Marcos
> **Universidad:** [Universidad]
> **Curso:** 2025/2026

---

## 📌 Resumen

Este TFM construye un *pipeline* completo de datos de fútbol que integra estadísticas de rendimiento con datos salariales de las 5 grandes ligas europeas (España, Inglaterra, Italia, Alemania y Francia) y la Süper Lig turca, durante las 6 últimas temporadas (20/21 → 25/26). El objetivo final es aplicar técnicas de aprendizaje automático para **predecir salarios a partir del rendimiento** (detectando jugadores sobrevalorados e infravalorados) y para **identificar similitudes de estilo entre jugadores**, presentando los resultados en una plataforma interactiva.

---

## 🎯 Objetivos

1. Construir una tabla maestra unificada con estadísticas de rendimiento + datos salariales de ~3.500 jugadores × 6 temporadas.
2. Entrenar un modelo de regresión que prediga el salario justo de un jugador en función de su rendimiento, y usar los residuos para identificar desajustes de mercado.
3. Construir un sistema de similitud entre jugadores que permita encontrar perfiles estadísticamente parecidos.
4. Desplegar los resultados en una aplicación interactiva con **Streamlit**.

---

## 📂 Estructura del proyecto

```
TFM/
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   ├── raw/                 # Datos originales sin tocar
│   │   ├── capology/        # 36 CSVs salariales (cg_<liga>_<temporada>.csv)
│   │   └── sofascore/       # 36 CSVs estadísticos (df_<liga>_<temporada>.csv)
│   ├── processed/           # Datos limpios por fuente
│   │   ├── capology/
│   │   └── sofascore/
│   └── master/              # Tablas integradas Sofascore + Capology
└── notebooks/
    ├── 01_ingesta/          # Scraping desde Sofascore y Capology
    ├── 02_preprocesamiento/ # Limpieza técnica por fuente
    ├── 03_procesamiento/    # Integración (matching + merge) por temporada
    ├── 04_eda/              # Análisis exploratorio
    ├── 05_fe/               # Feature engineering
    ├── 06_ml/               # Modelos de regresión y similitud
    └── 07_visualizacion/    # Aplicación Streamlit
```

---

## 🔌 Fuentes de datos

| Fuente | Contenido | Cobertura | Acceso |
|---|---|---|---|
| [Sofascore](https://www.sofascore.com) | 116 estadísticas de rendimiento por jugador y temporada | 6 ligas × 6 temporadas | API vía `ScraperFC` |
| [Capology](https://www.capology.com) | Salarios brutos anuales y semanales (EUR) | 6 ligas × 6 temporadas | Scraping vía `ScraperFC` |

Toda la extracción se realiza con la librería [**ScraperFC**](https://scraperfc.readthedocs.io/en/latest/index.html) desarrollada por Owen Seymour.

---

## 🧭 Pipeline metodológico

### 1. Ingesta (`01_ingesta/`)

Dos notebooks de scraping, uno por fuente. Se descargan los 36 dataframes de cada fuente (6 ligas × 6 temporadas), se normalizan los salarios de Capology a EUR, y se añaden columnas `data_country` y `data_season` como metadatos de trazabilidad. Los archivos se mueven manualmente a `data/raw/` para evitar repetir scraping (especialmente costoso en Capology).

La temporada 25/26, al estar en curso, se descarga de Sofascore como **snapshot con fecha** en el nombre (`df_<liga>_2526_snapshot_<YYYYMMDD>.csv`). En Capology no es necesario porque publica los datos como definitivos desde el inicio de temporada.

### 2. Preprocesamiento (`02_preprocesamiento/`)

Capa intermedia ligera, una por fuente. Se aplica una limpieza técnica mínima sin tomar decisiones analíticas:

- **Sofascore:** renombrado de columnas con espacios (`player id` → `player_id`), conversión de tipos y reordenación de columnas (identificadoras → stats clave → resto alfabético).
- **Capology:** eliminación del header embebido como fila, renombrado dinámico robusto a columnas extra (la 25/26 trae campos adicionales), parseo de valores monetarios (`"€ 33,330,000"` → `float`).

Se mantiene la nomenclatura de archivos (`cg_<liga>_<temporada>.csv` y `df_<liga>_<temporada>.csv`).

### 3. Procesamiento (`03_procesamiento/`)

**La fase más laboriosa del proyecto.** 30 notebooks (uno por liga × temporada cerrada) con plantilla idéntica que integra Sofascore + Capology mediante una estrategia de *matching* en cascada:

1. **Normalización de nombres** (NFKD + ASCII + minúsculas + limpieza de caracteres especiales).
2. **`TEAM_MAP`:** alineación manual de nombres de equipo entre ambas fuentes.
3. **Merge exacto normalizado** sobre `(player_norm, team_norm)`.
4. **Fuzzy matching escalonado** con `rapidfuzz` sobre los no emparejados:
   - Score ≥ 0.90 → aceptación automática
   - 0.75 ≤ score < 0.90 → revisión manual permisiva
   - 0.50 ≤ score < 0.75 → revisión manual estricta (rechazo por defecto)
   - score < 0.50 → revisión manual muy estricta (rechazo por defecto)
5. **Revisión final manual** de jugadores sin salario, ordenados por equipo y minutos jugados, comparando contra plantilla completa de Capology.
6. Guardado en `data/master/master_<liga>_<temporada>.csv`.

Las cifras de matching obtenidas se sitúan entre el **87% y el 95%**, con el resto de nulos justificados por casos reales del fútbol (canteranos sin ficha de primer equipo, traspasos en mercado de invierno, cesiones, etc.).

### 4. EDA (`04_eda/`)

Análisis exploratorio sobre la tabla maestra unificada. Se abordarán:

- Distribución del salario (presumiblemente muy asimétrica → análisis en escala logarítmica).
- Tratamiento de valores nulos y duplicados detectados durante el procesamiento.
- Análisis por liga, posición, edad y minutos jugados.
- Detección de outliers y comportamientos extremos.
- Correlaciones entre variables de rendimiento y salario.

### 5. Feature engineering (`05_fe/`)

Preparación de variables para el modelado:

- Normalización per-90 minutos para métricas comparables.
- Filtrado por minutos mínimos (a definir).
- Codificación de variables categóricas (posición, liga, club).
- Posible transformación logarítmica del target salarial.

### 6. Machine learning (`06_ml/`)

Dos bloques complementarios:

**a) Regresión sobre salarios (supervisado).**
Predecir `gross_annual_eur` (probablemente en escala log) a partir de las features de rendimiento. El **residuo** (predicción − valor real) actúa como indicador de desajuste:
- Residuo positivo elevado → jugador **infravalorado**.
- Residuo negativo elevado → jugador **sobrevalorado**.

**b) Similitud entre jugadores (no supervisado).**
Representación vectorial de cada jugador en el espacio estadístico normalizado para encontrar perfiles parecidos. Permite responder a "¿qué jugadores se parecen a X?" y refuerza las conclusiones de la regresión.

### 7. Visualización (`07_visualizacion/`)

Aplicación interactiva en **Streamlit** que combina ambos modelos: el usuario selecciona un jugador y obtiene su salario real, salario predicho, residuo (clasificación sobre/infravalorado) y top-N jugadores con perfil estadístico similar.

---

## ✅ Estado de avance

| Fase | Estado | Notas |
|---|---|---|
| 01 · Ingesta | ✅ Completo | Falta refrescar snapshots de la 25/26 hasta cierre de ligas |
| 02 · Preprocesamiento | ✅ Completo | |
| 03 · Procesamiento | 🟡 30/36 | Pendiente snapshots 25/26 + tabla master única |
| 04 · EDA | ⏳ Pendiente | |
| 05 · Feature engineering | ⏳ Pendiente | |
| 06 · Machine learning | ⏳ Pendiente | |
| 07 · Visualización (Streamlit) | ⏳ Pendiente | |
| Memoria LaTeX | 🟡 En curso | Plantilla de la universidad |

---

## 🧠 Decisiones metodológicas clave

- **Snapshots de la 25/26.** Se trabaja con datos provisionales con fecha en el nombre del archivo (`*_snapshot_<YYYYMMDD>.csv`) hasta el cierre de las ligas. Una vez cerradas todas las competiciones (las cinco grandes terminan a finales de mayo; la Süper Lig se alarga hasta principios de junio), se reejecutan únicamente las fases 01–03 para los 6 archivos de la 25/26.

- **Fuzzy matching escalonado con revisión manual.** Prioriza minimizar falsos positivos: por defecto solo se aceptan matches con score ≥ 0.90. Los rangos inferiores requieren confirmación explícita en listas blancas (`ACCEPT_LOW_FUZZY`, `ACCEPT_VERY_LOW_FUZZY`).

- **Nulos en salarios.** No se imputan en el procesamiento. Su tratamiento se decide en el EDA (fase 04) tras entender su naturaleza.

- **Estrategia de validación temporal en ML.** El modelo de regresión se entrena con las **5 temporadas cerradas (20/21 → 24/25)** y se aplica sobre la **25/26** para detectar desajustes de mercado actuales. Esta separación evita *data leakage* temporal y replica el escenario realista de un club que valora jugadores de cara a la próxima ventana de fichajes.

- **Modelado del salario en escala logarítmica.** Por la fuerte asimetría esperada en la distribución salarial (decisión a confirmar tras EDA).

---

## 🛠️ Reproducibilidad

- **Python:** 3.13.2
- **Dependencias:** ver `requirements.txt`
- **Instalación:**
  ```bash
  git clone <repo-url>
  cd TFM
  pip install -r requirements.txt
  ```
- **Ejecución:** los notebooks están numerados por orden de ejecución dentro de `notebooks/`. Las rutas se resuelven con `pathlib` desde la raíz del proyecto, sin dependencias absolutas.

---

## 📅 Próximos pasos

1. Generar la tabla master única concatenando los 36 dataframes de `data/master/`, añadiendo columnas `country` y `season` finales.
2. Comenzar el EDA (fase 04) sobre la tabla master.
3. Refrescar snapshots de la 25/26 hasta el cierre completo de las 6 ligas.
4. Reejecutar las fases 01–03 sobre los datos definitivos de la 25/26 cuando estén disponibles.

---

## 📬 Contacto

[Tu nombre] — [tu.email@universidad.com]
