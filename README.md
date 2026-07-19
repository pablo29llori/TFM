# TFM — Análisis del rendimiento y la valoración salarial de futbolistas mediante integración de datos y modelos de aprendizaje automático

> Trabajo Fin de Máster en Big Data
> **Autor:** Pablo Llorián González
> **Tutor:** Marcos Sergio Pacheco Dos Santos Lima Junior
> **Universidad:** Universidad Europea de Andalucía
> **Curso:** 2025/2026

---

## 📌 Resumen

Este TFM construye un *pipeline* completo de datos de fútbol que integra estadísticas de rendimiento con datos salariales de seis grandes ligas europeas (España, Inglaterra, Italia, Alemania, Francia y la Süper Lig turca) durante las 6 últimas temporadas (20/21 → 25/26). El objetivo final es aplicar técnicas de aprendizaje automático para **predecir salarios a partir del rendimiento** (detectando jugadores sobrevalorados e infravalorados), **identificar similitudes de estilo entre jugadores** y **descubrir arquetipos de jugador**, presentando los resultados en una plataforma interactiva.

La tabla maestra final integra **20.316 registros** correspondientes a **7.759 jugadores únicos** distribuidos en **171 equipos**, con una **cobertura salarial global del 91.3%**.

---

## 🎯 Objetivos

1. Construir una tabla maestra unificada con estadísticas de rendimiento + datos salariales de las 6 ligas durante 6 temporadas.
2. Entrenar un modelo de regresión que prediga el salario justo de un jugador en función de su rendimiento, y usar los residuos para identificar desajustes de mercado.
3. Construir un sistema de similitud entre jugadores que permita encontrar perfiles estadísticamente parecidos, útil para identificar reemplazos potenciales de jugadores sobrepagados.
4. Identificar arquetipos de jugador mediante *clustering* no supervisado, caracterizando los subtipos de estilo dentro de cada posición.
5. Desplegar los resultados en una aplicación interactiva con **Streamlit**.

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
│   ├── clean/               # Dataset analítico depurado (output fase 04 + filtros 05_01)
│   │   ├── master_clean.csv
│   │   └── master_filtered.csv
│   └── modeling/            # Datasets y artefactos por modelo (output fases 05 y 06)
│       ├── regression/      # regresion_dataset.csv + salarios_predichos.csv (artefacto 06_01)
│       └── similarity/      # similitud_outfielders.csv + similitud_keepers.csv + arquetipos.csv (artefacto 06_03)
└── notebooks/
    ├── 01_ingesta/          # Scraping desde Sofascore y Capology
    ├── 02_preprocesamiento/ # Limpieza técnica por fuente
    ├── 03_procesamiento/    # Integración (matching + merge) + tabla master única
    ├── 04_eda/              # Análisis exploratorio (5 notebooks)
    ├── 05_features_engineering/  # Feature engineering específico por modelo
    ├── 06_ml/               # Regresión salarial, similitud y arquetipos (3 notebooks)
    └── 07_visualizacion/    # Aplicación Streamlit (multipágina)
        ├── .streamlit/      #   config.toml: paleta base y tipografía
        ├── estilo.py        #   Estilo CSS común a todas las páginas
        ├── assets/          #   Logos de las competiciones
        ├── Inicio.py        #   Página principal
        └── pages/           #   Buscador, Jugador, Ligas, Clubes y Comparador
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

### 5. Feature engineering (`05_features_engineering/`)

Preparación de variables para el modelado. La fase se organiza en notebooks específicos por etapa, separando los filtros y limpiezas comunes (05_01) de los datasets específicos por modelo (05_02 para regresión, 05_03 para similitud).

