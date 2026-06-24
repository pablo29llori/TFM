import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Clubes", page_icon="🏟️", layout="wide")

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

POSICIONES = {"K": "Portero", "D": "Defensa", "M": "Centrocampista", "F": "Delantero"}
LIGAS = {
    "spain": "LaLiga", "england": "Premier League", "italy": "Serie A",
    "germany": "Bundesliga", "france": "Ligue 1", "turkey": "Süper Lig",
}
TEAM_FIX = {"FC Barcelona": "Barcelona"}
ORDEN_POS = {"K": 0, "D": 1, "M": 2, "F": 3}

def fmt_temporada(s):
    s = str(s)
    return f"20{s[:2]}/{s[2:]}"

@st.cache_data
def cargar_datos():
    df = pd.read_csv(FILT_PATH, dtype={"season": str})
    df["team"] = df["team"].replace(TEAM_FIX)
    try:
        sal = pd.read_csv(SAL_PATH, dtype={"season": str})
    except FileNotFoundError:
        sal = None
    return df, sal

df, sal = cargar_datos()

# ============ CABECERA ============
st.title("🏟️ Análisis por Club")
st.caption("Resumen de plantilla y valoración salarial")

# ============ FILTROS ENCADENADOS ============
c1, c2, c3 = st.columns(3)
with c1:
    liga = st.selectbox("Liga", options=sorted(df["country"].dropna().unique()),
                        format_func=lambda x: LIGAS.get(x, x))
with c2:
    temps = sorted(df[df["country"] == liga]["season"].unique(), reverse=True)
    temp = st.selectbox("Temporada", options=temps, format_func=fmt_temporada)
with c3:
    equipos = sorted(df[(df["country"] == liga) & (df["season"] == temp)]["team"].dropna().unique())
    club = st.selectbox("Club", options=equipos)

# Subconjunto del club + temporada
sub = df[(df["team"] == club) & (df["season"] == temp)].copy()

st.divider()

# ============ RESUMEN DEL CLUB ============
st.subheader(f"🏟️ {club} · {fmt_temporada(temp)}")

r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Jugadores", len(sub))
r2.metric("Edad media", f"{sub['age'].mean():.1f}")
gasto = sub["gross_annual_eur"].sum()
r3.metric("Gasto salarial", f"{gasto/1e6:.0f}M €" if pd.notna(gasto) else "N/D")
r4.metric("Goles", int(sub["goals"].sum()))
r5.metric("Rating medio", f"{sub['rating'].mean():.2f}")

if temp == "2526":
    st.info("ℹ️ Los datos de la temporada 2025/26 están actualizados hasta el 28/04/2026.")

st.divider()

# ============ PLANTILLA: REAL VS PREDICHO ============
st.subheader("👥 Plantilla")

# Cruzar con salarios predichos
plantilla = sub[["player", "position", "age", "gross_annual_eur"]].copy()
if sal is not None:
    plantilla = plantilla.merge(
        sub[["player_id"]].assign(player_id=sub["player_id"]).reset_index(drop=True),
        left_index=True, right_index=True, how="left"
    )
    plantilla = sub[["player", "position", "age", "gross_annual_eur", "player_id"]].copy()
    plantilla = plantilla.merge(
        sal[(sal["season"] == temp)][["player_id", "salario_predicho"]],
        on="player_id", how="left"
    )
else:
    plantilla["salario_predicho"] = np.nan

# Ordenar por posición (K, D, M, F) y dentro por salario
plantilla["_orden"] = plantilla["position"].map(ORDEN_POS)
plantilla = plantilla.sort_values(["_orden", "gross_annual_eur"], ascending=[True, False])

# Preparar tabla para mostrar
tabla = plantilla[["player", "position", "age", "gross_annual_eur", "salario_predicho"]].copy()
tabla["position"] = tabla["position"].map(POSICIONES)
tabla["age"] = tabla["age"].astype(int)
tabla["dif"] = (tabla["gross_annual_eur"] - tabla["salario_predicho"]) / 1e6
tabla["gross_annual_eur"] = (tabla["gross_annual_eur"] / 1e6).round(1)
tabla["salario_predicho"] = (tabla["salario_predicho"] / 1e6).round(1)
tabla["dif"] = tabla["dif"].round(1)
tabla.columns = ["Jugador", "Posición", "Edad", "Salario real (M€)", "Salario estimado (M€)", "Diferencia (M€)"]

st.dataframe(
    tabla.style
        .background_gradient(subset=["Diferencia (M€)"], cmap="RdYlGn_r")
        .format({"Salario real (M€)": "{:.1f}", "Salario estimado (M€)": "{:.1f}",
                 "Diferencia (M€)": "{:+.1f}", "Edad": "{:d}"}),
    use_container_width=True, hide_index=True,
    height=(len(tabla) + 1) * 35 + 3
)
st.caption("Diferencia = salario real − estimado. Positivo (rojo) = cobra más de lo que su rendimiento "
           "predice · Negativo (verde) = cobra menos. El estimado procede del modelo de regresión.")