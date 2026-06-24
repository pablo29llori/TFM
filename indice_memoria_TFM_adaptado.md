# Índice de la memoria — TFM adaptado

> **Análisis del rendimiento y la valoración salarial de futbolistas mediante integración de datos y modelos de aprendizaje automático**
> Pablo Llorián González · Máster en Big Data · Universidad Europea de Andalucía

---

## Nota sobre la adaptación

Este índice respeta **íntegramente la estructura oficial** de la plantilla de la universidad (capítulos 1–8, bibliografía y anexos). La única adaptación es la **reorganización interna del capítulo 4 (Desarrollo del proyecto)**: dado que el proyecto se compone de un pipeline de datos con 7 fases técnicas diferenciadas, se elevan estas fases a subsecciones de primer nivel dentro del desarrollo en lugar de concentrarlas en un único epígrafe 4.2. Esto mejora la legibilidad y la navegación sin alterar el esqueleto de la plantilla.

---

## 1. RESUMEN DEL PROYECTO

- **1.1. Contexto y justificación**
  El mercado salarial del fútbol profesional y la frecuente desconexión entre rendimiento deportivo y remuneración. Oportunidad de un enfoque basado en datos.
- **1.2. Planteamiento del problema**
  ¿Es posible estimar el salario esperado de un futbolista a partir de su rendimiento y, a partir de ahí, detectar jugadores sobre/infravalorados y proponer alternativas de perfil similar?
- **1.3. Objetivos del proyecto**
  Síntesis de los objetivos (desarrollados en el capítulo 3).
- **1.4. Resultados obtenidos**
  *(Se redacta al final)* Métricas de los modelos, validación y casos de uso de la plataforma.
- **1.5. Estructura de la memoria**
  Mapa de los capítulos.

## 2. ANTECEDENTES / ESTADO DEL ARTE

- **2.1. Estado del arte**
  Analítica deportiva moderna (métricas avanzadas: xG, xA). Modelos de valoración de jugadores existentes (Transfermarkt, CIES Football Observatory). Modelos de salario en economía laboral (ecuación de Mincer). Trabajos previos de machine learning aplicado a la valoración de futbolistas.
- **2.2. Contexto y justificación**
  Carácter diferencial del proyecto: integración de rendimiento + salario real en 6 ligas y 6 temporadas, con doble enfoque (regresión + similitud).
- **2.3. Planteamiento del problema**
  Formulación técnica del problema y preguntas de investigación.

## 3. OBJETIVOS

- **3.1. Objetivos generales**
  Construcción de una plataforma de análisis de valoración salarial basada en rendimiento.
- **3.2. Objetivos específicos**
  Ingesta multi-fuente; integración y limpieza; análisis exploratorio; modelo de regresión salarial; sistema de similitud entre jugadores; despliegue interactivo.
- **3.3. Beneficios del proyecto**
  Utilidad para clubes (scouting y negociación), agentes, analistas y aficionados.

## 4. DESARROLLO DEL PROYECTO

- **4.1. Planificación y metodología**
  Metodología de trabajo iterativa por fases. Cronograma. Control de versiones (GitHub). Entorno de trabajo.

- **4.2. Arquitectura de la solución**
  Visión global del pipeline (diagrama de las 7 fases). Flujo de datos desde la ingesta hasta el despliegue. Herramientas y tecnologías empleadas (Python, ScraperFC, pandas, scikit-learn, Streamlit).

- **4.3. Ingesta de datos** *(Fase 01)*
  Fuentes: Sofascore (rendimiento) y Capology (salarios). Scraping con ScraperFC. Estrategia de snapshots para la temporada en curso. *Incidencia y decisión sobre el bloqueo del scraper (anti-bot) y adopción del snapshot del 28/04 como dato definitivo de la 25/26.*

- **4.4. Preprocesamiento e integración** *(Fases 02–03)*
  Limpieza técnica por fuente. Estrategia de matching en cascada (normalización, TEAM_MAP, fuzzy matching escalonado con rapidfuzz, matches manuales). Construcción de la tabla maestra unificada. Cobertura salarial obtenida.

- **4.5. Análisis exploratorio de datos (EDA)** *(Fase 04)*
  Análisis del target salarial (log-normalidad, transformación logarítmica). Análisis de variables categóricas (posición, edad, nacionalidad; curva de Mincer). Análisis de correlaciones y redundancia (clustering jerárquico, PCA exploratorio). Relación rendimiento-salario por posición. Auditoría de calidad de datos (caso `goalsPrevented`).