- **`05_01_limpieza_y_filtros.ipynb`** — Aplicación de los filtros y limpiezas decididas en el EDA:
  - **Limpieza de `goalsPrevented`** para que sea estrictamente variable de portero (NaN para outfielders).
  - **Descarte del 8.6% de jugadores sin posición**: los 1.756 registros sin `position` asignada se eliminan. El análisis confirma que son jugadores marginales (mediana de 33 minutos y 2 apariciones), a los que Sofascore no asigna posición principal por falta de muestra. Crucialmente, el **100% de ellos carece de salario registrado** en Capology (sin ficha de primer equipo), por lo que su descarte no introduce sesgo en el modelo de regresión —ninguno tendría target— y el 93% tampoco superaría el filtro de minutos mínimos.
  - **Resolución del caso multi-liga**: para los 524 jugadores con dos filas en una misma temporada (cambio de liga en mercado de invierno), se conserva la fila con mayor `minutesPlayed`. Se descarta la agregación por la inconsistencia entre stats acumulables y ratios.
  - **Filtro de minutos**: se eliminan jugadores con menos de 450 minutos (5 partidos completos) para garantizar significancia estadística de las stats per-90 y reducir ruido.
  - Output: `data/clean/master_filtered.csv` — **14.202 filas × 121 columnas**, cobertura salarial del **99.9%**.

- **`05_02_features_regresion.ipynb`** — Construcción del dataset específico para el modelo de regresión salarial:
  - **Filtro del target**: solo filas con salario disponible (14.202 → 14.184 filas, cobertura 99.87%).
  - **Construcción del target**: `log_salary = log(gross_annual_eur)` siguiendo la decisión validada en el 04_02.
  - **Selección de features por cluster temático**: aplicación de los criterios derivados del clustering del 04_04 sobre el dataset filtrado. Estrategia de **núcleo informativo amplio**: se mantienen 2-3 variables representativas por cluster grande y se eliminan únicamente las redundancias evidentes (34 stats descartadas: 28 por correlación r ≥ 0.95 + 6 por baja cardinalidad informativa).
  - **Tratamiento de NaN estructurales**: `expectedGoals`, `expectedAssists` y `ballRecovery` no están disponibles en todas las temporadas (Sofascore las añadió progresivamente a partir de 22/23-23/24). Se imputan a 0 y se crean flags `*_available` para que los modelos basados en árboles puedan distinguir disponibilidad real de valor cero. Se descarta `outfielderBlocks` por cobertura inviable (solo 25/26 completa).
  - **Normalización per-90 minutos** sobre 61 stats acumulables. Se mantienen sin transformar los ratios, porcentajes, `rating` y `totwAppearances`.
  - **Edad**: se evaluó añadir `age_squared` (curva de Mincer) para capturar la concavidad de la relación edad-salario, pero finalmente se descartó por impacto despreciable en el R² y por dejar un ranking de importancia de variables más limpio. Se conserva `age` sin transformar.
  - **One-hot con baselines explícitas** para evitar multicolinealidad perfecta en modelos lineales: se codifican `position`, `country` y `season`, omitiendo una categoría de referencia por variable (`position_M`, `country_turkey`, `season_2021`). La elección permite que los coeficientes de las dummy restantes se interpreten como diferencias respecto a categorías "neutras" o de referencia económica/temporal.
  - **`nationality` se descarta como variable predictora**: el EDA (04_03/04_05) mostró que su relación con el salario es en gran medida espuria, ya que refleja sobre todo la liga en la que juega el futbolista (variable que el modelo ya recoge). Se conserva únicamente como metadato.
  - Output: `data/modeling/regression/regresion_dataset.csv` — **14.184 filas**, sin NaN ni infinitos, listo para entrenar. Las variables de histórico salarial (`salario_lag1`, `tendencia`) se incorporan en la fase de modelado (06_01).

