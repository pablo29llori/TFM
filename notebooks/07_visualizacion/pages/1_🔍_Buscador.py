import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics.pairwise import euclidean_distances

st.set_page_config(page_title="TFM - Scouting de futbolistas", page_icon="⚽", layout="wide")

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
h1 {
    color: #1b4332;
    border-bottom: 4px solid #40916c;
    padding-bottom: 0.3rem;
}
/* Permitir que el texto de las métricas se ajuste en varias líneas */
[data-testid="stMetricValue"] {
    white-space: normal;
    overflow-wrap: break-word;
    font-size: 1.6rem;
    line-height: 1.2;
}
[data-testid="stMetricLabel"] {
    white-space: normal;
}
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "data" / "modeling" / "similarity"

POSICIONES = {"K": "Portero", "D": "Defensa", "M": "Centrocampista", "F": "Delantero"}
EMOJI_POS = {"K": "🧤", "D": "🛡️", "M": "🎯", "F": "⚡"}
LIGAS = {
    "spain": "LaLiga", "england": "Premier League", "italy": "Serie A",
    "germany": "Bundesliga", "france": "Ligue 1", "turkey": "Süper Lig",
}
# Normalización de nombres de equipo inconsistentes entre temporadas
# (el snapshot 25/26 nombra al Barça "FC Barcelona"; el resto del histórico, "Barcelona")
TEAM_FIX = {"FC Barcelona": "Barcelona"}

def fmt_temporada(s):
    s = str(s)
    return f"20{s[:2]}/{s[2:]}"

@st.cache_data
def cargar_datos():
    of = pd.read_csv(SIM_DIR / "similitud_outfielders.csv")
    gk = pd.read_csv(SIM_DIR / "similitud_keepers.csv")
    of["team"] = of["team"].replace(TEAM_FIX)
    gk["team"] = gk["team"].replace(TEAM_FIX)
    return of, gk

of, gk = cargar_datos()
PCS_OF = [c for c in of.columns if c.startswith("PC")]
PCS_GK = [c for c in gk.columns if c.startswith("PC")]
of_cand = of[of["season"] == 2526].reset_index(drop=True)
gk_cand = gk[gk["season"] == 2526].reset_index(drop=True)

def buscar_similares(player_id, top_n=10, solo_mas_baratos=False, min_edad=None, max_edad=None, ligas=None):
    for df_full, df_cand, pcs in [(of, of_cand, PCS_OF), (gk, gk_cand, PCS_GK)]:
        m = df_full[df_full["player_id"] == player_id]
        if len(m) > 0:
            break
    if len(m) == 0:
        return None, None
    ref = m.sort_values("season").iloc[-1]
    cand = df_cand[(df_cand["position"] == ref["position"]) &
                   (df_cand["player_id"] != ref["player_id"])].copy()
    vec_ref = ref[pcs].values.reshape(1, -1).astype(float)
    cand["distancia"] = euclidean_distances(vec_ref, cand[pcs].values.astype(float)).flatten()
    sal_ref = ref["gross_annual_eur"]
    cand["ahorro_M"] = (sal_ref - cand["gross_annual_eur"]) / 1e6
    if solo_mas_baratos and pd.notna(sal_ref):
        cand = cand[cand["gross_annual_eur"] < sal_ref]
    if min_edad is not None:
        cand = cand[cand["age"] >= min_edad]
    if max_edad is not None:
        cand = cand[cand["age"] <= max_edad]
    if ligas:
        cand = cand[cand["country"].isin(ligas)]
    cand = cand.sort_values("distancia").head(top_n)
    return ref, cand

# Lista base: última temporada de cada jugador
todos = pd.concat([of, gk], ignore_index=True)
ultima = todos.sort_values("season").groupby("player_id", as_index=False).last()
ultima = ultima.sort_values("player")

# ============ CABECERA ============
st.title("🔍 Buscador de Reemplazos")
st.caption("Encuentra jugadores de perfil similar y menor coste para cualquier futbolista")

# ============ BÚSQUEDA + FILTROS QUE LA COMPLEMENTAN ============
st.subheader("1️⃣ Encuentra tu jugador")

colf1, colf2, colf3 = st.columns(3)
with colf1:
    f_pos = st.multiselect("Filtrar por posición",
        options=list(POSICIONES.keys()), format_func=lambda x: POSICIONES[x])
with colf2:
    f_liga = st.multiselect("Filtrar por liga",
        options=sorted(todos["country"].dropna().unique()),
        format_func=lambda x: LIGAS.get(x, x))

# Los equipos disponibles dependen de la liga elegida
if f_liga:
    equipos_disponibles = sorted(ultima[ultima["country"].isin(f_liga)]["team"].dropna().unique())
