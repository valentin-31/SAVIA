"""
SAVIA — Dashboard de monitoreo satelital de viñedos
Proyecto Integrador · Bases de Datos II · UNdeC 2026

Uso:
    streamlit run app.py

Requiere:
    - MongoDB corriendo en localhost:27017 (docker compose up -d)
    - seed.py ya ejecutado
    - pip install streamlit plotly pandas pymongo python-dotenv
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from dao import SaviaDAO
from db_models import cliente, usuario, parcela, observacion, campana, alerta, reporte

# ── Configuración de página ──────────────────────────────────────────────────

st.set_page_config(
    page_title="SAVIA",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

VERDE      = "#1D9E75"
VERDE_DARK = "#0F6E56"
AZUL       = "#378ADD"
NARANJA    = "#EF9F27"
ROJO       = "#E24B4A"

st.markdown(f"""
<style>
/* Botones de navegación en sidebar */
section[data-testid="stSidebar"] .stButton button {{
    text-align: left;
    justify-content: flex-start;
    font-size: 13px;
    padding: 6px 10px;
}}
/* Badge de estado */
.badge-ok   {{ background:#E1F5EE; color:#0F6E56; padding:2px 10px; border-radius:12px; font-size:12px; font-weight:500 }}
.badge-warn {{ background:#FAEEDA; color:#854F0B; padding:2px 10px; border-radius:12px; font-size:12px; font-weight:500 }}
.badge-red  {{ background:#FCEBEB; color:#A32D2D; padding:2px 10px; border-radius:12px; font-size:12px; font-weight:500 }}
</style>
""", unsafe_allow_html=True)


# ── DAO (singleton por sesión) ───────────────────────────────────────────────

@st.cache_resource
def get_dao() -> SaviaDAO:
    return SaviaDAO()

dao = get_dao()


# ── Session state ────────────────────────────────────────────────────────────

_DEFAULTS = {
    "logged_in":      False,
    "user_name":      None,
    "user_id":        None,
    "rol":            None,
    "cliente_id":     None,
    "cliente_nombre": None,
    "page":           "dashboard",
}

for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers de DB ────────────────────────────────────────────────────────────

def get_parcelas(cliente_id) -> list:
    return list(dao._db.parcelas.find({"cliente_id": cliente_id}))

def get_alertas_cliente(cliente_id) -> list:
    ids = [str(p["_id"]) for p in get_parcelas(cliente_id)]
    return list(dao._db.alertas.find({"parcela_id": {"$in": ids}}))

def nombre_parcelas(cliente_id) -> dict:
    return {str(p["_id"]): p["nombre"] for p in get_parcelas(cliente_id)}

def fmt_fecha(val) -> str:
    return str(val)[:10] if val else "—"


# ── Colores de gráficos ──────────────────────────────────────────────────────

PLOT_LAYOUT = dict(
    height=300,
    margin=dict(l=0, r=0, t=24, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", y=-0.25),
    yaxis=dict(gridcolor="rgba(128,128,128,0.12)"),
    xaxis=dict(gridcolor="rgba(128,128,128,0.12)"),
)

IDX_COLOR = {"ndvi": VERDE, "evi": AZUL, "ndwi": NARANJA}


# ════════════════════════════════════════════════════════════════════════════
# LOGIN
# ════════════════════════════════════════════════════════════════════════════

def show_login():
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("## 🌿 SAVIA")
        st.markdown(
            "Sistema de Almacenamiento de Índices de Vegetación para Investigación Agronómica"
        )
        st.divider()

        # Cargar usuarios activos
        usuarios = list(dao._db.usuarios.find({"activo": True}))
        clientes_map = {
            str(c["_id"]): c["nombre"]
            for c in dao._db.clientes.find({})
        }

        opciones = {"🔐  Superadmin (acceso total al sistema)": None}
        for u in usuarios:
            cname = clientes_map.get(str(u.get("cliente_id", "")), "?")
            label = f"{u['nombre']}  ·  {u['rol']}  ({cname})"
            opciones[label] = u

        seleccion = st.selectbox("Ingresar como:", list(opciones.keys()))

        if st.button("Entrar →", type="primary", use_container_width=True):
            usuario = opciones[seleccion]

            if usuario is None:
                st.session_state.update({
                    "logged_in":      True,
                    "user_name":      "Superadmin",
                    "user_id":        None,
                    "rol":            "superadmin",
                    "cliente_id":     None,
                    "cliente_nombre": "Sistema",
                    "page":           "clientes",
                })
            else:
                cid = usuario.get("cliente_id")
                st.session_state.update({
                    "logged_in":      True,
                    "user_name":      usuario["nombre"],
                    "user_id":        str(usuario["_id"]),
                    "rol":            usuario["rol"],
                    "cliente_id":     cid,
                    "cliente_nombre": clientes_map.get(str(cid), "?"),
                    "page":           "dashboard",
                })
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════

# Menú por rol: (icono, page_id, etiqueta)
MENUS = {
    "superadmin": [
        ("🏢", "clientes",    "Clientes"),
        ("👥", "usuarios",    "Usuarios globales"),
        ("🗺️", "parcelas",    "Parcelas"),
        ("🛰️", "observaciones","Observaciones"),
        ("🌾", "campanas",    "Campañas"),
        ("🔔", "alertas",     "Alertas"),
        ("📄", "reportes",    "Reportes"),
    ],
    "admin": [
        ("📊", "dashboard",   "Dashboard"),
        ("👥", "usuarios",    "Usuarios"),
        ("🗺️", "parcelas",    "Parcelas"),
        ("🛰️", "observaciones","Observaciones"),
        ("🌾", "campanas",    "Campañas"),
        ("🔔", "alertas",     "Alertas"),
        ("📄", "reportes",    "Reportes"),
    ],
    "operador": [
        ("📊", "dashboard",   "Dashboard"),
        ("🗺️", "parcelas",    "Parcelas"),
        ("🛰️", "observaciones","Observaciones"),
        ("🌾", "campanas",    "Campañas"),
        ("🔔", "alertas",     "Alertas"),
    ],
    "visor": [
        ("📊", "dashboard",   "Dashboard"),
        ("🗺️", "parcelas",    "Mis parcelas"),
        ("🛰️", "observaciones","Observaciones"),
        ("🔔", "alertas",     "Mis alertas"),
        ("📄", "reportes",    "Mis reportes"),
    ],
}

def show_sidebar():
    rol = st.session_state.rol

    with st.sidebar:
        st.markdown("### 🌿 SAVIA")
        st.caption(f"**{st.session_state.user_name}** · `{rol}`")
        st.caption(st.session_state.cliente_nombre)
        st.divider()

        alertas_activas = 0
        if st.session_state.cliente_id:
            alertas_activas = len([
                a for a in get_alertas_cliente(st.session_state.cliente_id)
                if a.get("estado") == "activa"
            ])

        for icono, page_id, label in MENUS.get(rol, []):
            # Badge de alertas en el ítem correspondiente
            suffix = f"  🔴 {alertas_activas}" if page_id == "alertas" and alertas_activas else ""
            activo = st.session_state.page == page_id
            if st.button(
                f"{icono}  {label}{suffix}",
                key=f"nav_{page_id}",
                use_container_width=True,
                type="primary" if activo else "secondary",
            ):
                st.session_state.page = page_id
                st.rerun()

        st.divider()
        if st.button("🚪  Cerrar sesión", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PÁGINAS
# ════════════════════════════════════════════════════════════════════════════

# ── Dashboard ────────────────────────────────────────────────────────────────

def page_dashboard():
    cid = st.session_state.cliente_id
    rol = st.session_state.rol

    st.title("Dashboard")
    st.caption(f"{st.session_state.cliente_nombre}  ·  Temporada 2023/2024")

    parcelas = get_parcelas(cid)
    alertas  = get_alertas_cliente(cid)
    alertas_activas = [a for a in alertas if a.get("estado") == "activa"]
    obs_total = sum(
        dao._db.observaciones.count_documents({"parcela_id": str(p["_id"])})
        for p in parcelas
    )

    # ── Métricas ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Parcelas activas", len(parcelas))
    c2.metric("Observaciones totales", obs_total)
    c3.metric("Alertas activas", len(alertas_activas))

    # NDVI promedio de la primera zona disponible
    zonas = list({p.get("zona") for p in parcelas if p.get("zona")})
    ndvi_prom = "—"
    if zonas:
        resultado = dao.get_ndvi_promedio_por_zona(cid, zona=zonas[0], temporada="2023/2024")
        if resultado:
            ndvi_prom = f"{resultado[0]['ndvi_promedio']:.2f}"
    c4.metric(f"NDVI prom. ({zonas[0] if zonas else '?'})", ndvi_prom)

    st.divider()

    col_izq, col_der = st.columns([3, 2])

    # ── Gráfico serie temporal ──
    with col_izq:
        st.subheader("Serie temporal de índices")
        if parcelas:
            p_sel = st.selectbox("Parcela", parcelas, format_func=lambda p: p["nombre"], key="dash_p")
            obs_lista = dao.get_observaciones(str(p_sel["_id"]))
            if obs_lista:
                df = pd.DataFrame(obs_lista)
                df["fecha"] = pd.to_datetime(df["fecha"])
                df = df.sort_values("fecha")

                fig = go.Figure()
                for idx, color in IDX_COLOR.items():
                    if idx in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df["fecha"], y=df[idx],
                            name=idx.upper(),
                            line=dict(color=color, width=2),
                            mode="lines+markers",
                            marker=dict(size=4),
                        ))
                fig.update_layout(**PLOT_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin observaciones para esta parcela.")
        else:
            st.info("No hay parcelas registradas.")

    # ── Alertas activas ──
    with col_der:
        st.subheader("Alertas activas")
        pnom = nombre_parcelas(cid)

        if alertas_activas:
            for a in alertas_activas[:5]:
                nombre_p = pnom.get(str(a.get("parcela_id")), "?")
                st.markdown(f"**{a['tipo'].replace('_', ' ').title()}** — {nombre_p}")
                st.caption(f"{a['indice']}: `{a['valor_detectado']}` (umbral: `{a['umbral']}`)")

                if rol in ("admin", "operador", "superadmin"):
                    cr, ci = st.columns(2)
                    if cr.button("Resolver ✓", key=f"d_r_{a['_id']}"):
                        dao.resolver_alerta(a["_id"])
                        st.rerun()
                    if ci.button("Ignorar ✗", key=f"d_i_{a['_id']}"):
                        dao.ignorar_alerta(a["_id"])
                        st.rerun()
                st.divider()
        else:
            st.success("Sin alertas activas. 🌿")

    # ── Tabla de parcelas ──
    st.subheader("Estado de parcelas")
    if parcelas:
        filas = []
        for p in parcelas:
            obs = dao.get_observaciones(str(p["_id"]))
            ndvi_ult = f"{obs[-1]['ndvi']:.2f}" if obs else "—"
            filas.append({
                "Nombre":         p["nombre"],
                "Zona":           p.get("zona", "—"),
                "Variedad":       p.get("variedad", "—"),
                "Superficie (ha)":p.get("superficie_ha", "—"),
                "NDVI última obs":ndvi_ult,
                "Observaciones":  len(obs),
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


# ── Parcelas ─────────────────────────────────────────────────────────────────

def page_parcelas():
    cid = st.session_state.cliente_id
    rol = st.session_state.rol

    st.title("Parcelas")

    # Formulario de alta (admin / superadmin)
    if rol in ("admin", "superadmin"):
        with st.expander("➕  Agregar nueva parcela"):
            with st.form("form_parcela"):
                c1, c2 = st.columns(2)
                nombre   = c1.text_input("Nombre *")
                zona     = c2.text_input("Zona *")
                cultivo  = c1.selectbox("Cultivo *", ["vid", "olivo", "nogal"])
                variedad = c2.text_input("Variedad (cepa)")
                sup      = c1.number_input("Superficie (ha)", min_value=0.1, step=0.1)
                alt      = c2.number_input("Altitud (msnm)", min_value=0, step=10)
                st.caption("Geometría GeoJSON — se puede cargar después desde GEE.")
                ok = st.form_submit_button("Registrar parcela", type="primary")
                if ok:
                    if not nombre or not zona:
                        st.error("Nombre y zona son obligatorios.")
                    else:
                        nueva = parcela(
                            cliente_id=cid,
                            nombre=nombre,
                            cultivo=cultivo,
                            variedad=variedad or None,
                            zona=zona,
                            superficie_ha=sup,
                            altitud_msnm=int(alt),
                            geometria={"type": "Polygon", "coordinates": [[]]},
                        )
                        dao.registrar_parcela(nueva)
                        st.success(f"✓ Parcela '{nombre}' registrada.")
                        st.rerun()

    # Filtros
    c1, c2 = st.columns(2)
    zona_fil    = c1.text_input("Filtrar por zona")
    cultivo_fil = c2.selectbox("Filtrar por cultivo", ["Todos", "vid", "olivo", "nogal"])

    parcelas = get_parcelas(cid)
    if zona_fil:
        parcelas = [p for p in parcelas if zona_fil.lower() in p.get("zona", "").lower()]
    if cultivo_fil != "Todos":
        parcelas = [p for p in parcelas if p.get("cultivo") == cultivo_fil]

    st.markdown(f"**{len(parcelas)} parcela(s)**")

    for p in parcelas:
        with st.expander(f"📍  {p['nombre']} — {p.get('zona', '?')}"):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Cultivo:** {p.get('cultivo', '—')}")
            c1.markdown(f"**Variedad:** {p.get('variedad', '—')}")
            c2.markdown(f"**Superficie:** {p.get('superficie_ha', '—')} ha")
            c2.markdown(f"**Altitud:** {p.get('altitud_msnm', '—')} msnm")
            n_obs = dao._db.observaciones.count_documents({"parcela_id": str(p["_id"])})
            c3.markdown(f"**Observaciones:** {n_obs}")
            c3.markdown(f"**ID:** `{str(p['_id'])[:20]}…`")


# ── Observaciones ─────────────────────────────────────────────────────────────

def page_observaciones():
    cid = st.session_state.cliente_id
    rol = st.session_state.rol

    st.title("Observaciones satelitales")

    parcelas = get_parcelas(cid)
    if not parcelas:
        st.info("No hay parcelas registradas.")
        return

    c1, c2, c3 = st.columns(3)
    p_sel = c1.selectbox("Parcela", parcelas, format_func=lambda p: p["nombre"])
    desde = c2.date_input("Desde", value=date(2023, 9, 1))
    hasta = c3.date_input("Hasta",  value=date.today())

    # Carga manual (operador / admin)
    if rol in ("admin", "operador", "superadmin"):
        with st.expander("➕  Cargar observación manual"):
            with st.form("form_obs"):
                c1, c2 = st.columns(2)
                f_obs  = c1.date_input("Fecha")
                nub    = c2.number_input("Nubosidad (%)", 0.0, 100.0, 5.0, step=0.5)
                ndvi_v = c1.number_input("NDVI", -1.0, 1.0, 0.60, step=0.01, format="%.2f")
                evi_v  = c2.number_input("EVI",  -1.0, 1.0, 0.45, step=0.01, format="%.2f")
                ndwi_v = c1.number_input("NDWI", -1.0, 1.0, 0.15, step=0.01, format="%.2f")
                if st.form_submit_button("Registrar", type="primary"):
                    obs_nueva = observacion(
                        parcela_id=str(p_sel["_id"]),
                        fecha=f_obs,
                        ndvi=ndvi_v,
                        evi=evi_v,
                        ndwi=ndwi_v,
                        nubosidad_pct=nub,
                    )
                    dao.registrar_observacion(obs_nueva)
                    st.success("✓ Observación registrada.")
                    st.rerun()

    obs_lista = dao.get_observaciones(str(p_sel["_id"]), desde=desde, hasta=hasta)

    if not obs_lista:
        st.info("Sin observaciones para ese período.")
        return

    df = pd.DataFrame(obs_lista)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha")

    indices = st.multiselect(
        "Índices a mostrar",
        ["ndvi", "evi", "ndwi"],
        default=["ndvi", "evi", "ndwi"],
    )

    fig = go.Figure()
    for idx in indices:
        if idx in df.columns:
            fig.add_trace(go.Scatter(
                x=df["fecha"], y=df[idx],
                name=idx.upper(),
                line=dict(color=IDX_COLOR[idx], width=2),
                mode="lines+markers",
                marker=dict(size=5),
            ))
    layout = {**PLOT_LAYOUT, "height": 380}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

    # NDVI promedio por zona
    zona = p_sel.get("zona")
    if zona:
        resultado = dao.get_ndvi_promedio_por_zona(cid, zona=zona, temporada="2023/2024")
        if resultado:
            r = resultado[0]
            cc1, cc2 = st.columns(2)
            cc1.metric(f"NDVI promedio — {zona}", f"{r['ndvi_promedio']:.2f}")
            cc2.metric("Total observaciones (zona)", r.get("total_observaciones", "—"))

    st.subheader("Tabla de observaciones")
    cols_mostrar = ["fecha", "ndvi", "evi", "ndwi", "nubosidad_pct", "fuente"]
    df_show = df[[c for c in cols_mostrar if c in df.columns]].copy()
    df_show.columns = [c.upper() for c in df_show.columns]
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ── Campañas ──────────────────────────────────────────────────────────────────

def page_campanas():
    cid = st.session_state.cliente_id
    rol = st.session_state.rol

    st.title("Campañas")

    parcelas = get_parcelas(cid)
    if not parcelas:
        st.info("No hay parcelas registradas.")
        return

    p_sel = st.selectbox("Parcela", parcelas, format_func=lambda p: p["nombre"])

    if rol in ("admin", "operador", "superadmin"):
        with st.expander("➕  Registrar campaña"):
            with st.form("form_campana"):
                c1, c2 = st.columns(2)
                temporada   = c1.text_input("Temporada", placeholder="2023/2024")
                fecha_cos   = c2.date_input("Fecha de cosecha")
                rendimiento = c1.number_input("Rendimiento (kg/ha)", min_value=0.0, step=100.0)
                notas       = st.text_area("Notas (heladas, sequías, etc.)")
                if st.form_submit_button("Registrar campaña", type="primary"):
                    if not temporada:
                        st.error("La temporada es obligatoria.")
                    else:
                        nueva = campana(
                            parcela_id=str(p_sel["_id"]),
                            temporada=temporada,
                            fecha_cosecha=fecha_cos,
                            rendimiento_kg_ha=rendimiento,
                            notas=notas or None,
                        )
                        dao.registrar_campana(nueva)
                        st.success("✓ Campaña registrada.")
                        st.rerun()

    campanas = dao.get_campanas(str(p_sel["_id"]))

    if not campanas:
        st.info("No hay campañas para esta parcela.")
        return

    df_c = pd.DataFrame(campanas)

    # Bar chart rendimiento por temporada
    fig = go.Figure(go.Bar(
        x=df_c["temporada"],
        y=df_c["rendimiento_kg_ha"],
        marker_color=VERDE,
        text=df_c["rendimiento_kg_ha"].apply(lambda v: f"{v:,.0f} kg/ha"),
        textposition="outside",
    ))
    fig.update_layout(
        title="Rendimiento histórico (kg/ha)",
        **{**PLOT_LAYOUT, "height": 280},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Rendimiento promedio por zona
    zona = p_sel.get("zona")
    if zona:
        st.subheader(f"Rendimiento promedio en {zona}")
        rend_zona = dao.get_rendimiento_promedio_por_zona(cid, zona=zona)
        if rend_zona:
            st.dataframe(pd.DataFrame(rend_zona), use_container_width=True, hide_index=True)

    st.subheader("Historial")
    cols = ["temporada", "fecha_cosecha", "rendimiento_kg_ha", "notas"]
    df_show = df_c[[c for c in cols if c in df_c.columns]].copy()
    df_show.columns = ["Temporada", "Fecha cosecha", "Rendimiento (kg/ha)", "Notas"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ── Alertas ───────────────────────────────────────────────────────────────────

def page_alertas():
    cid = st.session_state.cliente_id
    rol = st.session_state.rol

    st.title("Alertas")

    alertas = get_alertas_cliente(cid)
    pnom    = nombre_parcelas(cid)

    estado_sel = st.radio(
        "Estado",
        ["Todas", "activa", "resuelta", "ignorada"],
        horizontal=True,
    )
    if estado_sel != "Todas":
        alertas = [a for a in alertas if a.get("estado") == estado_sel]

    if not alertas:
        st.success("No hay alertas con ese filtro.")
        return

    ICONO_ESTADO = {"activa": "🔴", "resuelta": "🟢", "ignorada": "⚪"}

    for a in alertas:
        estado   = a.get("estado", "activa")
        icono    = ICONO_ESTADO.get(estado, "⚪")
        nombre_p = pnom.get(str(a.get("parcela_id")), "?")
        titulo   = a["tipo"].replace("_", " ").title()

        with st.expander(f"{icono}  {titulo} — {nombre_p}"):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Índice:** {a.get('indice')}")
            c1.markdown(f"**Valor detectado:** `{a.get('valor_detectado')}`")
            c2.markdown(f"**Umbral:** `{a.get('umbral')}`")
            c2.markdown(f"**Fecha:** {fmt_fecha(a.get('fecha'))}")
            c3.markdown(f"**Estado:** {estado}")

            if estado == "activa" and rol in ("admin", "operador", "superadmin"):
                cr, ci = st.columns(2)
                if cr.button("✓  Resolver", key=f"res_{a['_id']}"):
                    dao.resolver_alerta(a["_id"])
                    st.rerun()
                if ci.button("✗  Ignorar", key=f"ign_{a['_id']}"):
                    dao.ignorar_alerta(a["_id"])
                    st.rerun()


# ── Reportes ──────────────────────────────────────────────────────────────────

def page_reportes():
    cid = st.session_state.cliente_id
    rol = st.session_state.rol

    st.title("Reportes")

    if rol in ("admin", "superadmin"):
        with st.expander("➕  Generar nuevo reporte"):
            parcelas = get_parcelas(cid)
            with st.form("form_reporte"):
                nombre_r = st.text_input("Nombre del reporte")
                tipo_r   = st.selectbox(
                    "Tipo",
                    ["resumen_indices", "comparativa_parcelas", "estado_general"],
                )
                c1, c2 = st.columns(2)
                desde_r = c1.date_input("Desde", value=date(2023, 9, 1))
                hasta_r = c2.date_input("Hasta",  value=date.today())
                parc_sel = st.multiselect(
                    "Parcelas a incluir",
                    parcelas,
                    format_func=lambda p: p["nombre"],
                )
                if st.form_submit_button("Generar reporte", type="primary"):
                    if not nombre_r or not parc_sel:
                        st.error("Nombre y al menos una parcela son obligatorios.")
                    else:
                        nuevo = reporte(
                            cliente_id=cid,
                            nombre=nombre_r,
                            tipo=tipo_r,
                            periodo={"desde": str(desde_r), "hasta": str(hasta_r)},
                            parcelas_incluidas=[str(p["_id"]) for p in parc_sel],
                            fecha_generacion=date.today(),
                            generado_por=st.session_state.user_id,
                            resumen={},
                        )
                        dao.generar_reporte(nuevo)
                        st.success("✓ Reporte generado.")
                        st.rerun()

    reportes = dao.get_reportes_por_cliente(cid)

    if not reportes:
        st.info("No hay reportes generados.")
        return

    ICONO_RPT = {"generado": "📄", "visto": "✅", "enviado": "📤"}

    for r in reportes:
        estado = r.get("estado", "generado")
        icono  = ICONO_RPT.get(estado, "📄")
        with st.expander(f"{icono}  {r.get('nombre')} — {fmt_fecha(r.get('fecha_generacion'))}"):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Tipo:** {r.get('tipo')}")
            c1.markdown(f"**Estado:** `{estado}`")
            periodo = r.get("periodo", {})
            c2.markdown(f"**Período:** {periodo.get('desde', '?')} → {periodo.get('hasta', '?')}")
            c2.markdown(f"**Parcelas:** {len(r.get('parcelas_incluidas', []))}")

            resumen = r.get("resumen")
            if resumen:
                st.json(resumen)

            if estado != "visto":
                if st.button("Marcar como visto 👁", key=f"visto_{r['_id']}"):
                    dao.marcar_reporte_visto(r["_id"])
                    st.rerun()


# ── Usuarios ──────────────────────────────────────────────────────────────────

def page_usuarios():
    rol = st.session_state.rol

    # Superadmin ve todos; el resto ve solo los de su cliente
    if rol == "superadmin":
        clientes = list(dao._db.clientes.find({"activo": True}))
        cid_opts  = {c["nombre"]: c["_id"] for c in clientes}
        c_nombre  = st.selectbox("Cliente", list(cid_opts.keys()))
        cid       = cid_opts[c_nombre]
    else:
        cid = st.session_state.cliente_id

    st.title("Usuarios")

    if rol in ("admin", "superadmin"):
        with st.expander("➕  Agregar usuario"):
            with st.form("form_usuario"):
                c1, c2 = st.columns(2)
                nombre_u = c1.text_input("Nombre completo")
                email_u  = c2.text_input("Email")
                rol_u    = c1.selectbox("Rol", ["admin", "operador", "visor"])
                if st.form_submit_button("Registrar", type="primary"):
                    if not nombre_u or not email_u:
                        st.error("Nombre y email son obligatorios.")
                    else:
                        nuevo = usuario(
                            cliente_id=cid,
                            nombre=nombre_u,
                            email=email_u,
                            rol=rol_u,
                            fecha_alta=date.today(),
                        )
                        dao.registrar_usuario(nuevo)
                        st.success("✓ Usuario registrado.")
                        st.rerun()

    usuarios = dao.get_usuarios_por_cliente(cid)

    if not usuarios:
        st.info("No hay usuarios.")
        return

    filas = [{
        "Nombre": u.get("nombre"),
        "Email":  u.get("email"),
        "Rol":    u.get("rol"),
        "Alta":   fmt_fecha(u.get("fecha_alta")),
        "Activo": "✓" if u.get("activo") else "✗",
    } for u in usuarios]
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    # Desactivar usuario
    activos = [u for u in usuarios if u.get("activo")]
    if activos and rol in ("admin", "superadmin"):
        st.subheader("Revocar acceso")
        u_sel = st.selectbox("Usuario", activos, format_func=lambda u: u["nombre"])
        if st.button("Desactivar acceso", type="secondary"):
            dao.desactivar_usuario(u_sel["_id"])
            st.success(f"✓ Acceso de {u_sel['nombre']} revocado.")
            st.rerun()


# ── Clientes (superadmin) ─────────────────────────────────────────────────────

def page_clientes():
    st.title("Clientes — Vista superadmin")

    with st.expander("➕  Registrar nuevo cliente"):
        with st.form("form_cliente"):
            c1, c2 = st.columns(2)
            nombre_c = c1.text_input("Razón social")
            cuit_c   = c2.text_input("CUIT")
            tipo_c   = c1.selectbox("Tipo", ["bodega", "productor_independiente", "cooperativa"])
            plan_c   = c2.selectbox("Plan", ["basico", "profesional", "enterprise"])
            if st.form_submit_button("Registrar cliente", type="primary"):
                if not nombre_c or not cuit_c:
                    st.error("Razón social y CUIT son obligatorios.")
                else:
                    nuevo = cliente(
                        nombre=nombre_c,
                        cuit=cuit_c,
                        tipo=tipo_c,
                        plan=plan_c,
                        fecha_alta=date.today(),
                    )
                    dao.registrar_cliente(nuevo)
                    st.success("✓ Cliente registrado.")
                    st.rerun()

    clientes = list(dao._db.clientes.find({}))

    for c in clientes:
        activo = c.get("activo", True)
        icono  = "🟢" if activo else "🔴"
        with st.expander(f"{icono}  {c['nombre']}  ·  {c.get('plan', '?')}  ·  {c.get('tipo', '?')}"):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**CUIT:** {c.get('cuit', '—')}")
            c1.markdown(f"**Plan:** {c.get('plan', '—')}")
            c2.markdown(f"**Tipo:** {c.get('tipo', '—')}")
            c2.markdown(f"**Alta:** {fmt_fecha(c.get('fecha_alta'))}")
            n_parc = dao._db.parcelas.count_documents({"cliente_id": c["_id"]})
            n_usr  = dao._db.usuarios.count_documents({"cliente_id": c["_id"]})
            c3.markdown(f"**Parcelas:** {n_parc}")
            c3.markdown(f"**Usuarios:** {n_usr}")

            if activo:
                if st.button("Suspender acceso", key=f"susp_{c['_id']}", type="secondary"):
                    dao.suspender_cliente(c["_id"])
                    st.rerun()
            else:
                if st.button("Reactivar", key=f"react_{c['_id']}", type="primary"):
                    dao.reactivar_cliente(c["_id"])
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# ROUTER PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════

PAGES = {
    "dashboard":    page_dashboard,
    "parcelas":     page_parcelas,
    "observaciones":page_observaciones,
    "campanas":     page_campanas,
    "alertas":      page_alertas,
    "reportes":     page_reportes,
    "usuarios":     page_usuarios,
    "clientes":     page_clientes,
}

def main():
    if not st.session_state.logged_in:
        show_login()
        return

    show_sidebar()

    page_fn = PAGES.get(st.session_state.page)
    if page_fn:
        page_fn()
    else:
        st.error(f"Página desconocida: {st.session_state.page}")


if __name__ == "__main__":
    main()