- **`05_03_features_similitud.ipynb`** — Construcción de los datasets para el sistema de similitud entre jugadores. Las necesidades del FE divergen significativamente respecto al modelo de regresión, lo que justifica un notebook independiente:
  - **Sin filtro de salario**: las 14.202 filas se conservan completas. El universo de candidatos para sugerir reemplazos incluye canteranos, cesiones y jugadores sin ficha registrada en Capology.
  - **Variables contextuales excluidas del vector de similitud**: `country`, `season` y `nationality` no entran al cálculo. El objetivo es identificar similitud por *estilo de juego*, no por contexto de mercado. Se preservan `player`, `team`, `country`, `season`, `age` y `gross_annual_eur` como metadatos para permitir filtros post-consulta (p. ej. *"jugadores similares a X con edad ≤ 25"* o *"que jueguen en otra liga"*).
  - **Datasets separados outfielders / keepers**: las stats relevantes para porteros (saves, goalsPrevented, claims, runsOut...) y outfielders (goles, regates, pases clave...) son drásticamente distintas. Mezclarlos en un mismo espacio generaría ruido en las distancias.
  - **Selección de features específica por grupo**: ~50 features para outfielders cubriendo las 5 facetas del juego identificadas en el clustering del 04_04; ~24 features para keepers centradas en portería + pase desde portería.
  - **Tratamiento de NaN estructurales**: misma lógica que 05_02 (imputación a 0 en `expectedGoals`, `expectedAssists`, `ballRecovery`), sin flags (no aplican en cálculos de distancia).
  - **Normalización per-90 minutos** y **estandarización con `RobustScaler`** (mediana / IQR) antes del PCA, robusto a los outliers que generan las stats per-90 sobre minutos pequeños y coherente con el uso sistemático de la mediana en el resto del TFM.
  - **PCA con umbral del 85% de varianza explicada**: se generan **17 PCs para outfielders** y **13 PCs para keepers**. La reducción dimensional es necesaria para mitigar la maldición de la dimensionalidad en el k-NN posterior y para descorrelacionar los ejes (la distancia euclídea es más interpretable en el espacio PCA).
  - **Validación cualitativa**: la inspección manual de los top-N similares para jugadores conocidos confirma que el sistema captura correctamente el estilo de juego: Vinicius Jr. → Kvaratskhelia / Rafael Leão (extremos verticales); Lewandowski → Demirović / Joselu / Darwin Núñez (delanteros centro de área); Van Dijk → Jonny Evans / Willi Orbán (centrales sólidos); Kroos → Vitinha (mediocentros con pase). Para jugadores de élite, el **70-90% de los top-10 más similares vienen de ligas distintas** a la del consultado, validando que el sistema es genuinamente cross-liga.
  - Output: `data/modeling/similarity/similitud_outfielders.csv` (13.163 × 25) y `data/modeling/similarity/similitud_keepers.csv` (1.039 × 21).

### 6. Machine learning (`06_ml/`)

Tres notebooks complementarios que cubren un modelo supervisado y dos técnicas no supervisadas.