else:
    equipos_disponibles = sorted(ultima["team"].dropna().unique())

with colf3:
    f_equipo = st.multiselect("Filtrar por equipo", options=equipos_disponibles)

# Aplicar los filtros a la lista de jugadores seleccionables
filtrada = ultima.copy()
if f_pos:
    filtrada = filtrada[filtrada["position"].isin(f_pos)]
if f_liga:
    filtrada = filtrada[filtrada["country"].isin(f_liga)]
if f_equipo:
    filtrada = filtrada[filtrada["team"].isin(f_equipo)]

filtrada["etiqueta"] = filtrada["player"] + " — " + filtrada["team"] + " (" + filtrada["position"].map(POSICIONES) + ")"

st.write(f"*{len(filtrada)} jugadores disponibles con los filtros actuales*")

etiqueta_elegida = st.selectbox(
    "🔍 Selecciona el jugador:",
    options=filtrada["etiqueta"].tolist(),
    index=None,
    placeholder="Escribe para buscar..."
)

if etiqueta_elegida:
    jugador = filtrada[filtrada["etiqueta"] == etiqueta_elegida].iloc[0]
    pid = jugador["player_id"]

    st.divider()
    st.subheader(f"{EMOJI_POS.get(jugador['position'],'⚽')} {jugador['player']}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Equipo", jugador["team"])
    c2.metric("Posición", POSICIONES.get(jugador["position"]))
    c3.metric("Edad", int(jugador["age"]))
    sal = jugador["gross_annual_eur"]
    c4.metric("Salario", f"{sal/1e6:.1f}M €" if pd.notna(sal) else "N/D")
    c5.metric("Temporada", fmt_temporada(jugador["season"]))

    # Filtros de la BÚSQUEDA DE SIMILARES
    st.divider()
    st.subheader("2️⃣ Ajusta la búsqueda de reemplazos")
    with st.expander("⚙️ Opciones de búsqueda", expanded=True):
        g1, g2, g3 = st.columns(3)
        with g1:
            solo_baratos = st.checkbox("💰 Solo más baratos", value=True)
            top_n = st.slider("Nº de resultados", 5, 20, 10)
        with g2:
            rango_edad = st.slider("Rango de edad del reemplazo", 16, 40, (16, 40))
        with g3:
            ligas_sel = st.multiselect("Ligas del reemplazo (vacío = todas)",
                options=sorted(todos["country"].dropna().unique()),
                format_func=lambda x: LIGAS.get(x, x))

    if st.button("🔎 Buscar reemplazos", type="primary", use_container_width=True):
        ref, similares = buscar_similares(
            pid, top_n=top_n, solo_mas_baratos=solo_baratos,
            min_edad=rango_edad[0], max_edad=rango_edad[1],
            ligas=ligas_sel if ligas_sel else None
        )
        if similares is None or len(similares) == 0:
            st.warning("No se encontraron jugadores con esos filtros. Prueba a relajarlos.")
        else:
            st.subheader(f"🎯 {len(similares)} reemplazos similares a {ref['player']}")

            # Leyenda: barra de degradado continuo (igual escala que la tabla)
            st.markdown("""
            <div style="margin-bottom:0.8rem;">
                <div style="height:18px; border-radius:5px; border:1px solid #ccc;
                     background: linear-gradient(to right,
                         #a50026, #d73027, #f46d43, #fdae61, #fee08b,
                         #ffffbf,
                         #d9ef8b, #a6d96a, #66bd63, #1a9850, #006837);">
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-top:2px;">
                    <span>← Más caro</span>
                    <span>Salario similar</span>
                    <span>Más barato →</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            tabla = similares[["player", "team", "country", "age",
                               "gross_annual_eur", "ahorro_M"]].copy()
            tabla["country"] = tabla["country"].map(lambda x: LIGAS.get(x, x))
            tabla["age"] = tabla["age"].astype(int)
            tabla["gross_annual_eur"] = (tabla["gross_annual_eur"] / 1e6).round(1)
            tabla["ahorro_M"] = tabla["ahorro_M"].round(1)
            tabla.columns = ["Jugador", "Equipo", "Liga", "Edad", "Salario (M€)", "Ahorro (M€)"]
            st.dataframe(
                tabla.style
                    .background_gradient(subset=["Ahorro (M€)"], cmap="RdYlGn")
                    .format({"Salario (M€)": "{:.1f}", "Ahorro (M€)": "{:.1f}", "Edad": "{:d}"}),
                use_container_width=True, hide_index=True
            )
else:
    st.info("👆 Usa los filtros de arriba para acotar y selecciona un jugador.")