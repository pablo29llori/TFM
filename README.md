# TFM — Análisis del rendimiento y la valoración salarial de futbolistas mediante integración de datos y modelos de aprendizaje automático

> Trabajo Fin de Máster en Big Data
> **Autor:** Pablo Llorián González
> **Tutor:** Marcos Sergio Pacheco Dos Santos Lima Junior
> **Universidad:** Universidad Europea de Andalucía
> **Curso:** 2025/2026

---

## 📌 Resumen

Este TFM construye un *pipeline* completo de datos de fútbol que integra estadísticas de rendimiento con datos salariales de las 5 grandes ligas europeas (España, Inglaterra, Italia, Alemania y Francia) y la Süper Lig turca, durante las 6 últimas temporadas (20/21 → 25/26). El objetivo final es aplicar técnicas de aprendizaje automático para **predecir salarios a partir del rendimiento** (detectando jugadores sobrevalorados e infravalorados) y para **identificar similitudes de estilo entre jugadores**, presentando los resultados en una plataforma interactiva.

La tabla maestra final integra **20.316 registros** correspondientes a **7.759 jugadores únicos** distribuidos en **171 equipos**, con una **cobertura salarial global del 91.3%**.

---

## 🎯 Objetivos

1. Construir una tabla maestra unificada con estadísticas de rendimiento + datos salariales de las 6 ligas durante 6 temporadas.
2. Entrenar un modelo de regresión que prediga el salario justo de un jugador en función de su rendimiento, y usar los residuos para identificar desajustes de mercado.
3. Construir un sistema de similitud entre jugadores que permita encontrar perfiles estadísticamente parecidos, útil para identificar reemplazos potenciales de jugadores sobrepagados.
4. Desplegar los resultados en una aplicación interactiva con **Streamlit**.

---

## 📂 Estructura del proyecto