**a) Regresión salarial (`06_01_regresion_salarial.ipynb`).**
Predice `log(gross_annual_eur)` a partir de las features de rendimiento. El **residuo** (salario real − estimado) es el producto analítico: un residuo positivo señala posible sobrevaloración y uno negativo, infravaloración.
- **Validación:** partición **por jugador** — se reserva un 20% de los jugadores como conjunto de test (no interviene hasta la evaluación final) y sobre el resto se ajusta con **validación cruzada *GroupKFold* agrupada por `player_id`**. Así, todas las temporadas de un mismo futbolista caen siempre juntas y nunca se evalúa sobre alguien ya visto (evita *data leakage* por jugadores que repiten temporada).
- **Comparativa de modelos:** se comparan cuatro familias, dos lineales (Ridge, Lasso) y dos basadas en árboles (Random Forest, XGBoost), con resultados iniciales parecidos (R² ≈ 0.57). Se optimizan los hiperparámetros de **XGBoost** con **Optuna**, que se confirma como la mejor opción.
- **Global vs. segmentado:** se verifica empíricamente que un modelo **global** con la posición como *feature* iguala o supera a cuatro modelos independientes por posición, con mucha menos complejidad. Se adopta el modelo global.
- **Incorporación del histórico salarial (dos modelos):** el salto de calidad llega al añadir la trayectoria salarial del jugador mediante dos variables, `salario_lag1` (salario de la temporada anterior) y `tendencia` (evolución reciente). Como no todos los jugadores tienen año previo (debutantes, recién llegados de ligas no cubiertas), se adopta un **esquema de dos modelos**: *Modelo A* usa el histórico para quienes lo tienen y *Modelo B* recurre solo al rendimiento para el resto. Cada jugador se predice con el que le corresponde.
- **Resultados (conjunto de test):** el **modelo combinado alcanza R² ≈ 0.72** (MAE 0.45, RMSE 0.64), frente a **R² ≈ 0.59** del modelo basado solo en rendimiento (XGBoost) y **0.56** de la referencia lineal (Ridge). `salario_lag1` es, con diferencia, el predictor más influyente, seguido de la liga (Premier League) y de las métricas de rendimiento.
- **Interpretabilidad:** el modelo lineal de referencia (Ridge) confirma el *premium* de liga (`country_england` +) y la edad como uno de los coeficientes positivos destacados. La estimación se obtiene mediante validación cruzada (*out-of-fold*), de modo que el salario estimado de cada jugador procede de un modelo que nunca lo ha visto durante el entrenamiento.
- **Lectura del R²:** el modelo solo-rendimiento (≈ 0.59-0.60) mide de forma más honesta cuánto explica el rendimiento; buena parte del salto a 0.72 procede de la fuerte inercia del propio salario. El residuo (salario real − estimado) se interpreta como **señal de sobre/infravaloración, no como error**.
- **Artefacto exportado:** `data/modeling/regression/salarios_predichos.csv` (14.184 filas: `player_id`, `season`, salario real, estimado y residuo). El modelo de producción se reentrena con **todas las temporadas** antes de generar las predicciones, práctica estándar tras la validación.

**b) Similitud entre jugadores (`06_02_similitud.ipynb`).**
Sistema de recomendación que, dado un jugador, recupera los más parecidos por **búsqueda de vecinos más cercanos** (distancia euclídea sobre los vectores PCA del 05_03). Es el **núcleo de la plataforma**.
- **Matiz metodológico:** no es un modelo k-NN de predicción (no clasifica ni predice un valor) ni *clustering*; es recuperación de vecinos sobre un espacio aprendido. El componente de aprendizaje no supervisado reside en el **PCA**.
- **Universo de candidatos:** jugadores activos en 25/26 (descarta retirados), filtrados a la misma posición que el consultado.
- **Salario y ahorro potencial:** cada candidato se muestra con su salario real y el ahorro respecto al jugador de referencia, con filtros por edad, liga y "solo más baratos".
- **Validación cualitativa:** Pedri → Modrić / Barella / Vitinha; Lewandowski → Osimhen / Lautaro / Guirassy. Coherente futbolísticamente.

**c) Arquetipos de jugador (`06_03_arquetipos.ipynb`).**
*Clustering* **K-means por posición** sobre los vectores PCA, que descubre subtipos de estilo. A diferencia de la búsqueda de vecinos, K-means **sí aprende un modelo** (los centroides), reforzando el componente no supervisado del TFM.
- **Por qué por posición:** un *clustering* global se limita a reproducir la posición ya conocida (verificado empíricamente); segmentando emergen subtipos con valor informativo.
- **K=2 por posición (seis arquetipos).** El número de grupos se decide analizando el coeficiente de silueta no solo en su valor medio, sino en la calidad de cada grupo por separado (`silhouette_samples`). K=3 introduce siempre un grupo de baja calidad con muchos jugadores mal asignados, mientras que K=2 produce agrupaciones limpias y equilibradas. La asignación de nombres se hace leyendo el perfil de stats de cada *cluster* (no su número, que no es determinista).
- **Arquetipos resultantes:** defensas (Central de área, Defensa lateral), mediocentros (Medio creativo, Medio de contención) y delanteros (Rematador de área, Atacante asociativo). Validación: Lewandowski → Rematador de área; Vinicius → Atacante asociativo; Pedri/Rodri → Medio creativo.
- **Hallazgo:** los arquetipos más ofensivos y creativos concentran los salarios medios más altos dentro de cada posición.
- **Visualización** del espacio de estilo coloreado por arquetipo, proyectado en 2D (PCA).
- **Artefacto exportado:** `data/modeling/similarity/arquetipos.csv` (14.202 filas: `player_id`, `season`, `position`, `arquetipo`).

