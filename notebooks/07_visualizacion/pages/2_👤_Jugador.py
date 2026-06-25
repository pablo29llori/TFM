import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(page_title="Ficha de jugador", page_icon="👤", layout="wide")

# ============ ESTILO VISUAL ============
from estilo import aplicar_estilo
aplicar_estilo()

ROOT = Path(__file__).resolve().parents[3]
FILT_PATH = ROOT / "data" / "clean" / "master_filtered.csv"
SAL_PATH = ROOT / "data" / "modeling" / "regression" / "salarios_predichos.csv"
ARQ_PATH = ROOT / "data" / "modeling" / "similarity" / "arquetipos.csv"

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
    try:
        sal = pd.read_csv(SAL_PATH, dtype={"season": str})
    except FileNotFoundError:
        sal = None
    try:
        arq = pd.read_csv(ARQ_PATH, dtype={"season": str})
    except FileNotFoundError:
        arq = None
    return df, sal, arq

df, sal, arq = cargar_datos()

def calcular_percentiles(jugador, df):
    pos = jugador["position"]
    stats = STATS_POR_POS.get(pos, {})
    sub = df[df["position"] == pos]
    mins = jugador["minutesPlayed"]
    etiquetas, valores = [], []
    for col, nombre in stats.items():
        if col not in df.columns:
            continue
        # Si el jugador no tiene el dato (p. ej. xG en temporadas <22/23), se omite la faceta
        if pd.isna(jugador[col]):
            continue
        if col in NO_PER90:
            serie = sub[col]; valor = jugador[col]
        else:
            serie = sub[col] / sub["minutesPlayed"] * 90
            valor = jugador[col] / mins * 90
        # Comparar solo contra jugadores que tienen el dato medido (excluye NaN)
        serie = serie.dropna()
        if len(serie) == 0:
            continue
        pct = (serie < valor).mean() * 100
        etiquetas.append(nombre); valores.append(round(pct))
    return etiquetas, valores

# ============ CABECERA ============
st.title("👤 Ficha de Jugador")
st.caption("Perfil estadístico detallado · percentiles respecto a su posición")

# ============ SELECTOR CON FILTROS ESTRICTOS (encadenados) ============
c1, c2, c3 = st.columns(3)
with c1:
    f_liga = st.multiselect("Liga", options=sorted(df["country"].dropna().unique()),
                            format_func=lambda x: LIGAS.get(x, x))

base = df.copy()
if f_liga:
    base = base[base["country"].isin(f_liga)]
with c2:
    temporadas = sorted(base["season"].unique(), reverse=True)
    f_temp = st.multiselect("Temporada", options=temporadas, format_func=fmt_temporada)

if f_temp:
    base = base[base["season"].isin(f_temp)]
with c3:
    f_equipo = st.multiselect("Equipo", options=sorted(base["team"].dropna().unique()))

if f_equipo:
    base = base[base["team"].isin(f_equipo)]

filtrada = base.sort_values(["player", "season"])
filtrada["etiqueta"] = (filtrada["player"] + " — " + filtrada["team"] +
                        " (" + filtrada["season"].map(fmt_temporada) + ")")

st.write(f"*{len(filtrada)} fichas disponibles con los filtros actuales*")

etiqueta_elegida = st.selectbox(
    "🔍 Selecciona un jugador:",
    options=filtrada["etiqueta"].tolist(),
    index=None,
    placeholder="Escribe para buscar..."
)

