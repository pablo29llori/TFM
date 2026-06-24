import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(page_title="Ligas", page_icon="🏆", layout="wide")

# ============ ESTILO VISUAL ============
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
[data-testid="stMetricValue"] {
    white-space: normal; overflow-wrap: break-word;
    font-size: 1.6rem; line-height: 1.2;
}
[data-testid="stMetricLabel"] { white-space: normal; }
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).resolve().parents[3]
FILT_PATH = ROOT / "data" / "clean" / "master_filtered.csv"
SAL_PATH = ROOT / "data" / "modeling" / "regression" / "salarios_predichos.csv"

LIGAS = {
    "spain": "LaLiga", "england": "Premier League", "italy": "Serie A",
    "germany": "Bundesliga", "france": "Ligue 1", "turkey": "Süper Lig",
}
TEAM_FIX = {"FC Barcelona": "Barcelona"}

def fmt_temporada(s):
    s = str(s)
    return f"20{s[:2]}/{s[2:]}"

RANKINGS = {
    "goals": "Goles", "assists": "Asistencias", "expectedGoals": "Goles esperados (xG)",
    "keyPasses": "Pases clave", "successfulDribbles": "Regates completados",
    "tackles": "Entradas", "interceptions": "Intercepciones", "rating": "Rating medio",
}
NO_PER90 = {"rating"}

@st.cache_data
def cargar_datos():
    df = pd.read_csv(FILT_PATH, dtype={"season": str})
    df["team"] = df["team"].replace(TEAM_FIX)
    try:
        sal = pd.read_csv(SAL_PATH, dtype={"season": str})
        sal = sal.merge(df[["player_id", "season", "country", "team"]],
                        on=["player_id", "season"], how="left")
    except FileNotFoundError:
        sal = None
    return df, sal

df, sal = cargar_datos()

# ============ CABECERA ============
st.title("🏆 Análisis por Liga")
st.caption("Resumen de la competición y rankings de jugadores")

# ============ FILTROS ============
c1, c2 = st.columns(2)
with c1:
    liga = st.selectbox("Liga", options=sorted(df["country"].dropna().unique()),
                        format_func=lambda x: LIGAS.get(x, x))
with c2:
    temps = sorted(df[df["country"] == liga]["season"].unique(), reverse=True)
    temp = st.selectbox("Temporada", options=temps, format_func=fmt_temporada)

sub = df[(df["country"] == liga) & (df["season"] == temp)].copy()

st.divider()

# ============ RESUMEN AGREGADO ============
st.subheader(f"📊 {LIGAS.get(liga, liga)} · {fmt_temporada(temp)}")

r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Equipos", sub["team"].nunique())
r2.metric("Jugadores", len(sub))
r3.metric("Goles totales", int(sub["goals"].sum()))
gasto = sub["gross_annual_eur"].sum()
r4.metric("Gasto salarial", f"{gasto/1e6:.0f}M €" if pd.notna(gasto) else "N/D")
r5.metric("Rating medio", f"{sub['rating'].mean():.2f}")

if temp == "2526":
    st.info("ℹ️ Los datos de la temporada 2025/26 están actualizados hasta el 28/04/2026.")

st.divider()

# ============ RANKINGS ============
st.subheader("🥇 Rankings de jugadores")

cr1, cr2, cr3 = st.columns([2, 2, 1])
with cr1:
    metrica = st.selectbox("Estadística", options=list(RANKINGS.keys()),
                           format_func=lambda x: RANKINGS[x])
with cr2:
    modo = st.radio("Modo", ["Totales", "Por 90 min"], horizontal=True)
with cr3:
    top_n = st.number_input("Top", min_value=5, max_value=30, value=10, step=5)

tabla = sub.copy()
es_per90 = (modo == "Por 90 min") and (metrica not in NO_PER90)

if es_per90:
    tabla = tabla[tabla["minutesPlayed"] >= 900]
    tabla["valor"] = tabla[metrica] / tabla["minutesPlayed"] * 90
    nota_modo = "por 90 min · mínimo 900 minutos jugados"
else:
    tabla["valor"] = tabla[metrica]
    nota_modo = "totales de la temporada" if metrica not in NO_PER90 else "media de la temporada"

ranking = tabla.nlargest(int(top_n), "valor")[
    ["player", "team", "position", "valor", metrica, "minutesPlayed"]
].copy()
ranking.insert(0, "#", range(1, len(ranking) + 1))

ranking_display = ranking[["#", "player", "team", "position", "valor"]].copy()
ranking_display.columns = ["#", "Jugador", "Equipo", "Pos.", RANKINGS[metrica]]

lleva_decimales = es_per90 or (metrica in NO_PER90)
if lleva_decimales:
    ranking_display[RANKINGS[metrica]] = ranking_display[RANKINGS[metrica]].round(2)
    fmt = {RANKINGS[metrica]: "{:.2f}"}
else:
    ranking_display[RANKINGS[metrica]] = ranking_display[RANKINGS[metrica]].astype(int)
    fmt = {RANKINGS[metrica]: "{:d}"}

st.caption(f"{RANKINGS[metrica]} · {nota_modo}")
st.dataframe(
    ranking_display.style.background_gradient(
        subset=[RANKINGS[metrica]], cmap="Greens"
    ).format(fmt),
    use_container_width=True, hide_index=True, height=(len(ranking_display) + 1) * 35 + 3
)

# ============ EVOLUCIÓN SALARIAL: REAL VS PREDICHO ============
st.divider()
st.subheader("💶 Evolución salarial: real vs estimado")

if sal is None:
    st.warning("No se encontró `salarios_predichos.csv`. Genera el artefacto desde el notebook 06_01.")
else:
    e1, e2 = st.columns(2)
    with e1:
        ev_pais = st.selectbox("País", options=sorted(sal["country"].dropna().unique()),
                               format_func=lambda x: LIGAS.get(x, x), key="ev_pais")
    with e2:
        equipos_pais = ["(Toda la liga)"] + sorted(
            sal[sal["country"] == ev_pais]["team"].dropna().unique())
        ev_equipo = st.selectbox("Equipo (opcional)", options=equipos_pais, key="ev_equipo")

    # Filtrar
    ev = sal[sal["country"] == ev_pais].copy()
    titulo_ambito = LIGAS.get(ev_pais, ev_pais)
    if ev_equipo != "(Toda la liga)":
        ev = ev[ev["team"] == ev_equipo]
        titulo_ambito = ev_equipo

    # Agregar por temporada (media por jugador)
    eserie = ev.groupby("season").agg(
        real=("salario_real", "mean"),
        pred=("salario_predicho", "mean"),
    ).reset_index().sort_values("season")
    eserie["temp_label"] = eserie["season"].map(fmt_temporada)

    # Gráfica de líneas
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=eserie["temp_label"], y=eserie["real"] / 1e6, mode="lines+markers",
        name="Salario real", line=dict(color="#1b4332", width=3), marker=dict(size=8)))
    fig.add_trace(go.Scatter(
        x=eserie["temp_label"], y=eserie["pred"] / 1e6, mode="lines+markers",
        name="Salario estimado", line=dict(color="#e76f51", width=3, dash="dash"), marker=dict(size=8)))
    fig.update_layout(
        height=400, margin=dict(l=40, r=40, t=40, b=40),
        yaxis_title="Salario medio (M€)", xaxis_title="Temporada",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.markdown(f"**{titulo_ambito}** · salario medio por jugador")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("La línea continua es el salario real medio (Capology); la discontinua, el estimado por el "
               "modelo. Cuando el real supera al estimado, el ámbito paga por encima de lo que su "
               "rendimiento predice.")