En conjunto, el TFM emplea **tres técnicas no supervisadas** con propósitos distintos: PCA (representación), búsqueda de vecinos (recomendación) y K-means (tipología); además del modelo supervisado de regresión.

### 7. Visualización (`07_visualizacion/`)

Aplicación interactiva **multipágina** en **Streamlit** (`streamlit run Inicio.py`) que integra todos los modelos. Consume los artefactos generados en la fase 06 sin recalcular nada. Cinco secciones:

- **🏠 Inicio** — presentación del TFM, competiciones analizadas y créditos.
- **🔍 Buscador de reemplazos** — núcleo de la plataforma: selecciona un jugador (con filtros encadenados posición/liga/equipo) y obtiene los más similares activos en 25/26, con salario real y ahorro potencial. Filtros de la búsqueda por rango de edad, salario inferior y liga.
- **👤 Ficha de jugador** — datos, arquetipo, valoración salarial (real vs. estimado por el modelo), radar de percentiles por faceta (adaptado a la posición y calculado respecto a todos los jugadores de esa posición) y totales de la temporada. Permite cualquier jugador-temporada histórico.
- **🏆 Análisis por liga** — resumen agregado de la competición, rankings configurables de jugadores (totales o per-90) y evolución del salario medio real vs. estimado a lo largo de las temporadas.
- **🏟️ Análisis por club** — resumen de plantilla y tabla completa con salario real vs. estimado por jugador.
- **⚔️ Comparador** — dos jugadores de la misma posición enfrentados en un radar superpuesto y tabla comparativa de percentiles.

Detalles de diseño: tema visual centralizado en un único módulo (`estilo.py`) aplicado a todas las páginas, más un `config.toml` que fija la paleta base (verde césped moderno) y la tipografía (Inter); contenedor en tarjeta flotante, métricas como mini-tarjetas y barra lateral oscura. Otras correcciones: normalización de nombres de equipo inconsistentes entre temporadas (p. ej. "FC Barcelona" → "Barcelona", único renombrado real detectado por solapamiento de plantilla), filtros estrictos encadenados, nota del corte de datos del 28/04/2026 en las vistas de la temporada en curso, y manejo de las estadísticas no disponibles en todas las temporadas (los *expected goals/assists* solo existen desde 22/23): los percentiles se calculan únicamente contra jugadores con el dato medido y los rankings por liga ocultan esas métricas en las temporadas sin datos.

---

## ✅ Estado de avance

| Fase | Estado | Notas |
|---|---|---|
| 01 · Ingesta | ✅ Completo | Snapshot 28/04/2026 adoptado como definitivo para la 25/26 (bloqueo anti-bot de Sofascore) |
| 02 · Preprocesamiento | ✅ Completo | |
| 03 · Procesamiento | ✅ Completo | 25/26 fijada al snapshot del 28/04/2026 |
| 04 · EDA | ✅ Completo | 5 notebooks temáticos + `master_clean.csv` generado |
| 05 · Feature engineering | ✅ Completo | 05_01, 05_02 y 05_03 generan los datasets para regresión y similitud |
| 06 · Machine learning | ✅ Completo | Regresión (XGBoost + histórico, R² ≈ 0.72), similitud y arquetipos (K=2) + artefactos exportados |
| 07 · Visualización (Streamlit) | ✅ Completo | Plataforma multipágina con 5 secciones |
| Memoria LaTeX | ✅ Prácticamente completa | Redacción finalizada; en revisión final del tutor antes del depósito |

