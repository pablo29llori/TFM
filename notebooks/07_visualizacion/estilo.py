import streamlit as st

def aplicar_estilo():
    """Aplica el estilo visual común a todas las páginas de la plataforma."""
    st.markdown("""
    <style>
    /* ===== Tipografía e importación ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ===== Fondo general ===== */
    .stApp {
        background:
            radial-gradient(circle at 20% 15%, rgba(45,106,79,0.08) 0%, transparent 40%),
            radial-gradient(circle at 85% 80%, rgba(45,106,79,0.06) 0%, transparent 45%),
            linear-gradient(180deg, #f4faf6 0%, #eaf4ee 100%);
    }

    /* ===== Contenedor principal: tarjeta flotante ===== */
    .main .block-container {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 2.5rem 3rem;
        margin-top: 1.5rem;
        box-shadow: 0 4px 24px rgba(27,67,50,0.08);
        border: 1px solid rgba(45,106,79,0.10);
    }

    /* ===== Títulos ===== */
    h1 {
        color: #1b4332;
        font-weight: 800;
        letter-spacing: -0.02em;
        border-bottom: 3px solid #52b788;
        padding-bottom: 0.4rem;
    }
    h2, h3 {
        color: #2d6a4f;
        font-weight: 700;
        letter-spacing: -0.01em;
    }

    /* ===== Métricas como mini-tarjetas ===== */
    [data-testid="stMetric"] {
        background: #f4faf6;
        border: 1px solid rgba(45,106,79,0.12);
        border-radius: 12px;
        padding: 0.8rem 1rem;
    }
    [data-testid="stMetricValue"] {
        white-space: normal !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        font-size: 1.3rem;
        line-height: 1.25;
        color: #1b4332;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        white-space: normal;
        color: #52796f;
        font-weight: 600;
    }

    /* ===== Botones ===== */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
        transition: transform 0.1s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(45,106,79,0.25);
    }

    /* ===== Barra lateral ===== */
    [data-testid="stSidebar"] {
        background-color: #1b4332;
    }
    [data-testid="stSidebar"] * {
        color: #d8f3dc !important;
    }

    /* ===== Pestañas/expanders más suaves ===== */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #2d6a4f;
    }
    </style>
    """, unsafe_allow_html=True)