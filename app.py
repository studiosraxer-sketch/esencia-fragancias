import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
import json
import os
import base64
import html
import urllib.request
import re
import ssl

# --- IDENTIDAD DE LA EMPRESA (cambia estos dos textos a tu gusto) ---
NOMBRE_EMPRESA = "Esencia Fragancias"
SLOGAN = "Control de ventas, inventario y ganancias"

# El logo se busca junto a app.py con alguno de estos nombres: logo.png, logo.jpg, logo.jpeg, logo.webp, logo.svg
CARPETA_APP = os.path.dirname(os.path.abspath(__file__))

def _buscar_logo():
    for nombre in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp", "logo.svg"):
        ruta = os.path.join(CARPETA_APP, nombre)
        if os.path.isfile(ruta):
            return ruta
    return None

LOGO_RUTA = _buscar_logo()

_icono_pestana = "✨"
if LOGO_RUTA and not LOGO_RUTA.lower().endswith(".svg"):
    try:
        from PIL import Image
        _icono_pestana = Image.open(LOGO_RUTA)
    except Exception:
        _icono_pestana = "✨"

# Configuración de la página
st.set_page_config(page_title=NOMBRE_EMPRESA, page_icon=_icono_pestana, layout="wide")

@st.cache_data
def logo_data_uri():
    """Devuelve el logo como data-URI para incrustarlo en el HTML (o None si no hay logo)."""
    if not LOGO_RUTA:
        return None
    ext = LOGO_RUTA.rsplit(".", 1)[1].lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "svg": "image/svg+xml"}[ext]
    with open(LOGO_RUTA, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()

ESTILOS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
:root{--ac:#111111;--ac-inv:#FFFFFF;--card-bg:rgba(128,128,128,.08);--card-border:rgba(128,128,128,.28);--radius:16px;}
@media (prefers-color-scheme: dark){:root{--ac:#F5F5F5;--ac-inv:#111111;}}
html, body, .stApp, .stMarkdown, p, label, input, textarea, button, select, h1, h2, h3, h4{font-family:'Poppins',system-ui,-apple-system,'Segoe UI',sans-serif;}
.stApp{background-image:radial-gradient(1000px 440px at 8% -8%, rgba(128,128,128,.16), transparent 60%),radial-gradient(900px 420px at 100% 0%, rgba(128,128,128,.10), transparent 55%);background-attachment:fixed;}
.block-container{padding-top:2.2rem;padding-bottom:3rem;}
footer{visibility:hidden;}
.brand-banner{display:flex;align-items:center;gap:1.3rem;padding:1.1rem 1.7rem;border-radius:22px;background:linear-gradient(120deg,#050505 0%,#161616 55%,#383838 100%);border:1px solid rgba(255,255,255,.14);box-shadow:0 14px 34px rgba(0,0,0,.35);margin-bottom:1.5rem;position:relative;overflow:hidden;animation:fadeDown .6s ease both;}
.brand-banner::after{content:"";position:absolute;right:-70px;top:-70px;width:240px;height:240px;border-radius:50%;border:1px solid rgba(255,255,255,.16);animation:floaty 7s ease-in-out infinite;}
.brand-banner::before{content:"";position:absolute;right:110px;bottom:-95px;width:180px;height:180px;border-radius:50%;border:1px solid rgba(255,255,255,.10);animation:floaty 9s ease-in-out infinite reverse;}
.brand-logo{width:78px;height:78px;border-radius:50%;background:rgba(255,255,255,.10);display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 6px 18px rgba(0,0,0,.45);overflow:hidden;font-size:2rem;z-index:1;transition:transform .5s ease;}
.brand-banner:hover .brand-logo{transform:rotate(-6deg) scale(1.06);}
.brand-logo img{width:100%;height:100%;object-fit:cover;}
.brand-text{z-index:1;}
.brand-title{font-size:1.75rem;font-weight:600;line-height:1.15;color:#fff;text-transform:uppercase;letter-spacing:.28em;}
.brand-sub{font-size:.85rem;font-weight:300;color:rgba(255,255,255,.78);margin-top:.35rem;letter-spacing:.06em;}
.stApp h2{font-weight:600;letter-spacing:.01em;padding-bottom:.55rem;margin-bottom:1rem;background:linear-gradient(90deg,var(--ac),transparent) left bottom/110px 3px no-repeat;}
.stApp h3{font-weight:600;}
section[data-testid="stSidebar"]{border-right:1px solid var(--card-border);}
.side-brand{text-align:center;padding:.5rem 0 1rem;animation:fadeDown .6s ease both;}
.side-brand img{width:120px;height:120px;object-fit:cover;border-radius:50%;box-shadow:0 8px 22px rgba(0,0,0,.35);transition:transform .5s ease;}
.side-brand img:hover{transform:rotate(-6deg) scale(1.05);}
.side-brand .emoji{font-size:2.6rem;}
.side-brand .nm{font-weight:600;font-size:.95rem;margin-top:.7rem;text-transform:uppercase;letter-spacing:.24em;color:var(--ac);}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:.3rem;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label{width:100%;padding:.6rem .8rem;border-radius:13px;border:1px solid transparent;cursor:pointer;transition:all .22s ease;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover{background:rgba(128,128,128,.14);transform:translateX(4px);}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked){background:rgba(128,128,128,.20);border-color:rgba(128,128,128,.55);font-weight:600;box-shadow:inset 4px 0 0 var(--ac);}
div[data-testid="stForm"]{border:1px solid var(--card-border);border-radius:var(--radius);background:var(--card-bg);padding:1.2rem 1.3rem;transition:box-shadow .25s ease, border-color .25s ease;animation:fadeUp .45s ease both;}
div[data-testid="stForm"]:hover{box-shadow:0 10px 28px rgba(0,0,0,.14);border-color:rgba(128,128,128,.55);}
div[data-testid="stMetric"]{background:var(--card-bg);border:1px solid var(--card-border);border-left:5px solid var(--ac);border-radius:var(--radius);padding:.9rem 1.15rem;transition:transform .22s ease, box-shadow .22s ease;animation:fadeUp .45s ease both;}
div[data-testid="stMetric"]:hover{transform:translateY(-4px);box-shadow:0 12px 26px rgba(0,0,0,.18);}
div[data-testid="stMetricValue"]{font-weight:700;}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button{border-radius:12px;font-weight:600;border:1px solid var(--card-border);transition:transform .15s ease, box-shadow .2s ease, border-color .2s ease;}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover{transform:translateY(-2px);box-shadow:0 9px 20px rgba(0,0,0,.22);border-color:var(--ac);}
.stButton > button:active, .stFormSubmitButton > button:active{transform:translateY(0) scale(.97);}
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"], button[kind="primary"], button[kind="primaryFormSubmit"], .stFormSubmitButton > button{background:var(--ac);color:var(--ac-inv);border:1px solid var(--ac);}
button[data-testid="stBaseButton-primary"] p, button[data-testid="stBaseButton-primaryFormSubmit"] p, .stFormSubmitButton > button p{color:var(--ac-inv);}
button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover, .stFormSubmitButton > button:hover{filter:brightness(1.15);color:var(--ac-inv);}
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"]{border-radius:12px !important;}
div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="textarea"]:focus-within{box-shadow:0 0 0 3px rgba(128,128,128,.35);}
div[data-testid="stAlert"]{border-radius:14px;border:1px solid var(--card-border);animation:fadeUp .4s ease both;}
div[data-testid="stExpander"]{border-radius:14px;border:1px solid var(--card-border);}
div[data-testid="stDataFrame"]{border-radius:14px;overflow:hidden;border:1px solid var(--card-border);box-shadow:0 4px 14px rgba(0,0,0,.08);animation:fadeUp .45s ease both;}
button[data-baseweb="tab"]{font-weight:600;border-radius:10px 10px 0 0;transition:background .2s ease;}
button[data-baseweb="tab"]:hover{background:rgba(128,128,128,.14);}
div[data-baseweb="tab-highlight"]{background:var(--ac) !important;height:3px !important;}
hr{border:none;height:1px;background:linear-gradient(90deg,transparent,var(--card-border),transparent);}
::-webkit-scrollbar{width:9px;height:9px;}
::-webkit-scrollbar-thumb{background:rgba(128,128,128,.55);border-radius:9px;}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}
@keyframes fadeDown{from{opacity:0;transform:translateY(-14px);}to{opacity:1;transform:translateY(0);}}
@keyframes floaty{0%,100%{transform:translateY(0);}50%{transform:translateY(14px);}}
@media (max-width:640px){.brand-title{font-size:1.15rem;letter-spacing:.18em;}.brand-logo{width:56px;height:56px;}.brand-banner{padding:.9rem 1rem;gap:.9rem;}}
@media (prefers-reduced-motion: reduce){*{animation:none !important;transition:none !important;}}
"""

def _tema_actual():
    """'light' o 'dark' según el tema elegido en Streamlit (None si esta versión no lo informa)."""
    try:
        t = st.context.theme.type
        return t if t in ("light", "dark") else None
    except Exception:
        return None

TEMA = _tema_actual()
_override = ""
if TEMA == "dark":
    _override = ":root{--ac:#F5F5F5;--ac-inv:#111111;}"
elif TEMA == "light":
    _override = ":root{--ac:#111111;--ac-inv:#FFFFFF;}"
st.markdown("<style>" + ESTILOS_CSS + _override + "</style>", unsafe_allow_html=True)

# Colores de las gráficas según el tema (acento dorado para la ganancia)
if TEMA == "dark":
    COLORES_GRAF, COLOR_TOP = ["#F5F5F5", "#6B7280", "#D4AF37"], "#F5F5F5"
elif TEMA == "light":
    COLORES_GRAF, COLOR_TOP = ["#111111", "#9CA3AF", "#D4AF37"], "#111111"
else:
    COLORES_GRAF, COLOR_TOP = ["#9CA3AF", "#6B7280", "#D4AF37"], "#9CA3AF"

# --- CONEXIÓN A SUPABASE ---
SUPABASE_URL = "https://lrfftaubtxiadvwaxgbc.supabase.co"
SUPABASE_KEY = "sb_publishable__zmclp9PD_Lkq25kWxo6Vg_eNvVyPeY"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()

# --- FORMULACIÓN OFICIAL AL 30% DE CONCENTRACIÓN ---
RECETAS_BASE = {
    "20 ML": {"fragancia": 5.0, "feromonas": 0.5, "fijador": 0.5, "perfumol": 14.0},
    "30 ML": {"fragancia": 10.0, "feromonas": 1.0, "fijador": 1.0, "perfumol": 18.0},
    "50 ML": {"fragancia": 20.0, "feromonas": 2.0, "fijador": 2.0, "perfumol": 24.0},
    "100 ML": {"fragancia": 30.0, "feromonas": 2.5, "fijador": 2.5, "perfumol": 65.0}
}

def costo_esencia_por_gramo(facturas):
    """Costo promedio ponderado por gramo de cada esencia, según las facturas de compra."""
    acum = {}
    for f in facturas or []:
        try:
            items = json.loads(f.get("items_json") or "[]")
        except Exception:
            continue
        for i in items:
            gramos = float(i.get("cantidad", 0) or 0)
            if i.get("tipo") == "Esencia" and gramos > 0:
                g, c = acum.get(i["nombre"], (0.0, 0.0))
                acum[i["nombre"]] = (g + gramos, c + float(i.get("costo", 0) or 0))
    return {n: c / g for n, (g, c) in acum.items() if g > 0}

def costo_por_frasco(presentacion, esencia, insumos, costos_esencia):
    """Costo de materiales de 1 frasco: esencia + perfumol + fijador + feromonas + frasco."""
    f = RECETAS_BASE.get(presentacion)
    if not f:
        return 0.0
    costo = f["fragancia"] * costos_esencia.get(esencia, 0.0)
    for ins in insumos:
        n = ins["nombre"].lower()
        cu = float(ins.get("costo_unitario") or 0)
        if "perfumol" in n:
            costo += f["perfumol"] * cu
        elif "fijador" in n:
            costo += f["fijador"] * cu
        elif "feromonas" in n:
            costo += f["feromonas"] * cu
        elif presentacion.lower() in n:
            costo += cu
    return costo

def fmt_bs(monto):
    """Formato venezolano: 1.234,56"""
    return f"{monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _tasa_desde_bcv():
    """Lee la tasa USD directamente de la página oficial del BCV (fuente principal)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False          # el sitio del BCV suele fallar con la verificación de su certificado
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request("https://www.bcv.org.ve/", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
        pagina = r.read().decode("utf-8", errors="ignore")
    ini = pagina.index('id="dolar"')
    trozo = pagina[ini:ini + 2500]
    if 'id="euro"' in trozo[10:]:       # no invadir el bloque del euro
        trozo = trozo[:trozo.index('id="euro"', 10)]
    m = re.search(r"<strong>\s*([\d.,]+)\s*</strong>", trozo)
    if not m:
        raise ValueError("No encontré la tasa en la página del BCV")
    txt = m.group(1)
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    tasa = float(txt)
    if tasa <= 0:
        raise ValueError("Tasa inválida")
    f = re.search(r'date-display-single"[^>]*content="(\d{4}-\d{2}-\d{2})', pagina)
    return {"tasa": tasa, "fecha_valor": f.group(1) if f else None, "fuente": "BCV"}

def _tasa_desde_dolarapi():
    """Plan B: servicio gratuito ve.dolarapi.com (puede ir con retraso)."""
    req = urllib.request.Request("https://ve.dolarapi.com/v1/dolares/oficial", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        d = json.loads(r.read().decode("utf-8"))
    tasa = float(d.get("promedio") or d.get("venta") or 0)
    if tasa <= 0:
        raise ValueError("Tasa inválida")
    return {"tasa": tasa, "fecha_valor": None, "fecha": d.get("fechaActualizacion"), "fuente": "DolarApi"}

@st.cache_data(ttl=600, show_spinner=False)
def _descargar_tasa_bcv():
    """Primero la página oficial del BCV; si falla, el servicio alterno. Se guarda 10 min; si todo falla lanza error (no se guarda)."""
    try:
        return _tasa_desde_bcv()
    except Exception:
        return _tasa_desde_dolarapi()

def obtener_tasa_bcv():
    try:
        return _descargar_tasa_bcv()
    except Exception:
        return None

def fecha_tasa_legible(iso):
    """Convierte la fecha de la API a hora de Venezuela (dd/mm/aaaa hh:mm)."""
    try:
        dt = datetime.datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return dt.astimezone(datetime.timezone(datetime.timedelta(hours=-4))).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return None

# Inicializar estados de la sesión
if "carrito_ventas" not in st.session_state:
    st.session_state.carrito_ventas = []

if "confirmar_venta_modal" not in st.session_state:
    st.session_state.confirmar_venta_modal = False

if "carrito_compras" not in st.session_state:
    st.session_state.carrito_compras = []

if "confirmar_compra_modal" not in st.session_state:
    st.session_state.confirmar_compra_modal = False

# --- INTERFAZ PRINCIPAL ---
_logo = logo_data_uri()
_nombre = html.escape(NOMBRE_EMPRESA)
_slogan = html.escape(SLOGAN)
_logo_banner = f'<img src="{_logo}" alt="logo">' if _logo else "✨"
st.markdown(
    f'<div class="brand-banner"><div class="brand-logo">{_logo_banner}</div>'
    f'<div class="brand-text"><div class="brand-title">{_nombre}</div>'
    f'<div class="brand-sub">{_slogan}</div></div></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    if _logo:
        st.markdown(f'<div class="side-brand"><img src="{_logo}" alt="logo"><div class="nm">{_nombre}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="side-brand"><div class="emoji">✨</div><div class="nm">{_nombre}</div></div>', unsafe_allow_html=True)
    menu = st.radio(
        "Menú de Navegación",
        [
            "🛒 Registrar Venta (Multiproducto)",
            "📦 Compras y Entradas (Proveedores)",
            "👤 Cuentas por Cobrar (Créditos)",
            "💧 Catálogo de Esencias",
            "📦 Insumos Generales",
            "🧪 Cálculo de Consumo",
            "📊 Historial Diario de Ventas",
            "📈 Ganancias Mensuales",
            "🏆 Top 10 Fragancias del Mes",
        ],
        label_visibility="collapsed",
    )
    st.caption("📅 " + datetime.date.today().strftime("%d/%m/%Y"))

# ---------------------------------------------------------
# 1. MÓDULO DE VENTAS (CARRITO MULTIPRODUCTO)
# ---------------------------------------------------------
if menu == "🛒 Registrar Venta (Multiproducto)":
    st.header("🛒 Punto de Venta")

    # --- TASA BCV Y CONVERSOR ---
    info_tasa = obtener_tasa_bcv()
    tasa_auto = info_tasa["tasa"] if info_tasa else None
    c_t1, c_t2, c_t3 = st.columns([1.2, 1.6, 1])
    with c_t3:
        if st.button("🔄 Actualizar tasa", use_container_width=True):
            _descargar_tasa_bcv.clear()
            st.rerun()
        usar_manual = st.checkbox("✍️ Tasa manual", key="usar_tasa_manual")
    with c_t2:
        if usar_manual:
            tasa_in = st.number_input("Tasa manual (Bs por $)", min_value=0.0, value=float(tasa_auto or 0.0), step=0.01, format="%.2f", key="tasa_manual_valor")
            tasa_bcv = tasa_in if tasa_in > 0 else None
            st.caption("Estás usando una tasa escrita a mano.")
        else:
            tasa_bcv = tasa_auto
            if info_tasa and info_tasa.get("fuente") == "BCV":
                fv = info_tasa.get("fecha_valor")
                txt_fv = ""
                if fv:
                    try:
                        d_fv = datetime.date.fromisoformat(fv)
                        txt_fv = f" Fecha valor: {d_fv.strftime('%d/%m/%Y')}."
                        if d_fv > datetime.date.today():
                            txt_fv += " ℹ️ Es la tasa de un día futuro (el BCV la publica en la tarde); si hoy aún rige la anterior, usa '✍️ Tasa manual'."
                    except Exception:
                        pass
                st.caption("Tasa oficial leída de bcv.org.ve." + txt_fv)
            elif info_tasa:
                f_leg = fecha_tasa_legible(info_tasa.get("fecha"))
                st.warning("⚠️ No pude leer bcv.org.ve; uso una fuente alterna que puede ir con retraso" + (f" (actualizada {f_leg})" if f_leg else "") + ". Compara con bcv.org.ve o usa '✍️ Tasa manual'.")
            else:
                st.warning("⚠️ No pude obtener la tasa BCV. Pulsa 🔄 o activa '✍️ Tasa manual'.")
    with c_t1:
        st.metric("💱 Tasa BCV (Bs por $)", fmt_bs(tasa_bcv) if tasa_bcv else "—")

    if tasa_bcv:
        with st.expander("🧮 Conversor rápido $ ⇄ Bs"):
            cv1, cv2 = st.columns(2)
            with cv1:
                usd_in = st.number_input("Dólares ($)", min_value=0.0, value=0.0, step=1.0, key="conv_usd")
                st.markdown(f"**= Bs {fmt_bs(usd_in * tasa_bcv)}**")
            with cv2:
                bs_in = st.number_input("Bolívares (Bs)", min_value=0.0, value=0.0, step=100.0, key="conv_bs")
                st.markdown(f"**= $ {bs_in / tasa_bcv:,.2f}**")
    esencias = supabase.table("esencias").select("*").order("nombre").execute().data
    
    if not esencias:
        st.warning("⚠️ Debes registrar primero tus esencias en '💧 Catálogo de Esencias'.")
    else:
        col_izq, col_der = st.columns([1.1, 1.2])
        
        with col_izq:
            st.subheader("➕ Añadir Perfume")
            lista_esencias = [e['nombre'] for e in esencias]
            esencia_sel = st.selectbox("🔍 Esencia", lista_esencias)
            presentacion_sel = st.selectbox("📏 Tamaño", ["20 ML", "30 ML", "50 ML", "100 ML"])
            cant_sel = st.number_input("📦 Cantidad", min_value=1, value=1, step=1)
            precio_sel = st.number_input("💵 Precio ($)", min_value=0.0, value=0.0, step=0.5)
            if tasa_bcv and precio_sel > 0:
                st.caption(f"💱 ≈ Bs {fmt_bs(precio_sel * tasa_bcv)} por unidad")
            
            formula = RECETAS_BASE[presentacion_sel]
            g_req = formula['fragancia'] * cant_sel
            e_obj = [e for e in esencias if e['nombre'] == esencia_sel][0]
            
            st.caption(f"💧 Stock: {e_obj['stock_actual']:.1f}g | Requiere: {g_req:.1f}g")

            insumos_v = supabase.table("insumos").select("*").execute().data or []
            facturas_v = supabase.table("facturas_compras").select("items_json").execute().data
            costos_v = costo_esencia_por_gramo(facturas_v)
            costo_u = costo_por_frasco(presentacion_sel, esencia_sel, insumos_v, costos_v)
            if precio_sel > 0:
                gan_u = precio_sel - costo_u
                sobre_costo = f"{gan_u / costo_u * 100:.0f}%" if costo_u > 0 else "—"
                st.caption(f"🧮 Costo por frasco: ${costo_u:.2f} | Ganancia: ${gan_u:.2f} (margen {gan_u / precio_sel * 100:.0f}% del precio | {sobre_costo} sobre el costo)")
            else:
                st.caption(f"🧮 Costo por frasco: ${costo_u:.2f}")
            if esencia_sel not in costos_v:
                st.caption("⚠️ Esta esencia no tiene compras registradas: su costo cuenta como $0.")
            if not any(presentacion_sel.lower() in i['nombre'].lower() and float(i.get('costo_unitario') or 0) > 0 for i in insumos_v):
                st.caption(f"⚠️ Falta el costo del frasco de {presentacion_sel}: el costo real es mayor al mostrado.")
            
            if st.button("📥 Añadir al Pedido"):
                en_pedido = sum(i['g_esencia'] for i in st.session_state.carrito_ventas if i['esencia_id'] == e_obj['id'])
                if e_obj['stock_actual'] < g_req + en_pedido:
                    st.error(f"❌ Sin stock suficiente de '{esencia_sel}' (ya tienes {en_pedido:.1f}g de esta esencia en el pedido).")
                else:
                    item_carrito = {
                        "esencia": esencia_sel,
                        "esencia_id": e_obj['id'],
                        "presentacion": presentacion_sel,
                        "cantidad": cant_sel,
                        "precio_unitario": precio_sel,
                        "subtotal": cant_sel * precio_sel,
                        "g_esencia": g_req,
                        "ml_perfumol": formula['perfumol'] * cant_sel,
                        "g_fijador": formula['fijador'] * cant_sel,
                        "g_feromonas": formula['feromonas'] * cant_sel
                    }
                    st.session_state.carrito_ventas.append(item_carrito)
                    st.rerun()

        with col_der:
            st.subheader("🛍️ Pedido Actual")
            if not st.session_state.carrito_ventas:
                st.info("El pedido está vacío.")
            else:
                total_venta = sum(item['subtotal'] for item in st.session_state.carrito_ventas)
                for idx, item in enumerate(st.session_state.carrito_ventas):
                    c_det, c_sub, c_del = st.columns([3, 1.5, 0.5])
                    c_det.write(f"**{item['cantidad']}x** {item['esencia']} ({item['presentacion']})")
                    c_sub.write(f"${item['subtotal']:.2f}")
                    if tasa_bcv:
                        c_sub.caption(f"Bs {fmt_bs(item['subtotal'] * tasa_bcv)}")
                    if c_del.button("❌", key=f"del_cart_{idx}"):
                        st.session_state.carrito_ventas.pop(idx)
                        st.session_state.confirmar_venta_modal = False
                        st.rerun()
                
                st.divider()
                st.markdown(f"### 💰 Total: **${total_venta:.2f}**")
                if tasa_bcv:
                    st.markdown(f"#### 💱 Bs {fmt_bs(total_venta * tasa_bcv)}")
                    st.caption(f"Tasa BCV aplicada: {fmt_bs(tasa_bcv)} Bs por $")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    fecha_v = st.date_input("📅 Fecha", value=datetime.date.today())
                    tipo_pago = st.selectbox("💳 Pago", ["Pago Móvil", "Efectivo", "Punto de Venta", "Divisas", "Transferencia"])
                with col_p2:
                    condicion = st.selectbox("📌 Condición", ["Contado", "Crédito"])
                    nombre_cliente = "Cliente General"
                    fecha_pago_est = None
                    if condicion == "Crédito":
                        nombre_cliente = st.text_input("👤 Cliente", placeholder="Ej: Juan Pérez")
                        fecha_pago_est = st.date_input("📆 Fecha Cobro", value=datetime.date.today() + datetime.timedelta(days=15))

                if st.button("🚀 Procesar Venta", type="primary", use_container_width=True):
                    if condicion == "Crédito" and (not nombre_cliente or nombre_cliente == "Cliente General"):
                        st.error("⚠️ Para crédito debes ingresar el cliente.")
                    else:
                        st.session_state.confirmar_venta_modal = True

                if st.session_state.get("confirmar_venta_modal", False):
                    st.warning("⚠️ ¿Confirmas procesar esta venta?")
                    monto_bs_txt = f" (Bs {fmt_bs(total_venta * tasa_bcv)})" if tasa_bcv else ""
                    st.write(f"• Monto: ${total_venta:.2f}{monto_bs_txt} | Condición: {condicion} | Cliente: {nombre_cliente}")
                    col_conf_si, col_conf_no = st.columns(2)
                    
                    if col_conf_si.button("✅ Sí, Procesar", key="yes_sale", type="primary", use_container_width=True):
                        insumos_bd = supabase.table("insumos").select("*").execute().data
                        for item in st.session_state.carrito_ventas:
                            e_act = supabase.table("esencias").select("stock_actual").eq("id", item['esencia_id']).execute().data[0]
                            n_stk_e = float(e_act['stock_actual']) - item['g_esencia']
                            supabase.table("esencias").update({"stock_actual": n_stk_e}).eq("id", item['esencia_id']).execute()
                            
                            for ins in insumos_bd:
                                n_low = ins['nombre'].lower()
                                c_desc = 0
                                if "perfumol" in n_low:
                                    c_desc = item['ml_perfumol']
                                elif "fijador" in n_low:
                                    c_desc = item['g_fijador']
                                elif "feromonas" in n_low:
                                    c_desc = item['g_feromonas']
                                elif item['presentacion'].lower() in n_low:
                                    c_desc = item['cantidad']
                                    
                                if c_desc > 0:
                                    n_stk_i = float(ins['stock_actual']) - c_desc
                                    supabase.table("insumos").update({"stock_actual": n_stk_i}).eq("id", ins['id']).execute()
                            
                            v_data = {
                                "esencia_nombre": item['esencia'],
                                "presentacion": item['presentacion'],
                                "cantidad": item['cantidad'],
                                "tipo_pago": tipo_pago,
                                "condicion": condicion,
                                "cliente": nombre_cliente,
                                "total": item['subtotal'],
                                "fecha_venta": str(fecha_v),
                                "fecha_pago_estimada": str(fecha_pago_est) if condicion == "Crédito" else None,
                                "estado_credito": "Pendiente" if condicion == "Crédito" else "Pagado"
                            }
                            supabase.table("ventas").insert(v_data).execute()
                        
                        st.session_state.carrito_ventas = []
                        st.session_state.confirmar_venta_modal = False
                        st.success("🎉 Venta procesada con éxito.")
                        st.rerun()

                    if col_conf_no.button("❌ Cancelar", key="no_sale", use_container_width=True):
                        st.session_state.confirmar_venta_modal = False
                        st.rerun()

# ---------------------------------------------------------
# 2. COMPRAS Y ENTRADAS POR PEDIDO COMPLETO (CON COSTO POR ÍTEM)
# ---------------------------------------------------------
elif menu == "📦 Compras y Entradas (Proveedores)":
    st.header("📦 Compras y Entradas por Pedido / Factura")
    st.caption("Añade cada producto del pedido especificando la cantidad y su costo individual. El sistema totalizará la factura automáticamente.")
    
    esencias_bd = supabase.table("esencias").select("*").order("nombre").execute().data
    insumos_bd = supabase.table("insumos").select("*").order("nombre").execute().data
    
    col_c1, col_c2 = st.columns([1.1, 1.2])
    
    with col_c1:
        st.subheader("➕ Añadir Producto al Pedido")
        tipo_item = st.radio("Tipo de Producto", ["💧 Esencia / Fragancia", "📦 Insumo Base / Frascos"], horizontal=True)
        
        if "Esencia" in tipo_item:
            nombres_e = [e['nombre'] for e in esencias_bd] if esencias_bd else []
            item_sel = st.selectbox("💧 Esencia", nombres_e) if nombres_e else None
            cant_ingresar = st.number_input("📦 Gramos Comprados", min_value=0.0, value=0.0, step=10.0)
            costo_item = st.number_input("💵 Costo de estos Gramos ($)", min_value=0.0, value=0.0, step=0.5, help="Ejemplo: 10$ por los 500g")
            unidad_item = "g"
        else:
            nombres_i = [i['nombre'] for i in insumos_bd] if insumos_bd else []
            item_sel = st.selectbox("📦 Insumo Base", nombres_i) if nombres_i else None
            cant_ingresar = st.number_input("📦 Cantidad Comprada", min_value=0.0, value=0.0, step=1.0)
            costo_item = st.number_input("💵 Costo de esta Cantidad ($)", min_value=0.0, value=0.0, step=0.5, help="Ejemplo: 7$ por los 250ml")
            unidad_item = "unidades"
            if item_sel:
                i_match = [i for i in insumos_bd if i['nombre'] == item_sel]
                if i_match:
                    unidad_item = i_match[0].get('unidad', 'unidades')

        if st.button("📥 Añadir al Pedido"):
            if not item_sel or cant_ingresar <= 0:
                st.error("⚠️ Coloca una cantidad mayor a 0.")
            else:
                st.session_state.carrito_compras.append({
                    "tipo": "Esencia" if "Esencia" in tipo_item else "Insumo",
                    "nombre": item_sel,
                    "cantidad": cant_ingresar,
                    "costo": costo_item,
                    "unidad": unidad_item
                })
                st.success(f"✅ Agregado: {cant_ingresar}{unidad_item} de {item_sel} por ${costo_item:.2f}")

    with col_c2:
        st.subheader("📋 Detalle de la Factura de Compra")
        if not st.session_state.carrito_compras:
            st.info("El pedido está vacío. Agrega los productos desde la izquierda.")
        else:
            total_factura_auto = sum(itm['costo'] for itm in st.session_state.carrito_compras)
            
            for idx, itm in enumerate(st.session_state.carrito_compras):
                c_d, c_m, c_b = st.columns([3, 1.5, 0.5])
                c_d.write(f"• **+{itm['cantidad']} {itm['unidad']}** — {itm['nombre']}")
                c_m.write(f"**${itm['costo']:.2f} USD**")
                if c_b.button("❌", key=f"del_item_c_{idx}"):
                    st.session_state.carrito_compras.pop(idx)
                    st.session_state.confirmar_compra_modal = False
                    st.rerun()
            
            st.divider()
            st.markdown(f"### 💵 Total Invertido en la Factura: **${total_factura_auto:.2f} USD**")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fecha_compra_val = st.date_input("📅 Fecha del Pedido", value=datetime.date.today())
            with col_f2:
                proveedor_val = st.text_input("🏢 Proveedor", placeholder="Ej: Italiana de Fragancias")

            if st.button("🚀 Cargar Factura y Cargar Stock", type="primary", use_container_width=True):
                if not proveedor_val:
                    st.error("⚠️ Ingresa el nombre del proveedor.")
                else:
                    st.session_state.confirmar_compra_modal = True

            if st.session_state.get("confirmar_compra_modal", False):
                st.warning(f"⚠️ ¿Confirmas cargar este pedido de '{proveedor_val}'?")
                st.write(f"• **Inversión Total Calculada:** ${total_factura_auto:.2f} USD")
                st.write(f"• **Artículos:** {len(st.session_state.carrito_compras)} ítems")
                col_c_si, col_c_no = st.columns(2)
                
                if col_c_si.button("✅ Sí, Procesar Factura", key="yes_compra", type="primary", use_container_width=True):
                    for itm in st.session_state.carrito_compras:
                        if itm['tipo'] == "Esencia":
                            e_match = [e for e in esencias_bd if e['nombre'] == itm['nombre']][0]
                            n_stk = float(e_match['stock_actual']) + itm['cantidad']
                            n_ini = float(e_match['stock_inicial']) + itm['cantidad']
                            supabase.table("esencias").update({"stock_actual": n_stk, "stock_inicial": n_ini}).eq("id", e_match['id']).execute()
                        else:
                            i_match = [i for i in insumos_bd if i['nombre'] == itm['nombre']][0]
                            n_stk = float(i_match['stock_actual']) + itm['cantidad']
                            supabase.table("insumos").update({"stock_actual": n_stk}).eq("id", i_match['id']).execute()

                    factura_data = {
                        "fecha_compra": str(fecha_compra_val),
                        "proveedor": proveedor_val.strip(),
                        "items_json": json.dumps(st.session_state.carrito_compras),
                        "costo_total": total_factura_auto
                    }
                    supabase.table("facturas_compras").insert(factura_data).execute()
                    
                    st.session_state.carrito_compras = []
                    st.session_state.confirmar_compra_modal = False
                    st.success("🎉 Factura procesada y stock cargado con éxito.")
                    st.rerun()

                if col_c_no.button("❌ Cancelar", key="no_compra", use_container_width=True):
                    st.session_state.confirmar_compra_modal = False
                    st.rerun()

    st.divider()
    st.subheader("📋 Historial de Facturas Cargadas")
    facturas_hist = supabase.table("facturas_compras").select("*").order("id", desc=True).execute().data
    
    if facturas_hist:
        total_inv = sum(float(f.get("costo_total", 0) or 0) for f in facturas_hist)
        st.metric("💰 Inversión Total Acumulada", f"${total_inv:.2f} USD")
        for f in facturas_hist:
            fid = f['id']
            col_f_info, col_f_del = st.columns([4, 0.5])
            with col_f_info:
                st.markdown(f"### 🏢 {f.get('proveedor')}")
                st.write(f"• **Inversión Factura:** **${float(f.get('costo_total', 0)):.2f} USD** | 📅 **Fecha:** `{f.get('fecha_compra')}`")
                try:
                    items_list = json.loads(f.get("items_json", "[]"))
                    detalles_str = " | ".join([f"+{i['cantidad']}{i['unidad']} {i['nombre']} (${i.get('costo',0):.2f})" for i in items_list])
                    st.caption(f"📦 **Recibido:** {detalles_str}")
                except Exception:
                    pass
            with col_f_del:
                if st.button("🗑️", key=f"btn_del_fact_{fid}"):
                    st.session_state[f"confirm_del_fact_{fid}"] = True
                    
            if st.session_state.get(f"confirm_del_fact_{fid}", False):
                st.error("🚨 ¿Eliminar factura?")
                cy, cn = st.columns(2)
                if cy.button("🗑️ Sí", key=f"yes_df_{fid}", type="primary"):
                    supabase.table("facturas_compras").delete().eq("id", fid).execute()
                    st.session_state[f"confirm_del_fact_{fid}"] = False
                    st.rerun()
                if cn.button("❌ No", key=f"no_df_{fid}"):
                    st.session_state[f"confirm_del_fact_{fid}"] = False
                    st.rerun()
            st.write("---")
    else:
        st.info("Sin facturas cargadas.")

# ---------------------------------------------------------
# 3. CUENTAS POR COBRAR
# ---------------------------------------------------------
elif menu == "👤 Cuentas por Cobrar (Créditos)":
    st.header("👤 Cuentas por Cobrar")
    creditos = supabase.table("ventas").select("*").eq("condicion", "Crédito").order("id", desc=True).execute().data
    
    if creditos:
        tab_pend, tab_pag = st.tabs(["⏳ Deudas Pendientes", "✅ Deudas Cobradas"])
        with tab_pend:
            pendientes = [c for c in creditos if c.get("estado_credito") != "Pagado"]
            monto_pend = sum(float(c.get("total", 0) or 0) for c in pendientes)
            st.metric("💰 Total por Cobrar", f"${monto_pend:.2f}")
            st.divider()
            if pendientes:
                for c in pendientes:
                    cid = c['id']
                    col_info, col_btn = st.columns([3.2, 1.5])
                    with col_info:
                        st.markdown(f"### 👤 {c.get('cliente')}")
                        st.write(f"• **Pedido:** {c.get('cantidad')}x {c.get('esencia_nombre')} ({c.get('presentacion')})")
                        st.write(f"• **Deuda:** ${float(c.get('total', 0)):.2f} USD")
                    with col_btn:
                        c_pag, c_borr = st.columns([2, 1])
                        if c_pag.button("✅ Pagado", key=f"btn_pay_{cid}", type="primary"):
                            supabase.table("ventas").update({"estado_credito": "Pagado"}).eq("id", cid).execute()
                            st.rerun()
                        if c_borr.button("🗑️", key=f"btn_del_cred_{cid}"):
                            supabase.table("ventas").delete().eq("id", cid).execute()
                            st.rerun()
                    st.write("---")
            else:
                st.info("Sin deudas pendientes.")

        with tab_pag:
            pagados = [c for c in creditos if c.get("estado_credito") == "Pagado"]
            if pagados:
                for c in pagados:
                    st.write(f"✅ **{c.get('cliente')}** — ${float(c.get('total', 0)):.2f} USD")
            else:
                st.info("Sin historial de cobros.")
    else:
        st.info("Sin ventas a crédito.")

# ---------------------------------------------------------
# 4. CATÁLOGO DE ESENCIAS
# ---------------------------------------------------------
elif menu == "💧 Catálogo de Esencias":
    st.header("💧 Control de Esencias")
    esencias_actuales = supabase.table("esencias").select("*").order("nombre").execute().data
    col_a, col_b = st.columns([1, 1.3])
    
    with col_a:
        with st.form("nueva_esencia"):
            st.subheader("➕ Registrar Nueva Esencia")
            nombre_e = st.text_input("Nombre de Esencia")
            cant_ingresar = st.number_input("Stock Inicial (Gramos)", min_value=0.0, step=5.0)
            if st.form_submit_button("Guardar"):
                if nombre_e:
                    supabase.table("esencias").insert({"nombre": nombre_e.strip(), "stock_inicial": cant_ingresar, "stock_actual": cant_ingresar}).execute()
                    st.rerun()

        with st.form("ajustar_esencia"):
            st.subheader("⚙️ Ajuste Manual")
            esencia_nombres = [e['nombre'] for e in esencias_actuales] if esencias_actuales else []
            esencia_sel = st.selectbox("Esencia", esencia_nombres) if esencia_nombres else None
            tipo_op = st.radio("Operación", ["➕ Sumar", "➖ Restar"], horizontal=True)
            g_ajuste = st.number_input("Gramos", min_value=0.0, step=1.0)
            if st.form_submit_button("Aplicar"):
                if esencia_sel and g_ajuste > 0:
                    e_obj = [e for e in esencias_actuales if e['nombre'] == esencia_sel][0]
                    nstk = float(e_obj['stock_actual']) + g_ajuste if "Sumar" in tipo_op else float(e_obj['stock_actual']) - g_ajuste
                    supabase.table("esencias").update({"stock_actual": nstk}).eq("id", e_obj['id']).execute()
                    st.rerun()

    with col_b:
        st.subheader("📋 Inventario Actual")
        if esencias_actuales:
            for item in esencias_actuales:
                c1, c2, c3 = st.columns([3, 2, 0.5])
                c1.write(item['nombre'])
                c2.write(f"{float(item['stock_actual']):.1f} g")
                if c3.button("🗑️", key=f"del_e_{item['id']}"):
                    supabase.table("esencias").delete().eq("id", item['id']).execute()
                    st.rerun()
                st.write("---")

# ---------------------------------------------------------
# 5. INSUMOS GENERALES
# ---------------------------------------------------------
elif menu == "📦 Insumos Generales":
    st.header("📦 Insumos Generales")
    if st.session_state.get("msg_insumos"):
        st.success(st.session_state.pop("msg_insumos"))
    insumos_actuales = supabase.table("insumos").select("*").order("nombre").execute().data
    col_a, col_b = st.columns([1, 1.3])
    
    with col_a:
        st.subheader("⚡ Insumos Base")
        st.caption("Crea los insumos que falten (Perfumol, Feromonas, Fijador y frascos de 20, 30, 50 y 100 ml) con stock en 0 y sus costos. Los que ya existan no se duplican.")
        if st.button("⚡ Cargar insumos base"):
            # (nombre, unidad, costo unitario, texto con el que el sistema lo reconoce)
            insumos_base = [
                ("Perfumol", "ml", 0.0030, "perfumol"),
                ("Feromonas", "g", 0.0120, "feromonas"),
                ("Fijador", "g", 0.0095, "fijador"),
                ("Frasco 20 ML", "unidades", 0.0, "20 ml"),
                ("Frasco 30 ML", "unidades", 0.43, "30 ml"),
                ("Frasco 50 ML", "unidades", 0.61, "50 ml"),
                ("Frasco 100 ML", "unidades", 0.95, "100 ml"),
            ]
            creados, actualizados = [], []
            for nombre_b, unidad_b, costo_b, clave in insumos_base:
                existente = next((i for i in (insumos_actuales or []) if clave in i['nombre'].lower()), None)
                if existente is None:
                    supabase.table("insumos").insert({"nombre": nombre_b, "unidad": unidad_b, "stock_actual": 0, "costo_unitario": costo_b}).execute()
                    creados.append(nombre_b)
                elif not float(existente.get('costo_unitario') or 0) and costo_b > 0:
                    supabase.table("insumos").update({"costo_unitario": costo_b}).eq("id", existente['id']).execute()
                    actualizados.append(existente['nombre'])
            partes = []
            if creados:
                partes.append("Creados: " + ", ".join(creados))
            if actualizados:
                partes.append("Costo cargado en: " + ", ".join(actualizados))
            st.session_state.msg_insumos = " | ".join(partes) if partes else "Todos los insumos base ya existían."
            st.rerun()
        st.divider()

        with st.form("nuevo_insumo"):
            st.subheader("➕ Registrar Nuevo Insumo")
            nombre_ins = st.text_input("Nombre Insumo")
            un_med = st.selectbox("Unidad", ["ml", "g", "unidades"])
            stk_ini = st.number_input("Cantidad Inicial", min_value=0.0, step=1.0)
            if st.form_submit_button("Guardar"):
                if nombre_ins:
                    supabase.table("insumos").insert({"nombre": nombre_ins.strip(), "unidad": un_med, "stock_actual": stk_ini, "costo_unitario": 0}).execute()
                    st.rerun()

        with st.form("costo_insumo"):
            st.subheader("💲 Actualizar Costo Unitario")
            nombres_ins = [i['nombre'] for i in insumos_actuales] if insumos_actuales else []
            ins_costo_sel = st.selectbox("Insumo", nombres_ins) if nombres_ins else None
            nuevo_costo = st.number_input("Costo por unidad ($ por ml, g o unidad)", min_value=0.0, step=0.0001, format="%.4f")
            if st.form_submit_button("Guardar costo"):
                if ins_costo_sel:
                    ins_obj = [i for i in insumos_actuales if i['nombre'] == ins_costo_sel][0]
                    supabase.table("insumos").update({"costo_unitario": nuevo_costo}).eq("id", ins_obj['id']).execute()
                    st.rerun()

        with st.form("ajuste_stock_insumo"):
            st.subheader("📏 Ajustar Stock")
            if insumos_actuales:
                opciones_stock = {f"{i['nombre']} (actual: {float(i['stock_actual']):.1f} {i.get('unidad', '')})": i for i in insumos_actuales}
                ins_stock_sel = st.selectbox("Insumo", list(opciones_stock.keys()))
            else:
                opciones_stock, ins_stock_sel = {}, None
                st.caption("Aún no hay insumos para ajustar.")
            modo_ajuste = st.radio("Tipo de ajuste", ["Fijar cantidad exacta", "Sumar", "Restar"], horizontal=True)
            cant_ajuste = st.number_input("Cantidad", min_value=0.0, step=1.0)
            if st.form_submit_button("Aplicar ajuste"):
                if ins_stock_sel:
                    ins_obj = opciones_stock[ins_stock_sel]
                    stock_prev = float(ins_obj['stock_actual'] or 0)
                    if modo_ajuste == "Fijar cantidad exacta":
                        stock_nuevo = cant_ajuste
                    elif modo_ajuste == "Sumar":
                        stock_nuevo = stock_prev + cant_ajuste
                    else:
                        stock_nuevo = stock_prev - cant_ajuste
                    if stock_nuevo < 0:
                        st.error(f"No se puede restar {cant_ajuste:.1f}: el stock actual es {stock_prev:.1f}.")
                    else:
                        supabase.table("insumos").update({"stock_actual": stock_nuevo}).eq("id", ins_obj['id']).execute()
                        st.session_state.msg_insumos = f"Stock de {ins_obj['nombre']}: {stock_prev:.1f} → {stock_nuevo:.1f} {ins_obj.get('unidad', '')}"
                        st.rerun()

    with col_b:
        st.subheader("📋 Inventario Insumos")
        if insumos_actuales:
            for item in insumos_actuales:
                c1, c2, c3 = st.columns([3, 3, 0.5])
                c1.write(item['nombre'])
                c2.write(f"{float(item['stock_actual']):.1f} {item.get('unidad', '')} | ${float(item.get('costo_unitario') or 0):.4f} c/u")
                if c3.button("🗑️", key=f"del_i_{item['id']}"):
                    supabase.table("insumos").delete().eq("id", item['id']).execute()
                    st.rerun()
                st.write("---")

# ---------------------------------------------------------
# 6. CÁLCULO DE CONSUMO
# ---------------------------------------------------------
elif menu == "🧪 Cálculo de Consumo":
    st.header("🧪 Calculadora de Consumo")
    esencias = supabase.table("esencias").select("*").order("nombre").execute().data
    if esencias:
        e_sel = st.selectbox("Esencia", [e['nombre'] for e in esencias])
        p_sel = st.selectbox("Presentación", ["20 ML", "30 ML", "50 ML", "100 ML"])
        c_sel = st.number_input("Frascos", min_value=1, value=1, step=1)
        form = RECETAS_BASE[p_sel]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💧 Esencia", f"{form['fragancia']*c_sel:.1f} g")
        c2.metric("🧪 Perfumol", f"{form['perfumol']*c_sel:.1f} ml")
        c3.metric("✨ Fijador", f"{form['fijador']*c_sel:.1f} g")
        c4.metric("🧬 Feromonas", f"{form['feromonas']*c_sel:.1f} g")

# ---------------------------------------------------------
# 7. HISTORIAL DIARIO DE VENTAS
# ---------------------------------------------------------
elif menu == "📊 Historial Diario de Ventas":
    st.header("📊 Historial Diario")
    fecha_sel = st.date_input("📅 Selecciona la Fecha", value=datetime.date.today())
    ventas = supabase.table("ventas").select("*").order("id", desc=True).execute().data
    ventas_dia = [v for v in ventas if str(v.get("fecha_venta", "")).startswith(str(fecha_sel))] if ventas else []
    
    st.divider()
    monto_dia = sum(float(v.get("total", 0) or 0) for v in ventas_dia)
    st.metric("💵 Total el Día", f"${monto_dia:.2f}")
    if ventas_dia:
        st.dataframe(ventas_dia, use_container_width=True)

# ---------------------------------------------------------
# 8. GANANCIAS MENSUALES
# ---------------------------------------------------------
elif menu == "📈 Ganancias Mensuales":
    st.header("📈 Ganancias Mensuales")
    st.caption("Ganancia = ventas cobradas menos el costo de materiales de lo vendido (esencia, perfumol, fijador, feromonas y frasco). Las ventas a crédito pendientes aparecen como 'Por cobrar' hasta que se marquen como pagadas. 'Compras' es lo invertido en facturas ese mes y no se resta de la ganancia.")
    ventas = supabase.table("ventas").select("*").execute().data
    facturas = supabase.table("facturas_compras").select("*").execute().data
    insumos_c = supabase.table("insumos").select("*").execute().data or []
    costos_e = costo_esencia_por_gramo(facturas)

    ins_sin_costo = [i['nombre'] for i in insumos_c if not float(i.get('costo_unitario') or 0)]
    if ins_sin_costo:
        st.warning("⚠️ Insumos sin costo registrado (se cuentan como $0): " + ", ".join(ins_sin_costo) + ". Cárgalos en '📦 Insumos Generales'.")
    esencias_sin_costo = set()

    def fila_vacia():
        return {"Ventas cobradas": 0.0, "Costo de ventas": 0.0, "Ganancia": 0.0, "Por cobrar": 0.0, "Compras": 0.0}

    filas = {}
    for v in ventas or []:
        if not v.get("fecha_venta"):
            continue
        mes = str(v["fecha_venta"])[:7]
        d = filas.setdefault(mes, fila_vacia())
        t = float(v.get("total", 0) or 0)
        if v.get("estado_credito") == "Pendiente":
            d["Por cobrar"] += t
        else:
            esencia = v.get("esencia_nombre")
            if esencia not in costos_e:
                esencias_sin_costo.add(esencia or "General")
            cant = float(v.get("cantidad", 1) or 1)
            d["Ventas cobradas"] += t
            d["Costo de ventas"] += cant * costo_por_frasco(v.get("presentacion"), esencia, insumos_c, costos_e)
    for f in facturas or []:
        if not f.get("fecha_compra"):
            continue
        mes = str(f["fecha_compra"])[:7]
        d = filas.setdefault(mes, fila_vacia())
        d["Compras"] += float(f.get("costo_total", 0) or 0)

    if esencias_sin_costo:
        st.warning("⚠️ Sin costo de esencia (no hay compras registradas en '📦 Compras y Entradas'): " + ", ".join(sorted(esencias_sin_costo)) + ". Su costo se cuenta como $0 y la ganancia sale más alta de lo real.")

    if not filas:
        st.info("Aún no hay ventas ni compras registradas.")
    else:
        df_mes = pd.DataFrame.from_dict(filas, orient="index")
        df_mes.index.name = "Mes"
        df_mes["Ganancia"] = df_mes["Ventas cobradas"] - df_mes["Costo de ventas"]
        df_mes["Margen %"] = df_mes["Ganancia"] / df_mes["Ventas cobradas"].replace(0, float("nan")) * 100
        df_mes = df_mes.sort_index(ascending=False).round(2)

        mes_sel = st.selectbox("📅 Mes", list(df_mes.index))
        fila = df_mes.loc[mes_sel]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("💵 Ventas cobradas", f"${fila['Ventas cobradas']:.2f}")
        c2.metric("🧪 Costo de ventas", f"${fila['Costo de ventas']:.2f}")
        c3.metric("💰 Ganancia", f"${fila['Ganancia']:.2f}", delta=(f"{fila['Margen %']:.0f}% de margen" if pd.notna(fila['Margen %']) else None))
        c4.metric("⏳ Por cobrar", f"${fila['Por cobrar']:.2f}")
        c5.metric("🛒 Compras", f"${fila['Compras']:.2f}")

        st.divider()
        st.subheader("📅 Resumen por mes")
        st.dataframe(df_mes, use_container_width=True)
        st.bar_chart(df_mes[["Ventas cobradas", "Costo de ventas", "Ganancia"]].sort_index(), color=COLORES_GRAF, use_container_width=True)

# ---------------------------------------------------------
# 9. TOP 10 FRAGANCIAS
# ---------------------------------------------------------
elif menu == "🏆 Top 10 Fragancias del Mes":
    st.header("🏆 Top 10 Fragancias")
    ventas = supabase.table("ventas").select("*").execute().data
    ventas = [v for v in (ventas or []) if v.get("fecha_venta")]
    if not ventas:
        st.info("Aún no hay ventas registradas.")
    else:
        df = pd.DataFrame(ventas)
        df["mes"] = df["fecha_venta"].astype(str).str[:7]
        df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(1)
        df["esencia_nombre"] = df["esencia_nombre"].fillna("General")

        mes_sel = st.selectbox("📅 Mes", sorted(df["mes"].unique(), reverse=True))
        top = (
            df[df["mes"] == mes_sel]
            .groupby("esencia_nombre")["cantidad"].sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        top.columns = ["Fragancia", "Vendidos"]
        top["Vendidos"] = top["Vendidos"].astype(int)
        top.index = range(1, len(top) + 1)

        st.bar_chart(data=top, x="Fragancia", y="Vendidos", color=COLOR_TOP, use_container_width=True)
        st.dataframe(top, use_container_width=True)