### 📊 Métricas clave del dataset

**Pipeline de tablas:**

| Tabla | Filas | Columnas | Origen |
|---|---:|---:|---|
| `master_total.csv` | 20.316 | 122 | Output fase 03 (integración cruda) |
| `master_clean.csv` | 20.307 | 121 | Output fase 04 (post-EDA, depurado) |
| `master_filtered.csv` | 14.202 | 121 | Output 05_01 (filtros y multi-liga resuelto) |
| `regresion_dataset.csv` | 14.184 | 110 | Output 05_02 (FE específico para regresión) |
| `similitud_outfielders.csv` | 13.163 | 25 | Output 05_03 (8 metadatos + 17 PCs) |
| `similitud_keepers.csv` | 1.039 | 21 | Output 05_03 (8 metadatos + 13 PCs) |
| `salarios_predichos.csv` | 14.184 | 5 | Artefacto 06_01 (real, estimado y residuo) |
| `arquetipos.csv` | 14.202 | 4 | Artefacto 06_03 (arquetipo por jugador-temporada) |

**Métricas globales:**

| Métrica | Valor |
|---|---|
| Jugadores únicos (`player_id`) | 7.759 |
| Equipos únicos | 171 |
| Cobertura salarial global (`master_clean`) | 91.3% |
| Cobertura por liga × temporada | 82.6% – 97.3% |
| Cobertura tras filtros (`master_filtered`) | 99.9% |
| Variables stats numéricas originales | 110 |
| Stats tras selección por cluster (regresión) | 61 (per-90) + 16 estructurales |
| Dimensión intrínseca (PCA, 80% var.) | ~22 componentes |

---

## 🧠 Decisiones metodológicas clave

- **Snapshot definitivo de la 25/26 (28/04/2026).** La temporada en curso se trabajó inicialmente con *snapshots* fechados. Al intentar refrescarla, Sofascore activó una protección anti-bot (HTTP 403 *challenge*, detección de navegador no de IP) que impidió nuevas descargas pese a múltiples vías (VPN, navegador *headed*, reinstalación de la librería). Se adoptó como **dato definitivo el snapshot del 28/04/2026** (~92% de temporada disputada; los salarios anuales de Capology son fijos y el filtro de ≥450 min se supera sobradamente). Es una limitación documentada: las vistas de la 25/26 en la plataforma indican explícitamente el corte de datos.

- **Fuzzy matching escalonado con revisión manual.** Prioriza minimizar falsos positivos: por defecto solo se aceptan matches con score ≥ 0.90. Los rangos inferiores requieren confirmación explícita en listas blancas (`ACCEPT_LOW_FUZZY`, `ACCEPT_VERY_LOW_FUZZY`) y los casos imposibles para el fuzzy se resuelven con `MANUAL_MATCHES` explícitos.

- **Modelado del target en escala logarítmica.** La distribución salarial es fuertemente log-normal (skewness +6, kurtosis +74). La transformación `log(salario)` reduce ambas a valores próximos a cero (γ₁ = −0.30, γ₂ = +0.08), cercanos al óptimo absoluto identificado por Box-Cox (λ ≈ 0.077). Se elige el log sobre Box-Cox por su interpretabilidad económica directa (coeficientes como elasticidades porcentuales) y por ser el estándar de oro en economía laboral desde Mincer (1974).

- **Uso sistemático de la mediana** como medida de tendencia central, en coherencia con el carácter asimétrico del salario y siguiendo la práctica estándar en estadísticas de ingresos (INE, Eurostat, OCDE).

- **Modelo global con la posición como *feature* (no segmentado).** Aunque el EDA revela que las features predictivas del salario difieren por posición, se verificó empíricamente en la fase 06 que un único modelo global con la posición codificada iguala o supera a cuatro modelos independientes por posición: segmentar hace que cada modelo pierda los patrones comunes entre posiciones. Se adopta el modelo global.