- **4.6. Feature engineering** *(Fase 05)*
  Filtros y limpiezas (minutos mínimos, resolución multi-liga). Dataset de regresión (target logarítmico, normalización per-90, codificación con baselines, tratamiento de NaN estructurales). Dataset de similitud (exclusión de variables contextuales, segmentación por posición, reducción dimensional con PCA y RobustScaler).

- **4.7. Modelado y evaluación** *(Fase 06)*
  - Regresión salarial (supervisado): modelos baseline (Ridge/Lasso) y de árbol (Random Forest, XGBoost). Estrategia de validación temporal. Modelado segmentado por posición. Métricas y selección de modelo.
  - Similitud entre jugadores (no supervisado): k-NN sobre los vectores PCA. Validación cualitativa.
  - Integración de ambos modelos: detección de desajustes y propuesta de alternativas.

- **4.8. Despliegue: plataforma interactiva** *(Fase 07)*
  Diseño e implementación de la aplicación Streamlit. Funcionalidades. Arquitectura de la app.

- **4.9. Recursos requeridos**
  Lenguajes, librerías, fuentes de datos, hardware, herramientas (GitHub, Overleaf).

- **4.10. Presupuesto**
  Estimación de costes del proyecto (horas de desarrollo, infraestructura, coste hipotético de datos/APIs en un escenario productivo).

- **4.11. Viabilidad**
  Viabilidad técnica (demostrada por la implementación). Viabilidad legal (datos públicos, términos de servicio de las fuentes, consideraciones sobre datos personales de jugadores). Viabilidad económica.

- **4.12. Resultados del proyecto**
  Métricas finales de los modelos de regresión. Resultados del sistema de similitud. Casos de uso concretos (ejemplos de jugadores sobre/infravalorados detectados y reemplazos propuestos).

## 5. DISCUSIÓN

Interpretación crítica de los resultados. ¿Qué calidad tiene la predicción salarial? ¿Los residuos identifican casos reales conocidos del mercado? Limitaciones del estudio: snapshot de la temporada en curso, cobertura salarial parcial, sesgos del fuzzy matching, ausencia del valor de mercado como variable. Comparación con expectativas y con el estado del arte.

## 6. CONCLUSIONES

- **6.1. Conclusiones del trabajo**
  Grado de cumplimiento de los objetivos. Hallazgos principales. Aportaciones del proyecto.
- **6.2. Conclusiones personales**
  Aprendizajes, dificultades superadas (p. ej. la resolución de incidencias técnicas como el bloqueo del scraper), competencias adquiridas.

## 7. FUTURAS LÍNEAS DE TRABAJO

Incorporación de datos en tiempo real. Ampliación a más ligas y temporadas. Integración del valor de mercado (Transfermarkt) como variable o segundo target. Modelos de evolución temporal del jugador. Asistente conversacional (bot vía API) sobre la plataforma.

## Bibliografía

Referencias académicas (Mincer, analítica deportiva), documentación técnica (ScraperFC, scikit-learn, Streamlit) y fuentes de datos.

## 8. ANEXOS

Diccionario completo de variables. Tablas extensas (cobertura por liga-temporada, listados de matches manuales). Capturas de la plataforma Streamlit. Fragmentos de código relevantes. Enlace al repositorio.

---

## Resumen de la adaptación para comentar con Marcos

| Capítulo | Plantilla original | Adaptación propuesta |
|---|---|---|
| 1, 2, 3 | Sin cambios | Sin cambios |
| **4** | 4.1–4.6 (todo el técnico en 4.2) | **4.1–4.12**: cada fase del pipeline como subsección propia |
| 5, 6, 7 | Sin cambios | Sin cambios |
| Bibliografía, Anexos | Sin cambios | Sin cambios |

**Puntos a validar con el tutor:**
1. ¿Acepta la reorganización del capítulo 4 o prefiere ceñirse a 4.1–4.6 con subniveles más profundos?
2. Ubicación del EDA: propuesto dentro del desarrollo (4.5). ¿De acuerdo?
3. Resultados (4.12) separados de la discusión crítica (cap. 5). ¿De acuerdo?
4. Enfoque de "Presupuesto" (4.10) y "Viabilidad" (4.11) en un proyecto de análisis de datos (no de producto comercial).
