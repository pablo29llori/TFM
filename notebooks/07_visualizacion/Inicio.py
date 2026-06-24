import streamlit as st
from pathlib import Path

st.set_page_config(page_title="TFM - Plataforma de futbolistas", page_icon="⚽", layout="wide")



# --- Estilo visual ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(160deg, #d8f3dc 0%, #b7e4c7 50%, #95d5b2 100%);
}
.main .block-container {
    background-color: rgba(255, 255, 255, 0.92);
    border-radius: 18px;
    padding: 2rem 2.5rem;
    margin-top: 1rem;
}
h1 { color: #1b4332; border-bottom: 4px solid #40916c; padding-bottom: 0.3rem; }
.creditos {
    text-align: center; color: #40916c; font-size: 0.9rem;
    margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #b7e4c7;
}
</style>
""", unsafe_allow_html=True)

# ============ TÍTULO ============
st.title("⚽ Plataforma de Análisis de Futbolistas")
st.markdown("#### Análisis del rendimiento y la valoración salarial de futbolistas mediante integración de datos y modelos de aprendizaje automático")
st.caption("Trabajo de Fin de Máster · Máster en Big Data · Universidad Europea de Andalucía")

st.divider()

# ============ LIGAS ============
st.markdown("##### Competiciones analizadas")

ASSETS = Path(__file__).resolve().parent / "assets"
logos = [
    ("laliga.png", "LaLiga"),
    ("premier.png", "Premier League"),
    ("seriea.png", "Serie A"),
    ("bundesliga.png", "Bundesliga"),
    ("ligue1.png", "Ligue 1"),
    ("superlig.png", "Süper Lig"),
]

cols = st.columns(6)
for col, (archivo, nombre) in zip(cols, logos):
    ruta = ASSETS / archivo
    with col:
        if ruta.exists():
            st.image(str(ruta), use_container_width=True)
            st.markdown(f"<p style='text-align:center; font-weight:600; color:#1b4332; margin-top:0.3rem;'>{nombre}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='text-align:center;'>⚠️<br>{nombre}</p>", unsafe_allow_html=True)

st.divider()

# ============ DESCRIPCIÓN ============
st.markdown("""
Bienvenido a la plataforma de análisis de rendimiento y valoración salarial de futbolistas.
Usa el **menú de la izquierda** para navegar entre las secciones:

- **🔍 Buscador** — Encuentra reemplazos de perfil similar y menor coste para cualquier jugador.
- **👤 Jugador** — Ficha detallada con las estadísticas de un jugador.
- **🏆 Ligas** — Rankings y mejores jugadores por liga.
- **🏟️ Clubes** — Resumen de plantilla y gasto salarial por club.
""")

st.caption("Datos: Sofascore (rendimiento) y Capology (salarios) · Temporadas 2020/21 a 2025/26")

# ============ CRÉDITOS ============
st.markdown("""
<div class="creditos">
    Desarrollado por <b>Pablo Llorián González</b><br>
    Tutor: Marcos Sergio Pacheco Dos Santos Lima Junior · 2026
</div>
""", unsafe_allow_html=True)