- **Auditoría crítica de los datos.** Se identificó y documentó un sesgo estructural en la fuente: `goalsPrevented` aparece replicada en jugadores de campo en algunos casos (notablemente en Premier League 22/23). Corregido en 05_01 forzando la variable a NaN para todas las posiciones distintas de portero.

- **Filtro de exposición mínima (≥ 450 minutos).** Equivalente a 5 partidos completos. Por debajo de este umbral, las stats per-90 se vuelven inestables (un solo gol en 90 minutos da una tasa per-90 de 1.0, dominando la métrica). Decisión aplicada en 05_01: 14.202 filas conservadas con cobertura salarial del 99.9%, frente al 91.3% del dataset crudo.

- **Resolución del caso multi-liga por máximos minutos.** Los 524 jugadores con dos filas en una misma temporada (traspasos en mercado invernal entre ligas distintas) se reducen a una sola fila — la del club donde acumularon más minutos. Se descartó la agregación porque las stats acumulables (goles, pases) y los ratios (% acierto pase, rating) requieren tratamientos contradictorios.

- **Selección de features por cluster temático con núcleo informativo amplio.** Aplicada en 05_02. Se mantienen 2-3 variables representativas por cluster grande del 04_04 y se eliminan las redundancias críticas (34 stats descartadas). Estrategia coherente con el uso previsto de modelos basados en árboles (XGBoost, RF), que toleran multicolinealidad moderada. Para el modelo de similitud (05_03) se aplicará una reducción más agresiva.

- **Tratamiento de NaN estructurales con flags de disponibilidad.** Las stats `expectedGoals`, `expectedAssists` y `ballRecovery` no están disponibles uniformemente en todas las temporadas (Sofascore las incorporó progresivamente). En lugar de descartarlas o imputar con la mediana (que introduciría señal artificial), se imputan a 0 y se crean flags binarias `*_available`. Los modelos basados en árboles pueden aprender patrones diferenciados según la disponibilidad real del dato.

- **One-hot con baselines explícitas.** Aplicado en 05_02. Para evitar multicolinealidad perfecta en modelos lineales (cuando las dummy de una categórica suman 1, la matriz de diseño no tiene rango completo), se omite una categoría de referencia por variable: `position_M` (mediocampistas, categoría más frecuente), `country_turkey` (liga económicamente más débil, sirve como baseline para leer las demás como "premium sobre Turquía") y `season_2021` (primera temporada, los coeficientes capturan inflación acumulada).

- **`nationality` y `age_squared` descartadas como predictoras.** La nacionalidad refleja sobre todo la liga en la que juega el futbolista (relación espuria que la variable de liga ya captura), y `age_squared` aportaba una mejora despreciable en R² a costa de enturbiar el ranking de importancia. Ambas decisiones, alineadas con la revisión del tutor, simplifican el modelo sin coste predictivo.

- **Normalización per-90 minutos.** Estándar en analítica futbolística. Se aplica a todas las stats acumulables (goles, asistencias, pases, tiros, regates, tackles, etc.) para hacer comparables a jugadores con distintos minutos jugados. Los ratios y porcentajes ya están normalizados por construcción y se mantienen sin transformar.

- **Datasets separados por familia de posición para similitud.** Aplicado en 05_03. Se construyen dos espacios de similitud independientes: outfielders (D/M/F) y keepers. Las stats que caracterizan el rendimiento son drásticamente distintas (un portero tiene 50+ saves/temporada y 0 goles; un delantero al revés), por lo que mezclarlos en un mismo espacio de distancias generaría comparaciones absurdas. Dentro de outfielders sí se mantienen D, M y F juntos: comparten muchas más stats relevantes entre sí (pase, regate, duelos) y separar más reduciría excesivamente el tamaño de cada subconjunto.

