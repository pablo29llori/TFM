import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(page_title="Comparador", page_icon="⚔️", layout="wide")

# ============ ESTILO VISUAL ============
from estilo import aplicar_estilo
aplicar_estilo()

ROOT = Path(__file__).resolve().parents[3]
FILT_PATH = ROOT / "data" / "clean" / "master_filtered.csv"

POSICIONES = {"K": "Portero", "D": "Defensa", "M": "Centrocampista", "F": "Delantero"}
EMOJI_POS = {"K": "🧤", "D": "🛡️", "M": "🎯", "F": "⚡"}
LIGAS = {
    "spain": "LaLiga", "england": "Premier League", "italy": "Serie A",
    "germany": "Bundesliga", "france": "Ligue 1", "turkey": "Süper Lig",
}
TEAM_FIX = {"FC Barcelona": "Barcelona"}

def fmt_temporada(s):
    s = str(s)
    return f"20{s[:2]}/{s[2:]}"

STATS_POR_POS = {
    "F": {"goals": "Goles", "expectedGoals": "xG", "assists": "Asistencias",
          "keyPasses": "Pases clave", "successfulDribbles": "Regates", "aerialDuelsWon": "Duelos aéreos"},
    "M": {"assists": "Asistencias", "keyPasses": "Pases clave", "accuratePasses": "Pases acertados",
          "successfulDribbles": "Regates", "tackles": "Entradas", "interceptions": "Intercepciones"},
    "D": {"tackles": "Entradas", "interceptions": "Intercepciones", "clearances": "Despejes",
          "aerialDuelsWon": "Duelos aéreos", "accuratePasses": "Pases acertados", "keyPasses": "Pases clave"},
    "K": {"saves": "Paradas", "cleanSheet": "Porterías a 0", "goalsPrevented": "Goles evitados",
          "accuratePasses": "Pases acertados", "rating": "Rating", "aerialDuelsWon": "Duelos aéreos"},
}
NO_PER90 = {"rating", "cleanSheet"}

@st.cache_data
def cargar_datos():
    df = pd.read_csv(FILT_PATH, dtype={"season": str})
    df["team"] = df["team"].replace(TEAM_FIX)
    return df

df = cargar_datos()

def calcular_percentiles(jugador, df):
    pos = jugador["position"]
    stats = STATS_POR_POS.get(pos, {})
    sub = df[df["position"] == pos]
    mins = jugador["minutesPlayed"]
    etiquetas, valores = [], []
    for col, nombre in stats.items():
        if col not in df.columns:
            continue
        if pd.isna(jugador[col]):
            continue
        if col in NO_PER90:
            serie = sub[col]; valor = jugador[col]
        else:
            serie = sub[col] / sub["minutesPlayed"] * 90
            valor = jugador[col] / mins * 90
        serie = serie.dropna()
        if len(serie) == 0:
            continue
        pct = (serie < valor).mean() * 100
        etiquetas.append(nombre); valores.append(round(pct))
    return etiquetas, valores

def selector_jugador(df, etiqueta_col, key):
    """Devuelve la fila del jugador seleccionado mediante filtros encadenados."""
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        liga = st.selectbox("Liga", options=sorted(df["country"].dropna().unique()),
                            format_func=lambda x: LIGAS.get(x, x), key=f"liga_{key}")
    base = df[df["country"] == liga]
    with cc2:
        temp = st.selectbox("Temporada", options=sorted(base["season"].unique(), reverse=True),
                           format_func=fmt_temporada, key=f"temp_{key}")
    base = base[base["season"] == temp]
    with cc3:
        equipo = st.selectbox("Equipo", options=sorted(base["team"].dropna().unique()),
                             key=f"equipo_{key}")
    base = base[base["team"] == equipo]
    base = base.sort_values("player").copy()
    base["etiqueta"] = base["player"] + " — " + base["team"]
    elegido = st.selectbox("Jugador", options=base["etiqueta"].tolist(), index=None,
                           placeholder="Escribe para buscar...", key=f"jug_{key}")
    if elegido:
        return base[base["etiqueta"] == elegido].iloc[0]
    return None

# ============ CABECERA ============
st.title("⚔️ Comparador de Jugadores")
st.caption("Compara los perfiles de rendimiento de dos jugadores de la misma posición")

# ============ SELECTORES ============
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("##### 🔵 Jugador A")
    jug_a = selector_jugador(df, "etiqueta", "A")
with col_b:
    st.markdown("##### 🔴 Jugador B")
    jug_b = selector_jugador(df, "etiqueta", "B")

if jug_a is not None and jug_b is not None:
    # Comprobar misma posición
    if jug_a["position"] != jug_b["position"]:
        st.warning(f"⚠️ Los jugadores son de posiciones distintas "
                   f"({POSICIONES.get(jug_a['position'])} vs {POSICIONES.get(jug_b['position'])}). "
                   f"Para una comparación válida, elige dos jugadores de la misma posición.")
    else:
        st.divider()
        # Tarjetas comparativas
        col1, col2 = st.columns(2)
        for col, jug, color, emoji in [(col1, jug_a, "🔵", "A"), (col2, jug_b, "🔴", "B")]:
            with col:
                st.markdown(f"### {color} {jug['player']}")
                st.markdown(f"**{jug['team']}** · {POSICIONES.get(jug['position'])} · "
                           f"{int(jug['age'])} años · {fmt_temporada(jug['season'])}")
                salv = jug["gross_annual_eur"]
                st.markdown(f"💰 Salario: **{salv/1e6:.1f}M €**" if pd.notna(salv) else "💰 Salario: N/D")

        # Radar superpuesto
        st.divider()
        st.markdown("##### Comparación de perfiles (percentiles)")
        et_a, val_a = calcular_percentiles(jug_a, df)
        et_b, val_b = calcular_percentiles(jug_b, df)

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=val_a + [val_a[0]], theta=et_a + [et_a[0]], fill="toself",
            fillcolor="rgba(52,152,219,0.3)", line=dict(color="#2980b9", width=2),
            name=jug_a["player"]))
        fig.add_trace(go.Scatterpolar(
            r=val_b + [val_b[0]], theta=et_b + [et_b[0]], fill="toself",
            fillcolor="rgba(231,76,60,0.3)", line=dict(color="#c0392b", width=2),
            name=jug_b["player"]))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9))),
            showlegend=True, height=480, margin=dict(l=60, r=60, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabla comparativa
        st.markdown("##### Detalle por faceta")
        comp = pd.DataFrame({
            "Faceta": et_a,
            jug_a["player"]: val_a,
            jug_b["player"]: val_b,
        })
        st.dataframe(
            comp.style.background_gradient(subset=[jug_a["player"], jug_b["player"]],
                                           cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True, hide_index=True
        )
        st.caption("Valores en percentil respecto a todos los jugadores de su posición. "
                   "Más alto = mejor en esa faceta.")
else:
    st.info("👆 Selecciona dos jugadores para comparar sus perfiles.")