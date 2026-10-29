import hashlib
import hmac
import html
import math
import os
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import altair as alt
import gspread
import pandas as pd
import streamlit as st
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------- Marca (logo de Sofia Gauna)
MARCA_NOMBRE = "Sofia Gauna"
MARCA_SUB = "NUTRIÓLOGA"
CARPETA_APP = os.path.dirname(os.path.abspath(__file__))


def ruta_imagen(nombre: str) -> str:
    """Busca la imagen en assets/ o junto a app.py (por si se subió sin carpeta)."""
    for carpeta in (os.path.join(CARPETA_APP, "assets"), CARPETA_APP):
        ruta = os.path.join(carpeta, nombre)
        if os.path.exists(ruta):
            return ruta
    return ""


ICONO = ruta_imagen("icono.png")
HOJA_BLANCA = ruta_imagen("hoja_blanca.png")

st.set_page_config(
    page_title=f"{MARCA_NOMBRE} · Nutrióloga",
    page_icon=ICONO or "🌿",
    layout="wide" if st.session_state.get("admin") else "centered",
)


def hoja_svg(tam: int = 48, grosor: float = 1.6) -> str:
    """La hoja del logo como imagen (Streamlit limpia los <svg> sueltos dentro de st.html)."""
    import base64

    color = "#CFE6D5" if st.session_state.get("oscuro") else "#2F4A34"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="{color}" '
        f'stroke-width="{grosor}" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M32 6 C48 16 52 38 32 58 C12 38 16 16 32 6 Z"/><path d="M32 14 L32 62"/>'
        '<path d="M32 28 L41 21"/><path d="M32 38 L23 31"/><path d="M32 47 L42 40"/></svg>'
    )
    datos = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{datos}" width="{tam}" height="{tam}" alt="">'



def logo_vertical() -> str:
    return (
        f'<div class="marca">{hoja_svg(64)}<div class="m-nombre">{MARCA_NOMBRE}</div>'
        f'<div class="m-linea"></div><div class="m-sub">{MARCA_SUB}</div></div>'
    )


def logo_horizontal() -> str:
    return (
        f'<div class="marca-h">{hoja_svg(38, 1.8)}<div class="m-div"></div>'
        f'<div><div class="m-nombre">{MARCA_NOMBRE}</div><div class="m-sub">{MARCA_SUB}</div></div></div>'
    )

# Paleta: cremas y verdes suaves
CREMA = "#F1E9DA"
CREMA_2 = "#E2ECE3"
BORDE = "#D8E5DA"
SALVIA = "#7FA88A"
VERDE = "#5E8B6C"
VERDE_OSC = "#36594A"
VERDE_CLARO = "#E5EFE2"
TEXTO = "#33433A"

ESTILO = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Lora:wght@500;600;700&family=Cormorant+Garamond:wght@500&family=Montserrat:wght@500&display=swap');

html, body, .stApp, p, label, li, input, textarea, button, [data-testid="stMarkdownContainer"] {{
  font-family: 'Nunito', sans-serif;
}}
.stApp {{ background: {CREMA}; color: {TEXTO}; }}
h1, h2, h3 {{ font-family: 'Lora', serif !important; color: {VERDE_OSC} !important; letter-spacing: -.3px; }}
h1 {{ font-size: 2.1rem !important; }}
h3 {{ font-size: 1.25rem !important; margin-top: .6rem; }}
.block-container {{ max-width: 780px; padding-top: 4.2rem; padding-bottom: 4rem; }}
header[data-testid="stHeader"] {{ background: transparent; }}
footer {{ visibility: hidden; }}