- **Reducción dimensional por PCA para similitud.** Aplicado en 05_03. La similitud por k-NN sufre con la maldición de la dimensionalidad: en espacios de >50 variables las distancias se igualan y el sistema pierde discriminación. Se aplica PCA con umbral del 85% de varianza explicada, lo que reduce el espacio a 17 componentes para outfielders y 13 para keepers. Adicionalmente, el PCA descorrelaciona los ejes, por lo que la distancia euclídea sobre los PCs tiene una interpretación más limpia que sobre el espacio original con multicolinealidad residual.

- **`RobustScaler` antes de PCA en lugar de `StandardScaler`.** Aplicado en 05_03. Las stats per-90 generan outliers extremos por construcción (jugadores con pocos minutos pero muchos eventos puntuales). `StandardScaler` (media/σ) sería sensible a estos outliers y comprimiría artificialmente el rango del resto del dataset. `RobustScaler` (mediana/IQR) es robusto a colas pesadas y coherente con el uso sistemático de la mediana en el resto del proyecto.

- **Variables contextuales excluidas en similitud, mantenidas en regresión.** Decisión consciente y deliberada para que cada modelo capture lo que debe: la regresión necesita aprender el premium de liga e inflación temporal (que son señal real); la similitud quiere encontrar parecidos por estilo de juego, no por liga o temporada de juego (en este caso eso sería ruido). Las variables `country`, `season` y `nationality` se preservan como metadatos del dataset de similitud para permitir filtros post-consulta.

- **Estrategia de validación: partición por jugador (test 20% + GroupKFold).** Se reserva un 20% de los jugadores como conjunto de test y sobre el resto se ajusta con **validación cruzada GroupKFold agrupada por `player_id`**, siguiendo la indicación del tutor de que un mismo jugador no aparezca en varios conjuntos del *split*. Esto evita el *data leakage* derivado de jugadores que repiten a lo largo de las temporadas y proporciona una estimación honesta. El modelo combinado (con histórico) alcanza **R² ≈ 0.72** sobre el test, frente a ≈ 0.59 del modelo basado solo en rendimiento. El modelo de producción que alimenta la plataforma se reentrena después con todos los datos disponibles, práctica estándar una vez validado el modelo.

- **Dos usos del modelo de regresión (evaluación vs. producción).** La evaluación honesta se hace con GroupKFold por jugador (mide la capacidad predictiva). El modelo de producción, una vez validado, se reentrena con **todas las temporadas** (incluida la 25/26) antes de generar `salarios_predichos.csv`, para que las estimaciones de la temporada actual —las más relevantes para la herramienta— sean representativas y no extrapoladas.

- **Residuo como producto, no como error.** Por la compresión del modelo hacia la media (limitada por la ausencia de variables como valor de mercado o marca), las estrellas caras tienden a aparecer como "sobrevaloradas". Esto se asume conscientemente: el residuo se interpreta como **señal de desajuste de mercado**, y por ello el **núcleo de la plataforma es el sistema de similitud** (robusto y sin ese sesgo), quedando la regresión como capa complementaria.

- **Tres técnicas no supervisadas con propósitos distintos.** PCA para la representación (espacio de estilo), búsqueda de vecinos más cercanos para la recomendación de reemplazos, y K-means para la tipología (arquetipos por posición). La búsqueda de vecinos no es un k-NN predictivo ni *clustering*: es recuperación sobre el espacio aprendido por PCA.

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

## 📅 Estado y próximos pasos

El *pipeline* de datos y modelado (fases 01–06), la plataforma (fase 07) y la memoria están completos. El trabajo restante se centra en la entrega y la defensa:

1. **Depósito de la memoria** para la revisión final del tutor (fecha límite: 20 de julio; margen para ajustes hasta el 24 de julio).
2. **Preparación de la defensa**, apoyándose en la plataforma interactiva como demostración.

---

## 📬 Contacto

**Pablo Llorián González** — [22574279@live.uem.es](mailto:22574279@live.uem.es)
Repositorio: [github.com/pablo29llori/TFM](https://github.com/pablo29llori/TFM)