```
TFM/
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   ├── raw/                 # Datos originales sin tocar (output fase 01)
│   │   ├── capology/        # 36 CSVs salariales (cg_<liga>_<temporada>.csv)
│   │   └── sofascore/       # 36 CSVs estadísticos (df_<liga>_<temporada>.csv)
│   ├── processed/           # Datos limpios por fuente (output fase 02)
│   │   ├── capology/
│   │   └── sofascore/
│   ├── master/              # 36 masters por liga × temporada + master_total.csv (output fase 03)
│   └── clean/               # Dataset analítico depurado: master_clean.csv (output fase 04)
└── notebooks/
    ├── 01_ingesta/          # Scraping desde Sofascore y Capology
    ├── 02_preprocesamiento/ # Limpieza técnica por fuente
    ├── 03_procesamiento/    # Integración (matching + merge) + tabla master única
    ├── 04_eda/              # Análisis exploratorio (5 notebooks)
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

**La fase más laboriosa del proyecto.** 36 notebooks (uno por liga × temporada, incluyendo los 6 snapshots de la 25/26) con plantilla idéntica que integra Sofascore + Capology mediante una estrategia de *matching* en cascada:

1. **Normalización de nombres** (NFKD + ASCII + minúsculas + limpieza de caracteres especiales).
2. **`TEAM_MAP`:** alineación manual de nombres de equipo entre ambas fuentes.
3. **Merge exacto normalizado** sobre `(player_norm, team_norm)`.
4. **Fuzzy matching escalonado** con `rapidfuzz` sobre los no emparejados:
   - Score ≥ 0.90 → aceptación automática
   - 0.75 ≤ score < 0.90 → revisión manual permisiva
   - 0.50 ≤ score < 0.75 → revisión manual estricta (rechazo por defecto)
   - score < 0.50 → revisión manual muy estricta (rechazo por defecto)
5. **Revisión final manual** de jugadores sin salario, ordenados por equipo y minutos jugados, comparando contra plantilla completa de Capology.
6. **Matches manuales explícitos** (`MANUAL_MATCHES`) para resolver casos de apodos radicalmente distintos (p. ej. *Pacha* ↔ *Alfonso Espino*) o traspasos invernales entre ligas distintas.
7. Guardado en `data/master/master_<liga>_<temporada>.csv`.

Un notebook adicional (`03_master_total.ipynb`) concatena los 36 dataframes resultantes, renombra `data_country` → `country` y `data_season` → `season`, y guarda el resultado como `master_total.csv`. Esta tabla unificada es el input de la fase 04.

**Cobertura salarial obtenida:** 91.3% global (rango 82.6%–97.3% según liga × temporada). Los nulos restantes corresponden a casuísticas reales del fútbol (canteranos sin ficha de primer equipo, traspasos en mercado de invierno, cesiones, etc.).

### 4. EDA (`04_eda/`)

Análisis exploratorio estructurado en 5 notebooks temáticos, cuyo output principal es `data/clean/master_clean.csv`, dataset analítico depurado listo para feature engineering:

- **`04_01_carga_diagnostico_y_limpieza.ipynb`** — Tratamiento de duplicados puros (9 casos), salarios anómalos = 0 € convertidos a NaN (80 casos, mayoritariamente cedidos), conservación de los 524 casos multi-liga, imputación de nulos estructurales por posición (`goalsPrevented`, `outfielderBlocks`...) y optimización de tipos (`int` / `Int64` / `float`).
- **`04_02_target_salario.ipynb`** — Análisis univariante del target. Caracterización formal de la asimetría (skewness +6.04 → −0.30 con log-transform) y curtosis (+74.27 → +0.08). Tests de normalidad (D'Agostino-Pearson, Anderson-Darling), Q-Q plots y detección de outliers IQR. Validación de la **hipótesis log-normal** y comparativa con Box-Cox (λ óptimo ≈ 0.077, confirmando la idoneidad del log).
- **`04_03_categoricas.ipynb`** — Análisis de `position`, `age` y `nationality`. Detección de la **curva edad-salario** clásica (compatible con la ecuación de Mincer, 1974), trayectorias diferenciadas por posición y concentración del 62.4% del dataset en las 10 nacionalidades principales (las 6 primeras coinciden con las 6 ligas estudiadas).
- **`04_04_numericas_y_correlaciones.ipynb`** — Matriz de correlación 110×110, identificación de 27 pares con r ≥ 0.95. **Clustering jerárquico** que redescubre 5 facetas naturales del juego (Volumen/Pase posicional, Creación ofensiva, Definición, Portería, Duelos/Defensa). **PCA exploratorio**: la dimensión intrínseca del dataset es ~22 componentes (80% varianza), confirmando la fuerte redundancia.
- **`04_05_target_vs_features.ipynb`** — Correlaciones Pearson, Spearman e información mutua de las 110 stats con `log(salario)`. Análisis diferenciado por posición, que motiva el modelado segmentado en fase 06. **Auditoría de `goalsPrevented`**: detección de un sesgo estructural en la fuente (Sofascore replica la stat colectiva del portero del equipo en jugadores de campo en algunos casos puntuales, especialmente en Premier League 22/23), con decisión de limpieza para fase 05.

### 5. Feature engineering (`05_fe/`)

Preparación de variables para el modelado. Decisiones acumuladas del EDA que se aplicarán:

- Limpieza de `goalsPrevented` para que sea estrictamente variable de portero.
- Tratamiento del 8.6% de jugadores sin posición asignada.
- Selección de features por cluster temático (eliminación de redundancia).
- Normalización per-90 minutos para stats que escalan con tiempo de juego.
- Codificación de variables categóricas (`position` *one-hot*, `nationality` reducida a top-N + "Otras").
- Transformación logarítmica del target salarial.
- Tratamiento de los 524 casos multi-liga (decisión empírica entre agregación, selección por minutos máximos o tratamiento como observaciones independientes).

### 6. Machine learning (`06_ml/`)

Dos bloques complementarios:

**a) Regresión sobre salarios (supervisado).**
Predecir `log(gross_annual_eur)` a partir de las features de rendimiento. El **residuo** (predicción − valor real) actúa como indicador de desajuste:
- Residuo positivo elevado → jugador **infravalorado**.
- Residuo negativo elevado → jugador **sobrevalorado**.

Se evaluarán modelos no lineales (XGBoost, Random Forest, Gradient Boosting) por encima de modelos lineales, dada la evidencia de relaciones no monótonas detectadas en el EDA (información mutua). Se comparará el enfoque **modelos separados por posición** vs. **modelo único con interacciones `posición × stat`**.

**b) Similitud entre jugadores (no supervisado).**
Representación vectorial de cada jugador en un espacio estadístico reducido (PCA o selección por cluster temático) para encontrar perfiles parecidos. Permite responder a "¿qué jugadores se parecen a X y cuánto cobran?" y refuerza las conclusiones de la regresión: la combinación regresión + similitud permite **detectar a un jugador sobrepagado y proponer alternativas más baratas con perfil estadístico similar**.

### 7. Visualización (`07_visualizacion/`)

Aplicación interactiva en **Streamlit** que combina ambos modelos: el usuario selecciona un jugador y obtiene su salario real, salario predicho, residuo (clasificación sobre/infravalorado) y top-N jugadores con perfil estadístico similar.

---

## ✅ Estado de avance

| Fase | Estado | Notas |
|---|---|---|
| 01 · Ingesta | ✅ Completo | Falta refrescar snapshots de la 25/26 al cierre de ligas |
| 02 · Preprocesamiento | ✅ Completo | |
| 03 · Procesamiento | ✅ Completo* | *Snapshots 25/26 pendientes de actualización al cierre de ligas |
| 04 · EDA | ✅ Completo | 5 notebooks temáticos + `master_clean.csv` generado |
| 05 · Feature engineering | ⏳ Pendiente | |
| 06 · Machine learning | ⏳ Pendiente | |
| 07 · Visualización (Streamlit) | ⏳ Pendiente | |
| Memoria LaTeX | 🟡 En curso | Plantilla de la universidad — redacción en paralelo |

### 📊 Métricas clave del dataset actual

| Métrica | Valor |
|---|---|
| Filas totales | 20.316 |
| Columnas | 122 (master_total) / 121 (master_clean) |
| Jugadores únicos (`player_id`) | 7.759 |
| Equipos únicos | 171 |
| Cobertura salarial global | 91.3% |
| Cobertura por liga × temporada | 82.6% – 97.3% |
| Variables stats numéricas | 110 |
| Dimensión intrínseca (PCA, 80% var.) | ~22 componentes |

---

## 🧠 Decisiones metodológicas clave

- **Snapshots de la 25/26.** Se trabaja con datos provisionales con fecha en el nombre del archivo (`*_snapshot_<YYYYMMDD>.csv`) hasta el cierre de las ligas. Una vez cerradas todas las competiciones (las cinco grandes terminan a finales de mayo; la Süper Lig se alarga hasta principios de junio), se reejecutan únicamente las fases 01–03 para los 6 archivos de la 25/26.

- **Fuzzy matching escalonado con revisión manual.** Prioriza minimizar falsos positivos: por defecto solo se aceptan matches con score ≥ 0.90. Los rangos inferiores requieren confirmación explícita en listas blancas (`ACCEPT_LOW_FUZZY`, `ACCEPT_VERY_LOW_FUZZY`) y los casos imposibles para el fuzzy se resuelven con `MANUAL_MATCHES` explícitos.

- **Modelado del target en escala logarítmica.** La distribución salarial es fuertemente log-normal (skewness +6, kurtosis +74). La transformación `log(salario)` reduce ambas a valores próximos a cero (γ₁ = −0.30, γ₂ = +0.08), cercanos al óptimo absoluto identificado por Box-Cox (λ ≈ 0.077). Se elige el log sobre Box-Cox por su interpretabilidad económica directa (coeficientes como elasticidades porcentuales) y por ser el estándar de oro en economía laboral desde Mincer (1974).

- **Uso sistemático de la mediana** como medida de tendencia central, en coherencia con el carácter asimétrico del salario y siguiendo la práctica estándar en estadísticas de ingresos (INE, Eurostat, OCDE).

- **Modelado segmentado por posición.** El análisis por posición revela que las features predictivas del salario son drásticamente distintas para porteros, defensas, mediocentros y delanteros. Esto motiva considerar modelos separados o interacciones `posición × stat` en la fase 06.

- **Auditoría crítica de los datos.** Se identificó y documentó un sesgo estructural en la fuente: `goalsPrevented` aparece replicada en jugadores de campo en algunos casos (notablemente en Premier League 22/23). Se corregirá en fase 05 forzando la variable a NaN para todas las posiciones distintas de portero.

- **Estrategia de validación temporal en ML.** *(Decisión abierta hasta fase 06.)* Se evaluarán dos esquemas:
  - **Opción A:** entrenar con 20/21 → 24/25 y aplicar sobre 25/26 para detectar desajustes de la temporada actual.
  - **Opción C:** train con 20/21 → 23/24, validación sobre 24/25 con métricas reales (RMSE, R², MAE), y aplicación final sobre 25/26.
  La opción C aporta mayor rigor estadístico al disponer de ground truth para validar.

- **Multi-fila por jugador en una misma temporada.** Los 524 casos de jugadores que cambiaron de liga a mitad de temporada se conservan tal cual en el dataset. La decisión sobre cómo agregarlos para el modelado se toma en la fase 05.

---

## 🛠️ Reproducibilidad

- **Python:** 3.13.2
- **Dependencias:** ver `requirements.txt`
- **Instalación:**
  ```bash
  git clone https://github.com/pablo29llori/TFM.git
  cd TFM
  pip install -r requirements.txt
  ```
- **Ejecución:** los notebooks están numerados por orden de ejecución dentro de `notebooks/`. Las rutas se resuelven con `pathlib` desde la raíz del proyecto, sin dependencias absolutas.

---

## 📅 Próximos pasos

1. **Redacción de la memoria LaTeX** en paralelo, documentando todo el trabajo realizado en las fases 01-04.
2. **Refrescar snapshots de la 25/26** hasta el cierre completo de las 6 ligas (finales de mayo / principios de junio).
3. **Reejecutar las fases 01–03** sobre los datos definitivos de la 25/26 cuando estén disponibles.
4. **Fase 05 — Feature engineering:** aplicar todas las decisiones acumuladas en el EDA.
5. **Fase 06 — Machine learning:** desarrollo de los modelos de regresión salarial y de similitud entre jugadores.
6. **Fase 07 — Aplicación Streamlit** integrando ambos modelos.
7. **Revisión final y entrega** de la memoria a mediados de julio.

---

## 📬 Contacto

**Pablo Llorián González** — [22574279@live.uem.es](mailto:22574279@live.uem.es)
Repositorio: [github.com/pablo29llori/TFM](https://github.com/pablo29llori/TFM)