/* Pestañas como botones redondeados */
[data-baseweb="tab-list"] {{
  background: {CREMA_2}; border-radius: 999px; padding: 5px; gap: 4px;
  overflow-x: auto; scrollbar-width: none;
}}
[data-baseweb="tab-list"]::-webkit-scrollbar {{ display: none; }}
button[data-baseweb="tab"] {{
  border-radius: 999px !important; padding: 8px 16px !important; height: auto !important;
  background: transparent; color: {TEXTO}; white-space: nowrap;
}}
button[data-baseweb="tab"] p {{ font-weight: 700; font-size: .95rem; }}
button[data-baseweb="tab"][aria-selected="true"] {{
  background: #fff !important; color: {VERDE_OSC} !important;
  box-shadow: 0 2px 8px rgba(54, 89, 74, .12);
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{ display: none !important; }}
[data-baseweb="tab-panel"] {{ padding-top: 1.1rem; }}

/* Botones */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {{
  border-radius: 999px; font-weight: 700; padding: .55rem 1.3rem;
  border: 1px solid {BORDE}; background: #fff; color: {VERDE_OSC};
  transition: all .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {{
  background: {VERDE_CLARO}; border-color: {SALVIA}; color: {VERDE_OSC};
}}
button[kind="primary"], button[kind="primaryFormSubmit"] {{
  background: {VERDE} !important; border-color: {VERDE} !important; color: #fff !important;
}}
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {{
  background: {VERDE_OSC} !important; border-color: {VERDE_OSC} !important;
}}

/* Campos: 16px evita que el celular haga zoom al tocarlos */
input, textarea, [data-baseweb="select"] div {{ font-size: 16px !important; }}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {{
  border-radius: 12px !important; background: #fff !important;
}}

/* Tarjetas */
[data-testid="stForm"] {{
  background: #fff; border: 1px solid {BORDE}; border-radius: 20px; padding: 1.3rem;
  box-shadow: 0 4px 18px rgba(54, 89, 74, .06);
}}
[data-testid="stMetric"] {{
  background: #fff; border: 1px solid {BORDE}; border-radius: 18px; padding: 14px 16px;
  box-shadow: 0 2px 10px rgba(54, 89, 74, .05);
}}
[data-testid="stMetricLabel"] p {{ font-weight: 700; color: {VERDE}; }}
[data-testid="stMetricValue"] {{ font-family: 'Lora', serif; color: {VERDE_OSC}; }}
[data-testid="stExpander"] details {{ background: #fff; border-radius: 16px; border-color: {BORDE}; }}
[data-testid="stAlert"] {{ border-radius: 14px; }}
.stVegaLiteChart, [data-testid="stVegaLiteChart"] {{
  background: #fff; border: 1px solid {BORDE}; border-radius: 18px; padding: 10px;
}}

/* Bloques propios */
.hero {{ text-align: center; margin: .5rem 0 1.4rem; }}
.hero .logo {{
  width: 84px; height: 84px; margin: 0 auto 10px; border-radius: 50%;
  background: {VERDE_CLARO}; display: flex; align-items: center; justify-content: center;
  font-size: 42px; box-shadow: 0 0 0 8px {CREMA_2};
}}
.hero h1 {{ margin: 0; padding: 0; }}
.hero p {{ color: #6b7a70; margin: .3rem 0 0; font-size: 1.02rem; }}
.saludo {{
  background: linear-gradient(135deg, #FFFFFF 0%, {VERDE_CLARO} 100%);
  border: 1px solid {BORDE}; border-radius: 22px; padding: 18px 20px; margin-bottom: 1rem;
}}
.saludo .s-hola {{ font-family: 'Lora', serif; font-size: 1.7rem; font-weight: 700; color: {VERDE_OSC}; }}
.saludo .s-sub {{ color: #5f6f64; margin-top: 2px; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
.chip {{
  background: #fff; border: 1px solid {BORDE}; border-radius: 999px; padding: 6px 12px;
  font-size: .9rem; color: {VERDE_OSC}; font-weight: 600;
}}
.vacio {{
  text-align: center; background: #fff; border: 1px dashed {BORDE}; border-radius: 18px;
  padding: 26px 16px; color: #6b7a70;
}}
.vacio .icono {{ font-size: 34px; }}

@media (max-width: 640px) {{
  .block-container {{ padding: 3.8rem .9rem 3rem; }}
  h1 {{ font-size: 1.7rem !important; }}
  .saludo .s-hola {{ font-size: 1.45rem; }}
  button[data-baseweb="tab"] {{ padding: 7px 12px !important; }}
}}
</style>"""
st.html(ESTILO)


def vacio(icono: str, texto: str):
    st.html(f'<div class="vacio"><div class="icono">{icono}</div>{html.escape(texto)}</div>')

CSS_EXTRA = """<style>
[class*="st-key-tarjeta_"] {
  background:#fff; border:1px solid #D8E5DA; border-left:6px solid #B5D3BC; border-radius:16px;
  padding:12px 14px 4px; box-shadow:0 2px 10px rgba(54,89,74,.06); gap:.25rem;
}
[class*="st-key-tarjeta_ok_"] { background:#F1F8F0; border-left-color:#5E8B6C; }
.t-com { font-size:12px; font-weight:800; color:#5E8B6C; letter-spacing:1px; text-transform:uppercase;
  display:flex; justify-content:space-between; align-items:center; gap:8px; }
.t-com .kc { background:#E5EFE2; color:#36594A; border-radius:999px; padding:2px 9px; font-size:11px;
  letter-spacing:.3px; white-space:nowrap; }
.t-body { font-size:15px; color:#33433A; line-height:1.4; margin-top:4px; }
.t-body .m-tit { font-family:'Lora',serif; font-weight:700; color:#36594A; text-transform:uppercase;
  font-size:16px; margin:2px 0 4px; }
.t-body .m-sep { border-top:1px solid #E8EEE5; margin:7px 0; }
.t-hecho { text-decoration: line-through; opacity:.55; }
.score { background:linear-gradient(135deg,#FFFFFF 0%,#E5EFE2 100%); border:1px solid #D8E5DA;
  border-radius:20px; padding:16px 18px; margin:6px 0 12px; }
.score .s-top { display:flex; align-items:baseline; flex-wrap:wrap; gap:4px; }
.score .s-num { font-family:'Lora',serif; font-size:2.1rem; font-weight:700; color:#36594A; line-height:1; }
.score .s-de { color:#6b7a70; font-weight:600; }
.score .barra { height:12px; background:#E2ECE3; border-radius:999px; overflow:hidden; margin:12px 0 8px; }
.score .barra div { height:100%; background:linear-gradient(90deg,#B5D3BC,#5E8B6C); border-radius:999px; }
.score .s-msg { font-weight:700; color:#5E8B6C; }
.meta-card { background:#fff; border:1px solid #D8E5DA; border-radius:16px; padding:10px 14px;
  margin:4px 0 10px; color:#36594A; font-weight:600; }
.meta-card b { font-family:'Lora',serif; }
.aviso { font-size:.95rem; line-height:1.5; }
.agua { background:#fff; border:1px solid #D8E5DA; border-radius:18px; padding:12px 16px; margin:4px 0 8px; }
.agua .a-top { color:#36594A; display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px; }
.agua .a-msg { color:#5E8B6C; font-weight:700; font-size:.9rem; }
.agua .gotas { display:flex; flex-wrap:wrap; gap:4px; margin-top:8px; font-size:22px; }
.agua .gota { filter:grayscale(1); opacity:.28; }
.agua .gota.llena { filter:none; opacity:1; }
.logros { background:#fff; border:1px solid #D8E5DA; border-radius:18px; padding:14px 16px; margin:10px 0; }
.logros .l-top { color:#36594A; margin-bottom:10px; }
.insignias { display:flex; flex-wrap:wrap; gap:10px; }
.insignia { background:#E5EFE2; border-radius:14px; padding:8px 12px; text-align:center; min-width:74px; }
.insignia .i-ico { font-size:26px; }
.insignia .i-txt { font-size:.78rem; font-weight:700; color:#36594A; }
.insignia.bloqueada { background:#F1F1EE; filter:grayscale(1); opacity:.45; }
.instalar { background:linear-gradient(135deg,#FFFFFF 0%,#F8F3E6 100%); border:1px solid #E6DECB;
  border-radius:20px; padding:16px 18px; margin:4px 0 8px; color:#33433A; }
.instalar .i-tit { font-family:'Lora',serif; font-size:1.2rem; font-weight:700; color:#36594A; }
.instalar .i-sub { color:#6b7a70; margin:2px 0 10px; }
.instalar ol { margin:0; padding-left:1.2rem; }
.instalar li { margin:6px 0; line-height:1.45; }
.instalar .btn { display:inline-block; background:#E5EFE2; color:#36594A; border-radius:8px;
  padding:1px 8px; font-weight:700; white-space:nowrap; }
.marca { display:flex; flex-direction:column; align-items:center; gap:12px; color:#2F4A34; margin:4px 0 6px; }
.marca .m-nombre { font-family:'Cormorant Garamond', Georgia, serif; font-weight:500; font-size:3.4rem;
  line-height:1; letter-spacing:.5px; }
.marca .m-linea { width:90px; height:1px; background:currentColor; opacity:.45; }
.marca .m-sub { font-family:'Montserrat', Arial, sans-serif; font-weight:500; font-size:.85rem;
  letter-spacing:8px; padding-left:8px; }
.marca-h { display:flex; align-items:center; gap:12px; color:#2F4A34; }
.marca-h .m-div { width:1px; height:40px; background:currentColor; opacity:.4; }
.marca-h .m-nombre { font-family:'Cormorant Garamond', Georgia, serif; font-weight:500; font-size:1.55rem; line-height:1; }
.marca-h .m-sub { font-family:'Montserrat', Arial, sans-serif; font-weight:500; font-size:.62rem;
  letter-spacing:4px; margin-top:5px; }
.hero-sub { text-align:center; color:#6b7a70; margin:.2rem 0 1.4rem; font-size:1.02rem; }
@media (max-width: 640px) { .marca .m-nombre { font-size:2.6rem; } .marca .m-sub { letter-spacing:6px; } }
.alerta { background:#FFF8EC; border:1px solid #F0DDB8; border-radius:14px; padding:10px 14px; margin:6px 0; }
/* Selector de paciente fijo arriba al hacer scroll (panel) */
[class*="st-key-selpac_"] {
  background: #FFFFFF; border: 1px solid #D8E5DA; border-left: 6px solid #5E8B6C;
  border-radius: 16px; padding: 8px 14px 12px; margin-bottom: 6px;
  box-shadow: 0 6px 18px rgba(54,89,74,.14);
}
[class*="st-key-selpac_"] [data-testid="stWidgetLabel"] p { font-weight: 800 !important; color: #36594A !important; }
/* Quitar el marco de "enfoque" que el navegador dibuja alrededor del área principal */
[data-testid="stMain"], [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"],
section.main, .main, [role="tabpanel"], [data-baseweb="tab-panel"] {
  outline: none !important;
}
[data-testid="stMain"]:focus, [data-testid="stMain"]:focus-visible,
[data-testid="stAppViewContainer"]:focus, [role="tabpanel"]:focus, [role="tabpanel"]:focus-visible {
  outline: none !important; box-shadow: none !important;
}
/* Etiqueta chiquita fija en la esquina con la paciente seleccionada */
.chip-pac {
  position: fixed; left: 16px; bottom: 16px; z-index: 990;
  background: #5E8B6C; color: #FFFFFF !important; text-decoration: none !important;
  border-radius: 999px; padding: 8px 14px; font-weight: 700; font-size: .88rem;
  box-shadow: 0 6px 16px rgba(54,89,74,.3); max-width: 70vw;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.chip-pac:hover { background: #36594A; }
/* Pestañas principales en forma de cápsula (selectores estables por rol) */
[data-testid="stTabs"] [role="tablist"] {
  display:flex; flex-wrap:wrap; gap:10px !important; background:transparent !important;
  padding:4px 0 10px !important; border-bottom:none !important; box-shadow:none !important;
}
[data-testid="stTabs"] [role="tab"] {
  border-radius:999px !important; padding:11px 22px !important; height:auto !important; margin:0 !important;
  background:#FFFFFF !important; border:1.5px solid #CFE0D2 !important; justify-content:center;
  box-shadow:0 2px 8px rgba(54,89,74,.08) !important; transition:all .15s ease;
}
[data-testid="stTabs"] [role="tab"] p { font-size:1.05rem !important; font-weight:700 !important; color:#36594A !important; }
[data-testid="stTabs"] [role="tab"]:hover { background:#E5EFE2 !important; border-color:#9DC2A5 !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background:#5E8B6C !important; border-color:#5E8B6C !important; box-shadow:0 4px 12px rgba(54,89,74,.25) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p { color:#FFFFFF !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"] {
  display:none !important;
}
@media (max-width: 640px) {
  [data-testid="stTabs"] [role="tablist"] { flex-wrap:nowrap; gap:6px !important; }
  [data-testid="stTabs"] [role="tab"] { padding:11px 6px !important; flex:1 1 0; justify-content:center; min-width:0; }
  [data-testid="stTabs"] [role="tab"] p { font-size:.9rem !important; white-space:nowrap; }
}
</style>"""
st.html(CSS_EXTRA)

# ---------------------------------------------------------------- Modo oscuro
CSS_OSCURO = """<style>
.stApp { background:#1B2420 !important; color:#E4ECE6 !important; }
.stApp p, .stApp label, .stApp li, [data-testid="stMarkdownContainer"],
[data-testid="stWidgetLabel"] p { color:#E4ECE6 !important; }
[data-testid="stCaptionContainer"], .stApp small { color:#9FB3A6 !important; }
h1, h2, h3 { color:#BFE3CB !important; }
[data-baseweb="tab-list"] { background:#26332C !important; }
button[data-baseweb="tab"] p { color:#C9D9CE !important; }
button[data-baseweb="tab"][aria-selected="true"] { background:#35463C !important; box-shadow:none !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color:#FFFFFF !important; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button,
[data-testid="stLinkButton"] a, [data-testid="stBaseButton-segmented_control"] {
  background:#26332C !important; color:#E4ECE6 !important; border-color:#3D5045 !important; }
.stButton > button:hover, .stDownloadButton > button:hover { background:#2F4037 !important; }
button[kind="primary"], button[kind="primaryFormSubmit"] {
  background:#6FA07E !important; border-color:#6FA07E !important; color:#10251A !important; }
[data-baseweb="input"], [data-baseweb="input"] > div, [data-baseweb="textarea"], [data-baseweb="base-input"],
[data-baseweb="select"] > div, [data-testid="stTextArea"] div, [data-testid="stNumberInput"] div,
[data-testid="stDateInput"] div { background-color:#26332C !important; border-color:#3D5045 !important; }
input, textarea { color:#E4ECE6 !important; -webkit-text-fill-color:#E4ECE6 !important;
  background-color:#26332C !important; }
[data-baseweb="select"] span, [data-baseweb="select"] div { color:#E4ECE6 !important; }
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [role="listbox"] {
  background:#26332C !important; color:#E4ECE6 !important; }
[data-baseweb="popover"] li:hover { background:#35463C !important; }
[data-testid="stForm"], [data-testid="stMetric"], [data-testid="stExpander"] details,
[data-testid="stVegaLiteChart"], .stVegaLiteChart, [data-testid="stVerticalBlockBorderWrapper"] {
  background:#222D27 !important; border-color:#3D5045 !important; box-shadow:none !important; }
[data-testid="stExpander"] summary:hover { background:#2A3830 !important; }
[data-testid="stMetricValue"] { color:#BFE3CB !important; }
[data-testid="stMetricLabel"] p { color:#8FC29F !important; }
.saludo { background:linear-gradient(135deg,#222D27 0%,#2C3D33 100%) !important; border-color:#3D5045 !important; }
.saludo .s-hola { color:#BFE3CB !important; }
.saludo .s-sub, .hero p { color:#9FB3A6 !important; }
.hero .logo { background:#2C3D33 !important; box-shadow:0 0 0 8px #26332C !important; }
.chip { background:#26332C !important; border-color:#3D5045 !important; color:#CFE3D5 !important; }
.vacio, .agua, .logros, .meta-card, .instalar, [class*="st-key-tarjeta_"], .card-menu,
.menu-wrap, table.menu, .score {
  background:#222D27 !important; border-color:#3D5045 !important; color:#E4ECE6 !important; box-shadow:none !important; }
[class*="st-key-tarjeta_ok_"] { background:#25392D !important; border-left-color:#6FA07E !important; }
.score { background:linear-gradient(135deg,#222D27 0%,#2C3D33 100%) !important; }
.score .s-num, .t-body .m-tit, .m-tit, .meta-card b, .instalar .i-tit, .logros .l-top { color:#BFE3CB !important; }
.score .barra { background-color:#2F3D35 !important; }
.t-com, .card-menu .c-com, .score .s-msg, .agua .a-msg { color:#8FC29F !important; }
.t-body, .agua .a-top, .instalar, .instalar .i-sub { color:#E4ECE6 !important; }
.t-com .kc, .instalar .btn, .insignia { background:#2C3D33 !important; color:#CFE3D5 !important; }
.insignia .i-txt { color:#CFE3D5 !important; }
.insignia.bloqueada { background:#26302B !important; }
.m-sep, .t-body .m-sep { border-color:#3D5045 !important; }
table.menu th, .dia-head, .g-head { background:#3F6A50 !important; color:#FFFFFF !important; }
table.menu td { border-color:#3D5045 !important; color:#E4ECE6 !important; background:#222D27; }
table.menu td.comida, .g-comida { background:#2C3D33 !important; color:#BFE3CB !important; }
table.menu tr.indic td, .card-menu.indic { background:#2E2A22 !important; }
.alerta { background:#3A3222 !important; border-color:#5A4B2E !important; color:#F2E6CC !important; }
.marca, .marca-h { color:#CFE6D5 !important; }
.hero-sub { color:#9FB3A6 !important; }
/* Encabezados de los desplegables (al abrirse se ponían claros) */
[data-testid="stExpander"] summary, [data-testid="stExpander"] details[open] > summary,
[data-testid="stExpanderDetails"] { background:#26332C !important; color:#E4ECE6 !important; }
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary svg { color:#E4ECE6 !important; fill:#E4ECE6 !important; }
[data-testid="stExpanderDetails"] { background:#222D27 !important; }
/* Selectores, fechas, contraseñas y cuadros de texto */
[data-baseweb="select"] div, [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div { background-color:#26332C !important; }
[data-baseweb="tag"], [data-baseweb="tag"] div, [data-baseweb="tag"] span {
  background-color:#5E8B6C !important; color:#FFFFFF !important; }
[data-testid="stTextInput"] button, [data-testid="stNumberInput"] button,
[data-testid="stDateInput"] button { background:#26332C !important; color:#E4ECE6 !important; }
[data-testid="stDateInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {
  color:#E4ECE6 !important; -webkit-text-fill-color:#E4ECE6 !important; opacity:1 !important; }
input::placeholder, textarea::placeholder { color:#7F9487 !important; -webkit-text-fill-color:#7F9487 !important; }
[data-testid="stTextArea"] textarea, [data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextArea"] [data-baseweb="base-input"] { background-color:#26332C !important;
  color:#E4ECE6 !important; -webkit-text-fill-color:#E4ECE6 !important; }
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] div { background:transparent !important; }
/* Calendario y menús desplegables */
[data-baseweb="calendar"], [data-baseweb="calendar"] div, [data-baseweb="datepicker"] {
  background-color:#26332C !important; color:#E4ECE6 !important; }
[data-baseweb="calendar"] [aria-selected="true"] div { background-color:#5E8B6C !important; }
[data-baseweb="menu"], [data-baseweb="menu"] li { background:#26332C !important; color:#E4ECE6 !important; }
/* Casillas y radios */
[data-testid="stCheckbox"] label span, [data-baseweb="radio"] div { border-color:#6FA07E !important; }
/* Avisos de Streamlit */
[data-testid="stAlert"] * { color:#E4ECE6 !important; }
/* Fondo general (también detrás de la barra del celular) */
html, body { background:#1B2420 !important; }
header[data-testid="stHeader"] { background:transparent !important; }
/* Botones Por día / Semana / Súper */
[data-testid="stButtonGroup"] button, [data-testid*="segmented_control"] {
  background:#26332C !important; border-color:#3D5045 !important; }
[data-testid="stButtonGroup"] button p, [data-testid="stButtonGroup"] button div,
[data-testid="stButtonGroup"] button span { color:#E4ECE6 !important; }
[data-testid="stButtonGroup"] button[kind$="Active"], [data-testid*="segmented_controlActive"],
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[aria-pressed="true"] {
  background:#5E8B6C !important; border-color:#6FA07E !important; }
[data-testid="stButtonGroup"] button[kind$="Active"] p, [data-testid*="segmented_controlActive"] p {
  color:#FFFFFF !important; }
/* Selectores: caja completa, flecha y lista de opciones */
[data-testid="stSelectbox"] div, [data-testid="stMultiSelect"] div {
  background-color:#26332C !important; color:#E4ECE6 !important; }
[data-testid="stTextInput"] div, [data-testid="stTextInput"] button {
  background-color:#26332C !important; color:#E4ECE6 !important; }
[data-testid="stTextInput"] svg { fill:#E4ECE6 !important; color:#E4ECE6 !important; }
[data-testid="stTextInput"] [data-testid="stWidgetLabel"], [data-testid="stTextInput"] [data-testid="stWidgetLabel"] div,
[data-testid="stSelectbox"] [data-testid="stWidgetLabel"], [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] div,
[data-testid="stMultiSelect"] [data-testid="stWidgetLabel"], [data-testid="stMultiSelect"] [data-testid="stWidgetLabel"] div {
  background-color:transparent !important; }
[data-testid="stSelectbox"] svg, [data-testid="stMultiSelect"] svg { fill:#E4ECE6 !important; color:#E4ECE6 !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"], [data-testid="stMultiSelect"] [data-baseweb="tag"] * {
  background-color:#5E8B6C !important; color:#FFFFFF !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [data-baseweb="popover"] ul,
[data-baseweb="popover"] li, [role="listbox"], [role="option"] {
  background-color:#26332C !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] li *, [role="option"], [role="option"] * {
  color:#E4ECE6 !important; -webkit-text-fill-color:#E4ECE6 !important; opacity:1 !important; }
[data-baseweb="popover"] li[aria-selected="true"], [role="option"][aria-selected="true"],
[data-baseweb="popover"] li:hover, [role="option"]:hover { background-color:#3A5245 !important; }
/* Mensajes flotantes (cita agendada, cancelada, etc.) */
[data-testid="stToast"], [data-testid="stToastContainer"] > div {
  background:#2C3D33 !important; border:1px solid #3D5045 !important; }
[data-testid="stToast"] *, [data-testid="stToastContainer"] * { color:#E4ECE6 !important; }
/* Radios */
[data-testid="stRadio"] label p { color:#E4ECE6 !important; }
[data-testid="stTabs"] [role="tab"] { background:#26332C !important; border-color:#3D5045 !important; box-shadow:none !important; }
[data-testid="stTabs"] [role="tab"] p { color:#DCEBE0 !important; }
[data-testid="stTabs"] [role="tab"]:hover { background:#2F4037 !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background:#6FA07E !important; border-color:#6FA07E !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p { color:#10251A !important; }
[data-testid="stTabs"] [role="tablist"] { background:transparent !important; }
[class*="st-key-selpac_"] { background:#222D27 !important; border-color:#3D5045 !important;
  border-left-color:#6FA07E !important; box-shadow:0 6px 18px rgba(0,0,0,.35) !important; }
[class*="st-key-selpac_"] [data-testid="stWidgetLabel"] p { color:#BFE3CB !important; }
.chip-pac { background:#6FA07E !important; color:#10251A !important; }
</style>"""


def es_oscuro() -> bool:
    return bool(st.session_state.get("oscuro"))


def _sincronizar_tema():
    if st.session_state.get("oscuro"):
        st.query_params["tema"] = "oscuro"
    elif "tema" in st.query_params:
        del st.query_params["tema"]


def interruptor_tema(clave: str):
    st.toggle("🌙", key="oscuro", on_change=_sincronizar_tema, help="Modo oscuro")


if "oscuro" not in st.session_state:
    st.session_state.oscuro = st.query_params.get("tema") == "oscuro"
if st.session_state.oscuro:
    st.html(CSS_OSCURO)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                "septiembre", "octubre", "noviembre", "diciembre"]
ORDEN_COMIDAS = ["Desayuno", "Almuerzo", "Colación 1", "Comida", "Colación 2", "Cena", "Indicaciones"]
COLUMNAS_MENU = ["dia", "comida", "titulo", "platillo", "notas", "kcal"]
COLUMNAS_PACIENTE_EXTRA = [
    "meta_peso", "cambiar_pwd", "acepto_aviso", "estatura_m", "fecha_nacimiento", "meta_agua"
]
METRICAS = {
    "Peso (kg)": "peso_kg",
    "Grasa (%)": "grasa_pct",
    "Músculo (%)": "musculo_pct",
    "Circunferencia abdominal (cm)": "cintura_cm",
    "Cadera (cm)": "cadera_cm",
    "Músculo (kg)": "musculo_kg",  # registros anteriores
}


def metricas_con_datos(med: pd.DataFrame) -> list:
    """Solo las métricas que esa paciente sí tiene capturadas."""
    con = [k for k, c in METRICAS.items() if c in med.columns and med[c].notna().any()]
    return con or ["Peso (kg)"]
# Hojas que la app crea sola si no existen
HOJAS_NUEVAS = {
    "Bloqueos": ["fecha", "hora", "motivo"],
    "NotasPrivadas": ["id_paciente", "fecha", "nota"],
    "Registro": ["id_paciente", "fecha", "comida", "kcal"],
    "Agua": ["id_paciente", "fecha", "vasos"],
    "Pagos": ["id_pago", "id_paciente", "fecha", "monto", "metodo", "concepto", "id_cita"],
}


# ================================================================ Conexión
def credenciales():
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )


@st.cache_resource
def conectar():
    try:
        # Reintenta solo (con espera creciente) si Google dice "demasiadas solicitudes"
        cliente = gspread.authorize(credenciales(), http_client=gspread.BackOffHTTPClient)
    except (AttributeError, TypeError):
        cliente = gspread.authorize(credenciales())
    return cliente.open(st.secrets["sheet_name"])


@st.cache_resource
def drive():
    return AuthorizedSession(credenciales())


# ---------------------------------------------------------------- Memoria compartida
# Las pestañas y sus encabezados se recuerdan para no pedírselos a Google en cada clic.
# Cada hoja tiene un número de "versión": al guardar en una hoja solo esa se vuelve a leer.
@st.cache_resource
def _memoria() -> dict:
    return {"pestanas": {}, "encabezados": {}, "versiones": {}}


def _pestana(nombre: str):
    mem = _memoria()["pestanas"]
    if nombre not in mem:
        mem[nombre] = conectar().worksheet(nombre)
    return mem[nombre]


def invalidar(nombre: str):
    """Avisa que la hoja cambió: la próxima lectura viene fresca de Google (para todos)."""
    versiones = _memoria()["versiones"]
    versiones[nombre] = versiones.get(nombre, 0) + 1
    _memoria()["encabezados"].pop(nombre, None)


def reintentar(funcion, *args, intentos: int = 4, **kwargs):
    """Respaldo extra: si Google limita las solicitudes, espera y vuelve a intentar."""
    import time

    for i in range(intentos):
        try:
            return funcion(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            codigo = getattr(getattr(e, "response", None), "status_code", None)
            if codigo not in (429, 500, 503) or i == intentos - 1:
                raise
            time.sleep(2 ** (i + 1))


def hoja(nombre: str):
    """Devuelve la pestaña; si es una de las hojas nuevas y no existe, la crea."""
    try:
        return reintentar(_pestana, nombre)
    except gspread.WorksheetNotFound:
        encabezados = HOJAS_NUEVAS.get(nombre)
        if not encabezados:
            raise
        ws = conectar().add_worksheet(title=nombre, rows=1000, cols=max(6, len(encabezados)))
        ws.append_row(encabezados)
        _memoria()["pestanas"][nombre] = ws
        invalidar(nombre)
        return ws


def encabezados_de(nombre: str) -> list:
    mem = _memoria()["encabezados"]
    if nombre not in mem:
        mem[nombre] = reintentar(hoja(nombre).row_values, 1)
    return list(mem[nombre])


def asegurar_columnas(nombre: str, columnas: list[str]):
    """Agrega al Sheet los encabezados que falten."""
    encabezados = encabezados_de(nombre)
    faltan = [c for c in columnas if c not in encabezados]
    if faltan:
        ws = hoja(nombre)
        if ws.col_count < len(encabezados) + len(faltan):
            reintentar(ws.add_cols, len(faltan))
        for k, c in enumerate(faltan):
            reintentar(ws.update_cell, 1, len(encabezados) + k + 1, c)
        invalidar(nombre)
        _memoria()["encabezados"][nombre] = encabezados + faltan
    return encabezados + faltan


@st.cache_data(ttl=180, show_spinner=False)
def _leer(nombre: str, version: int) -> pd.DataFrame:
    try:
        ws = reintentar(_pestana, nombre)
    except gspread.WorksheetNotFound:
        return pd.DataFrame(columns=HOJAS_NUEVAS.get(nombre, []))
    valores = reintentar(ws.get_all_values)
    if not valores:
        return pd.DataFrame(columns=HOJAS_NUEVAS.get(nombre, []))
    encabezados = [c for c in valores[0]]
    _memoria()["encabezados"][nombre] = encabezados
    filas = [f + [""] * (len(encabezados) - len(f)) for f in valores[1:]]
    df = pd.DataFrame([f[: len(encabezados)] for f in filas], columns=encabezados)
    df = df.loc[:, [c for c in df.columns if c]]
    # Igual que antes: números como números (para teléfonos, kcal, pesos…)
    for c in df.columns:
        convertida = pd.to_numeric(df[c], errors="coerce")
        if df[c].astype(str).str.strip().ne("").any() and convertida[df[c].astype(str).str.strip() != ""].notna().all():
            if (convertida.dropna() % 1 == 0).all():
                convertida = convertida.astype("Int64")
            df[c] = convertida.astype(object).where(df[c].astype(str).str.strip() != "", "")
    if "id_paciente" in df.columns:
        df["id_paciente"] = df["id_paciente"].astype(str).str.strip().str.upper()
    return df


def leer(nombre: str) -> pd.DataFrame:
    """Lee una hoja (desde la memoria si nadie la ha cambiado; se refresca cada 3 min)."""
    return _leer(nombre, _memoria()["versiones"].get(nombre, 0)).copy()


def agregar_filas(nombre: str, filas: list[dict]):
    """Agrega filas respetando el orden de los encabezados (y crea columnas que falten)."""
    claves = list(dict.fromkeys(k for f in filas for k in f))
    encabezados = asegurar_columnas(nombre, claves)
    valores = [[f.get(c, "") for c in encabezados] for f in filas]
    reintentar(hoja(nombre).append_rows, valores, value_input_option="RAW")
    invalidar(nombre)


def actualizar_celda(nombre: str, fila_df: int, columna: str, valor):
    """fila_df = índice del DataFrame leído con leer() (fila 0 = fila 2 del Sheet)."""
    encabezados = asegurar_columnas(nombre, [columna])
    reintentar(hoja(nombre).update_cell, fila_df + 2, encabezados.index(columna) + 1, valor)
    invalidar(nombre)


def _vivo(nombre: str) -> pd.DataFrame:
    """Lectura directa de Google (para borrar sin riesgo de equivocarse de fila)."""
    valores = reintentar(hoja(nombre).get_all_values)
    if len(valores) < 2:
        return pd.DataFrame()
    enc = valores[0]
    return pd.DataFrame([(f + [""] * len(enc))[: len(enc)] for f in valores[1:]], columns=enc)


def borrar_donde(nombre: str, **campos):
    """Borra las filas donde todas las columnas indicadas coinciden (leyendo en vivo)."""
    ws = hoja(nombre)
    vivo = _vivo(nombre)
    if vivo.empty:
        return
    mask = pd.Series(True, index=vivo.index)
    for col, val in campos.items():
        mask &= vivo[col].astype(str).str.strip().str.upper() == str(val).strip().upper()
    for i in sorted(vivo.index[mask], reverse=True):
        reintentar(ws.delete_rows, int(i) + 2)
    invalidar(nombre)


def borrar_menu(pid: str, fecha: str):
    """Borra el menú de una paciente con esa fecha_inicio (leyendo el Sheet en vivo)."""
    ws = hoja("Menus")
    vivo = _vivo("Menus")
    if vivo.empty:
        return
    mask = (vivo["id_paciente"].astype(str).str.strip().str.upper() == pid) & (
        vivo["fecha_inicio"].apply(fecha_iso) == fecha
    )
    for i in sorted(vivo.index[mask], reverse=True):
        reintentar(ws.delete_rows, int(i) + 2)
    invalidar("Menus")


def idx_paciente(pid: str):
    pacientes = leer("Pacientes")
    filas = pacientes.index[pacientes["id_paciente"] == pid]
    return int(filas[0]) if len(filas) else None


# ================================================================ Utilidades
def a_numero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype(str).str.replace(",", "."), errors="coerce")


def sin_acentos(texto) -> str:
    t = unicodedata.normalize("NFKD", str(texto).strip().lower())
    return "".join(ch for ch in t if not unicodedata.combining(ch))


def hora_hhmm(valor) -> str:
    """'9:00', '09:00', '9:00:00' -> '09:00'."""
    partes = str(valor).strip().split(":")
    try:
        return f"{int(partes[0]):02d}:{int(partes[1]) if len(partes) > 1 else 0:02d}"
    except ValueError:
        return str(valor).strip()


def fecha_iso(valor) -> str:
    f = pd.to_datetime(str(valor).strip(), errors="coerce")
    return "" if pd.isna(f) else f.strftime("%Y-%m-%d")


def fecha_bonita(d) -> str:
    return f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]}"


def ahora_mx() -> datetime:
    # Hora del centro de México (sin horario de verano desde 2022)
    return datetime.now(timezone(timedelta(hours=-6))).replace(tzinfo=None)


def citas_limpias(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return pd.DataFrame(
            columns=["id_cita", "id_paciente", "fecha", "hora", "estado", "notas", "inicio"]
        )
    df["id_paciente"] = df["id_paciente"].astype(str).str.strip().str.upper()
    df["fecha"] = df["fecha"].apply(fecha_iso)
    df["hora"] = df["hora"].apply(hora_hhmm)
    df["estado"] = df["estado"].astype(str).str.strip().str.lower()
    df["inicio"] = pd.to_datetime(df["fecha"] + " " + df["hora"], errors="coerce")
    return df


def siguiente_id(serie: pd.Series, prefijo: str) -> str:
    nums = pd.to_numeric(serie.astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    maximo = nums.max()
    return f"{prefijo}{(0 if pd.isna(maximo) else int(maximo)) + 1:03d}"


# ================================================================ Contraseñas
def crear_hash(password: str) -> str:
    sal = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), sal, 200_000).hex()
    return f"{sal.hex()}${h}"


def verificar(password: str, guardado: str) -> bool:
    """El Sheet guarda 'sal$hash'."""
    try:
        sal, hash_guardado = guardado.split("$")
        calculado = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(sal), 200_000
        ).hex()
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(calculado, hash_guardado)



def numero(valor):
    """Convierte '65', '65.5', '65,5' a float; vacío o inválido -> None."""
    try:
        v = float(str(valor).replace(",", ".").strip())
        return None if pd.isna(v) else v
    except ValueError:
        return None


def link_whatsapp(telefono, mensaje: str):
    digitos = re.sub(r"\D", "", str(telefono))
    if len(digitos) == 10:  # número mexicano sin lada de país
        digitos = "52" + digitos
    if len(digitos) < 11:
        return None
    return f"https://wa.me/{digitos}?text={quote(mensaje)}"


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", sin_acentos(texto)).strip("_")


# ================================================================ Gráfica
def grafica_metrica(med: pd.DataFrame, nombre: str, columna: str, meta=None):
    base = alt.Chart(med.dropna(subset=[columna])).encode(
        x=alt.X("fecha:T", title=None, axis=alt.Axis(format="%d %b", tickCount=6)),
        y=alt.Y(f"{columna}:Q", title=None, scale=alt.Scale(zero=False, nice=True)),
        tooltip=[
            alt.Tooltip("fecha:T", title="Fecha", format="%d/%m/%Y"),
            alt.Tooltip(f"{columna}:Q", title=nombre),
        ],
    )
    area = base.mark_area(
        interpolate="monotone",
        line=False,
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color="#1B2420" if es_oscuro() else "#FFFFFF", offset=0),
                   alt.GradientStop(color="#2F4A3B" if es_oscuro() else VERDE_CLARO, offset=1)],
            x1=1, x2=1, y1=1, y2=0,
        ),
    )
    linea = base.mark_line(interpolate="monotone", color=VERDE, strokeWidth=3)
    puntos = base.mark_circle(size=90, color=VERDE, stroke="#fff", strokeWidth=2, opacity=1)
    capas = area + linea + puntos
    if meta is not None:
        df_meta = pd.DataFrame({"meta": [meta]})
        regla = alt.Chart(df_meta).mark_rule(
            color="#C9A66B", strokeDash=[6, 5], strokeWidth=2
        ).encode(y="meta:Q", tooltip=[alt.Tooltip("meta:Q", title="Meta")])
        etiqueta = alt.Chart(df_meta).mark_text(
            align="left", dx=6, dy=-9, color="#A8864B", font="Nunito", fontWeight="bold"
        ).encode(y="meta:Q", x=alt.value(0), text=alt.value(f"Meta: {meta:g}"))
        capas = capas + regla + etiqueta
    return (
        capas.properties(height=280, background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#9FB3A6" if es_oscuro() else "#6b7a70", labelFont="Nunito", labelFontSize=12,
            gridColor="#2E3A33" if es_oscuro() else "#E8EFE8", domain=False, ticks=False,
        )
    )


def mediciones_de(pid: str) -> pd.DataFrame:
    med = leer("Mediciones")
    med = med[med["id_paciente"] == pid].copy()
    if med.empty:
        return med
    med["fecha"] = pd.to_datetime(med["fecha"], errors="coerce")
    for c in METRICAS.values():
        med[c] = a_numero(med[c]) if c in med.columns else float("nan")
    return med.dropna(subset=["fecha"]).sort_values("fecha")


# ================================================================ PDFs de Canva (Google Drive)
@st.cache_data(ttl=300)
def listar_pdfs() -> list[dict]:
    """PDFs que la nutrióloga compartió con la cuenta de la app."""
    q = "mimeType='application/pdf' and trashed=false"
    carpeta = str(st.secrets.get("drive_folder_id", "")).strip()
    if carpeta:
        q += f" and '{carpeta}' in parents"
    archivos, token = [], None
    while True:
        r = drive().get(
            "https://www.googleapis.com/drive/v3/files",
            params={
                "q": q,
                "fields": "nextPageToken, files(id,name,modifiedTime)",
                "pageSize": 1000,
                "pageToken": token,
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
            },
        )
        r.raise_for_status()
        datos = r.json()
        archivos += datos.get("files", [])
        token = datos.get("nextPageToken")
        if not token:
            return archivos


def normalizar_nombre(texto) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos(texto)).strip()


def pdf_de(pid: str, nombre: str):
    """El PDF más reciente cuyo nombre empiece con el código (P001 ...) o con el
    nombre completo de la paciente seguido de la fecha (ALMA EDITH AGUIRRE. 10 octubre...)."""
    try:
        archivos = listar_pdfs()
    except Exception:
        return None
    n_nombre, n_id = normalizar_nombre(nombre), pid.lower()
    propios = []
    for a in archivos:
        n = normalizar_nombre(a["name"].removesuffix(".pdf"))
        por_id = n.split(" ")[0] == n_id
        resto = n[len(n_nombre):].strip()
        por_nombre = bool(n_nombre) and n.startswith(n_nombre) and (resto == "" or resto[0].isdigit())
        if por_id or por_nombre:
            propios.append(a)
    return max(propios, key=lambda a: a["modifiedTime"]) if propios else None


@st.cache_data(ttl=600, show_spinner="Cargando PDF…")
def descargar_pdf(file_id: str, modificado: str) -> bytes:
    r = drive().get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        params={"alt": "media", "supportsAllDrives": True},
    )
    r.raise_for_status()
    return r.content


@st.cache_data(show_spinner=False)
def pdf_a_imagenes(datos: bytes) -> list[bytes]:
    import pymupdf

    doc = pymupdf.open(stream=datos, filetype="pdf")
    return [pagina.get_pixmap(dpi=150).tobytes("png") for pagina in doc]


def mostrar_pdf(archivo: dict, clave: str):
    datos = descargar_pdf(archivo["id"], archivo["modifiedTime"])
    try:
        for img in pdf_a_imagenes(datos):
            st.image(img, use_container_width=True)
    except ImportError:
        st.caption("Descarga el PDF para verlo.")
    nombre = archivo["name"] if archivo["name"].lower().endswith(".pdf") else archivo["name"] + ".pdf"
    st.download_button(
        "⬇️ Descargar PDF",
        datos,
        file_name=nombre,
        mime="application/pdf",
        use_container_width=True,
        key=clave,
    )


# ================================================================ Menú con el estilo de la nutrióloga
CSS_MENU = """<style>
.menu-wrap{overflow-x:auto;border:1px solid #DCE6D8;border-radius:16px;box-shadow:0 2px 12px rgba(54,89,74,.06)}
table.menu{border-collapse:collapse;width:100%;min-width:950px;table-layout:fixed;background:#fff;color:#33433A;
  font-family:'Nunito',sans-serif;font-size:13px;line-height:1.35}
table.menu th{background:#6F9A7C;color:#fff;font-weight:400;padding:9px 6px;letter-spacing:.5px}
table.menu td{border:1px solid #DCE6D8;padding:8px 9px;vertical-align:middle}
table.menu td.comida{background:#E5EFE2;color:#5E8B6C;font-weight:700;text-align:center;
  text-transform:uppercase;width:92px}
table.menu td.junta{text-align:center}
table.menu tr.indic td{background:#F6F0E1}
.m-tit{font-family:'Lora',serif;font-weight:700;color:#36594A;text-transform:uppercase;text-align:center;margin-bottom:6px}
.m-sep{border-top:1px solid #E8EEE5;margin:7px 0}
.dia-head{background:#6F9A7C;color:#fff;border-radius:14px;padding:10px 16px;
  font-family:'Lora',serif;font-weight:600;letter-spacing:1px;text-transform:uppercase}
.card-menu{background:#fff;color:#33433A;border-left:6px solid #9DC2A5;border-radius:14px;box-shadow:0 2px 10px rgba(54,89,74,.06);
  padding:12px 14px;margin:10px 0;font-family:'Nunito',sans-serif;font-size:15px}
.card-menu .c-com{font-size:12px;font-weight:700;color:#5E8B6C;letter-spacing:1px;
  text-transform:uppercase;margin-bottom:4px;opacity:.8}
.card-menu .m-tit{text-align:left;font-size:16px;margin-bottom:4px}
.card-menu.indic{background:#F6F0E1}
</style>"""


def menu_limpio(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reindex(columns=COLUMNAS_MENU).fillna("").astype(str)
    for c in COLUMNAS_MENU:
        df[c] = df[c].str.strip()
    return df[(df["platillo"] != "") | (df["titulo"] != "")]


def items_de(m: pd.DataFrame, dia: str, comida: str) -> pd.DataFrame:
    """Lo específico del día manda; si no hay, se usa lo de 'Todos'."""
    de_comida = m[m["comida"] == comida]
    propios = de_comida[de_comida["dia"] == dia]
    return propios if not propios.empty else de_comida[de_comida["dia"] == "Todos"]


def es_titulo(linea: str) -> bool:
    return linea == linea.upper() and any(ch.isalpha() for ch in linea)


def texto_html(texto: str) -> str:
    """Líneas en MAYÚSCULAS = título en negritas; línea en blanco = separador."""
    partes, sep = [], False
    for linea in str(texto).splitlines():
        linea = linea.strip()
        if not linea:
            sep = bool(partes)
            continue
        if sep:
            partes.append('<div class="m-sep"></div>')
            sep = False
        clase = ' class="m-tit"' if es_titulo(linea) else ""
        partes.append(f"<div{clase}>{html.escape(linea)}</div>")
    return "".join(partes)


def celda_html(items: pd.DataFrame) -> str:
    bloques = []
    for _, f in items.iterrows():
        b = ""
        if f["titulo"]:
            b += f'<div class="m-tit">{html.escape(f["titulo"])}</div>'
        if f["platillo"]:
            b += texto_html(f["platillo"])
        if f["notas"]:
            b += f'<div class="m-sep"></div>{texto_html(f["notas"])}'
        bloques.append(b)
    return '<div class="m-sep"></div>'.join(bloques)


def menu_semana_html(m: pd.DataFrame) -> str:
    m = menu_limpio(m)
    filas = []
    for comida in ORDEN_COMIDAS[:-1]:
        if comida not in set(m["comida"]):
            continue
        celdas = [celda_html(items_de(m, d, comida)) for d in DIAS]
        tds, i = "", 0
        while i < len(DIAS):  # junta días seguidos iguales, como en su formato
            j = i
            while j + 1 < len(DIAS) and celdas[j + 1] == celdas[i]:
                j += 1
            span = j - i + 1
            clase = ' class="junta"' if span > 1 else ""
            tds += f'<td colspan="{span}"{clase}>{celdas[i]}</td>'
            i = j + 1
        k = kcal_de(m, comida)
        etiqueta = comida + (
            f'<div style="font-size:11px;font-weight:600;text-transform:none;opacity:.85;'
            f'margin-top:2px">{k} kcal</div>' if k else ""
        )
        filas.append(f'<tr><td class="comida">{etiqueta}</td>{tds}</tr>')
    indic = m[m["comida"] == "Indicaciones"]
    if not indic.empty:
        filas.append(
            f'<tr class="indic"><td class="comida">Indicaciones</td>'
            f'<td colspan="7">{celda_html(indic)}</td></tr>'
        )
    cabecera = "<tr><th>COMIDA</th>" + "".join(f"<th>{d.upper()}</th>" for d in DIAS) + "</tr>"
    return (
        f'{CSS_MENU}<div class="menu-wrap"><table class="menu"><thead>{cabecera}</thead>'
        f'<tbody>{"".join(filas)}</tbody></table></div>'
    )


def menu_dia_html(m: pd.DataFrame, dia: str) -> str:
    m = menu_limpio(m)
    tarjetas = ""
    for comida in ORDEN_COMIDAS[:-1]:
        items = items_de(m, dia, comida)
        if not items.empty:
            tarjetas += f'<div class="card-menu"><div class="c-com">{comida}</div>{celda_html(items)}</div>'
    indic = m[m["comida"] == "Indicaciones"]
    if not indic.empty:
        tarjetas += (
            f'<div class="card-menu indic"><div class="c-com">Indicaciones</div>'
            f"{celda_html(indic)}</div>"
        )
    return f'{CSS_MENU}<div class="dia-head">{dia}</div>{tarjetas}'


CSS_CUADRICULA = """<style>
.block-container { max-width: 1500px !important; }
.g-head { background:#6F9A7C; color:#fff; border-radius:10px; text-align:center; padding:8px 4px;
  font-weight:800; font-size:.78rem; letter-spacing:.6px; }
.g-comida { background:#E5EFE2; color:#36594A; border-radius:10px; text-align:center; padding:10px 4px;
  font-weight:800; font-size:.8rem; letter-spacing:.5px; margin-bottom:6px; }
textarea { font-size:13.5px !important; line-height:1.4 !important; }
[data-testid="stTextArea"] textarea,
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextArea"] [data-baseweb="base-input"] {
  background-color:#F8F3E6 !important; color:#33433A !important;
  -webkit-text-fill-color:#33433A !important;
}
[data-testid="stTextArea"] textarea { border-radius:12px !important; }
</style>"""

CSS_CUADRICULA_OSCURO = CSS_CUADRICULA.replace(
    "background-color:#F8F3E6 !important; color:#33433A !important;\n  -webkit-text-fill-color:#33433A !important;",
    "background-color:#26332C !important; color:#E4ECE6 !important;\n  -webkit-text-fill-color:#E4ECE6 !important;",
).replace(
    ".g-comida { background:#E5EFE2; color:#36594A;", ".g-comida { background:#2C3D33; color:#BFE3CB;"
).replace(".g-head { background:#6F9A7C;", ".g-head { background:#3F6A50;")


def texto_de(items: pd.DataFrame) -> str:
    """Convierte filas guardadas al texto que se edita en la cuadrícula."""
    bloques = []
    for _, f in items.iterrows():
        lineas = []
        if f["titulo"]:
            lineas.append(f["titulo"].upper())
        if f["platillo"]:
            lineas.append(f["platillo"])
        if f["notas"]:
            lineas += ["", f["notas"]]
        bloques.append("\n".join(lineas))
    return "\n\n".join(bloques)


def capturar_semana(actual: pd.DataFrame, tiempos: list[str], k: str) -> list[dict]:
    """Dibuja la semana como en Canva y devuelve las filas a guardar."""
    st.html(CSS_CUADRICULA_OSCURO if es_oscuro() else CSS_CUADRICULA)
    anchos = [1.1] + [1] * 7
    filas = []

    cab = st.columns(anchos, gap="small")
    cab[0].html('<div class="g-head">COMIDA</div>')
    for col, d in zip(cab[1:], DIAS):
        col.html(f'<div class="g-head">{d.upper()}</div>')

    for comida in tiempos:
        de_c = actual[actual["comida"] == comida]
        solo_todos = not de_c.empty and set(de_c["dia"]) == {"Todos"}
        clave_igual = f"igual_{k}_{comida}"
        igual = st.session_state.get(clave_igual, solo_todos)

        cols = st.columns([1.1, 7] if igual else anchos, gap="small")
        with cols[0]:
            st.html(f'<div class="g-comida">{comida.upper()}</div>')
            st.toggle("Igual toda la semana", value=solo_todos, key=clave_igual)
            kcal = st.number_input(
                "kcal", min_value=0, step=10, value=kcal_de(de_c, comida),
                key=f"kcal_{k}_{comida}", placeholder="kcal", label_visibility="collapsed",
            )
            kcal = kcal or ""

        if igual:
            inicial = texto_de(de_c[de_c["dia"] == "Todos"]) or texto_de(items_de(de_c, "Lunes", comida))
            t = cols[1].text_area(
                comida, label_visibility="collapsed", value=inicial, height=110, key=f"todos_{k}_{comida}",
            )
            if t.strip():
                filas.append({"dia": "Todos", "comida": comida, "titulo": "", "platillo": t.strip(),
                              "notas": "", "kcal": kcal})
        else:
            for col, d in zip(cols[1:], DIAS):
                t = col.text_area(
                    f"{comida} {d}", label_visibility="collapsed", value=texto_de(items_de(de_c, d, comida)), height=170,
                    key=f"c_{k}_{comida}_{d}",
                    placeholder="OMELETTE\n2 huevos + espinacas\n\n2 tortillas" if d == "Lunes" else "",
                )
                if t.strip():
                    filas.append({"dia": d, "comida": comida, "titulo": "", "platillo": t.strip(),
                                  "notas": "", "kcal": kcal})
        st.write("")

    # Indicaciones (agua, etc.)
    cols = st.columns([1.1, 7], gap="small")
    cols[0].html('<div class="g-comida">INDICACIONES</div>')
    t = cols[1].text_area(
        "Indicaciones", label_visibility="collapsed", value=texto_de(actual[actual["comida"] == "Indicaciones"]), height=80,
        key=f"indic_{k}", placeholder="2.8 litros de agua al día (11 vasos aprox)…",
    )
    if t.strip():
        filas.append({"dia": "Todos", "comida": "Indicaciones", "titulo": "", "platillo": t.strip(), "notas": ""})
    return filas


def menu_excel(m: pd.DataFrame, nombre: str, vigente) -> bytes:
    """Menú semanal en Excel con el mismo formato de la app."""
    from io import BytesIO

    from openpyxl import Workbook
    from openpyxl.cell.rich_text import CellRichText, TextBlock
    from openpyxl.cell.text import InlineFont
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    m = menu_limpio(m)
    wb = Workbook()
    ws = wb.active
    ws.title = "Menú"

    fino = Side(style="thin", color="C9D8C9")
    borde = Border(left=fino, right=fino, top=fino, bottom=fino)
    verde = PatternFill("solid", fgColor="6F9A7C")
    verde_claro = PatternFill("solid", fgColor="E5EFE2")
    crema = PatternFill("solid", fgColor="F6F0E1")
    centro = Alignment(horizontal="center", vertical="center", wrap_text=True)
    normal = InlineFont(rFont="Calibri", sz=10, color="33433A")
    negrita = InlineFont(rFont="Calibri", sz=10, b=True, color="36594A")

    ws.merge_cells("A1:H1")
    ws["A1"] = f"Menú de {nombre}"
    ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="36594A")
    ws.merge_cells("A2:H2")
    ws["A2"] = f"Vigente desde el {vigente:%d/%m/%Y}" if vigente is not None else ""
    ws["A2"].font = Font(name="Calibri", size=11, color="6B7A70")

    def texto_rico(texto: str):
        partes = CellRichText()
        lineas = [ln.strip() for ln in texto.splitlines()]
        for i, ln in enumerate(lineas):
            fin = "\n" if i < len(lineas) - 1 else ""
            partes.append(TextBlock(negrita if ln and es_titulo(ln) else normal, ln + fin))
        return partes, len(lineas)

    fila = 4
    for col, titulo in enumerate(["COMIDA"] + [d.upper() for d in DIAS], start=1):
        c = ws.cell(fila, col, titulo)
        c.fill, c.alignment, c.border = verde, centro, borde
        c.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    ws.row_dimensions[fila].height = 22

    def fila_comida(etiqueta: str, textos: list[str], relleno=None):
        nonlocal fila
        fila += 1
        c = ws.cell(fila, 1, etiqueta.upper())
        c.fill, c.alignment, c.border = verde_claro, centro, borde
        c.font = Font(name="Calibri", size=10, bold=True, color="36594A")
        max_lineas, i = 1, 0
        while i < len(textos):
            j = i
            while j + 1 < len(textos) and textos[j + 1] == textos[i]:
                j += 1
            celda = ws.cell(fila, i + 2)
            if textos[i]:
                celda.value, n = texto_rico(textos[i])
                ancho = j - i + 1
                max_lineas = max(max_lineas, n + len(textos[i]) // (30 * ancho))
            for k in range(i, j + 1):
                ws.cell(fila, k + 2).border = borde
                if relleno:
                    ws.cell(fila, k + 2).fill = relleno
            celda.alignment = centro
            if j > i:
                ws.merge_cells(start_row=fila, start_column=i + 2, end_row=fila, end_column=j + 2)
            i = j + 1
        ws.row_dimensions[fila].height = max(30, 14 * max_lineas + 8)

    for comida in ORDEN_COMIDAS[:-1]:
        if comida in set(m["comida"]):
            k = kcal_de(m, comida)
            etiqueta = f"{comida}\n{k} kcal" if k else comida
            fila_comida(etiqueta, [texto_de(items_de(m, d, comida)) for d in DIAS])
    indic = m[m["comida"] == "Indicaciones"]
    if not indic.empty:
        fila_comida("Indicaciones", [texto_de(indic)] * 7, relleno=crema)

    ws.column_dimensions["A"].width = 16
    for letra in "BCDEFGH":
        ws.column_dimensions[letra].width = 26
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    salida = BytesIO()
    wb.save(salida)
    return salida.getvalue()



def menus_de(pid: str):
    """Todos los menús de la paciente: ({fecha: df}, fecha_vigente)."""
    menus = leer("Menus")
    if menus.empty:
        return {}, None
    m = menus[menus["id_paciente"] == pid].copy()
    if m.empty:
        return {}, None
    m["fecha_dt"] = pd.to_datetime(m["fecha_inicio"].apply(fecha_iso), errors="coerce")
    m = m.dropna(subset=["fecha_dt"])
    por_fecha = {f: g for f, g in m.groupby("fecha_dt")}
    if not por_fecha:
        return {}, None
    hoy = pd.Timestamp(ahora_mx().date())
    # El vigente es el más reciente que ya empezó (si no hay, el más próximo)
    ya = [f for f in por_fecha if f <= hoy]
    vigente = max(ya) if ya else min(por_fecha)
    return por_fecha, vigente


def kcal_de(m: pd.DataFrame, comida: str):
    if "kcal" not in m.columns:
        return None
    v = pd.to_numeric(m.loc[m["comida"] == comida, "kcal"], errors="coerce").dropna()
    return int(v.iloc[0]) if not v.empty else None


def comidas_del_dia(m: pd.DataFrame, dia: str) -> list[str]:
    return [c for c in ORDEN_COMIDAS[:-1] if not items_de(m, dia, c).empty]


# ---------------------------------------------------------------- Lista del súper
_CANT = r"(?:\d+/\d+|\d+(?:[.,]\d+)?(?:\s*-\s*\d+)?|[½⅓¼¾]|(?:medi[oa]|un[oa]?)(?=\s))"
_UNID = (
    r"(?:gr|grs|g|kg|ml|lt|l|litros?|tazas?|cucharadas?|cucharaditas?|cdas?|cdtas?|"
    r"rebanadas?|rebs?|reb|piezas?|pzas?|pz|latas?|filetes?|scoops?|sobres?|vasos?|"
    r"porciones?|puños?|tiras?|rodajas?|bolsitas?)\b\.?"
)
_PATRON_CANT = re.compile(rf"^\s*(?:{_CANT})?\s*(?:{_UNID})?\s*(?:de\s+)?", re.IGNORECASE)


def lista_super(m: pd.DataFrame) -> list[dict]:
    """Arma una lista sugerida a partir del menú (cuántos días aparece cada cosa)."""
    m = menu_limpio(m)
    conteo = {}
    for d in DIAS:
        vistos_hoy = set()
        for comida in ORDEN_COMIDAS[:-1]:
            for _, f in items_de(m, d, comida).iterrows():
                for linea in "\n".join([f["platillo"], f["notas"]]).splitlines():
                    linea = linea.strip()
                    if not linea or es_titulo(linea) or sin_acentos(linea).startswith(("elige", "libre")):
                        continue
                    for parte in re.split(r"\s\+\s|\s/\s|,|\by\b(?=\s+\d)", linea):
                        parte = parte.strip(" .;:-")
                        nombre = _PATRON_CANT.sub("", parte).strip(" .;:-()")
                        if len(nombre) < 3:
                            continue
                        clave = sin_acentos(nombre)
                        item = conteo.setdefault(clave, {"nombre": nombre[0].upper() + nombre[1:],
                                                         "dias": 0, "ejemplos": []})
                        if clave not in vistos_hoy:
                            item["dias"] += 1
                            vistos_hoy.add(clave)
                        if parte != nombre and parte not in item["ejemplos"] and len(item["ejemplos"]) < 2:
                            item["ejemplos"].append(parte)
    return sorted(conteo.values(), key=lambda x: (-x["dias"], x["nombre"]))


# ---------------------------------------------------------------- Tarjetas de comida
def tarjeta_comida(m: pd.DataFrame, dia: str, comida: str, hecho: bool, clave: str,
                   marcar=None, kcal=None):
    items = items_de(m, dia, comida)
    with st.container(key=f"tarjeta_{'ok_' if hecho else ''}{clave}"):
        kc = f'<span class="kc">{kcal} kcal</span>' if kcal else ""
        cuerpo = celda_html(items)
        st.html(
            f'<div class="t-com"><span>{"✅ " if hecho else ""}{comida}</span>{kc}</div>'
            f'<div class="t-body">{cuerpo}</div>'
        )
        if marcar is not None:
            st.checkbox("Ya lo comí", value=hecho, key=f"chk_{clave}", on_change=marcar)


def score_html(kcal_hechas, kcal_total, n_hechas, n_total) -> str:
    if kcal_total:
        pct = min(kcal_hechas / kcal_total, 1)
        top = (f'<span class="s-num">{kcal_hechas:,}</span>'
               f'<span class="s-de">de {kcal_total:,} kcal</span>')
    else:
        pct = n_hechas / n_total if n_total else 0
        top = f'<span class="s-num">{n_hechas}</span><span class="s-de">de {n_total} comidas</span>'
    if n_hechas == 0:
        msg = "¡Empecemos el día! Marca cada comida al terminarla 💪"
    elif n_hechas < n_total:
        msg = f"¡Vas muy bien! {n_hechas} de {n_total} comidas 🌱"
    else:
        msg = "🎉 ¡Completaste tu menú de hoy!"
    return (
        f'<div class="score"><div class="s-top">🔥 {top}</div>'
        f'<div class="barra"><div style="width:{pct * 100:.0f}%"></div></div>'
        f'<div class="s-msg">{msg}</div></div>'
    )


# ================================================================ Agua, racha e IMC
INSIGNIAS = [
    (3, "🌱", "3 días"),
    (7, "🥉", "1 semana"),
    (15, "🥈", "15 días"),
    (30, "🥇", "1 mes"),
    (60, "🏆", "2 meses"),
]


def edad_de(fecha_nac):
    f = pd.to_datetime(fecha_iso(fecha_nac), errors="coerce")
    if pd.isna(f):
        return None
    hoy = ahora_mx().date()
    return hoy.year - f.year - ((hoy.month, hoy.day) < (f.month, f.day))


def meta_agua_de(p) -> int:
    v = numero(p.get("meta_agua", ""))
    return int(v) if v else 8


def vasos_de(pid: str, fecha: str) -> int:
    agua = leer("Agua")
    if agua.empty:
        return 0
    agua = agua[(agua["id_paciente"] == pid) & (agua["fecha"].apply(fecha_iso) == fecha)]
    v = pd.to_numeric(agua["vasos"], errors="coerce").dropna()
    return int(v.max()) if not v.empty else 0


def guardar_vasos(pid: str, fecha: str, vasos: int):
    """Actualiza el número del día (1 llamada); si es el primer vaso del día, agrega la fila."""
    agua = leer("Agua")
    if not agua.empty:
        filas = agua.index[(agua["id_paciente"] == pid) & (agua["fecha"].apply(fecha_iso) == fecha)]
        if len(filas):
            actualizar_celda("Agua", int(filas[0]), "vasos", max(vasos, 0))
            return
    if vasos > 0:
        agregar_filas("Agua", [{"id_paciente": pid, "fecha": fecha, "vasos": vasos}])


def agua_html(vasos: int, meta: int) -> str:
    gotas = "".join(
        f'<span class="gota{" llena" if i < vasos else ""}">💧</span>' for i in range(max(meta, vasos))
    )
    msg = "🎉 ¡Meta de agua cumplida!" if vasos >= meta else f"Te faltan {meta - vasos} vasos"
    return (
        f'<div class="agua"><div class="a-top"><b>Agua</b> · {vasos} de {meta} vasos'
        f'<span class="a-msg">{msg}</span></div><div class="gotas">{gotas}</div></div>'
    )


def dias_cumplidos(pid: str) -> set:
    """Días (AAAA-MM-DD) en que la paciente marcó al menos el 80% de sus comidas."""
    registro = leer("Registro")
    por_fecha, _ = menus_de(pid)
    if registro.empty or not por_fecha:
        return set()
    r = registro[registro["id_paciente"] == pid].copy()
    if r.empty:
        return set()
    r["fecha"] = r["fecha"].apply(fecha_iso)
    fechas_menu = sorted(por_fecha)
    limpios = {}
    ok = set()
    for f, grupo in r.groupby("fecha"):
        d = pd.Timestamp(f)
        aplicables = [x for x in fechas_menu if x <= d]
        mf = max(aplicables) if aplicables else fechas_menu[0]
        if mf not in limpios:
            limpios[mf] = menu_limpio(por_fecha[mf])
        esperadas = len(comidas_del_dia(limpios[mf], DIAS[d.weekday()]))
        if esperadas and grupo["comida"].nunique() >= max(1, math.ceil(esperadas * 0.8)):
            ok.add(f)
    return ok


def rachas(ok: set, hoy) -> tuple[int, int]:
    """(racha actual, mejor racha). La actual cuenta hasta hoy o hasta ayer."""
    d = hoy if str(hoy) in ok else hoy - timedelta(days=1)
    actual = 0
    while str(d) in ok:
        actual += 1
        d -= timedelta(days=1)
    mejor, corrida, previo = 0, 0, None
    for f in sorted(pd.Timestamp(x).date() for x in ok):
        corrida = corrida + 1 if previo and (f - previo).days == 1 else 1
        mejor = max(mejor, corrida)
        previo = f
    return actual, mejor


def logros_html(mejor: int, actual: int) -> str:
    fichas = ""
    for dias, icono, texto in INSIGNIAS:
        ganada = mejor >= dias
        fichas += (
            f'<div class="insignia{"" if ganada else " bloqueada"}">'
            f'<div class="i-ico">{icono}</div><div class="i-txt">{texto}</div></div>'
        )
    return (
        f'<div class="logros"><div class="l-top">🔥 Racha actual: <b>{actual} día'
        f'{"s" if actual != 1 else ""}</b> · Mejor racha: <b>{mejor}</b></div>'
        f'<div class="insignias">{fichas}</div></div>'
    )


def imc(peso, estatura):
    if peso is None or estatura is None or pd.isna(peso) or not estatura:
        return None
    est = estatura / 100 if estatura > 3 else estatura  # acepta 1.60 o 160
    return peso / (est ** 2)


def categoria_imc(valor) -> str:
    if valor is None:
        return ""
    if valor < 18.5:
        return "Bajo peso"
    if valor < 25:
        return "Normal"
    if valor < 30:
        return "Sobrepeso"
    return "Obesidad"


# ================================================================ PDF del menú (formato de la nutrióloga)
def menu_pdf(m: pd.DataFrame, paciente: dict, fecha_menu, peso=None) -> bytes:
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def limpio(t: str) -> str:
        for a, b in {"⅓": "1/3", "½": "1/2", "¼": "1/4", "¾": "3/4", "⅔": "2/3"}.items():
            t = t.replace(a, b)
        return html.escape(t)

    verde = colors.HexColor("#5E8B6C")
    verde_osc = colors.HexColor("#36594A")
    verde_cl = colors.HexColor("#E5EFE2")
    crema = colors.HexColor("#F6F0E1")
    linea = colors.HexColor("#C9D8C9")
    texto = colors.HexColor("#33433A")

    e_celda = ParagraphStyle("c", fontName="Helvetica", fontSize=8.6, leading=10.6, textColor=texto,
                             alignment=TA_LEFT)
    e_celda_c = ParagraphStyle("cc", parent=e_celda, alignment=TA_CENTER)
    e_tit = ParagraphStyle("t", parent=e_celda, fontName="Helvetica-Bold", textColor=verde_osc,
                           alignment=TA_CENTER, fontSize=9, leading=11)
    e_com = ParagraphStyle("com", parent=e_tit, fontSize=8.2)
    e_head = ParagraphStyle("h", parent=e_celda, fontName="Helvetica-Bold", textColor=colors.white,
                            alignment=TA_CENTER, fontSize=8)

    def celda(texto_celda: str, centrado: bool):
        if not texto_celda.strip():
            return ""
        partes = []
        for ln in texto_celda.splitlines():
            ln = ln.strip()
            if not ln:
                partes.append(Spacer(1, 4))
            elif es_titulo(ln):
                partes.append(Paragraph(limpio(ln), e_tit))
            else:
                partes.append(Paragraph(limpio(ln), e_celda_c if centrado else e_celda))
        return partes

    m = menu_limpio(m)
    responsable = str(st.secrets.get("nombre_nutriologa", "")).upper()
    cedula = str(st.secrets.get("cedula_profesional", ""))
    encabezado = f"NUTRIÓLOGA {responsable or MARCA_NOMBRE.upper()}"
    if cedula:
        encabezado += f"   CED. PROF. {cedula}"
    fecha_txt = f"{fecha_menu.day} {MESES_LARGOS[fecha_menu.month - 1]} {fecha_menu.year}"

    kcal_total = sum(k for k in (kcal_de(m, c) for c in ORDEN_COMIDAS[:-1]) if k)
    edad = edad_de(paciente.get("fecha_nacimiento", ""))
    est = numero(paciente.get("estatura_m", ""))
    datos = [
        f"<b>Paciente:</b> {limpio(str(paciente.get('nombre', '')).upper())}",
        f"<b>Edad:</b> {edad} años" if edad else "",
        f"<b>Peso:</b> {peso:.1f} kg" if peso else "",
        f"<b>Altura:</b> {est:.2f} mts" if est else "",
        f"<b>Kcal diarias:</b> {kcal_total:,}" if kcal_total else "",
    ]
    e_dato = ParagraphStyle("d", parent=e_celda, fontSize=8, textColor=verde_osc)

    ancho_com, ancho_dia = 82, 94
    filas = [[Paragraph("COMIDA", e_head)] + [Paragraph(d.upper(), e_head) for d in DIAS]]
    estilos = [
        ("BACKGROUND", (0, 0), (-1, 0), verde),
        ("GRID", (0, 0), (-1, -1), 0.5, linea),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for comida in ORDEN_COMIDAS[:-1]:
        if comida not in set(m["comida"]):
            continue
        r = len(filas)
        textos = [texto_de(items_de(m, d, comida)) for d in DIAS]
        k = kcal_de(m, comida)
        etiqueta = [Paragraph(limpio(comida.upper()), e_com)]
        if k:
            etiqueta.append(Paragraph(f"{k} kcal", e_celda_c))
        fila = [etiqueta]
        i = 0
        while i < 7:
            j = i
            while j + 1 < 7 and textos[j + 1] == textos[i]:
                j += 1
            fila.append(celda(textos[i], centrado=j > i))
            fila += [""] * (j - i)
            if j > i:
                estilos.append(("SPAN", (i + 1, r), (j + 1, r)))
            i = j + 1
        filas.append(fila)
        estilos.append(("BACKGROUND", (0, r), (0, r), verde_cl))
    indic = m[m["comida"] == "Indicaciones"]
    if not indic.empty:
        r = len(filas)
        filas.append([Paragraph("INDICACIONES", e_com), celda(texto_de(indic), centrado=False)] + [""] * 6)
        estilos += [("SPAN", (1, r), (7, r)), ("BACKGROUND", (0, r), (-1, r), crema)]

    tabla = Table(filas, colWidths=[ancho_com] + [ancho_dia] * 7, repeatRows=1)
    tabla.setStyle(TableStyle(estilos))

    ancho_total = ancho_com + ancho_dia * 7
    from reportlab.platypus import Image as ImagenPDF

    hoja = ImagenPDF(HOJA_BLANCA, width=22, height=22) if HOJA_BLANCA else ""
    cabecera = Table(
        [[hoja,
          Paragraph(limpio(encabezado), ParagraphStyle("e", parent=e_head, alignment=TA_LEFT, fontSize=11)),
          Paragraph(f"Menú: {fecha_txt}", ParagraphStyle("f", parent=e_head, fontSize=10,
                                                          alignment=2))]],
        colWidths=[34, ancho_total * 0.7 - 34, ancho_total * 0.3],
    )
    cabecera.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2F4A34")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    fila_datos = Table(
        [[Paragraph(d, e_dato) for d in datos]],
        colWidths=[ancho_total * 0.32] + [ancho_total * 0.17] * 4,
    )
    fila_datos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), crema),
        ("GRID", (0, 0), (-1, -1), 0.5, linea),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    salida = BytesIO()
    doc = SimpleDocTemplate(
        salida, pagesize=landscape(letter),
        leftMargin=24, rightMargin=24, topMargin=22, bottomMargin=22,
        title=f"Menú {paciente.get('nombre', '')}",
    )
    doc.build([cabecera, fila_datos, Spacer(1, 6), tabla])
    return salida.getvalue()


def ultimo_peso(pid: str):
    med = mediciones_de(pid)
    if med.empty:
        return None
    v = med["peso_kg"].dropna()
    return float(v.iloc[-1]) if not v.empty else None


# ================================================================ Tarjeta para compartir (tipo Spotify Wrapped)
PALETAS_TARJETA = {
    "Bosque": {"arriba": "#2F4A34", "abajo": "#6F9A7C", "texto": "#F7F5EF", "acento": "#CFE6D5",
               "suave": "#B9CDBF", "circulo": "#3E5E45"},
    "Salvia": {"arriba": "#A9CBB1", "abajo": "#E8F1E4", "texto": "#22382A", "acento": "#2F4A34",
               "suave": "#4F6B57", "circulo": "#F7F5EF"},
    "Crema": {"arriba": "#F7F5EF", "abajo": "#E9DCC3", "texto": "#2F4A34", "acento": "#5E8B6C",
              "suave": "#6B7A70", "circulo": "#FFFFFF"},
}


def _fuente(nombre: str, tam: int, variante: str | None = None):
    from PIL import ImageFont

    ruta = ruta_imagen(nombre)
    if ruta:
        try:
            f = ImageFont.truetype(ruta, tam)
            if variante:
                try:
                    f.set_variation_by_name(variante)
                except Exception:
                    pass
            return f
        except OSError:
            pass
    try:
        return ImageFont.truetype("DejaVuSans.ttf", tam)
    except OSError:
        return ImageFont.load_default(tam)


def boton_compartir(png: bytes, nombre_archivo: str):
    """Botón que abre el menú de Compartir del celular (Instagram, WhatsApp, Guardar imagen…)."""
    import base64
    import json

    import streamlit.components.v1 as components

    datos = base64.b64encode(png).decode()
    components.html(
        f"""
<button id="compartir" style="width:100%;padding:13px 16px;border:none;border-radius:999px;
  background:#5E8B6C;color:#fff;font:600 16px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  cursor:pointer">📤 Compartir</button>
<div id="aviso" style="font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#6b7a70;
  margin-top:6px;text-align:center"></div>
<script>
const datos = "{datos}";
const nombre = {json.dumps(nombre_archivo)};
const aviso = document.getElementById("aviso");
document.getElementById("compartir").addEventListener("click", async () => {{
  try {{
    const bin = atob(datos);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const archivo = new File([bytes], nombre, {{ type: "image/png" }});
    if (navigator.canShare && navigator.canShare({{ files: [archivo] }})) {{
      await navigator.share({{ files: [archivo], title: "Mi progreso" }});
    }} else {{
      aviso.textContent = "Tu navegador no permite compartir directo. Usa Descargar o mantén presionada la imagen.";
    }}
  }} catch (e) {{
    if (e.name !== "AbortError") {{
      aviso.textContent = "No se pudo abrir Compartir aquí. Mantén presionada la imagen para guardarla.";
    }}
  }}
}});
</script>""",
        height=95,
    )


def datos_tarjeta(pid: str, p: dict) -> dict:
    """Junta los números de la paciente para la tarjeta."""
    hoy = ahora_mx().date()
    d = {"nombre": str(p.get("nombre", "")).split()[0].title() if p.get("nombre") else ""}

    med = mediciones_de(pid)
    if not med.empty:
        pesos = med[["fecha", "peso_kg"]].dropna()
        if len(pesos) >= 2:
            ini, fin = float(pesos["peso_kg"].iloc[0]), float(pesos["peso_kg"].iloc[-1])
            d["peso_kg"] = fin - ini
            d["peso_pct"] = (fin - ini) / ini * 100 if ini else None
        cint = med[["fecha", "cintura_cm"]].dropna()
        if len(cint) >= 2:
            d["cintura_cm"] = float(cint["cintura_cm"].iloc[-1]) - float(cint["cintura_cm"].iloc[0])

    inicio = pd.to_datetime(fecha_iso(p.get("fecha_alta", "")), errors="coerce")
    if pd.isna(inicio) and not med.empty:
        inicio = med["fecha"].min()
    if not pd.isna(inicio):
        d["inicio"] = inicio
        d["dias_plan"] = max((pd.Timestamp(hoy) - inicio).days, 0)

    ok = dias_cumplidos(pid)
    d["racha_actual"], d["racha_mejor"] = rachas(ok, hoy)

    registro = leer("Registro")
    d["comidas"] = int((registro["id_paciente"] == pid).sum()) if not registro.empty else 0
    agua = leer("Agua")
    if not agua.empty:
        d["vasos"] = int(pd.to_numeric(agua.loc[agua["id_paciente"] == pid, "vasos"], errors="coerce").fillna(0).sum())
    citas = citas_limpias(leer("Citas"))
    d["consultas"] = int(((citas["id_paciente"] == pid) & (citas["estado"] == "atendida")).sum())
    return d


@st.cache_data(show_spinner=False, max_entries=60)
def tarjeta_png(d: dict, paleta: str, ver_pct: bool, ver_kg: bool, ver_cintura: bool) -> bytes:
    from io import BytesIO

    from PIL import Image, ImageDraw

    ancho, alto = 1080, 1920
    c = PALETAS_TARJETA.get(paleta, PALETAS_TARJETA["Bosque"])

    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    # Fondo degradado
    a, b = rgb(c["arriba"]), rgb(c["abajo"])
    img = Image.new("RGB", (ancho, alto))
    dib = ImageDraw.Draw(img)
    for y in range(alto):
        t = y / (alto - 1)
        dib.line([(0, y), (ancho, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    # Círculos decorativos suaves
    capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    dc.ellipse((640, -220, 1320, 460), fill=rgb(c["acento"]) + (34,))
    dc.ellipse((-260, 1380, 420, 2060), fill=rgb(c["acento"]) + (26,))
    img = Image.alpha_composite(img.convert("RGBA"), capa)
    dib = ImageDraw.Draw(img)

    texto, acento, suave = rgb(c["texto"]), rgb(c["acento"]), rgb(c["suave"])
    serif = lambda t, v="Medium": _fuente("Lora-Variable.ttf", t, v)  # noqa: E731
    sans = lambda t: _fuente("Poppins-Regular.ttf", t)  # noqa: E731
    sans_m = lambda t: _fuente("Poppins-Medium.ttf", t)  # noqa: E731
    sans_b = lambda t: _fuente("Poppins-Bold.ttf", t)  # noqa: E731

    def espaciado(xy, txt, fuente, color, sep, centrado=False):
        x, y = xy
        anchos = [dib.textlength(ch, font=fuente) for ch in txt]
        total = sum(anchos) + sep * (len(txt) - 1)
        if centrado:
            x = (ancho - total) / 2
        for ch, w in zip(txt, anchos):
            dib.text((x, y), ch, font=fuente, fill=color)
            x += w + sep

    # --- Marca
    hoja = ruta_imagen("hoja_blanca.png")
    if hoja:
        h = Image.open(hoja).convert("RGBA").resize((86, 86))
        tinta = Image.new("RGBA", h.size, texto + (255,))
        img.paste(tinta, ((ancho - 86) // 2, 96), h)
    f = serif(58)
    w = dib.textlength(MARCA_NOMBRE, font=f)
    dib.text(((ancho - w) / 2, 196), MARCA_NOMBRE, font=f, fill=texto)
    espaciado((0, 276), MARCA_SUB, sans_m(22), suave, 9, centrado=True)

    # --- Título
    x0 = 90
    dib.text((x0, 360), "Mi progreso", font=serif(118, "SemiBold"), fill=texto)
    sub = d.get("nombre", "")
    if d.get("inicio") is not None:
        ini = d["inicio"]
        sub += f" · desde {MESES_LARGOS[ini.month - 1]} {ini.year}"
    dib.text((x0, 505), sub, font=sans(38), fill=suave)

    # --- Número principal
    peso_kg, peso_pct = d.get("peso_kg"), d.get("peso_pct")
    if ver_kg and peso_kg is not None and abs(peso_kg) >= 0.1:
        grande, l1, l2 = f"{'−' if peso_kg < 0 else '+'}{abs(peso_kg):.1f} kg", "de cambio en mi peso", "desde que empecé mi plan"
    elif ver_pct and peso_pct is not None and abs(peso_pct) >= 0.1:
        grande, l1, l2 = f"{'−' if peso_pct < 0 else '+'}{abs(peso_pct):.1f}%", "de cambio en mi peso", "desde que empecé mi plan"
    elif d.get("racha_mejor", 0) >= 2:
        n = d["racha_mejor"]
        grande, l1, l2 = f"{n} días", "mi mejor racha", "cumpliendo mi menú"
    elif d.get("comidas", 0) > 0:
        grande, l1, l2 = f"{d['comidas']}", "comidas cumplidas", "de mi plan de alimentación"
    else:
        grande, l1, l2 = "Día 1", "empezando mi plan", "con mi nutrióloga"
    fg = sans_b(210)
    while dib.textlength(grande, font=fg) > ancho - 2 * x0 and fg.size > 90:
        fg = sans_b(fg.size - 10)
    dib.text((x0 - 6, 590), grande, font=fg, fill=acento)
    dib.text((x0, 845), l1, font=sans_m(44), fill=texto)
    dib.text((x0, 905), l2, font=sans(40), fill=suave)

    # --- Mis números (estilo ranking)
    filas = []
    if d.get("racha_mejor"):
        filas.append(("Racha más larga", f"{d['racha_mejor']} días"))
    if d.get("comidas"):
        filas.append(("Comidas cumplidas", f"{d['comidas']}"))
    if d.get("vasos"):
        filas.append(("Vasos de agua", f"{d['vasos']}"))
    if ver_cintura and d.get("cintura_cm") is not None and abs(d["cintura_cm"]) >= 0.5:
        filas.append(("Circ. abdominal", f"{'−' if d['cintura_cm'] < 0 else '+'}{abs(d['cintura_cm']):.0f} cm"))
    if d.get("consultas"):
        filas.append(("Consultas", f"{d['consultas']}"))
    if d.get("dias_plan"):
        filas.append(("Días en mi plan", f"{d['dias_plan']}"))
    filas = filas[:5]

    y = 1020
    if filas:
        espaciado((x0, y), "MIS NÚMEROS", sans_m(28), suave, 6)
        y += 70
        for i, (etiqueta, valor) in enumerate(filas, start=1):
            dib.text((x0, y - 10), str(i), font=serif(66, "Bold"), fill=acento)
            dib.text((x0 + 80, y + 4), etiqueta, font=sans(42), fill=texto)
            fv = sans_b(46)
            dib.text((ancho - x0 - dib.textlength(valor, font=fv), y), valor, font=fv, fill=texto)
            y += 98
            if i < len(filas):
                dib.line([(x0 + 80, y - 22), (ancho - x0, y - 22)], fill=suave + (), width=1)

    if not filas:
        fq = serif(76, "Medium")
        dib.text((x0, 1140), "Este es el comienzo", font=fq, fill=texto)
        dib.text((x0, 1240), "de algo muy bueno.", font=fq, fill=texto)

    # --- Logros
    ganadas = [(dias, txt) for dias, _, txt in INSIGNIAS if d.get("racha_mejor", 0) >= dias]
    y = max(y + 20, 1590)
    r = 66
    if ganadas and y + 130 + r <= 1810:
        espaciado((x0, y), "MIS LOGROS", sans_m(28), suave, 6)
        cx, cy = x0 + r, y + 130
        for dias, txt in ganadas[:5]:
            dib.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgb(c["circulo"]), outline=acento, width=4)
            num, uni = (str(dias), "días") if dias < 30 else (("1", "mes") if dias == 30 else ("2", "meses"))
            fn, fu = serif(52, "Bold"), sans_m(22)
            dib.text((cx - dib.textlength(num, font=fn) / 2, cy - 48), num, font=fn, fill=acento)
            dib.text((cx - dib.textlength(uni, font=fu) / 2, cy + 12), uni, font=fu, fill=texto)
            cx += 2 * r + 30

    # --- Pie
    pie = "Mi Nutrición · " + MARCA_NOMBRE
    fp = sans(28)
    dib.text(((ancho - dib.textlength(pie, font=fp)) / 2, 1846), pie, font=fp, fill=suave)

    salida = BytesIO()
    img.convert("RGB").save(salida, format="PNG", optimize=True)
    return salida.getvalue()


# ================================================================ Aviso para agregar a inicio
def tipo_dispositivo() -> str:
    try:
        ua = str(st.context.headers.get("User-Agent", ""))
    except Exception:
        return "otro"
    if any(x in ua for x in ("Instagram", "FBAN", "FBAV", "TikTok")):
        return "app_social"
    if "iPhone" in ua or "iPad" in ua:
        return "iphone_otro" if any(x in ua for x in ("CriOS", "FxiOS", "EdgiOS")) else "iphone"
    if "Android" in ua:
        return "android"
    return "otro"


PASOS_INSTALAR = {
    "iphone": [
        'Toca el botón <span class="btn">Compartir ⬆️</span> en la barra de abajo de Safari.',
        'Desliza hacia abajo y elige <span class="btn">Agregar a inicio ➕</span>.',
        'Toca <span class="btn">Agregar</span> arriba a la derecha. ¡Listo!',
    ],
    "iphone_otro": [
        'Toca el botón <span class="btn">Compartir ⬆️</span> junto a la barra de dirección.',
        'Elige <span class="btn">Agregar a inicio ➕</span>. Si no aparece, abre este link en '
        '<b>Safari</b> y repite.',
        'Toca <span class="btn">Agregar</span>. ¡Listo!',
    ],
    "android": [
        'Toca el menú <span class="btn">⋮</span> arriba a la derecha de Chrome.',
        'Elige <span class="btn">Agregar a pantalla principal</span> o '
        '<span class="btn">Instalar app</span>.',
        'Confirma con <span class="btn">Agregar</span>. ¡Listo!',
    ],
    "app_social": [
        'Toca el menú <span class="btn">⋯</span> de arriba.',
        'Elige <span class="btn">Abrir en el navegador</span> (Safari o Chrome).',
        'Ahí podrás agregarla a tu pantalla de inicio.',
    ],
}


def aviso_instalar(p: dict):
    """Tarjeta con los pasos para guardar la app en el celular (solo celulares)."""
    tipo = tipo_dispositivo()
    if tipo not in PASOS_INSTALAR:
        return
    if str(p.get("app_instalada", "")).strip() or st.session_state.get("ocultar_instalar"):
        return
    pasos = "".join(f"<li>{x}</li>" for x in PASOS_INSTALAR[tipo])
    st.html(
        '<div class="instalar"><div class="i-tit">📲 Guarda Mi Nutrición en tu celular</div>'
        '<div class="i-sub">Así la abres con un toque, como cualquier app.</div>'
        f"<ol>{pasos}</ol></div>"
    )
    c1, c2 = st.columns(2)
    if c1.button("✅ Ya la agregué", key="ya_instalada", use_container_width=True):
        idx = idx_paciente(p["id_paciente"])
        if idx is not None:
            actualizar_celda("Pacientes", idx, "app_instalada", ahora_mx().strftime("%Y-%m-%d"))
        st.session_state.paciente["app_instalada"] = "SI"
        st.rerun()
    if c2.button("Ahora no", key="ocultar_instalar_btn", use_container_width=True):
        st.session_state.ocultar_instalar = True
        st.rerun()


# ================================================================ Aviso de privacidad
def texto_aviso() -> str:
    responsable = st.secrets.get("nombre_nutriologa", "La nutrióloga responsable de tu tratamiento")
    contacto = st.secrets.get("contacto_privacidad", "los datos de contacto de tu nutrióloga")
    return f"""
**Responsable.** {responsable} es responsable del uso y protección de tus datos personales.

**Datos que se recaban.** Datos de identificación y contacto (nombre, teléfono y correo) y
**datos de salud, que la ley considera sensibles**: peso, medidas corporales, porcentaje de grasa
y músculo, objetivo, plan de alimentación, notas de consulta y el registro de las comidas que marques.

**Para qué se usan.** Para dar seguimiento a tu tratamiento nutricional, elaborar tus planes de
alimentación, mostrarte tu progreso y administrar tus citas. No se usan con fines publicitarios.

**Dónde se guardan.** En servicios de Google (Google Sheets y Google Drive) con acceso restringido
a tu nutrióloga.

**Transferencias.** Tus datos no se comparten con terceros, salvo en los casos que la ley lo exija.

**Tus derechos.** Puedes acceder, rectificar, cancelar u oponerte al uso de tus datos (derechos ARCO),
así como revocar tu consentimiento, comunicándote a: {contacto}.

**Cambios.** Cualquier cambio a este aviso se te informará dentro de esta app.
"""


# ================================================================ Login y pantallas previas
def pantalla_login():
    _, c_tema = st.columns([5, 1])
    with c_tema:
        interruptor_tema("login")
    st.html(
        logo_vertical() + '<div class="hero-sub">Tu menú, tu progreso y tus citas en un solo lugar.</div>'
    )
    tab_pac, tab_nut = st.tabs(["🙋‍♀️ Soy paciente", "🩺 Soy la nutrióloga"])

    with tab_pac:
        with st.form("login"):
            pid = st.text_input("Código de paciente", placeholder="P001").strip().upper()
            pwd = st.text_input("Contraseña", type="password")
            entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if entrar:
            pacientes = leer("Pacientes")
            fila = pacientes[pacientes["id_paciente"] == pid]
            if (
                not fila.empty
                and str(fila.iloc[0]["activo"]).strip().upper() == "SI"
                and verificar(pwd, str(fila.iloc[0]["contrasena"]))
            ):
                st.session_state.paciente = fila.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Código o contraseña incorrectos.")

    with tab_nut:
        with st.form("login_admin"):
            pwd = st.text_input("Contraseña de administradora", type="password")
            entrar = st.form_submit_button("Entrar al panel", type="primary", use_container_width=True)
        if entrar:
            if hmac.compare_digest(pwd, str(st.secrets["admin_password"])):
                st.session_state.admin = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")


def boton_salir(clave: str):
    if st.button("Salir", key=clave):
        st.session_state.clear()
        st.rerun()


def pantalla_aviso():
    p = st.session_state.paciente
    st.html(
        '<div class="hero"><div class="logo">🔒</div><h1>Aviso de privacidad</h1>'
        "<p>Antes de empezar, lee cómo cuidamos tu información.</p></div>"
    )
    with st.container(border=True, height=380):
        st.markdown(texto_aviso())
    acepto = st.checkbox(
        "Leí el aviso de privacidad y doy mi consentimiento expreso para el tratamiento de mis "
        "datos personales, incluidos mis datos de salud."
    )
    if st.button("Continuar", type="primary", disabled=not acepto, use_container_width=True):
        idx = idx_paciente(p["id_paciente"])
        momento = ahora_mx().strftime("%Y-%m-%d %H:%M")
        actualizar_celda("Pacientes", idx, "acepto_aviso", momento)
        st.session_state.paciente["acepto_aviso"] = momento
        st.rerun()
    boton_salir("salir_aviso")


def formulario_contrasena(p: dict, pedir_actual: bool, clave: str) -> bool:
    with st.form(clave, clear_on_submit=True):
        actual = st.text_input("Contraseña actual", type="password") if pedir_actual else ""
        nueva = st.text_input("Nueva contraseña", type="password")
        confirma = st.text_input("Repite la nueva contraseña", type="password")
        enviar = st.form_submit_button("Guardar contraseña", type="primary", use_container_width=True)
    if not enviar:
        return False
    idx = idx_paciente(p["id_paciente"])
    guardada = str(leer("Pacientes").loc[idx, "contrasena"])
    if pedir_actual and not verificar(actual, guardada):
        st.error("La contraseña actual no es correcta.")
    elif len(nueva) < 6:
        st.error("La nueva contraseña debe tener al menos 6 caracteres.")
    elif nueva != confirma:
        st.error("Las contraseñas no coinciden.")
    elif verificar(nueva, guardada):
        st.error("Elige una contraseña diferente a la anterior.")
    else:
        actualizar_celda("Pacientes", idx, "contrasena", crear_hash(nueva))
        actualizar_celda("Pacientes", idx, "cambiar_pwd", "NO")
        st.session_state.paciente["cambiar_pwd"] = "NO"
        return True
    return False


def pantalla_primera_contrasena():
    p = st.session_state.paciente
    st.html(
        '<div class="hero"><div class="logo">🔑</div><h1>Crea tu contraseña</h1>'
        "<p>La que te dio tu nutrióloga es temporal. Elige una que solo tú conozcas.</p></div>"
    )
    if formulario_contrasena(p, pedir_actual=False, clave="primera_pwd"):
        st.toast("Contraseña guardada ✅")
        st.rerun()
    boton_salir("salir_pwd")


# ================================================================ Vista paciente
def vista_paciente():
    p = st.session_state.paciente
    pid = p["id_paciente"]
    meta = numero(p.get("meta_peso", ""))

    ahora = ahora_mx()
    hoy_iso = str(ahora.date())
    citas_todas = citas_limpias(leer("Citas"))
    proxima = citas_todas[
        (citas_todas["id_paciente"] == pid)
        & (citas_todas["estado"] == "agendada")
        & (citas_todas["inicio"] > ahora)
    ].sort_values("inicio")

    chips = []
    if str(p.get("objetivo", "")).strip():
        chips.append(f"🎯 {html.escape(str(p['objetivo']))}")
    if not proxima.empty:
        c = proxima.iloc[0]
        chips.append(f"📅 Próxima cita: {fecha_bonita(c['inicio'])} · {c['hora']}")
    else:
        chips.append("📅 Sin cita agendada")
    racha_actual, racha_mejor = rachas(dias_cumplidos(pid), ahora.date())
    if racha_actual:
        chips.append(f"🔥 Racha: {racha_actual} día{'s' if racha_actual != 1 else ''}")
    c_logo, c_tema = st.columns([3, 1], vertical_alignment="center")
    with c_logo:
        st.html(logo_horizontal())
    with c_tema:
        interruptor_tema("paciente")
    nombre_corto = html.escape(str(p["nombre"]).split()[0].title())
    saludo = "Buenos días" if ahora.hour < 12 else "Buenas tardes" if ahora.hour < 19 else "Buenas noches"
    st.html(
        f'<div class="saludo"><div class="s-hola">¡Hola, {nombre_corto}! 🌿</div>'
        f'<div class="s-sub">{saludo}. Aquí tienes todo lo de tu plan.</div>'
        f'<div class="chips">{"".join(f"<span class=chip>{ch}</span>" for ch in chips)}</div></div>'
    )
    aviso_instalar(p)

    tab_menu, tab_progreso, tab_citas = st.tabs(["🍽️ Mi menú", "📈 Mi progreso", "📅 Mis citas"])

    # ---------------------------------------------------------- Mi menú
    with tab_menu:
        por_fecha, vigente = menus_de(pid)
        archivo = pdf_de(pid, str(p["nombre"]))

        if not por_fecha and not archivo:
            vacio("🍽️", "Tu nutrióloga aún no te ha asignado un menú.")
        else:
            elegido = vigente
            if len(por_fecha) > 1:
                fechas = sorted(por_fecha, reverse=True)
                elegido = st.selectbox(
                    "Menú",
                    fechas,
                    index=fechas.index(vigente),
                    format_func=lambda f: (
                        f"{'Vigente' if f == vigente else 'Anterior' if f < vigente else 'Próximo'}"
                        f" · desde el {f:%d/%m/%Y}"
                    ),
                )
            m = menu_limpio(por_fecha[elegido]) if por_fecha else pd.DataFrame()

            vistas = []
            if not m.empty:
                vistas += ["Por día", "Semana", "🛒 Súper"]
            if archivo:
                vistas.append("PDF")
            vista = st.segmented_control(
                "Ver menú", vistas, default=vistas[0], label_visibility="collapsed"
            ) if vistas else None
            vista = vista or (vistas[0] if vistas else None)

            if vista is None:
                vacio("🍽️", "Tu nutrióloga aún no te ha asignado un menú.")
            elif vista == "PDF":
                mostrar_pdf(archivo, "pdf_paciente")

            elif vista == "Por día":
                dia = st.selectbox("Día", DIAS, index=ahora.weekday())
                es_hoy = dia == DIAS[ahora.weekday()] and elegido == vigente
                comidas = comidas_del_dia(m, dia)
                kcal = {c: kcal_de(m, c) for c in comidas}

                hechas = set()
                if es_hoy:
                    registro = leer("Registro")
                    if not registro.empty:
                        registro["fecha"] = registro["fecha"].apply(fecha_iso)
                        hechas = set(
                            registro.loc[
                                (registro["id_paciente"] == pid) & (registro["fecha"] == hoy_iso),
                                "comida",
                            ]
                        )
                    kcal_total = sum(v for v in kcal.values() if v)
                    kcal_hechas = sum(kcal[c] or 0 for c in comidas if c in hechas)
                    st.html(score_html(
                        kcal_hechas, kcal_total, len(hechas & set(comidas)), len(comidas)
                    ))
                    meta_ag = meta_agua_de(p)
                    vasos = vasos_de(pid, hoy_iso)
                    st.html(agua_html(vasos, meta_ag))
                    a1, a2, _ = st.columns([2, 1, 3])
                    if a1.button("💧 + Un vaso", key="mas_agua", use_container_width=True):
                        guardar_vasos(pid, hoy_iso, vasos + 1)
                        st.rerun()
                    if a2.button("➖", key="menos_agua", use_container_width=True, disabled=vasos == 0):
                        guardar_vasos(pid, hoy_iso, vasos - 1)
                        st.rerun()

                st.html(f'{CSS_MENU}<div class="dia-head">{"Hoy · " if es_hoy else ""}{dia}</div>')
                for comida in comidas:
                    clave = f"{slug(comida)}_{slug(dia)}"
                    marcar = None
                    if es_hoy:
                        def marcar(comida=comida, clave=clave):
                            if st.session_state[f"chk_{clave}"]:
                                agregar_filas("Registro", [{
                                    "id_paciente": pid, "fecha": hoy_iso,
                                    "comida": comida, "kcal": kcal.get(comida) or "",
                                }])
                            else:
                                borrar_donde("Registro", id_paciente=pid, fecha=hoy_iso, comida=comida)
                    tarjeta_comida(m, dia, comida, comida in hechas, clave, marcar, kcal.get(comida))

                indic = m[m["comida"] == "Indicaciones"]
                if not indic.empty:
                    st.html(
                        f'{CSS_MENU}<div class="card-menu indic"><div class="c-com">Indicaciones</div>'
                        f"{celda_html(indic)}</div>"
                    )

            elif vista == "Semana":
                st.html(menu_semana_html(m))

            else:  # Súper
                items = lista_super(m)
                if not items:
                    vacio("🛒", "No pude armar la lista con este menú.")
                else:
                    st.caption("Lista sugerida a partir de tu menú. Revisa las cantidades.")
                    with st.container(border=True):
                        for i, it in enumerate(items):
                            dias = "todos los días" if it["dias"] == 7 else (
                                f"{it['dias']} día" + ("s" if it["dias"] > 1 else ""))
                            ejemplo = f" · {', '.join(it['ejemplos'])}" if it["ejemplos"] else ""
                            st.checkbox(
                                f"**{it['nombre']}**  \n:gray[{dias}{ejemplo}]",
                                key=f"super_{slug(it['nombre'])}_{i}",
                            )

            if vista in ("Por día", "Semana") and not m.empty:
                d1, d2 = st.columns(2)
                try:
                    d1.download_button(
                        "📥 Descargar en Excel",
                        menu_excel(m, str(p["nombre"]), elegido),
                        file_name=f"Menu {p['nombre']} {elegido:%d-%m-%Y}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="excel_menu",
                    )
                except ImportError:
                    pass
                try:
                    d2.download_button(
                        "📄 Descargar en PDF",
                        menu_pdf(m, p, elegido, ultimo_peso(pid)),
                        file_name=f"Menu {p['nombre']} {elegido:%d-%m-%Y}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="pdf_menu",
                    )
                except ImportError:
                    pass

    # ---------------------------------------------------------- Mi progreso
    with tab_progreso:
        med = mediciones_de(pid)
        if med.empty:
            vacio("📈", "Aún no tienes mediciones. Aparecerán aquí después de tu primera consulta.")
        else:
            primera, ultima = med.iloc[0], med.iloc[-1]
            st.caption(
                f"Desde {primera['fecha']:%d/%m/%Y} · Última medición {ultima['fecha']:%d/%m/%Y}"
            )
            tarjetas = [
                ("Peso (kg)", "peso_kg", "off"),
                ("Grasa (%)", "grasa_pct", "inverse"),
                ("Circ. abdominal (cm)", "cintura_cm", "inverse"),
            ]
            for col, (nombre, c, color) in zip(st.columns(3), tarjetas):
                if pd.isna(ultima[c]) or pd.isna(primera[c]):
                    col.metric(nombre, "—")
                else:
                    col.metric(
                        nombre,
                        f"{ultima[c]:.1f}",
                        f"{ultima[c] - primera[c]:+.1f}",
                        delta_color=color,
                    )

            datos = []
            if not pd.isna(ultima["peso_kg"]) and not pd.isna(primera["peso_kg"]) and primera["peso_kg"]:
                cambio = (ultima["peso_kg"] - primera["peso_kg"]) / primera["peso_kg"] * 100
                datos.append(f"⚖️ Cambio de peso: <b>{cambio:+.1f}%</b> desde el inicio")
            valor_imc = imc(ultima["peso_kg"], numero(p.get("estatura_m", "")))
            if valor_imc:
                datos.append(f"📐 IMC actual: <b>{valor_imc:.1f}</b>")
            if meta is not None and not pd.isna(ultima["peso_kg"]):
                falta = ultima["peso_kg"] - meta
                if abs(falta) < 0.1:
                    txt = "🎉 ¡Llegaste a tu meta!"
                else:
                    txt = f"te faltan <b>{abs(falta):.1f} kg</b>"
                datos.append(f"🎯 Meta: <b>{meta:g} kg</b> · {txt}")
            if datos:
                st.html('<div class="meta-card">' + "<br>".join(datos) + "</div>")

            elegida = st.selectbox("Ver evolución de", metricas_con_datos(med))
            st.altair_chart(
                grafica_metrica(
                    med, elegida, METRICAS[elegida], meta if METRICAS[elegida] == "peso_kg" else None
                ),
                use_container_width=True,
            )

            notas = med[med["notas"].astype(str).str.strip() != ""]
            if not notas.empty:
                with st.expander("Notas de tus consultas", expanded=False):
                    for _, fila in notas.iloc[::-1].iterrows():
                        st.markdown(f"**{fila['fecha']:%d/%m/%Y}** — {fila['notas']}")

        st.subheader("🏅 Mis logros")
        st.html(logros_html(racha_mejor, racha_actual))
        st.caption("Un día cuenta para tu racha cuando marcas al menos el 80% de tus comidas.")

        st.subheader("📤 Comparte tu progreso")
        with st.container(border=True):
            paleta = st.segmented_control(
                "Color de tu tarjeta", list(PALETAS_TARJETA), default="Bosque", key="paleta_tarjeta"
            ) or "Bosque"
            st.caption("Tú decides qué se ve. Tus datos de peso no aparecen a menos que los actives.")
            o1, o2, o3 = st.columns(3)
            ver_pct = o1.checkbox("% de peso", value=False, key="t_pct")
            ver_kg = o2.checkbox("Kilos", value=False, key="t_kg")
            ver_cin = o3.checkbox("Circ. abdominal", value=False, key="t_cin")
            try:
                png = tarjeta_png(datos_tarjeta(pid, p), paleta, ver_pct, ver_kg, ver_cin)
                nombre_archivo = f"Mi progreso {str(p.get('nombre', '')).split()[0].title()}.png"
                v1, v2 = st.columns([1, 1], vertical_alignment="center")
                v1.image(png, use_container_width=True)
                with v2:
                    boton_compartir(png, nombre_archivo)
                    st.download_button(
                        "📥 Descargar",
                        png,
                        file_name=nombre_archivo,
                        mime="image/png",
                        use_container_width=True,
                        key="descargar_tarjeta",
                    )
                    st.caption(
                        "¿No se abre el menú de compartir? Mantén presionada la imagen "
                        "y elige **Guardar en Fotos** o **Compartir**."
                    )
            except Exception:
                st.caption("No pude generar la tarjeta en este momento.")

    # ---------------------------------------------------------- Citas
    with tab_citas:
        citas = citas_limpias(leer("Citas"))
        mias = citas[
            (citas["id_paciente"] == pid)
            & (citas["estado"] == "agendada")
            & (citas["inicio"] > ahora)
        ].sort_values("inicio")

        st.subheader("Mis próximas citas")
        if mias.empty:
            vacio("📅", "No tienes citas agendadas. Elige un horario aquí abajo.")
        for idx, cita in mias.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{fecha_bonita(cita['inicio'])}** · {cita['hora']} hrs")
                if c2.button("Cancelar", key=f"cancelar_{cita['id_cita']}"):
                    st.session_state.confirmar = cita["id_cita"]

                if st.session_state.get("confirmar") == cita["id_cita"]:
                    st.warning("¿Seguro que quieres cancelar esta cita?")
                    s1, s2 = st.columns(2)
                    if s1.button("Sí, cancelar", key=f"si_{cita['id_cita']}", type="primary"):
                        actualizar_celda("Citas", idx, "estado", "cancelada")
                        st.session_state.pop("confirmar", None)
                        st.toast("Cita cancelada")
                        st.rerun()
                    if s2.button("No", key=f"no_{cita['id_cita']}"):
                        st.session_state.pop("confirmar", None)
                        st.rerun()

        st.subheader("Agendar una cita")
        if not mias.empty:
            st.info("Ya tienes una cita próxima. Si necesitas otro horario, cancélala primero.")
        else:
            opciones = horarios_libres(citas, ahora)
            if not opciones:
                st.caption("No hay horarios disponibles por ahora.")
            else:
                dia = st.selectbox("Día", list(opciones), format_func=fecha_bonita)
                hora = st.radio("Horario", opciones[dia], horizontal=True)
                nota = st.text_input("Motivo o comentario (opcional)")

                if st.button("Agendar cita", type="primary", use_container_width=True):
                    # Volver a leer en vivo por si alguien tomó el horario hace un momento
                    actuales = citas_limpias(_vivo("Citas"))
                    inicio = datetime.strptime(f"{dia} {hora}", "%Y-%m-%d %H:%M")
                    tomado = (
                        (actuales["estado"] == "agendada") & (actuales["inicio"] == inicio)
                    ).any()
                    if tomado:
                        st.error("Ese horario se acaba de ocupar. Elige otro.")
                        invalidar("Citas")
                    else:
                        agregar_filas("Citas", [{
                            "id_cita": siguiente_id(actuales["id_cita"], "C"),
                            "id_paciente": pid,
                            "fecha": str(dia),
                            "hora": hora,
                            "estado": "agendada",
                            "notas": nota,
                        }])
                        st.toast("¡Cita agendada! ✅")
                        st.rerun()

    st.write("")
    with st.expander("⚙️ Mi cuenta"):
        st.markdown("**Cambiar contraseña**")
        if formulario_contrasena(p, pedir_actual=True, clave="cambiar_pwd_cuenta"):
            st.success("Contraseña actualizada ✅")
    boton_salir("salir_paciente")


def bloqueos_limpios() -> pd.DataFrame:
    b = leer("Bloqueos")
    if b.empty:
        return pd.DataFrame(columns=["fecha", "hora", "motivo"])
    b = b.copy()
    b["fecha"] = b["fecha"].apply(fecha_iso)
    b["hora"] = b["hora"].apply(lambda h: hora_hhmm(h) if str(h).strip() else "")
    return b


def horarios_libres(citas: pd.DataFrame, ahora: datetime) -> dict:
    """{fecha: [horas libres]} de los próximos 30 días."""
    horarios = leer("Horarios")
    horarios["dia"] = horarios["dia_semana"].apply(sin_acentos)
    horarios["hora"] = horarios["hora"].apply(hora_hhmm)
    ocupadas = set(citas.loc[citas["estado"] == "agendada", "inicio"].dropna())

    bloq = bloqueos_limpios()
    dias_bloq = set(bloq.loc[bloq["hora"] == "", "fecha"])
    horas_bloq = set(zip(bloq.loc[bloq["hora"] != "", "fecha"], bloq.loc[bloq["hora"] != "", "hora"]))

    opciones = {}
    for i in range(31):
        dia = ahora.date() + timedelta(days=i)
        if str(dia) in dias_bloq:
            continue
        horas = sorted(horarios.loc[horarios["dia"] == sin_acentos(DIAS[dia.weekday()]), "hora"])
        libres = []
        for h in horas:
            inicio = datetime.strptime(f"{dia} {h}", "%Y-%m-%d %H:%M")
            if (
                inicio > ahora + timedelta(hours=2)
                and inicio not in ocupadas
                and (str(dia), h) not in horas_bloq
            ):
                libres.append(h)
        if libres:
            opciones[dia] = libres
    return opciones


# ================================================================ Panel: seguimiento, horario y pagos
def alertas_seguimiento(pacientes: pd.DataFrame, citas: pd.DataFrame, ahora: datetime) -> list:
    """[(id, nombre, [motivos])] de pacientes activas que necesitan seguimiento."""
    if pacientes.empty:
        return []
    registro = leer("Registro")
    if not registro.empty:
        registro = registro.copy()
        registro["fecha"] = registro["fecha"].apply(fecha_iso)
    hace7 = str(ahora.date() - timedelta(days=6))
    resultado = []
    for _, fila in pacientes.iterrows():
        if str(fila.get("activo", "")).upper() != "SI":
            continue
        pid = fila["id_paciente"]
        motivos = []
        suyas = citas[citas["id_paciente"] == pid].dropna(subset=["inicio"])
        proxima = suyas[(suyas["estado"] == "agendada") & (suyas["inicio"] > ahora)]
        atendidas = suyas[suyas["estado"] == "atendida"]
        if proxima.empty:
            if atendidas.empty:
                motivos.append("sin consultas registradas")
            else:
                dias = (ahora - atendidas["inicio"].max()).days
                if dias > 30:
                    motivos.append(f"{dias} días sin cita")
        por_fecha, vigente = menus_de(pid)
        if not por_fecha:
            motivos.append("sin menú")
        else:
            dias_menu = (pd.Timestamp(ahora.date()) - vigente).days
            if dias_menu > 45:
                motivos.append(f"menú de hace {dias_menu} días")
            sin_marcar = registro.empty or registro[
                (registro["id_paciente"] == pid) & (registro["fecha"] >= hace7)
            ].empty
            if sin_marcar:
                motivos.append("no ha marcado comidas en 7 días")
        if motivos:
            resultado.append((pid, str(fila["nombre"]), motivos))
    return resultado


def editar_horario():
    horarios = leer("Horarios")
    actuales = set()
    if not horarios.empty:
        actuales = set(zip(horarios["dia_semana"].apply(sin_acentos), horarios["hora"].apply(hora_hhmm)))
    horas = sorted({f"{h:02d}:00" for h in range(7, 22)} | {h for _, h in actuales})
    tabla = pd.DataFrame(
        {"Hora": horas, **{d: [(sin_acentos(d), h) in actuales for h in horas] for d in DIAS}}
    )
    editado = st.data_editor(
        tabla,
        hide_index=True,
        disabled=["Hora"],
        use_container_width=True,
        key="editor_horario",
        column_config={d: st.column_config.CheckboxColumn(d[:3]) for d in DIAS},
    )
    st.caption("Palomea los horarios en que das consulta. Las citas ya agendadas no se modifican.")
    if st.button("Guardar horario", type="primary"):
        filas = [[d, fila["Hora"]] for d in DIAS for _, fila in editado.iterrows() if fila[d]]
        ws = hoja("Horarios")
        reintentar(ws.clear)
        reintentar(ws.append_rows, [["dia_semana", "hora"]] + filas, value_input_option="RAW")
        invalidar("Horarios")
        st.toast("Horario guardado ✅")
        st.rerun()


def seccion_pagos(pacientes: pd.DataFrame, nombres: dict):
    pagos = leer("Pagos").copy()
    if not pagos.empty:
        pagos["fecha"] = pagos["fecha"].apply(fecha_iso)
        pagos["monto"] = pd.to_numeric(pagos["monto"], errors="coerce").fillna(0)
        pagos["mes"] = pagos["fecha"].str[:7]
    else:
        pagos = pd.DataFrame(columns=HOJAS_NUEVAS["Pagos"] + ["mes"])

    ahora = ahora_mx()
    mes_actual = ahora.strftime("%Y-%m")
    meses = sorted(set(pagos["mes"].dropna()) | {mes_actual}, reverse=True)

    def nombre_mes(m: str) -> str:
        a, n = m.split("-")
        return f"{MESES_LARGOS[int(n) - 1].capitalize()} {a}"

    mes = st.selectbox("Mes", meses, format_func=nombre_mes, key="mes_pagos")
    del_mes = pagos[pagos["mes"] == mes]
    anio, num = map(int, mes.split("-"))
    previo = f"{anio - 1}-12" if num == 1 else f"{anio}-{num - 1:02d}"
    total, total_prev = del_mes["monto"].sum(), pagos.loc[pagos["mes"] == previo, "monto"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos del mes", f"${total:,.0f}", f"{total - total_prev:+,.0f} vs mes anterior"
              if total_prev else None)
    c2.metric("Pagos", len(del_mes))
    c3.metric("Promedio por pago", f"${(total / len(del_mes)) if len(del_mes) else 0:,.0f}")

    # Ingresos de los últimos 6 meses
    ultimos = []
    for i in range(5, -1, -1):
        y, mm = anio, num - i
        while mm <= 0:
            y, mm = y - 1, mm + 12
        clave = f"{y}-{mm:02d}"
        ultimos.append({"mes": f"{MESES[mm - 1]} {str(y)[2:]}", "orden": clave,
                        "total": float(pagos.loc[pagos["mes"] == clave, "monto"].sum())})
    grafica = (
        alt.Chart(pd.DataFrame(ultimos))
        .mark_bar(color=VERDE, cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=34)
        .encode(
            x=alt.X("mes:N", sort=alt.SortField("orden"), title=None),
            y=alt.Y("total:Q", title=None, axis=alt.Axis(format="$,.0f")),
            tooltip=[alt.Tooltip("mes:N", title="Mes"), alt.Tooltip("total:Q", title="Ingresos", format="$,.0f")],
        )
        .properties(height=220, background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor="#6b7a70", labelFont="Nunito",
                        gridColor="#2E3A33" if es_oscuro() else "#E8EFE8",
                        domain=False, ticks=False)
    )
    st.altair_chart(grafica, use_container_width=True)

    precio = numero(st.secrets.get("precio_consulta", "")) or None
    metodos = ["Efectivo", "Transferencia", "Tarjeta"]

    # Citas atendidas sin pago
    citas = citas_limpias(leer("Citas"))
    pagadas = set(pagos["id_cita"].astype(str)) if "id_cita" in pagos.columns else set()
    sin_pago = citas[
        (citas["estado"] == "atendida")
        & (citas["fecha"].str[:7] == mes)
        & (~citas["id_cita"].astype(str).isin(pagadas))
    ].sort_values("inicio")
    if not sin_pago.empty:
        st.subheader(f"Consultas sin pago ({len(sin_pago)})")
        for _, cita in sin_pago.iterrows():
            with st.container(border=True):
                a, b, c, d = st.columns([3, 1.4, 1.6, 1.2], vertical_alignment="bottom")
                a.markdown(
                    f"**{nombres.get(cita['id_paciente'], cita['id_paciente'])}**  \n"
                    f"{fecha_bonita(cita['inicio'])} · {cita['hora']}"
                )
                monto = b.number_input("Monto", min_value=0.0, step=50.0, value=precio,
                                       key=f"monto_{cita['id_cita']}")
                metodo = c.selectbox("Método", metodos, key=f"met_{cita['id_cita']}")
                if d.button("Registrar", key=f"pago_{cita['id_cita']}", use_container_width=True):
                    if not monto:
                        st.error("Escribe el monto.")
                    else:
                        agregar_filas("Pagos", [{
                            "id_pago": siguiente_id(pagos["id_pago"], "PG"),
                            "id_paciente": cita["id_paciente"],
                            "fecha": cita["fecha"],
                            "monto": monto,
                            "metodo": metodo,
                            "concepto": "Consulta",
                            "id_cita": cita["id_cita"],
                        }])
                        st.toast("Pago registrado ✅")
                        st.rerun()

    with st.expander("➕ Registrar otro pago"):
        with st.form("pago_manual", clear_on_submit=True):
            c1, c2 = st.columns(2)
            pid = c1.selectbox(
                "Paciente", pacientes["id_paciente"].tolist(),
                format_func=lambda x: f"{x} · {nombres.get(x, '')}",
            ) if not pacientes.empty else None
            fecha = c2.date_input("Fecha", value=ahora.date(), format="DD/MM/YYYY")
            c3, c4, c5 = st.columns(3)
            monto = c3.number_input("Monto", min_value=0.0, step=50.0, value=precio)
            metodo = c4.selectbox("Método", metodos)
            concepto = c5.selectbox("Concepto", ["Consulta", "Primera consulta", "Paquete", "Otro"])
            guardar = st.form_submit_button("Guardar pago", type="primary")
        if guardar:
            if not pid or not monto:
                st.error("Elige la paciente y escribe el monto.")
            else:
                agregar_filas("Pagos", [{
                    "id_pago": siguiente_id(pagos["id_pago"], "PG"),
                    "id_paciente": pid,
                    "fecha": str(fecha),
                    "monto": monto,
                    "metodo": metodo,
                    "concepto": concepto,
                    "id_cita": "",
                }])
                st.toast("Pago registrado ✅")
                st.rerun()

    st.subheader("Pagos del mes")
    if del_mes.empty:
        st.caption("No hay pagos registrados este mes.")
    for _, pg in del_mes.sort_values("fecha", ascending=False).iterrows():
        with st.container(border=True):
            a, b, c = st.columns([4, 2, 1], vertical_alignment="center")
            f = pd.Timestamp(pg["fecha"])
            a.markdown(
                f"**{nombres.get(pg['id_paciente'], pg['id_paciente'])}**  \n"
                f"{fecha_bonita(f)} · {pg['concepto']} · {pg['metodo']}"
            )
            b.markdown(f"### ${pg['monto']:,.0f}")
            if c.button("🗑️", key=f"bp_{pg['id_pago']}"):
                borrar_donde("Pagos", id_pago=pg["id_pago"])
                st.rerun()


# ================================================================ Panel general
def elegir_paciente(pacientes: pd.DataFrame, clave: str, etiqueta_fija: bool = False):
    if pacientes.empty:
        st.info("Aún no hay pacientes.")
        return None
    nombres = dict(zip(pacientes["id_paciente"], pacientes["nombre"]))
    st.html(f'<div id="ancla_{clave}"></div>')
    with st.container(key=f"selpac_{clave}"):
        pid = st.selectbox(
            "👤 Paciente",
            pacientes["id_paciente"].tolist(),
            format_func=lambda x: f"{x} · {nombres.get(x, '')}",
            key=clave,
        )
    if etiqueta_fija and pid:
        # Se queda en la esquina al bajar; al tocarla regresa al selector
        st.html(
            f'<a class="chip-pac" href="#ancla_{clave}" title="Cambiar de paciente">'
            f'👤 {html.escape(str(nombres.get(pid, pid)))}</a>'
        )
    return pid


def panel_nutriologa():
    col_titulo, col_tema, col_act, col_salir = st.columns([6, 1, 1, 1], vertical_alignment="center")
    with col_titulo:
        st.html(
            '<div class="saludo" style="margin:0;display:flex;align-items:center;gap:22px;flex-wrap:wrap">'
            + logo_horizontal() + '<div class="s-hola" style="margin-left:auto">Panel general</div></div>'
        )
    with col_tema:
        interruptor_tema("panel")
    with col_act:
        if st.button("🔄", key="actualizar_panel", help="Volver a leer los datos del Google Sheet"):
            for hoja_n in ["Pacientes", "Mediciones", "Menus", "Horarios", "Citas", *HOJAS_NUEVAS]:
                invalidar(hoja_n)
            st.toast("Datos actualizados")
            st.rerun()
    with col_salir:
        boton_salir("salir_admin")

    pacientes = leer("Pacientes")
    nombres = dict(zip(pacientes["id_paciente"], pacientes["nombre"]))
    telefonos = dict(zip(pacientes["id_paciente"], pacientes.get("telefono", pd.Series(dtype=str))))

    tab_agenda, tab_pac, tab_med, tab_menu, tab_pagos = st.tabs(
        ["📅 Agenda", "👥 Pacientes", "📏 Mediciones", "🍽️ Menús", "💰 Pagos"]
    )

    # ---------------------------------------------------------- Agenda
    with tab_agenda:
        ahora = ahora_mx()
        citas = citas_limpias(leer("Citas"))
        agendadas = citas[citas["estado"] == "agendada"].dropna(subset=["inicio"])
        hoy = agendadas[agendadas["inicio"].dt.date == ahora.date()]
        proximas = agendadas[agendadas["inicio"] > ahora].sort_values("inicio")
        pendientes = agendadas[agendadas["inicio"] <= ahora].sort_values("inicio")

        activos = (pacientes["activo"].astype(str).str.upper() == "SI").sum() if not pacientes.empty else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Citas hoy", len(hoy))
        c2.metric("Próximas", len(proximas))
        c3.metric("Pacientes activos", int(activos))

        avisos = alertas_seguimiento(pacientes, citas, ahora)
        if avisos:
            with st.expander(f"⚠️ Seguimiento · {len(avisos)} paciente(s)", expanded=True):
                for pid_a, nombre_a, motivos in avisos:
                    a, b = st.columns([4, 1], vertical_alignment="center")
                    a.html(
                        f'<div class="alerta"><b>{html.escape(nombre_a)}</b> · '
                        f'{" · ".join(html.escape(x) for x in motivos)}</div>'
                    )
                    enlace = link_whatsapp(
                        telefonos.get(pid_a, ""),
                        f"Hola {nombre_a.split()[0].title()}, ¿cómo vas con tu plan? "
                        "Cuando gustes agenda tu siguiente cita en la app 🌿",
                    )
                    if enlace:
                        b.link_button("💬 Escribirle", enlace, use_container_width=True)

        def tarjeta_cita(idx, cita, pasada: bool):
            with st.container(border=True):
                a, b = st.columns([3, 2])
                nombre = str(nombres.get(cita["id_paciente"], cita["id_paciente"]))
                a.markdown(f"**{fecha_bonita(cita['inicio'])} · {cita['hora']}**  \n{nombre}")
                if str(cita["notas"]).strip():
                    a.caption(cita["notas"])
                if pasada:
                    if b.button("✅ Atendida", key=f"at_{cita['id_cita']}"):
                        actualizar_celda("Citas", idx, "estado", "atendida")
                        st.rerun()
                    if b.button("✖ No asistió", key=f"na_{cita['id_cita']}"):
                        actualizar_celda("Citas", idx, "estado", "cancelada")
                        st.rerun()
                else:
                    mensaje = (
                        f"Hola {nombre.split()[0].title()}, te recuerdo tu cita de nutrición el "
                        f"{fecha_bonita(cita['inicio']).lower()} a las {cita['hora']} hrs. ¡Te espero! 🌿"
                    )
                    enlace = link_whatsapp(telefonos.get(cita["id_paciente"], ""), mensaje)
                    if enlace:
                        b.link_button("💬 Recordar por WhatsApp", enlace, use_container_width=True)
                    if b.button("Cancelar", key=f"ca_{cita['id_cita']}", use_container_width=True):
                        actualizar_celda("Citas", idx, "estado", "cancelada")
                        st.rerun()

        if not pendientes.empty:
            st.subheader("Por marcar")
            for idx, cita in pendientes.iterrows():
                tarjeta_cita(idx, cita, pasada=True)

        st.subheader("Próximas citas")
        if proximas.empty:
            st.caption("No hay citas próximas.")
        for idx, cita in proximas.iterrows():
            tarjeta_cita(idx, cita, pasada=False)

        # --- Bloqueos
        st.subheader("🚫 Días y horarios bloqueados")
        horarios = leer("Horarios")
        horas_posibles = sorted(set(horarios["hora"].apply(hora_hhmm))) if not horarios.empty else []
        with st.expander("➕ Bloquear días u horarios"):
            with st.form("bloqueo", clear_on_submit=True):
                c1, c2 = st.columns(2)
                desde = c1.date_input("Desde", value=ahora.date(), format="DD/MM/YYYY")
                hasta = c2.date_input("Hasta", value=ahora.date(), format="DD/MM/YYYY")
                que = st.radio("¿Qué bloqueo?", ["Todo el día", "Solo un horario"], horizontal=True)
                hora_b = st.selectbox("Horario", horas_posibles) if horas_posibles else ""
                motivo = st.text_input("Motivo (opcional)", placeholder="Vacaciones")
                bloquear = st.form_submit_button("Bloquear", type="primary")
            if bloquear:
                if hasta < desde:
                    st.error("La fecha final es antes de la inicial.")
                elif (hasta - desde).days > 90:
                    st.error("Bloquea máximo 90 días a la vez.")
                else:
                    hora_guardar = "" if que == "Todo el día" else hora_b
                    dias = [desde + timedelta(days=i) for i in range((hasta - desde).days + 1)]
                    agregar_filas("Bloqueos", [
                        {"fecha": str(d), "hora": hora_guardar, "motivo": motivo.strip()} for d in dias
                    ])
                    afectadas = agendadas[agendadas["inicio"].dt.date.isin(dias)]
                    if hora_guardar:
                        afectadas = afectadas[afectadas["hora"] == hora_guardar]
                    if not afectadas.empty:
                        st.warning(
                            f"Ojo: ya hay {len(afectadas)} cita(s) agendada(s) en ese periodo. "
                            "No se cancelan solas; revísalas en la agenda."
                        )
                    st.toast("Bloqueado ✅")

        bloq = bloqueos_limpios()
        bloq = bloq[bloq["fecha"] >= str(ahora.date())].sort_values(["fecha", "hora"])
        if bloq.empty:
            st.caption("No hay bloqueos próximos.")
        for _, fila in bloq.iterrows():
            with st.container(border=True):
                a, b = st.columns([4, 1], vertical_alignment="center")
                f = pd.Timestamp(fila["fecha"])
                cuando = "todo el día" if not fila["hora"] else f"{fila['hora']} hrs"
                motivo = f" · {fila['motivo']}" if str(fila["motivo"]).strip() else ""
                a.markdown(f"**{fecha_bonita(f)}** · {cuando}{motivo}")
                if b.button("Quitar", key=f"qb_{fila['fecha']}_{fila['hora']}"):
                    borrar_donde("Bloqueos", fecha=fila["fecha"], hora=fila["hora"])
                    st.rerun()

        # --- Horario semanal
        st.subheader("🕒 Horario de atención")
        with st.expander("Editar horario de la semana"):
            editar_horario()

    # ---------------------------------------------------------- Pacientes
    with tab_pac:
        aviso = st.session_state.pop("aviso_panel", None)
        if aviso:
            st.success(aviso)
        st.subheader("Mis pacientes")
        if not pacientes.empty:
            columnas = [c for c in ["id_paciente", "nombre", "telefono", "objetivo", "meta_peso", "activo"]
                        if c in pacientes.columns]
            st.dataframe(pacientes[columnas].astype(str), hide_index=True, use_container_width=True)

        with st.expander("➕ Dar de alta paciente"):
            with st.form("alta", clear_on_submit=True):
                nombre = st.text_input("Nombre completo")
                c1, c2 = st.columns(2)
                telefono = c1.text_input("Teléfono (10 dígitos)")
                correo = c2.text_input("Correo")
                c3, c4 = st.columns(2)
                objetivo = c3.text_input("Objetivo", placeholder="Bajar grasa")
                meta_peso = c4.number_input("Meta de peso (kg)", min_value=0.0, step=0.5, value=None)
                c5, c6, c7 = st.columns(3)
                nacimiento = c5.date_input(
                    "Fecha de nacimiento", value=None, min_value=datetime(1930, 1, 1),
                    max_value=ahora_mx(), format="DD/MM/YYYY",
                )
                estatura = c6.number_input("Estatura (m)", min_value=0.0, max_value=2.5, step=0.01, value=None)
                meta_agua = c7.number_input("Vasos de agua al día", min_value=1, max_value=20, value=8)
                pwd = st.text_input("Contraseña temporal", type="password")
                guardar = st.form_submit_button("Guardar paciente", type="primary")
            if guardar:
                if not nombre.strip() or len(pwd) < 6:
                    st.error("Escribe el nombre y una contraseña de al menos 6 caracteres.")
                else:
                    ids = pacientes["id_paciente"] if not pacientes.empty else pd.Series(dtype=str)
                    nuevo = siguiente_id(ids, "P")
                    agregar_filas("Pacientes", [{
                        "id_paciente": nuevo,
                        "nombre": nombre.strip(),
                        "telefono": telefono.strip(),
                        "correo": correo.strip(),
                        "contrasena": crear_hash(pwd),
                        "objetivo": objetivo.strip(),
                        "fecha_alta": str(ahora_mx().date()),
                        "activo": "SI",
                        "meta_peso": meta_peso if meta_peso else "",
                        "fecha_nacimiento": str(nacimiento) if nacimiento else "",
                        "estatura_m": estatura if estatura else "",
                        "meta_agua": meta_agua,
                        "cambiar_pwd": "SI",
                        "acepto_aviso": "",
                    }])
                    st.session_state.aviso_panel = (
                        f"Paciente creada: **{nombre.strip()}**. Compártele su código **{nuevo}** y su "
                        "contraseña temporal; al entrar se le pedirá crear la suya. "
                        "Ya está seleccionada en Mediciones y Menús."
                    )
                    # Dejarla seleccionada en las demás pestañas
                    for clave in ("pac_med", "pac_menu", "pac_editar", "pac_notas"):
                        st.session_state[clave] = nuevo
                    st.rerun()

        with st.expander("✏️ Editar paciente"):
            pid = elegir_paciente(pacientes, "pac_editar")
            if pid:
                idx = pacientes.index[pacientes["id_paciente"] == pid][0]
                fila_p = pacientes.loc[idx]
                with st.form(f"datos_{pid}"):
                    d1, d2 = st.columns(2)
                    tel_n = d1.text_input("Teléfono", value=str(fila_p.get("telefono", "")))
                    obj_n = d2.text_input("Objetivo", value=str(fila_p.get("objetivo", "")))
                    d3, d4, d5, d6 = st.columns(4)
                    nac_actual = pd.to_datetime(fecha_iso(fila_p.get("fecha_nacimiento", "")), errors="coerce")
                    nac_n = d3.date_input(
                        "Fecha de nacimiento", value=None if pd.isna(nac_actual) else nac_actual.date(),
                        min_value=datetime(1930, 1, 1), max_value=ahora_mx(), format="DD/MM/YYYY",
                    )
                    est_n = d4.number_input(
                        "Estatura (m)", min_value=0.0, max_value=2.5, step=0.01,
                        value=numero(fila_p.get("estatura_m", "")),
                    )
                    meta_n = d5.number_input(
                        "Meta de peso (kg)", min_value=0.0, step=0.5,
                        value=numero(fila_p.get("meta_peso", "")),
                    )
                    agua_n = d6.number_input(
                        "Vasos de agua al día", min_value=1, max_value=20,
                        value=int(numero(fila_p.get("meta_agua", "")) or 8),
                    )
                    guardar_datos = st.form_submit_button("Guardar datos", type="primary")
                if guardar_datos:
                    for col, val in {
                        "telefono": tel_n.strip(),
                        "objetivo": obj_n.strip(),
                        "fecha_nacimiento": str(nac_n) if nac_n else "",
                        "estatura_m": est_n if est_n else "",
                        "meta_peso": meta_n if meta_n else "",
                        "meta_agua": agua_n,
                    }.items():
                        if str(val) != str(fila_p.get(col, "")):
                            actualizar_celda("Pacientes", idx, col, val)
                    st.toast("Datos guardados ✅")
                    st.rerun()

                c1, c2 = st.columns(2)
                nueva = c2.text_input("Contraseña temporal nueva", type="password", key=f"pwd_{pid}")
                if c2.button("Restablecer contraseña", key=f"gpwd_{pid}"):
                    if len(nueva) < 6:
                        st.error("Mínimo 6 caracteres.")
                    else:
                        actualizar_celda("Pacientes", idx, "contrasena", crear_hash(nueva))
                        actualizar_celda("Pacientes", idx, "cambiar_pwd", "SI")
                        st.success("Listo. Al entrar se le pedirá crear una nueva.")
                activa = str(pacientes.loc[idx, "activo"]).upper() == "SI"
                if st.button("Desactivar acceso" if activa else "Activar acceso", key=f"act_{pid}"):
                    actualizar_celda("Pacientes", idx, "activo", "NO" if activa else "SI")
                    st.rerun()

        with st.expander("📝 Notas privadas"):
            st.caption("Solo tú las ves.")
            pid = elegir_paciente(pacientes, "pac_notas")
            if pid:
                with st.form(f"nota_{pid}", clear_on_submit=True):
                    texto = st.text_area("Nueva nota", height=110)
                    guardar = st.form_submit_button("Guardar nota", type="primary")
                if guardar and texto.strip():
                    agregar_filas("NotasPrivadas", [{
                        "id_paciente": pid,
                        "fecha": ahora_mx().strftime("%Y-%m-%d %H:%M:%S"),
                        "nota": texto.strip(),
                    }])
                    st.rerun()
                notas = leer("NotasPrivadas")
                notas = notas[notas["id_paciente"] == pid] if not notas.empty else notas
                for _, n in notas.sort_values("fecha", ascending=False).iterrows():
                    with st.container(border=True):
                        a, b = st.columns([5, 1])
                        f = pd.to_datetime(n["fecha"], errors="coerce")
                        a.caption(f"{f:%d/%m/%Y %H:%M}" if not pd.isna(f) else str(n["fecha"]))
                        a.write(n["nota"])
                        if b.button("🗑️", key=f"bn_{pid}_{n['fecha']}"):
                            borrar_donde("NotasPrivadas", id_paciente=pid, fecha=n["fecha"])
                            st.rerun()

    # ---------------------------------------------------------- Mediciones
    with tab_med:
        pid = elegir_paciente(pacientes, "pac_med", etiqueta_fija=True)
        if pid:
            # Cumplimiento de los últimos 7 días (comidas que la paciente marcó)
            por_fecha, vigente = menus_de(pid)
            registro = leer("Registro")
            if por_fecha and not registro.empty:
                m_v = menu_limpio(por_fecha[vigente])
                hace7 = ahora_mx().date() - timedelta(days=6)
                registro["fecha"] = registro["fecha"].apply(fecha_iso)
                r = registro[(registro["id_paciente"] == pid) & (registro["fecha"] >= str(hace7))]
                esperadas = sum(
                    len(comidas_del_dia(m_v, DIAS[(hace7 + timedelta(days=i)).weekday()]))
                    for i in range(7)
                )
                marcadas = len(r)
                c1, c2, c3 = st.columns(3)
                c1.metric("Comidas marcadas (7 días)", marcadas)
                c2.metric("Cumplimiento", f"{(marcadas / esperadas * 100) if esperadas else 0:.0f}%")
                c3.metric("Días con registro", r["fecha"].nunique())

            with st.form("medicion", clear_on_submit=True):
                fecha = st.date_input(
                    "Fecha de la consulta", value=ahora_mx().date(), format="DD/MM/YYYY"
                )
                c1, c2, c3 = st.columns(3)
                peso = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, value=None)
                grasa = c2.number_input("Grasa (%)", min_value=0.0, step=0.1, value=None)
                musculo = c3.number_input("Músculo (%)", min_value=0.0, max_value=100.0, step=0.1, value=None)
                c4, c5 = st.columns(2)
                cintura = c4.number_input("Circunferencia abdominal (cm)", min_value=0.0, step=0.5, value=None)
                cadera = c5.number_input("Cadera (cm)", min_value=0.0, step=0.5, value=None)
                notas = st.text_area("Notas para la paciente (ella las verá)")
                guardar = st.form_submit_button("Guardar medición", type="primary")
            if guardar:
                if peso is None:
                    st.error("Al menos captura el peso.")
                else:
                    def o_vacio(v):
                        return "" if v is None else v

                    agregar_filas("Mediciones", [{
                        "id_paciente": pid,
                        "fecha": str(fecha),
                        "peso_kg": peso,
                        "cintura_cm": o_vacio(cintura),
                        "cadera_cm": o_vacio(cadera),
                        "grasa_pct": o_vacio(grasa),
                        "musculo_pct": o_vacio(musculo),
                        "notas": notas.strip(),
                    }])
                    st.toast("Medición guardada ✅")
                    st.rerun()

            med = mediciones_de(pid)
            if not med.empty:
                fila_p = pacientes[pacientes["id_paciente"] == pid].iloc[0]
                meta = numero(fila_p.get("meta_peso", ""))
                peso_u = med["peso_kg"].dropna()
                valor_imc = imc(peso_u.iloc[-1] if not peso_u.empty else None,
                                numero(fila_p.get("estatura_m", "")))
                edad = edad_de(fila_p.get("fecha_nacimiento", ""))
                resumen = []
                if edad:
                    resumen.append(f"{edad} años")
                if valor_imc:
                    resumen.append(f"IMC {valor_imc:.1f} ({categoria_imc(valor_imc)})")
                if meta:
                    resumen.append(f"meta {meta:g} kg")
                if resumen:
                    st.caption(" · ".join(resumen))
                elegida = st.selectbox("Ver evolución de", metricas_con_datos(med), key="met_admin")
                st.altair_chart(
                    grafica_metrica(
                        med, elegida, METRICAS[elegida], meta if METRICAS[elegida] == "peso_kg" else None
                    ),
                    use_container_width=True,
                )
                tabla = med.drop(columns=["id_paciente"]).iloc[::-1].copy()
                tabla["fecha"] = tabla["fecha"].dt.strftime("%d/%m/%Y")
                nombres_col = {"fecha": "Fecha", "notas": "Notas", **{c: k for k, c in METRICAS.items()}}
                columnas = ["fecha"] + [c for c in METRICAS.values() if c in tabla and tabla[c].notna().any()]
                if "notas" in tabla:
                    columnas.append("notas")
                tabla = tabla[columnas].rename(columns=nombres_col)
                st.dataframe(tabla, hide_index=True, use_container_width=True)

    # ---------------------------------------------------------- Menús
    with tab_menu:
        pid = elegir_paciente(pacientes, "pac_menu", etiqueta_fija=True)
        if pid:
            nombre_pac = str(nombres.get(pid, ""))
            sub_captura, sub_pdf = st.tabs(["✏️ Capturar menú", "📄 PDF de Canva"])

            with sub_captura:
                menus = leer("Menus")
                todos = (
                    menus[menus["id_paciente"] == pid].copy() if not menus.empty else pd.DataFrame()
                )
                if todos.empty:
                    actual = pd.DataFrame(columns=COLUMNAS_MENU)
                    todos = pd.DataFrame(columns=["fecha_iso"])
                    version = "nuevo"
                else:
                    todos["fecha_iso"] = todos["fecha_inicio"].apply(fecha_iso)
                    version = max(todos["fecha_iso"])
                    actual = menu_limpio(todos[todos["fecha_iso"] == version])

                presentes = [c for c in ORDEN_COMIDAS[:-1] if c in set(actual["comida"])]
                elegidos = st.multiselect(
                    "Tiempos de comida",
                    ORDEN_COMIDAS[:-1],
                    default=presentes or ["Almuerzo", "Colación 1", "Comida", "Colación 2", "Cena"],
                    key=f"tiempos_{pid}_{version}",
                )
                tiempos = [c for c in ORDEN_COMIDAS[:-1] if c in elegidos]

                filas = capturar_semana(actual, tiempos, f"{pid}_{version}")

                total = sum(
                    {f["comida"]: f["kcal"] for f in filas if f.get("kcal")}.values()
                )
                if total:
                    st.caption(f"Total del día: **{total:,} kcal**")

                with st.expander("👀 Vista previa (como lo verá la paciente)"):
                    if filas:
                        st.html(menu_semana_html(pd.DataFrame(filas)))
                    else:
                        st.caption("Aún no hay nada escrito.")

                c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
                inicio = c1.date_input(
                    "Vigente a partir de", value=ahora_mx().date(), format="DD/MM/YYYY"
                )
                if c2.button("💾 Guardar menú", type="primary", use_container_width=True):
                    if not filas:
                        st.error("El menú está vacío.")
                    else:
                        # Si ya existe un menú con esa misma fecha, se reemplaza
                        if (todos["fecha_iso"] == str(inicio)).any():
                            borrar_menu(pid, str(inicio))
                        agregar_filas("Menus", [
                            {"id_paciente": pid, "fecha_inicio": str(inicio), **f} for f in filas
                        ])
                        st.toast("Menú guardado ✅")
                        st.rerun()

                if version != "nuevo":
                    fila_p = pacientes[pacientes["id_paciente"] == pid].iloc[0].to_dict()
                    try:
                        st.download_button(
                            f"📄 Descargar PDF del menú guardado ({pd.to_datetime(version):%d/%m/%Y})",
                            menu_pdf(actual, fila_p, pd.to_datetime(version), ultimo_peso(pid)),
                            file_name=f"{nombre_pac.upper()}. {pd.to_datetime(version):%d-%m-%Y}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"pdf_admin_menu_{pid}",
                        )
                    except ImportError:
                        st.caption("Para el PDF instala: py -m pip install reportlab")

            with sub_pdf:
                archivo = pdf_de(pid, nombre_pac)
                if archivo:
                    fecha_mod = pd.to_datetime(archivo["modifiedTime"]).tz_convert("America/Mexico_City")
                    st.success(
                        f"La paciente ve: **{archivo['name']}** (subido el {fecha_mod:%d/%m/%Y})"
                    )
                    with st.expander("Ver PDF"):
                        mostrar_pdf(archivo, f"pdf_admin_{pid}")
                else:
                    st.info("No encontré un PDF para esta paciente.")

                correo_app = st.secrets["gcp_service_account"]["client_email"]
                with st.expander("¿Cómo subir un PDF?"):
                    st.markdown(
                        f"""1. En Canva: *Compartir → Descargar (PDF)*, o *Guardar en Google Drive*.
2. Ponlo en tu carpeta de Drive de menús, compartida (como Lector) con: `{correo_app}`
3. El nombre debe empezar con el **nombre completo** de la paciente
(*{nombre_pac or "NOMBRE"}. 10 octubre 2026*) o con su **código** (*{pid} 10 octubre 2026*).
4. La paciente ve siempre el más reciente."""
                    )
                if st.button("🔄 Buscar PDFs nuevos", key=f"buscar_pdf_{pid}"):
                    listar_pdfs.clear()
                    st.rerun()

    # ---------------------------------------------------------- Pagos
    with tab_pagos:
        seccion_pagos(pacientes, nombres)


# ================================================================ Arranque
if st.session_state.get("admin"):
    panel_nutriologa()
elif "paciente" in st.session_state:
    paciente = st.session_state.paciente
    if not str(paciente.get("acepto_aviso", "")).strip():
        pantalla_aviso()
    elif str(paciente.get("cambiar_pwd", "")).strip().upper() == "SI":
        pantalla_primera_contrasena()
    else:
        vista_paciente()
else:
    pantalla_login()