if etiqueta_elegida:
    jugador = filtrada[filtrada["etiqueta"] == etiqueta_elegida].iloc[0]

    st.divider()
    st.subheader(f"{EMOJI_POS.get(jugador['position'],'⚽')} {jugador['player']}")

    # Buscar el arquetipo del jugador
    arquetipo_txt = None
    if arq is not None:
        fila_arq = arq[(arq["player_id"] == jugador["player_id"]) &
                       (arq["season"] == jugador["season"])]
        if len(fila_arq) > 0:
            arquetipo_txt = fila_arq.iloc[0]["arquetipo"]

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Equipo", jugador["team"])
    m2.metric("Posición", POSICIONES.get(jugador["position"]))
    m3.metric("Edad", int(jugador["age"]))
    salv = jugador["gross_annual_eur"]
    m4.metric("Salario", f"{salv/1e6:.1f}M €" if pd.notna(salv) else "N/D")
    m5.metric("Temporada", fmt_temporada(jugador["season"]))

    # Arquetipo como etiqueta destacada (con espacio para verse entero)
    if arquetipo_txt:
        st.markdown(
            f"<div style='margin-top:0.8rem;'>"
            f"<span style='background:#40916c; color:white; padding:6px 16px; "
            f"border-radius:20px; font-weight:600; font-size:1rem;'>"
            f"🎭 Arquetipo: {arquetipo_txt}</span></div>",
            unsafe_allow_html=True
        )

    # --- Salario predicho (modelo de regresión) ---
    if sal is not None:
        fila_sal = sal[(sal["player_id"] == jugador["player_id"]) &
                       (sal["season"] == jugador["season"])]
        if len(fila_sal) > 0:
            pred = fila_sal.iloc[0]["salario_predicho"]
            real = fila_sal.iloc[0]["salario_real"]
            st.divider()
            st.markdown("##### 💶 Valoración salarial (modelo de regresión)")
            s1, s2, s3 = st.columns(3)
            s1.metric("Salario real", f"{real/1e6:.1f}M €")
            s2.metric("Salario estimado por rendimiento", f"{pred/1e6:.1f}M €")
            diff = (real - pred) / 1e6
            if diff > 0:
                s3.metric("Diferencia", f"+{diff:.1f}M €", "Cobra más de lo estimado", delta_color="inverse")
            else:
                s3.metric("Diferencia", f"{diff:.1f}M €", "Cobra menos de lo estimado", delta_color="inverse")
            st.caption("El salario estimado se basa solo en el rendimiento. Una diferencia positiva sugiere "
                       "que el jugador cobra por encima de lo que su rendimiento predice (y viceversa).")

    st.divider()
    col_radar, col_stats = st.columns([1.2, 1])
    with col_radar:
        st.markdown("##### Perfil de rendimiento (percentiles)")
        etiquetas, valores = calcular_percentiles(jugador, df)
        etiquetas_c = etiquetas + [etiquetas[0]]
        valores_c = valores + [valores[0]]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=valores_c, theta=etiquetas_c, fill="toself",
            fillcolor="rgba(64,145,108,0.4)", line=dict(color="#1b4332", width=2),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9))),
            showlegend=False, height=420, margin=dict(l=60, r=60, t=30, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Percentil respecto a todos los jugadores de su misma posición (todas las ligas y "
                   "temporadas). 100 = supera a todos · 50 = en la media")
    with col_stats:
        st.markdown("##### Facetas (percentil)")
        etiquetas, valores = calcular_percentiles(jugador, df)
        tabla_pct = pd.DataFrame({"Faceta": etiquetas, "Percentil": valores})
        st.dataframe(
            tabla_pct.style.background_gradient(subset=["Percentil"], cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True, hide_index=True
        )
        st.markdown("**Totales:**")
        tot = []
        for col, nombre in [("minutesPlayed","Minutos"),("appearances","Partidos"),
                            ("goals","Goles"),("assists","Asistencias"),("rating","Rating medio")]:
            if col in jugador and pd.notna(jugador[col]):
                val = int(jugador[col]) if col != "rating" else round(jugador[col], 2)
                tot.append(f"- **{nombre}:** {val}")
        st.markdown("\n".join(tot))

    if jugador["season"] == "2526":
        st.info("ℹ️ Los datos de la temporada 2025/26 están actualizados hasta el 28/04/2026.")
else:
    st.info("👆 Usa los filtros para encontrar un jugador y ver su ficha.")