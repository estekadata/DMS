from __future__ import annotations

import hmac
import textwrap
from pathlib import Path
from datetime import datetime

from sqlalchemy import create_engine, text as sqltext
from sqlalchemy.engine import Engine

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go


def md_html(html: str) -> None:
    s = textwrap.dedent(html).strip()
    s = "\n".join(line.lstrip() for line in s.splitlines())
    st.markdown(s, unsafe_allow_html=True)


# =========================
# localStorage helpers
# =========================
def localstorage_get(key: str, default: str = "") -> str:
    components.html(
        f"""
        <script>
        const v = window.localStorage.getItem({key!r}) || {default!r};
        const url = new URL(window.location);
        url.searchParams.set({("ls_" + key)!r}, v);
        window.history.replaceState(null, "", url.toString());
        </script>
        """,
        height=0,
    )
    return st.query_params.get("ls_" + key, default)


def localstorage_set(key: str, value: str) -> None:
    components.html(
        f"""
        <script>
        window.localStorage.setItem({key!r}, {value!r});
        </script>
        """,
        height=0,
    )


# =========================
# CONFIG
# =========================
SUPABASE_DB_URL = st.secrets.get("SUPABASE_DB_URL") or st.secrets.get("DATABASE_URL") or st.secrets.get("POSTGRES_URL")
LOGO_PATH = Path("assets/multirex.jpg")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {
    "primary": "#6366f1",
    "secondary": "#8b5cf6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6",
}


# =========================
# CSS
# =========================
def inject_custom_css():
    md_html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }

        .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); position: relative; }
        .main::before {
            content: '';
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background-image:
                radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 50%);
            pointer-events: none;
        }

        .block-container { padding: 2rem 3rem !important; max-width: 1400px; position: relative; z-index: 1; }

        h1, h2, h3 { color: #1f2937; font-weight: 700; }

        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1), 0 0 0 1px rgba(255, 255, 255, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.15), 0 0 0 1px rgba(255, 255, 255, 0.25);
        }

        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transition: left 0.5s ease;
        }
        .stButton > button:hover::before { left: 100%; }
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4); }
        .stButton > button:active { transform: translateY(0px); }

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div {
            border-radius: 10px;
            border: 2px solid #e5e7eb;
            transition: all 0.3s ease;
            padding: 0.75rem 1rem;
            font-size: 0.95rem;
        }
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
            transform: translateY(-1px);
        }
        .stTextInput > div > div > input::placeholder { color: #9ca3af; }

        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
        }
        [data-testid="stSidebar"] * { color: white !important; }

        .stSuccess {
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            border-left: 4px solid #10b981;
            border-radius: 12px;
            padding: 1rem;
            animation: slideIn 0.3s ease-out;
        }
        .stError {
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
            border-left: 4px solid #ef4444;
            border-radius: 12px;
            padding: 1rem;
            animation: slideIn 0.3s ease-out;
        }
        .stWarning {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 4px solid #f59e0b;
            border-radius: 12px;
            padding: 1rem;
        }
        .stInfo {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            border-left: 4px solid #3b82f6;
            border-radius: 12px;
            padding: 1rem;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stTabs [data-baseweb="tab"]:hover { background-color: rgba(102, 126, 234, 0.1); }

        ::-webkit-scrollbar { width: 12px; height: 12px; }
        ::-webkit-scrollbar-track { background: rgba(241, 241, 241, 0.5); border-radius: 10px; }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        * Style pour la carte de recherche par plaque */
        .plaque-card {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
            border: 2px solid #e5e7eb;
        }

        /* Style pour l'affichage visuel de la plaque d'immatriculation */
        .plaque-visual {
            /* Dégradé bleu style plaque française */
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            
            /* Bordure épaisse bleue foncée */
            border: 4px solid #1e3a8a;
            border-radius: 8px;
            
            /* Espacement intérieur */
            padding: 1rem 1.5rem;
            
            /* Police monospace style plaque */
            font-family: 'Courier New', monospace;
            font-size: 2rem;
            font-weight: 900;
            color: white;
            text-align: center;
            
            /* Espacement entre les lettres */
            letter-spacing: 0.3rem;
            
            /* Ombres pour effet 3D */
            box-shadow: 
                0 4px 6px rgba(0, 0, 0, 0.2),
                inset 0 2px 4px rgba(255, 255, 255, 0.2);
        }
        </style>
        """
    )


# =========================
# AUTH
# =========================
def show_logo(width: int = 200):
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)


def check_password() -> bool:
    if st.session_state.get("authenticated") is True:
        return True

    md_html(
        """
        <style>
        section[data-testid="stSidebar"] { display: none; }
        .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; }
        .main .block-container { max-width: 480px !important; padding-top: 3rem !important; }

        div[data-testid="stTextInput"] > div > div > input {
            background-color: #f9fafb !important;
            border: 2px solid #e5e7eb !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            font-size: 15px !important;
        }
        div[data-testid="stTextInput"] > div > div > input:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }
        div[data-testid="stTextInput"] label {
            color: #374151 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            margin-bottom: 8px !important;
        }
        .stButton button {
            border-radius: 10px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            font-size: 15px !important;
        }
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
        }
        .stButton button[kind="secondary"] {
            background: white !important;
            color: #374151 !important;
            border: 2px solid #e5e7eb !important;
        }
        </style>
        """
    )

    inject_custom_css()
    md_html("<div style='height: 20px;'></div>")

    md_html(
        """
        <div style='text-align: center; margin-bottom: 40px;'>
            <div style='font-size: 60px; margin-bottom: 16px;'>🚗</div>
            <h1 style='
                color: white;
                font-size: 32px;
                font-weight: 800;
                margin: 0 0 12px 0;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            '>Multirex Auto DMS</h1>
            <p style='
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                margin: 0;
            '>Système de gestion intelligent</p>
        </div>
        """
    )

    md_html(
        """
            <h2 style='
                color: #111827;
                font-size: 24px;
                font-weight: 700;
                margin: 24px 0 8px 0;
            '>Connexion Admin</h2>
            <p style='
                color: #6b7280;
                font-size: 14px;
                margin: 0;
            '>Accédez à votre tableau de bord</p>
        </div>
        """
    )

    user = st.text_input("Utilisateur", key="login_user", placeholder="IDENTIFIANT")
    pwd = st.text_input("Mot de passe", type="password", key="login_pwd", placeholder="Votre mot de passe")

    md_html("<div style='height: 24px;'></div>")

    col1, col2 = st.columns([1, 1])
    with col1:
        login = st.button("🔐 Se connecter (Admin)", type="primary", use_container_width=True)
    with col2:
        login_casse = st.button("🔧 Accès Casse", use_container_width=True)

    if login:
        admin_user = st.secrets.get("ADMIN_USER", "")
        admin_pwd = st.secrets.get("ADMIN_PASSWORD", "")

        if hmac.compare_digest(user, admin_user) and hmac.compare_digest(pwd, admin_pwd):
            st.session_state["authenticated"] = True
            st.session_state["mode"] = "admin"
            st.session_state["page"] = "home"
            st.success("✅ Connexion réussie !")
            st.balloons()
            st.rerun()
        else:
            st.error("❌ Identifiants incorrects")

    if login_casse:
        st.session_state["authenticated"] = True
        st.session_state["mode"] = "casse"
        st.session_state["page"] = "casse"
        st.rerun()

    md_html("</div>")

    md_html(
        """
        <div style='text-align: center; margin-top: 32px;'>
            <div style='
                display: inline-flex;
                gap: 12px;
                background: rgba(255, 255, 255, 0.95);
                padding: 12px 24px;
                border-radius: 50px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            '>
                <span style='color: #667eea; font-weight: 600; font-size: 13px;'>📊 Analytics</span>
                <span style='color: #667eea; font-weight: 600; font-size: 13px;'>⚡ Temps réel</span>
                <span style='color: #667eea; font-weight: 600; font-size: 13px;'>🔒 Sécurisé</span>
            </div>
            <p style='
                color: rgba(255, 255, 255, 0.8);
                margin-top: 24px;
                font-size: 13px;
            '>Multirex Auto © 2025</p>
        </div>
        """
    )

    return False


def logout_button():
    if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# =========================
# DB helpers
# =========================
@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    url = SUPABASE_DB_URL
    if not url:
        st.error("SUPABASE_DB_URL (ou DATABASE_URL / POSTGRES_URL) manquant dans .streamlit/secrets.toml")
        st.stop()
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


@st.cache_data(show_spinner=False, ttl=300)
def sql_df(query: str, params: dict | None = None) -> pd.DataFrame:
    q = (query or "").lstrip().lower()
    if not (q.startswith("select") or q.startswith("with")):
        raise ValueError(
            "❌ sql_df() est réservé aux requêtes SELECT/WITH.\n"
            "Utilise exec_sql() ou exec_sql_scalar() pour écrire en base."
        )

    eng = get_engine()
    with eng.connect() as conn:
        return pd.read_sql_query(sqltext(query), conn, params=params or {})


def exec_sql(query: str, params: dict | None = None) -> None:
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(sqltext(query), params or {})


def assert_db_ready():
    q = """
    SELECT 1
    FROM information_schema.views
    WHERE table_schema = 'public'
      AND table_name = 'v_moteurs_dispo'
    LIMIT 1
    """
    df = sql_df(q)
    if df.empty:
        st.error("Vue v_moteurs_dispo absente sur PostgreSQL (schema public)")
        st.stop()


# =========================
# Upload helpers
# =========================
def save_uploaded_file(file_obj, prefix: str, ext: str) -> str | None:
    if file_obj is None:
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{prefix}_{ts}.{ext}"
    path = UPLOAD_DIR / fname
    with open(path, "wb") as f:
        f.write(file_obj.getvalue())
    return str(path)


def add_column_if_missing(table: str, col_def: str):
    col_name = col_def.split()[0]
    q = """
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = :t
      AND column_name = :c
    LIMIT 1
    """
    exists = not sql_df(q, {"t": table, "c": col_name}).empty
    if not exists:
        exec_sql(f"ALTER TABLE {table} ADD COLUMN {col_def};")


# =========================
# Tables casses
# =========================

def exec_sql_scalar(query: str, params: dict | None = None):
    """
    Exécute une requête SQL et retourne une seule valeur (ex: id via RETURNING).
    À utiliser UNIQUEMENT pour INSERT/UPDATE/DELETE avec RETURNING.
    """
    eng = get_engine()
    try:
        with eng.begin() as conn:
            res = conn.execute(sqltext(query), params or {})
            row = res.fetchone()
            return row[0] if row else None
    except Exception as e:
        st.exception(e)
        raise


def ensure_breaker_tables():
    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS public.breakers (
          id BIGSERIAL PRIMARY KEY,
          name TEXT NOT NULL UNIQUE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS public.breaker_click_offers (
          id BIGSERIAL PRIMARY KEY,
          breaker_id BIGINT NOT NULL REFERENCES public.breakers(id) ON DELETE CASCADE,
          code_moteur TEXT NOT NULL,
          marque TEXT,
          energie TEXT,
          type_nom TEXT,
          type_modele TEXT,
          type_annee TEXT,
          prix_demande DOUBLE PRECISION,
          qty INTEGER NOT NULL DEFAULT 1,
          note TEXT,
          immatriculation TEXT,
          vin TEXT,
          photo_moteur_path TEXT,
          photo_plaque_path TEXT,
          audio_path TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    exec_sql(
        """
        CREATE TABLE IF NOT EXISTS public.breaker_free_offers (
          id BIGSERIAL PRIMARY KEY,
          breaker_id BIGINT NOT NULL REFERENCES public.breakers(id) ON DELETE CASCADE,
          texte TEXT NOT NULL,
          prix_demande DOUBLE PRECISION,
          note TEXT,
          immatriculation TEXT,
          vin TEXT,
          photo_moteur_path TEXT,
          photo_plaque_path TEXT,
          audio_path TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    for col in [
        "immatriculation TEXT",
        "vin TEXT",
        "photo_moteur_path TEXT",
        "photo_plaque_path TEXT",
        "audio_path TEXT",
    ]:
        add_column_if_missing("breaker_click_offers", col)
        add_column_if_missing("breaker_free_offers", col)


def get_or_create_breaker(name: str) -> int:
    name = (name or "").strip()
    if not name:
        raise ValueError("Nom casse vide")

    # First, try to find existing breaker
    q_select = """
    SELECT id FROM public.breakers WHERE name = :name LIMIT 1;
    """
    df = sql_df(q_select, {"name": name})
    
    if not df.empty:
        return int(df.iloc[0]["id"])
    
    # If not found, insert new one
    q_insert = """
    INSERT INTO public.breakers(name)
    VALUES (:name)
    RETURNING id;
    """
    breaker_id = exec_sql_scalar(q_insert, {"name": name})
    return int(breaker_id)


def insert_click_offer(
    breaker_id: int,
    code_moteur: str,
    marque: str | None,
    energie: str | None,
    type_nom: str | None,
    type_modele: str | None,
    type_annee: str | None,
    prix_demande: float | None,
    qty: int = 1,
    note: str | None = None,
    immatriculation: str | None = None,
    vin: str | None = None,
    photo_moteur_path: str | None = None,
    photo_plaque_path: str | None = None,
    audio_path: str | None = None,
):
    exec_sql(
        """
        INSERT INTO breaker_click_offers(
          breaker_id, code_moteur, marque, energie, type_nom, type_modele, type_annee,
          prix_demande, qty, note, immatriculation, vin, photo_moteur_path, photo_plaque_path, audio_path
        ) VALUES(
          :breaker_id, :code_moteur, :marque, :energie, :type_nom, :type_modele, :type_annee,
          :prix_demande, :qty, :note, :immatriculation, :vin, :photo_moteur_path, :photo_plaque_path, :audio_path
        )
        """,
        {
            "breaker_id": int(breaker_id),
            "code_moteur": (code_moteur or "").strip().upper(),
            "marque": marque,
            "energie": energie,
            "type_nom": type_nom,
            "type_modele": type_modele,
            "type_annee": type_annee,
            "prix_demande": prix_demande,
            "qty": int(qty),
            "note": note,
            "immatriculation": immatriculation,
            "vin": vin,
            "photo_moteur_path": photo_moteur_path,
            "photo_plaque_path": photo_plaque_path,
            "audio_path": audio_path,
        },
    )


def insert_free_offer(
    breaker_id: int,
    texte: str,
    prix_demande: float | None,
    note: str | None = None,
    immatriculation: str | None = None,
    vin: str | None = None,
    photo_moteur_path: str | None = None,
    photo_plaque_path: str | None = None,
    audio_path: str | None = None,
):
    exec_sql(
        """
        INSERT INTO breaker_free_offers(
          breaker_id, texte, prix_demande, note, immatriculation, vin, photo_moteur_path, photo_plaque_path, audio_path
        )
        VALUES(
          :breaker_id, :texte, :prix_demande, :note, :immatriculation, :vin, :photo_moteur_path, :photo_plaque_path, :audio_path
        )
        """,
        {
            "breaker_id": int(breaker_id),
            "texte": (texte or "").strip(),
            "prix_demande": prix_demande,
            "note": note,
            "immatriculation": immatriculation,
            "vin": vin,
            "photo_moteur_path": photo_moteur_path,
            "photo_plaque_path": photo_plaque_path,
            "audio_path": audio_path,
        },
    )


@st.cache_data(show_spinner=False, ttl=120)
def get_recent_click_offers(limit: int = 50) -> pd.DataFrame:
    q = """
    SELECT
      o.created_at,
      b.name AS casse,
      o.code_moteur,
      o.marque,
      o.energie,
      o.type_nom,
      o.type_modele,
      o.type_annee,
      o.prix_demande,
      o.qty,
      o.note,
      o.immatriculation,
      o.vin,
      o.photo_moteur_path,
      o.photo_plaque_path,
      o.audio_path
    FROM breaker_click_offers o
    JOIN breakers b ON b.id = o.breaker_id
    ORDER BY o.id DESC
    LIMIT :lim
    """
    return sql_df(q, {"lim": int(limit)})


@st.cache_data(show_spinner=False, ttl=120)
def get_recent_free_offers(limit: int = 50) -> pd.DataFrame:
    q = """
    SELECT
      o.created_at,
      b.name AS casse,
      o.texte,
      o.prix_demande,
      o.note,
      o.immatriculation,
      o.vin,
      o.photo_moteur_path,
      o.photo_plaque_path,
      o.audio_path
    FROM breaker_free_offers o
    JOIN breakers b ON b.id = o.breaker_id
    ORDER BY o.id DESC
    LIMIT :lim
    """
    return sql_df(q, {"lim": int(limit)})


@st.cache_data(show_spinner=False, ttl=60)
def get_breaker_stats_today(breaker_id: int) -> dict:
    q = """
    SELECT
      (SELECT COUNT(*) FROM breaker_click_offers
        WHERE breaker_id = :bid AND created_at::date = CURRENT_DATE) AS n_click,
      (SELECT COUNT(*) FROM breaker_free_offers
        WHERE breaker_id = :bid AND created_at::date = CURRENT_DATE) AS n_free
    """
    row = sql_df(q, {"bid": int(breaker_id)}).iloc[0].to_dict()
    return {"click": int(row["n_click"]), "free": int(row["n_free"]), "total": int(row["n_click"]) + int(row["n_free"])}

# ========================================
# NOUVELLES FONCTIONS À AJOUTER DANS LE FICHIER main.py
# À placer après la fonction get_breaker_stats_today() 
# et avant la section "# ========================= Matching"
# ========================================


# =========================
# Recherche par plaque
# =========================

@st.cache_data(show_spinner=False, ttl=300)
def search_plaque(plaque: str) -> pd.DataFrame:
    """
    Recherche une plaque dans la base et retourne les infos du véhicule.
    
    La recherche normalise automatiquement la plaque :
    - Convertit en majuscules
    - Supprime les espaces
    - Supprime les tirets
    
    Exemples :
        "AB-123-CD" → recherche "AB123CD"
        "ab 123 cd" → recherche "AB123CD"
        "AB123CD"   → recherche "AB123CD"
    
    Args:
        plaque: Numéro de plaque d'immatriculation (format libre)
    
    Returns:
        DataFrame avec les infos du véhicule (vide si non trouvé)
    """
    if not plaque or not plaque.strip():
        return pd.DataFrame()
    
    # Normaliser la plaque (enlever espaces, tirets, majuscules)
    plaque_norm = plaque.upper().replace(" ", "").replace("-", "")
    
    q = """
    SELECT 
        plaque,
        code_moteur,
        marque,
        modele,
        annee,
        energie
    FROM public.plaques_vehicules
    WHERE REPLACE(REPLACE(UPPER(plaque), ' ', ''), '-', '') = :plaque
    LIMIT 1
    """
    return sql_df(q, {"plaque": plaque_norm})


def filter_besoins_by_plaque(besoins: pd.DataFrame, plaque_info: dict) -> pd.DataFrame:
    """
    Filtre les besoins en fonction des informations de la plaque.
    
    Logique de filtrage :
    1. D'abord, cherche par code moteur EXACT
       → Si trouvé, retourne uniquement ces besoins
    2. Sinon, cherche par marque ET énergie
       → Retourne les besoins qui correspondent
    3. Si rien ne correspond, retourne tous les besoins
    
    Args:
        besoins: DataFrame des besoins actuels
        plaque_info: Dict avec les infos du véhicule
                    (code_moteur, marque, energie, etc.)
    
    Returns:
        DataFrame filtré des besoins
        
    Examples:
        >>> plaque_info = {"code_moteur": "K9K", "marque": "RENAULT", "energie": "DIESEL"}
        >>> besoins_filtres = filter_besoins_by_plaque(besoins, plaque_info)
        # Retourne uniquement les besoins K9K
    """
    if besoins.empty or not plaque_info:
        return besoins
    
    # 1️⃣ Recherche par code moteur exact (priorité)
    code = plaque_info.get("code_moteur", "").upper()
    if code:
        exact_match = besoins[besoins["code_moteur"].str.upper() == code]
        if not exact_match.empty:
            return exact_match
    
    # 2️⃣ Sinon recherche par marque + energie
    marque = plaque_info.get("marque", "").upper()
    energie = plaque_info.get("energie", "").upper()
    
    filtered = besoins.copy()
    
    if marque:
        filtered = filtered[filtered["marque"].str.upper().str.contains(marque, na=False)]
    
    if energie:
        filtered = filtered[filtered["energie"].str.upper().str.contains(energie, na=False)]
    
    # 3️⃣ Retourne les résultats filtrés ou tous les besoins si rien ne correspond
    return filtered if not filtered.empty else besoins
# =========================
# Matching
# =========================
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).upper().strip()
    text = text.replace("-", " ").replace("_", " ").replace(".", " ")
    import re
    text = re.sub(r"\s+", " ", text)
    return text


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def get_motor_synonyms() -> dict:
    return {
        "RENAULT": ["REN", "RENO", "R"],
        "PEUGEOT": ["PEU", "PSA", "P"],
        "CITROEN": ["CIT", "CITRO", "C"],
        "VOLKSWAGEN": ["VW", "VOLKS"],
        "MERCEDES": ["MERC", "MB", "MERCEDES-BENZ"],
        "BMW": ["BM"],
        "AUDI": ["AUD"],
        "FORD": ["F"],
        "OPEL": ["OP"],
        "FIAT": ["FIA"],
        "DIESEL": ["GASOIL", "GAZOLE", "HDI", "DCI", "TDI", "CDI", "TDCI", "D"],
        "ESSENCE": ["ESS", "E", "TSI", "TFSI", "TCE"],
        "ELECTRIQUE": ["ELEC", "EV", "ELECTRIC"],
        "HYBRIDE": ["HYB", "HYBRID"],
        "TURBO": ["T", "TURB"],
        "INJECTION": ["INJ", "I"],
        "COMMON RAIL": ["CR", "COMMONRAIL"],
        "BOITE": ["BV", "BA", "GEARBOX"],
        "AUTOMATIQUE": ["AUTO", "AT", "BVA"],
        "MANUELLE": ["MAN", "MT", "BVM"],
    }


def create_search_variants(text: str) -> list:
    if not text:
        return []
    synonyms = get_motor_synonyms()
    variants = [normalize_text(text)]
    norm = normalize_text(text)

    for key, values in synonyms.items():
        for value in values:
            if value in norm:
                variants.append(norm.replace(value, key))
            if key in norm:
                for v in values:
                    variants.append(norm.replace(key, v))

    return list(set(variants))


def smart_match_motor(search_text: str, besoins: pd.DataFrame) -> pd.DataFrame:
    if not search_text or besoins.empty:
        return besoins

    search_norm = normalize_text(search_text)
    search_variants = create_search_variants(search_text)

    scores = []
    for idx, row in besoins.iterrows():
        score = 0

        motor_text = " ".join(
            [
                str(row.get("code_moteur", "")),
                str(row.get("marque", "")),
                str(row.get("energie", "")),
                str(row.get("type_nom", "")),
                str(row.get("type_modele", "")),
                str(row.get("type_annee", "")),
            ]
        )
        motor_norm = normalize_text(motor_text)

        if search_norm in motor_norm:
            score += 100

        for variant in search_variants:
            if variant and variant in motor_norm:
                score += 50

        search_words = search_norm.split()
        motor_words = motor_norm.split()

        for sword in search_words:
            if len(sword) >= 2:
                for mword in motor_words:
                    if sword in mword or mword in sword:
                        score += 10

        if search_norm in str(row.get("code_moteur", "")).upper():
            score += 200

        scores.append((idx, score))

    scored = [(idx, score) for idx, score in scores if score > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    if scored:
        matched_indices = [idx for idx, _ in scored]
        return besoins.loc[matched_indices].copy()

    return pd.DataFrame()


def suggest_motor_description(row: dict) -> str:
    parts = []
    if row.get("marque"):
        parts.append(str(row["marque"]))

    if row.get("energie"):
        energie = str(row["energie"]).upper()
        if "DIESEL" in energie or "DCI" in energie or "HDI" in energie:
            parts.append("Diesel")
        elif "ESSENCE" in energie or "TSI" in energie or "TCE" in energie:
            parts.append("Essence")

    if row.get("type_nom"):
        parts.append(str(row["type_nom"]))
    if row.get("type_modele"):
        parts.append(str(row["type_modele"]))
    if row.get("type_annee"):
        parts.append(str(row["type_annee"]))

    return " ".join(parts) if parts else row.get("code_moteur", "")


# =========================
# NAV
# =========================
def set_page(name: str):
    st.session_state["page"] = name


def get_page() -> str:
    return st.session_state.get("page", "home")


def render_home():
    md_html(
        """
        <div style='text-align: center; margin-bottom: 3rem;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🏠 Tableau de bord</h1>
            <p style='color: #6b7280; font-size: 1.1rem;'>Choisissez une section pour commencer</p>
        </div>
        """
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        if st.button("📈", key="btn_ventes", use_container_width=True):
            set_page("ventes")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 1rem;'><h3>Ventes</h3><p style='color: #6b7280;'>Analyse des ventes</p></div>")

    with c2:
        if st.button("🎯", key="btn_besoins", use_container_width=True):
            set_page("besoins")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 1rem;'><h3>Besoins</h3><p style='color: #6b7280;'>Besoins casses</p></div>")

    with c3:
        if st.button("📊", key="btn_analyse", use_container_width=True):
            set_page("analyse")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 1rem;'><h3>Analyse</h3><p style='color: #6b7280;'>Statistiques</p></div>")

    with c4:
        if st.button("🛠️", key="btn_casse", use_container_width=True):
            set_page("casse")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 1rem;'><h3>Accès Casse</h3><p style='color: #6b7280;'>Interface casses</p></div>")

    with c5:
        if st.button("💶", key="btn_prix", use_container_width=True):
            set_page("mise_a_jour_prix")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 1rem;'><h3>Mise à jour des prix</h3><p style='color: #6b7280;'>Propositions achat</p></div>")


# =========================
# Queries (cache perf)
# =========================
@st.cache_data(show_spinner=False, ttl=120)
def get_kpis_stock() -> dict:
    q = """
    SELECT
      SUM(CASE WHEN est_disponible = 1 THEN 1 ELSE 0 END) AS dispo,
      SUM(CASE WHEN est_disponible = 0 THEN 1 ELSE 0 END) AS vendus,
      COUNT(*) AS total
    FROM v_moteurs_dispo
    """
    row = sql_df(q).iloc[0].to_dict()
    return {k: int(row[k]) for k in row.keys()}


@st.cache_data(show_spinner=False, ttl=300)
def get_ventes_recents(n_months: int) -> pd.DataFrame:
    q = """
    SELECT
      em.date_validation::date AS jour,
      to_char(em.date_validation, 'YYYY-MM') AS mois,
      vd.type_nom AS code_moteur,
      vd.marque AS marque,
      vd.energie AS energie,
      LEFT(tm.nom_type_moteur, 3) as type_moteur,
      COUNT(*) AS nb_vendus
    FROM tbl_expeditions_moteurs em
    JOIN tbl_moteurs m
      ON m.n_moteur = em.n_moteur
    LEFT JOIN v_moteurs_dispo vd
      ON vd.n_moteur = m.n_moteur
    left join tbl_types_moteurs tm 
      ON     m.n_type_moteur=tm.n_type_moteur 
    WHERE em.date_validation >= NOW() - make_interval(months => :months)
        AND vd.type_nom IS NOT NULL
        AND TRIM(vd.type_nom) <> ''
    GROUP BY jour, mois, vd.type_nom, vd.marque, vd.energie,LEFT(tm.nom_type_moteur, 3) 
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_ventes_recents_boites(n_months: int) -> pd.DataFrame:
    q = """
    SELECT
      eb."date_validation"::date AS jour,
      to_char(eb."date_validation", 'YYYY-MM') AS mois,
      eb."N_BV"::text AS code_boite,
      COUNT(*) AS nb_vendus
    FROM "tbl_EXPEDITIONS_boîtes" eb
    WHERE eb."date_validation" >= NOW() - (:months || ' months')::interval
    GROUP BY jour, mois, code_boite
    """
    return sql_df(q, {"months": int(n_months)})


def ensure_stock_views():
    exec_sql("""
    CREATE OR REPLACE VIEW v_boites_dispo AS
    SELECT
      b.*,
      CASE
        WHEN b.stock = true AND (b.Vendu IS NULL OR b.vendu = false) THEN 1
        ELSE 0
      END AS est_disponible
    FROM tbl_boites b;
    """)


# ========================================
# VERSION FINALE CORRIGÉE de get_besoins_moteurs()
# REMPLACE les 2 versions existantes par celle-ci
# ========================================

@st.cache_data(show_spinner=False, ttl=300)
def get_besoins_moteurs(top_n: int = 50) -> pd.DataFrame:
    """
    Récupère les besoins de moteurs avec infos complètes depuis tbl_types_moteurs
    """
    q = """
    WITH ventes AS (
        SELECT
            UPPER(m.code_moteur) AS code_moteur,
            m.n_type_moteur,
            COUNT(*) AS nb_vendus_3m
        FROM tbl_expeditions_moteurs em
        JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
        WHERE em.date_validation >= NOW() - INTERVAL '3 months'
          AND m.code_moteur IS NOT NULL
          AND TRIM(m.code_moteur) <> ''
        GROUP BY UPPER(m.code_moteur), m.n_type_moteur
    ),
    achats AS (
        SELECT
            UPPER(m.code_moteur) AS code_moteur,
            AVG(CASE WHEN r.date_achat >= NOW() - INTERVAL '3 months'  THEN m.prix_achat_moteur END) AS prix_moy_3m,
            AVG(CASE WHEN r.date_achat >= NOW() - INTERVAL '6 months'  THEN m.prix_achat_moteur END) AS prix_moy_6m,
            AVG(CASE WHEN r.date_achat >= NOW() - INTERVAL '12 months' THEN m.prix_achat_moteur END) AS prix_moy_12m
        FROM tbl_moteurs m
        JOIN tbl_receptions r ON r.n_reception = m.num_reception
        WHERE m.prix_achat_moteur IS NOT NULL
          AND r.date_achat IS NOT NULL
        GROUP BY UPPER(m.code_moteur)
    ),
    stock_dispo AS (
        SELECT
            UPPER(code_moteur) AS code_moteur,
            COUNT(*) AS nb_stock_dispo
        FROM v_moteurs_dispo
        WHERE est_disponible = 1
          AND (archiver IS NULL OR archiver = True)
        GROUP BY UPPER(code_moteur)
    ),
    infos_types AS (
        -- Récupère les infos depuis tbl_types_moteurs
        SELECT DISTINCT
            m.n_type_moteur,
            COALESCE(tm.constructeur_nom, '') AS marque,
            COALESCE(tm.energie, '') AS energie,
            COALESCE(tm.nom_type_moteur, '') AS type_nom,
            COALESCE(tm.modele_vehicule, '') AS type_modele,
            COALESCE(CAST(tm.annee_debut AS TEXT), '') AS type_annee
        FROM tbl_moteurs m
        LEFT JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
        WHERE m.n_type_moteur IS NOT NULL
    )
    SELECT
        v.code_moteur,
        LEFT(COALESCE(i.type_nom, ''), 3) AS type_moteur,
        i.marque,
        i.energie,
        i.type_nom,
        i.type_modele,
        i.type_annee,
        v.nb_vendus_3m,
        COALESCE(s.nb_stock_dispo, 0) AS nb_stock_dispo,
        ROUND(a.prix_moy_3m, 2)  AS prix_moy_achat_3m,
        ROUND(a.prix_moy_6m, 2)  AS prix_moy_achat_6m,
        ROUND(a.prix_moy_12m, 2) AS prix_moy_achat_12m
    FROM ventes v
    LEFT JOIN achats a ON a.code_moteur = v.code_moteur
    LEFT JOIN stock_dispo s ON s.code_moteur = v.code_moteur
    LEFT JOIN infos_types i ON i.n_type_moteur = v.n_type_moteur
    ORDER BY v.nb_vendus_3m DESC
    LIMIT :topn
    """
    df = sql_df(q, {"topn": int(top_n)})
    if not df.empty:
        df["score_urgence"] = (df["nb_vendus_3m"] / (df["nb_stock_dispo"] + 1)).round(2)
        df = df.sort_values(["score_urgence", "nb_vendus_3m"], ascending=False)
    return df


@st.cache_data(show_spinner=False, ttl=300)
def get_prix_vente_moy_code_3m() -> pd.DataFrame:
    q = """
    SELECT
      UPPER(m.code_moteur) AS code_moteur,
      AVG(em.prix_vente_moteur) AS prix_vente_moy_3m,
      COUNT(*) AS nb_ventes_3m
    FROM tbl_EXPEDITIONS_moteurs em
    JOIN tbl_MOTEURS m ON m.n_moteur = em.n_moteur
    WHERE em.date_validation >= NOW() - INTERVAL '3 months'
      AND em.prix_vente_moteur IS NOT NULL
      AND em.prix_vente_moteur > 0
      AND m.code_moteur IS NOT NULL
      AND TRIM(m.code_moteur) <> ''
    GROUP BY UPPER(m.code_moteur)
    """
    return sql_df(q)


@st.cache_data(show_spinner=False, ttl=300)
def get_stock_dispo_par_code() -> pd.DataFrame:
    q = """
    SELECT
      UPPER(code_moteur) AS code_moteur,
      COUNT(*) AS nb_stock_dispo
    FROM v_moteurs_dispo
    WHERE est_disponible = 1
      AND (archiver IS NULL OR archiver = True)
      AND code_moteur IS NOT NULL
      AND TRIM(code_moteur) <> ''
    GROUP BY UPPER(code_moteur)
    """
    return sql_df(q)


@st.cache_data(show_spinner=False, ttl=300)
def get_stock_dispo_breakdown() -> pd.DataFrame:
    return sql_df(
        """
        SELECT marque, energie, COUNT(*) as n
        FROM v_moteurs_dispo
        WHERE est_disponible = 1
          AND (archiver IS NULL OR archiver = True)
        GROUP BY marque, energie
        """
    )


@st.cache_data(show_spinner=False, ttl=120)
def get_kpis_from_view(view_name: str) -> dict:
    q = f"""
    SELECT
      SUM(CASE WHEN est_disponible = 1 THEN 1 ELSE 0 END) AS dispo,
      SUM(CASE WHEN est_disponible = 0 THEN 1 ELSE 0 END) AS vendus,
      COUNT(*) AS total
    FROM {view_name}
    """
    row = sql_df(q).iloc[0].to_dict()
    return {k: int(row[k]) for k in row.keys()}


def get_kpis_boites() -> dict:
    return get_kpis_from_view("v_boites_dispo")


@st.cache_data(show_spinner=False, ttl=300)
def get_prix_achat_dispo(limit: int = 200000) -> pd.DataFrame:
    return sql_df(
        f"""
        SELECT prix_achat_moteur AS prix
        FROM v_moteurs_dispo
        WHERE est_disponible = 1
          AND prix_achat_moteur IS NOT NULL
          AND prix_achat_moteur > 0
        LIMIT {int(limit)}
        """
    )





@st.cache_data(show_spinner=False, ttl=300)
def get_prix_achat_par_mois(n_months: int) -> pd.DataFrame:
    q = """
    SELECT
      to_char(r."date_achat", 'YYYY-MM') AS mois,
      AVG(m."prix_achat_moteur") AS prix_achat_moy
    FROM tbl_MOTEURS m
    JOIN tbl_RECEPTIONS r ON r."n_reception" = m."num_reception"
    WHERE r."date_achat" >= NOW() - (:months || ' months')::interval
      AND m."prix_achat_moteur" IS NOT NULL
      AND m."prix_achat_moteur" > 0
    GROUP BY mois
    ORDER BY mois;
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_prix_vente_par_mois(n_months: int) -> pd.DataFrame:
    q = """
    SELECT
      to_char(em."date_validation", 'YYYY-MM') AS mois,
      AVG(em."prix_vente_moteur") AS prix_vente_moy
    FROM tbl_EXPEDITIONS_moteurs em
    WHERE em."date_validation" >= NOW() - (:months || ' months')::interval
      AND em."prix_vente_moteur" IS NOT NULL
      AND em."prix_vente_moteur" > 0
    GROUP BY mois
    ORDER BY mois;
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_prix_achat_par_mois_code(n_months: int, code: str) -> pd.DataFrame:
    q = """
    SELECT
      to_char(r."date_achat", 'YYYY-MM') AS mois,
      AVG(m."prix_achat_moteur") AS prix_achat_moy
    FROM tbl_MOTEURS m
    JOIN tbl_RECEPTIONS r ON r."n_reception" = m."num_reception"
    WHERE r."date_achat" >= NOW() - (:months || ' months')::interval
      AND UPPER(m."code_moteur") = :code
      AND m."prix_achat_moteur" IS NOT NULL
      AND m."prix_achat_moteur" > 0
    GROUP BY mois
    ORDER BY mois;
    """
    return sql_df(q, {"months": int(n_months), "code": code.upper()})


@st.cache_data(show_spinner=False, ttl=300)
def get_prix_vente_par_mois_code(n_months: int, code: str) -> pd.DataFrame:
    q = """
    SELECT
      to_char(em."date_validation", 'YYYY-MM') AS mois,
      AVG(em."prix_vente_moteur") AS prix_vente_moy
    FROM tbl_EXPEDITIONS_moteurs em
    JOIN tbl_MOTEURS m ON m."n_moteur" = em."n_moteur"
    WHERE em."date_validation" >= NOW() - (:months || ' months')::interval
      AND UPPER(m."code_moteur") = :code
      AND em."prix_vente_moteur" IS NOT NULL
      AND em."prix_vente_moteur" > 0
    GROUP BY mois
    ORDER BY mois;
    """
    return sql_df(q, {"months": int(n_months), "code": code.upper()})


@st.cache_data(show_spinner=False, ttl=300)
def get_price_movers(kind: str, window_months: int = 3, lookback_months: int = 12, min_count: int = 5) -> pd.DataFrame:
    if kind not in {"achat", "vente"}:
        raise ValueError("kind doit être 'achat' ou 'vente'")

    lb = int(lookback_months)
    w = int(window_months)

    if kind == "achat":
        q = f"""
        WITH base AS (
          SELECT
            UPPER(m."code_moteur") AS code_moteur,
            r."date_achat" AS dt,
            m."prix_achat_moteur" AS prix
          FROM tbl_MOTEURS m
          JOIN tbl_RECEPTIONS r ON r."n_reception" = m."num_reception"
          WHERE r."date_achat" >= NOW() - INTERVAL '{lb} months'
            AND m."prix_achat_moteur" IS NOT NULL
            AND m."prix_achat_moteur" > 0
        ),
        agg AS (
          SELECT
            code_moteur,
            AVG(CASE WHEN dt >= NOW() - INTERVAL '{w} months' THEN prix END) AS avg_recent,
            AVG(CASE WHEN dt <  NOW() - INTERVAL '{w} months'
                      AND dt >= NOW() - INTERVAL '{w*2} months' THEN prix END) AS avg_prev,
            SUM(CASE WHEN dt >= NOW() - INTERVAL '{w} months' THEN 1 ELSE 0 END) AS n_recent,
            SUM(CASE WHEN dt <  NOW() - INTERVAL '{w} months'
                      AND dt >= NOW() - INTERVAL '{w*2} months' THEN 1 ELSE 0 END) AS n_prev
          FROM base
          GROUP BY code_moteur
        )
        SELECT
          code_moteur,
          n_recent,
          n_prev,
          ROUND(avg_prev::numeric, 2) AS avg_prev,
          ROUND(avg_recent::numeric, 2) AS avg_recent,
          ROUND((avg_recent - avg_prev)::numeric, 2) AS delta,
          CASE WHEN avg_prev IS NULL OR avg_prev = 0 THEN NULL
               ELSE ROUND(((avg_recent - avg_prev) / avg_prev * 100.0)::numeric, 2)
          END AS pct
        FROM agg
        WHERE n_recent >= :minc AND n_prev >= :minc
          AND avg_recent IS NOT NULL AND avg_prev IS NOT NULL;
        """
    else:
        q = f"""
        WITH base AS (
          SELECT
            UPPER(m."code_moteur") AS code_moteur,
            em."date_validation" AS dt,
            em."prix_vente_moteur" AS prix
          FROM tbl_EXPEDITIONS_moteurs em
          JOIN tbl_MOTEURS m ON m."n_moteur" = em."n_moteur"
          WHERE em."date_validation" >= NOW() - INTERVAL '{lb} months'
            AND em."prix_vente_moteur" IS NOT NULL
            AND em."prix_vente_moteur" > 0
        ),
        agg AS (
          SELECT
            code_moteur,
            AVG(CASE WHEN dt >= NOW() - INTERVAL '{w} months' THEN prix END) AS avg_recent,
            AVG(CASE WHEN dt <  NOW() - INTERVAL '{w} months'
                      AND dt >= NOW() - INTERVAL '{w*2} months' THEN prix END) AS avg_prev,
            SUM(CASE WHEN dt >= NOW() - INTERVAL '{w} months' THEN 1 ELSE 0 END) AS n_recent,
            SUM(CASE WHEN dt <  NOW() - INTERVAL '{w} months'
                      AND dt >= NOW() - INTERVAL '{w*2} months' THEN 1 ELSE 0 END) AS n_prev
          FROM base
          GROUP BY code_moteur
        )
        SELECT
          code_moteur,
          n_recent,
          n_prev,
          ROUND(avg_prev::numeric, 2) AS avg_prev,
          ROUND(avg_recent::numeric, 2) AS avg_recent,
          ROUND((avg_recent - avg_prev)::numeric, 2) AS delta,
          CASE WHEN avg_prev IS NULL OR avg_prev = 0 THEN NULL
               ELSE ROUND(((avg_recent - avg_prev) / avg_prev * 100.0)::numeric, 2)
          END AS pct
        FROM agg
        WHERE n_recent >= :minc AND n_prev >= :minc
          AND avg_recent IS NOT NULL AND avg_prev IS NOT NULL;
        """

    return sql_df(q, {"minc": int(min_count)})


@st.cache_data(show_spinner=False, ttl=600)
def get_code_info() -> pd.DataFrame:
    q = """
    SELECT
      UPPER(code_moteur) AS code_moteur,
      MAX(marque) AS marque,
      MAX(energie) AS energie,
      MAX(type_nom) AS type_nom,
      MAX(type_modele) AS type_modele,
      MAX(type_annee) AS type_annee
    FROM v_moteurs_dispo
    WHERE code_moteur IS NOT NULL
      AND TRIM(code_moteur) <> ''
    GROUP BY UPPER(code_moteur)
    """
    return sql_df(q)


# =========================
# Pages avec Plotly
# =========================
def piece_selector(key: str = "piece_type") -> str:
    if key not in st.session_state:
        st.session_state[key] = "moteurs"
    choix = st.radio(
        "Analyse",
        ["moteurs", "boites"],
        index=0 if st.session_state[key] == "moteurs" else 1,
        horizontal=True,
        key=key,
        label_visibility="collapsed",
    )
    return choix


def render_ventes():
    if st.button("⬅ Retour à l'accueil", use_container_width=False):
        set_page("home")
        st.rerun()

    st.markdown("## 📈 Analyse des ventes")

    piece = piece_selector("ventes_piece")

    n_months = st.slider("Période d'analyse (mois)", min_value=1, max_value=24, value=3, step=1)

    if piece == "moteurs":
        ventes = get_ventes_recents(n_months)
        code_col = "code_moteur"
    else:
        ventes = get_ventes_recents_boites(n_months)
        code_col = "code_boite"

    if ventes.empty:
        st.warning("Aucune vente sur la période.")
        return

    ventes_mois = ventes.groupby("mois")["nb_vendus"].sum().reset_index()
    fig1 = px.line(
        ventes_mois,
        x="mois",
        y="nb_vendus",
        title=f"Ventes par mois (sur {n_months} mois)",
        labels={"mois": "Mois", "nb_vendus": "Nombre de ventes"},
    )
    fig1.update_traces(line_color=COLORS["primary"], line_width=3, marker=dict(size=8))
    fig1.update_layout(template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        top_codes = (
            ventes
            .groupby("type_moteur")["nb_vendus"]
            .sum()
            .sort_values(ascending=False)
            .head(20)
            .reset_index()
        )

        fig2 = px.bar(
            top_codes,
            x="type_moteur",
            y="nb_vendus",
            title="Top 20 types moteur vendus (3 caractères)",
            labels={"type_moteur": "Type moteur", "nb_vendus": "Nombre de ventes"},
        )
        fig2.update_traces(marker_color=COLORS["secondary"])
        fig2.update_layout(template="plotly_white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        if piece == "moteurs" and "marque" in ventes.columns:
            marques = ventes[ventes["marque"].notna() & (ventes["marque"] != "")]
            if not marques.empty:
                top_marques = marques.groupby("marque")["nb_vendus"].sum().sort_values(ascending=False).head(15).reset_index()
                fig3 = px.bar(
                    top_marques,
                    x="marque",
                    y="nb_vendus",
                    title="Top 15 marques vendues",
                    labels={"marque": "Marque", "nb_vendus": "Nombre de ventes"},
                )
                fig3.update_traces(marker_color=COLORS["info"])
                fig3.update_layout(template="plotly_white", showlegend=False)
                st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📋 Voir le détail des ventes"):
        st.dataframe(ventes.sort_values(["mois", "nb_vendus"], ascending=[False, False]), use_container_width=True)


def render_besoins():
    if st.button("⬅ Retour à l'accueil", use_container_width=False):
        set_page("home")
        st.rerun()

    st.markdown("## 🎯 Besoins actuels")
    piece = piece_selector("besoins_piece")

    topn = st.slider("Nombre de besoins affichés", min_value=10, max_value=200, value=50, step=10)
    if piece == "moteurs":
        besoins = get_besoins_moteurs(topn)
    else:
        besoins = get_besoins_boites(topn)

    if besoins.empty:
        st.warning("Aucun besoin calculé.")
        return

    st.info("💡 Besoins calculés sur les ventes des 3 derniers mois avec analyse du stock et prix moyens")

        # combien de barres on veut afficher (piloté par le slider)
    topk = min(int(topn), len(besoins))  # topn = ton slider "Nombre de besoins affichés"

    # agrégation par type_moteur (ou autre clé via code_col)
    code_col = "type_moteur" if piece == "moteurs" else "code_boite"

    top_urgent = (
        besoins
        .groupby(code_col, as_index=False)["score_urgence"]
        .max()
        .sort_values("score_urgence", ascending=False)
        .head(topk)
    )

    fig = px.bar(
        top_urgent,
        x=code_col,
        y="score_urgence",
        title=f"Top {topk} besoins les plus urgents",
        labels={code_col: "Type moteur" if piece == "moteurs" else "Code boîte",
                "score_urgence": "Score d'urgence"},
        color="score_urgence",
        color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"],
    )
    fig.update_layout(template="plotly_white", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    base_cols = [code_col, "nb_vendus_3m", "nb_stock_dispo", "score_urgence"]
    optional_cols = ["marque", "energie", "type_nom", "type_modele", "type_annee"]
    cols_to_show = [c for c in base_cols + optional_cols if c in besoins.columns]

    st.dataframe(besoins[cols_to_show], use_container_width=True)


def render_casse():
    # ✅ (1) + ✅ (2) : éviter KeyError si refresh / session reset
    st.session_state.setdefault("breaker_ok", False)
    st.session_state.setdefault("breaker_id", None)

    st.markdown("## 🛠️ Interface Casse - Mode Rapide")

    access_code = st.secrets.get("BREAKER_ACCESS_CODE", "")
    if not access_code:
        st.error("BREAKER_ACCESS_CODE manquant dans .streamlit/secrets.toml")
        st.stop()

    if not st.session_state["breaker_ok"]:
        md_html(
            """
            <div style='text-align: center; margin-bottom: 2rem;'>
                <div style='font-size: 60px; margin-bottom: 1rem;'>🔧</div>
                <h2 style='color: white; margin: 0;'>Interface Rapide Casse</h2>
                <p style='color: rgba(255,255,255,0.9); font-size: 18px;'>Déclarez vos moteurs en 10 secondes</p>
            </div>
            """
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            md_html(
                """
                <div style='
                    background: white;
                    padding: 2.5rem;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
                '>
                """
            )

            md_html("<div style='margin-top: 1.5rem;'></div>")

            saved_name = localstorage_get("breaker_name", "")
            saved_code = localstorage_get("breaker_code", "")

            breaker_name = st.text_input(
                "🏢 Nom de votre casse",
                key="breaker_name",
                value=saved_name,
                placeholder="Ex: Casse Auto 32",
            )
            code = st.text_input(
                "🔑 Code d'accès",
                type="password",
                key="breaker_code",
                value=saved_code,
                placeholder="Votre code",
            )

            if st.button("✅ Accéder à l'interface", type="primary", use_container_width=True):
                if hmac.compare_digest((code or "").strip(), access_code):
                    if not breaker_name.strip():
                        st.error("Veuillez entrer le nom de votre casse")
                    else:
                        st.session_state["breaker_ok"] = True
                        st.session_state["breaker_id"] = get_or_create_breaker(breaker_name.strip())

                        localstorage_set("breaker_name", breaker_name.strip())
                        localstorage_set("breaker_code", (code or "").strip())

                        st.success("✅ Connexion réussie !")
                        st.rerun()
                else:
                    st.error("❌ Code incorrect")

            md_html("</div>")
        return

    # ✅ (3) : lecture safe de breaker_id (évite KeyError)
    breaker_id_raw = st.session_state.get("breaker_id")

    # Si l'ID n'existe pas (session reset, refresh, etc.), on revient au login casse
    if breaker_id_raw is None:
        st.session_state["breaker_ok"] = False
        st.warning("Session casse expirée, merci de vous reconnecter.")
        st.rerun()

    try:
        breaker_id = int(breaker_id_raw)
    except Exception:
        st.session_state["breaker_ok"] = False
        st.warning("Session casse invalide, merci de vous reconnecter.")
        st.rerun()

    md_html(
        """
        <div style='
            background: white;
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        '>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h3 style='margin: 0; color: #111827;'>✅ Mode Rapide Activé</h3>
                    <p style='margin: 0.5rem 0 0 0; color: #6b7280; font-size: 14px;'>Tapez ce que vous voyez, on s'occupe du reste !</p>
                </div>
            </div>
        </div>
        """
    )

    stats = get_breaker_stats_today(breaker_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("📬 Offres aujourd'hui", stats["total"])
    c2.metric("🎯 Ciblées", stats["click"])
    c3.metric("📝 Libres", stats["free"])

    if st.button("🚪 Quitter", key="logout_casse"):
        st.session_state["breaker_ok"] = False
        st.session_state.pop("breaker_id", None)
        st.rerun()
    # ========================================
    # ⬇️ DÉBUT DU CODE À AJOUTER ⬇️
    # ========================================

    # Séparateur visuel
    st.markdown("---")

    # Carte de recherche par plaque
    md_html("""
    <div class='plaque-card'>
        <div style='text-align: center; margin-bottom: 1.5rem;'>
            <h2 style='margin: 0 0 0.5rem 0; color: #111827;'>🚗 Recherche par Plaque</h2>
            <p style='margin: 0; color: #6b7280; font-size: 0.95rem;'>
                Identifiez instantanément le moteur et son niveau d'urgence
            </p>
        </div>
    </div>
    """)

    # Champ de saisie de la plaque
    plaque_input = st.text_input(
        "Numéro de plaque",
        key="plaque_search",
        placeholder="Ex: AB-123-CD ou AB123CD",
        label_visibility="collapsed",
    )

    # Initialiser la variable plaque_data
    plaque_data = None

    # Si une plaque est saisie
    if plaque_input and plaque_input.strip():
        plaque_df = search_plaque(plaque_input.strip())
        
        if not plaque_df.empty:
            plaque_data = plaque_df.iloc[0].to_dict()
            
            # Affichage visuel de la plaque style immatriculation française
            plaque_display = plaque_data.get("plaque", "").upper()
            md_html(f"""
            <div style='text-align: center; margin: 2rem 0;'>
                <div class='plaque-visual'>
                    🇫🇷 {plaque_display}
                </div>
            </div>
            """)
            
            # Affichage des informations du véhicule en métriques
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("🏷️ Code Moteur", plaque_data.get("code_moteur", "—"))
            with col_p2:
                st.metric("🏭 Marque", plaque_data.get("marque", "—"))
            with col_p3:
                st.metric("⚡ Énergie", plaque_data.get("energie", "—"))
            
            col_p4, col_p5 = st.columns(2)
            with col_p4:
                st.metric("🚘 Modèle", plaque_data.get("modele", "—"))
            with col_p5:
                st.metric("📅 Année", plaque_data.get("annee", "—"))
            
            st.success("✅ Véhicule identifié ! Les besoins ci-dessous sont filtrés automatiquement.")
        else:
            st.warning(f"❌ Plaque '{plaque_input}' non trouvée dans la base")
            st.info("💡 Ajoutez cette plaque dans Supabase pour l'identifier automatiquement la prochaine fois")

    # Séparateur avant la recherche classique
    st.markdown("---")

    # ========================================
    # ⬆️ FIN DU CODE À AJOUTER ⬆️
    # ========================================
    st.markdown("### 🔍 Recherche Intelligente")
    st.caption("💡 **Astuce**: Tapez comme vous parlez ! Ex: 'Renault diesel 1.5' ou 'K9K' ou 'Clio diesel 2015'")

    col_search, col_nb = st.columns([3, 1])
    with col_search:
        search = st.text_input(
            "Rechercher",
            key="casse_search",
            placeholder="Ex: Renault diesel, K9K, Peugeot 1.6 HDI, Clio 2015...",
            label_visibility="collapsed",
        )
    with col_nb:
        topn = st.selectbox("Moteurs", [20, 50, 100, 200], index=1, key="casse_topn", label_visibility="collapsed")

    besoins = get_besoins_moteurs(topn)

    if besoins.empty:
        st.info("Aucun besoin actuellement")
        return

    if plaque_data:
        besoins = filter_besoins_by_plaque(besoins, plaque_data)
        if besoins.empty:
            st.warning(f"❌ Aucun besoin ne correspond au moteur {plaque_data.get('code_moteur', '')}")
            st.info("💡 Ce moteur n'est pas recherché actuellement")
            return
        else:
            st.success(f"🎯 {len(besoins)} moteur(s) correspondant à la plaque !")

    # Filtrage par recherche texte (seulement si pas de plaque active)
    if search and search.strip() and not plaque_data:  # ⬅️ AJOUTER "and not plaque_data"
        besoins_filtered = smart_match_motor(search.strip(), besoins)

        if besoins_filtered.empty:
            st.warning(f"❌ Aucun moteur trouvé pour '{search}'")
            st.info("💡 Essayez avec : le code moteur, la marque, le carburant, ou le modèle")

            st.markdown("**Suggestions de recherche :**")
            suggestions = ["Renault diesel", "K9K", "1.6 HDI", "TSI", "DCI", "TDI"]
            cols = st.columns(len(suggestions))
            for i, sug in enumerate(suggestions):
                with cols[i]:
                    if st.button(sug, key=f"sug_{i}", use_container_width=True):
                        st.session_state["casse_search"] = sug
                        st.rerun()
            return
        else:
            besoins = besoins_filtered
            st.success(f"✅ {len(besoins)} moteur(s) trouvé(s) !")

    if not besoins.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Moteurs affichés", len(besoins))
        with col2:
            urgents = len(besoins[besoins["score_urgence"] > 5])
            st.metric("🔥 Urgents", urgents)
        with col3:
            prix_moyen = besoins["prix_moy_achat_3m"].mean()
            st.metric("💰 Prix moyen", f"{prix_moyen:.0f}€" if not pd.isna(prix_moyen) else "—")

    st.markdown("---")

    PAGE_SIZE = 20
    if "casse_page" not in st.session_state:
        st.session_state["casse_page"] = 1

    total = len(besoins)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    colp1, colp2, colp3 = st.columns([1, 2, 1])
    with colp1:
        if st.button("⬅️", disabled=st.session_state["casse_page"] <= 1):
            st.session_state["casse_page"] -= 1
            st.rerun()
    with colp2:
        st.caption(f"Page {st.session_state['casse_page']} / {pages} • {total} moteurs")
    with colp3:
        if st.button("➡️", disabled=st.session_state["casse_page"] >= pages):
            st.session_state["casse_page"] += 1
            st.rerun()

    start = (st.session_state["casse_page"] - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    besoins = besoins.iloc[start:end].copy()

    st.markdown("### 🎯 Moteurs recherchés (vue rapide)")

    for idx, row in besoins.iterrows():
        code = row.get("code_moteur", "")
        score = float(row.get("score_urgence", 0) or 0)
        prix = row.get("prix_moy_achat_3m", None)
        stock = int(row.get("nb_stock_dispo", 0) or 0)
        vendus = int(row.get("nb_vendus_3m", 0) or 0)

        marque = row.get("marque", "")
        energie = row.get("energie", "")
        type_nom = row.get("type_nom", "")
        type_modele = row.get("type_modele", "")
        type_annee = row.get("type_annee", "")

        desc_casse = suggest_motor_description(row)

        if score > 5:
            border_color, urgence_label, urgence_bg = "#dc2626", "🔥 TRÈS URGENT", "#fee2e2"
        elif score > 2:
            border_color, urgence_label, urgence_bg = "#d97706", "⚠️ URGENT", "#fef3c7"
        else:
            border_color, urgence_label, urgence_bg = "#059669", "✓ Normal", "#d1fae5"

        md_html(f"""
        <div style='background:white;border-left:6px solid {border_color};border-radius:14px;padding:14px;margin-bottom:12px;
                    box-shadow:0 2px 10px rgba(0,0,0,0.08);'>
          <div style='display:flex;justify-content:space-between;align-items:center;gap:12px;'>
            <div style='display:flex;align-items:center;gap:10px;'>
              <span style='font-family:monospace;font-weight:900;font-size:20px;
                           background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
                           color:white;padding:8px 12px;border-radius:10px;'>{code}</span>
              <span style='background:{urgence_bg};color:{border_color};padding:6px 10px;border-radius:10px;
                           font-weight:700;font-size:12px;'>{urgence_label}</span>
            </div>
            <div style='text-align:right;'>
              <div style='font-size:11px;color:#6b7280;font-weight:700;'>PRIX MOYEN</div>
              <div style='font-size:18px;color:#111827;font-weight:900;'>{f"{int(prix):d}€" if pd.notna(prix) and float(prix) > 0 else "—"}</div>
            </div>
          </div>

          <div style='margin-top:10px;background:#f9fafb;padding:10px;border-radius:10px;'>
            <div style='color:#111827;font-weight:800;font-size:14px;'>🗣️ "{desc_casse}"</div>
          </div>
        </div>
        """)

        if st.button("✅ Je l'ai", key=f"have_{idx}", type="primary", use_container_width=True):
            st.session_state[f"modal_open_{idx}"] = True

        with st.expander("Détails + proposer autre chose", expanded=bool(st.session_state.get(f"modal_open_{idx}", False))):
            st.caption(f"📋 {marque} {energie} • {type_nom} {type_modele} {type_annee}".strip())
            c1, c2, c3 = st.columns(3)
            c1.metric("Vendus 3M", vendus)
            c2.metric("En stock", stock)
            c3.metric("Urgence", f"{score:.2f}")

            st.divider()
            st.subheader("✅ Envoyer mon offre")
            col1, col2 = st.columns(2)
            with col1:
                prix_propose = st.number_input(
                    "💰 Votre prix (€)",
                    min_value=0.0,
                    value=float(prix) if pd.notna(prix) and float(prix) > 0 else 100.0,
                    step=10.0,
                    key=f"prix_{idx}",
                )
                qty = st.number_input("📦 Quantité", min_value=1, value=1, key=f"qty_{idx}")
            with col2:
                note = st.text_area(
                    "📝 Infos rapides",
                    key=f"note_{idx}",
                    placeholder="Ex: 120k km, bon état, dispo suite",
                    height=90,
                )

            if st.button("📩 Envoyer", key=f"send_{idx}", type="primary", use_container_width=True):
                insert_click_offer(
                    breaker_id=breaker_id,
                    code_moteur=code,
                    marque=marque if pd.notna(marque) else None,
                    energie=energie if pd.notna(energie) else None,
                    type_nom=type_nom if pd.notna(type_nom) else None,
                    type_modele=type_modele if pd.notna(type_modele) else None,
                    type_annee=type_annee if pd.notna(type_annee) else None,
                    prix_demande=float(prix_propose) if prix_propose > 0 else None,
                    qty=int(qty),
                    note=note.strip() if note.strip() else None,
                    immatriculation=None,
                    vin=None,
                    photo_moteur_path=None,
                    photo_plaque_path=None,
                    audio_path=None,
                )
                st.session_state[f"modal_open_{idx}"] = False
                st.success(f"✅ {code} enregistré !")
                st.balloons()
                st.rerun()

            st.divider()
            st.subheader("💬 Proposer une alternative")
            alt_desc = st.text_input(
                "Décrivez ce que vous avez",
                key=f"alt_desc_{idx}",
                placeholder=f"Ex: proche de {code}, autre année, autre version…",
            )
            alt_prix = st.number_input("Prix (€)", min_value=0.0, value=100.0, step=10.0, key=f"alt_prix_{idx}")
            alt_note = st.text_input("Note", key=f"alt_note_{idx}", placeholder="Infos complémentaires")

            if st.button("📩 Envoyer alternative", key=f"send_alt_{idx}", use_container_width=True):
                if not alt_desc.strip():
                    st.error("Veuillez décrire votre proposition")
                else:
                    insert_free_offer(
                        breaker_id=breaker_id,
                        texte=f"Alternative pour {code}: {alt_desc}",
                        prix_demande=float(alt_prix) if alt_prix > 0 else None,
                        note=alt_note.strip() if alt_note.strip() else None,
                        immatriculation=None,
                        vin=None,
                        photo_moteur_path=None,
                        photo_plaque_path=None,
                        audio_path=None,
                    )
                    st.session_state[f"modal_open_{idx}"] = False
                    st.success("✅ Proposition envoyée !")
                    st.balloons()
                    st.rerun()

    st.divider()

    with st.expander("➕ Moteur totalement hors liste"):
        st.caption("Pour les moteurs qui ne sont dans aucune catégorie ci-dessus")

        col1, col2 = st.columns([2, 1])
        with col1:
            texte = st.text_input(
                "Ce que vous voyez / avez",
                key="casse_free_txt",
                placeholder="Ex: Moteur Fiat 1.3 Multijet 2018 95cv 80k km",
            )
        with col2:
            free_prix = st.number_input("Prix (€)", min_value=0.0, value=0.0, step=10.0, key="casse_free_prix")

        free_note = st.text_area(
            "Détails",
            key="casse_free_note",
            placeholder="État, kilométrage, disponibilité...",
            height=80,
        )

        if st.button("📩 Envoyer", use_container_width=True, key="send_free"):
            if not texte.strip():
                st.error("Veuillez décrire le moteur")
            else:
                insert_free_offer(
                    breaker_id=breaker_id,
                    texte=texte.strip(),
                    prix_demande=float(free_prix) if free_prix > 0 else None,
                    note=free_note.strip() if free_note.strip() else None,
                    immatriculation=None,
                    vin=None,
                    photo_moteur_path=None,
                    photo_plaque_path=None,
                    audio_path=None,
                )
                st.success("✅ Moteur envoyé !")
                st.balloons()
                st.rerun()



def normalize_code_moteur(x) -> str:
    if x is None:
        return ""
    s = str(x).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    try:
        f = float(s.replace(",", "."))
        if f.is_integer():
            return str(int(f))
    except Exception:
        pass
    return s


def render_analyse():
    if st.button("⬅ Retour à l'accueil", use_container_width=False):
        set_page("home")
        st.rerun()

    st.markdown("## 📊 Analyse avancée")
    piece = piece_selector("analyse_piece")

    tabs = st.tabs(["📦 Stock", "💰 Prix", "📈 Tendances", "📥 Offres"])

    with tabs[0]:
        st.markdown("### Stock disponible")
        if piece == "moteurs":
            dispo = get_stock_dispo_breakdown()
        else:
            # NOTE: fonction non fournie dans ton extrait; je ne touche pas
            dispo = get_stock_dispo_breakdown_boites()

        col1, col2 = st.columns(2)
        with col1:
            dispo_marque = dispo[dispo["marque"].notna() & (dispo["marque"] != "")]
            if not dispo_marque.empty:
                s = dispo_marque.groupby("marque")["n"].sum().sort_values(ascending=False).head(15).reset_index()
                fig = px.bar(s, x="marque", y="n", title="Top 15 marques en stock", labels={"marque": "Marque", "n": "Quantité"})
                fig.update_traces(marker_color=COLORS["primary"])
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            dispo_energie = dispo[dispo["energie"].notna() & (dispo["energie"] != "")]
            if not dispo_energie.empty:
                s = dispo_energie.groupby("energie")["n"].sum().reset_index()
                fig = px.pie(s, values="n", names="energie", title="Répartition par énergie")
                fig.update_traces(textposition="inside", textinfo="percent+label")
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        prix = get_prix_achat_dispo(limit=200000)
        if not prix.empty:
            fig = px.histogram(prix, x="prix", nbins=40, title="Distribution des prix d'achat", labels={"prix": "Prix d'achat (€)", "count": "Fréquence"})
            fig.update_traces(marker_color=COLORS["success"])
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.markdown("### Évolution des prix")
        n_months = st.slider("Période (mois)", 3, 36, 12, 1, key="prix_n_months")

        achats = get_prix_achat_par_mois(n_months)
        ventes = get_prix_vente_par_mois(n_months)
        df_global = pd.merge(achats, ventes, on="mois", how="outer").sort_values("mois")

        if not df_global.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_global["mois"], y=df_global["prix_achat_moy"], mode="lines+markers", name="Prix achat",
                                     line=dict(color=COLORS["primary"], width=3), marker=dict(size=8)))
            fig.add_trace(go.Scatter(x=df_global["mois"], y=df_global["prix_vente_moy"], mode="lines+markers", name="Prix vente",
                                     line=dict(color=COLORS["success"], width=3), marker=dict(size=8)))

            fig.update_layout(title="Évolution mensuelle des prix moyens", xaxis_title="Mois", yaxis_title="Prix (€)",
                              template="plotly_white", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            df_global["marge_moy_estimee"] = df_global["prix_vente_moy"] - df_global["prix_achat_moy"]
            st.dataframe(df_global, use_container_width=True)

    with tabs[2]:
        st.markdown("### Variations de prix")

        col1, col2, col3 = st.columns(3)
        with col1:
            window = st.selectbox("Fenêtre (mois)", [1, 2, 3, 4, 6], index=2)
        with col2:
            minc = st.selectbox("Min observations", [3, 5, 10, 20], index=1)
        with col3:
            topk = st.selectbox("Top affiché", [10, 20, 30, 50], index=1)

        movers_achat = get_price_movers("achat", window_months=window, lookback_months=max(12, window * 4), min_count=minc)
        movers_vente = get_price_movers("vente", window_months=window, lookback_months=max(12, window * 4), min_count=minc)

        code_info = get_code_info()

        def enrich(df: pd.DataFrame) -> pd.DataFrame:
            if df is None or df.empty:
                return df
            out = df.merge(code_info, on="code_moteur", how="left")
            cols = [
                "code_moteur", "marque", "energie", "type_nom", "type_modele", "type_annee",
                "n_recent", "n_prev", "avg_prev", "avg_recent", "delta", "pct",
            ]
            cols = [c for c in cols if c in out.columns]
            return out[cols]

        movers_achat_e = enrich(movers_achat)
        movers_vente_e = enrich(movers_vente)

        col4, col5 = st.columns(2)

        with col4:
            st.markdown("#### 🔺 Achats - Hausses")
            if not movers_achat_e.empty:
                up = movers_achat_e.sort_values("pct", ascending=False).head(int(topk))
                st.dataframe(up, use_container_width=True, height=300)

            st.markdown("#### 🔻 Achats - Baisses")
            if not movers_achat_e.empty:
                down = movers_achat_e.sort_values("pct", ascending=True).head(int(topk))
                st.dataframe(down, use_container_width=True, height=300)

        with col5:
            st.markdown("#### 🔺 Ventes - Hausses")
            if not movers_vente_e.empty:
                up = movers_vente_e.sort_values("pct", ascending=False).head(int(topk))
                st.dataframe(up, use_container_width=True, height=300)

            st.markdown("#### 🔻 Ventes - Baisses")
            if not movers_vente_e.empty:
                down = movers_vente_e.sort_values("pct", ascending=True).head(int(topk))
                st.dataframe(down, use_container_width=True, height=300)

        st.divider()
        st.markdown("### Détail par code moteur")

        candidates = []
        if not movers_achat_e.empty:
            candidates += movers_achat_e.sort_values("pct", ascending=False)["code_moteur"].head(200).tolist()
        if not movers_vente_e.empty:
            candidates += movers_vente_e.sort_values("pct", ascending=False)["code_moteur"].head(200).tolist()
        candidates = sorted(list(dict.fromkeys([c for c in candidates if c])))

        if candidates:
            code = st.selectbox("Choisir un code moteur", candidates)
            achats_code = get_prix_achat_par_mois_code(n_months, code)
            ventes_code = get_prix_vente_par_mois_code(n_months, code)
            df_code = pd.merge(achats_code, ventes_code, on="mois", how="outer").sort_values("mois")

            if not df_code.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_code["mois"], y=df_code["prix_achat_moy"], mode="lines+markers", name="Prix achat",
                                         line=dict(color=COLORS["primary"], width=3)))
                fig.add_trace(go.Scatter(x=df_code["mois"], y=df_code["prix_vente_moy"], mode="lines+markers", name="Prix vente",
                                         line=dict(color=COLORS["success"], width=3)))
                fig.update_layout(title=f"Évolution prix pour {code}", xaxis_title="Mois", yaxis_title="Prix (€)", template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

                df_code["marge_moy_estimee"] = df_code["prix_vente_moy"] - df_code["prix_achat_moy"]
                st.dataframe(df_code, use_container_width=True)

    with tabs[3]:
        st.markdown("### 📥 Offres reçues des casses")

        col6, col7 = st.columns(2)
        with col6:
            st.markdown("#### Offres ciblées")
            df_off = get_recent_click_offers(limit=200)
            st.dataframe(df_off, use_container_width=True, height=400)

        with col7:
            st.markdown("#### Offres libres")
            df_free = get_recent_free_offers(limit=200)
            st.dataframe(df_free, use_container_width=True, height=400)


def render_mise_a_jour_prix():
    import numpy as np
    import re

    if st.button("⬅ Retour à l'accueil", use_container_width=False):
        set_page("home")
        st.rerun()

    md_html(
        """
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 style='font-size: 2.2rem; margin-bottom: 0.4rem;'>💶 Mise à jour des prix</h1>
            <p style='color: #6b7280; font-size: 1.05rem; margin: 0;'>
                Propositions de prix d'achat basées sur ventes, urgence et stock
            </p>
        </div>
        """
    )

    md_html(
        """
        <div class='metric-card' style='margin-bottom: 1rem;'>
            <p style='margin:0; color:#6b7280; font-weight:600;'>Principe</p>
            <p style='margin:0.5rem 0 0 0; color:#111827; font-weight:700;'>
                Prix achat proposé = Prix vente moyen 3 mois × (1 - marge_effective)
            </p>
            <p style='margin:0.25rem 0 0 0; color:#6b7280; font-size: 0.95rem;'>
                marge_effective = marge_cible ± ajustements urgence / surstock
            </p>
        </div>
        """
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        marge_cible = st.slider("🎯 Marge cible (%)", 5, 60, 35, 1, key="maj_prix_marge") / 100.0
    with c2:
        bonus_urgence = st.slider("🔥 Bonus urgence (points de marge)", 0, 20, 8, 1, key="maj_prix_bonus") / 100.0
    with c3:
        malus_surstock = st.slider("📦 Malus surstock (points de marge)", 0, 20, 5, 1, key="maj_prix_malus") / 100.0

    st.markdown("---")

    md_html(
        """
        <div class='metric-card' style='margin-bottom: 1rem;'>
            <h3 style='margin:0 0 0.5rem 0;'>📎 Fichiers Excel</h3>
            <p style='margin:0; color:#6b7280;'>
                Catalogue prix + export tbl MOTEURS pour le mapping.
            </p>
        </div>
        """
    )

    file_cat = st.file_uploader("📄 Catalogue prix (Type moteur)", type=["xlsx"], key="maj_prix_cat")
    file_mot = st.file_uploader("⚙️ tbl MOTEURS.xlsx", type=["xlsx"], key="maj_prix_mot")

    with st.expander("🧪 Debug fichiers", expanded=False):
        st.write("Catalogue:", None if file_cat is None else file_cat.name)
        st.write("Moteurs:", None if file_mot is None else file_mot.name)

    if file_cat is None:
        st.info("Importe le catalogue prix pour continuer.")
        return

    try:
        cat = pd.read_excel(file_cat, engine="openpyxl")
    except Exception as e:
        st.error(f"Erreur lecture catalogue : {e}")
        return

    possible_cols = [c for c in cat.columns if str(c).strip().lower() in ["type moteur", "type_moteur", "typemoteur"]]
    if not possible_cols:
        st.error("Colonne 'Type moteur' introuvable.")
        st.write(list(cat.columns))
        return

    col_type = possible_cols[0]
    cat = cat[cat[col_type].notna()].copy()

    cat["type_moteur_excel"] = (
        cat[col_type]
        .astype(str)
        .str.replace("\u00A0", " ", regex=False)
        .str.strip()
        .str.upper()
    )

    cat["code_moteur_join"] = None
    cat["mapping_status"] = "❌ Non mappé"

    if file_mot is not None:
        try:
            mot = pd.read_excel(file_mot, engine="openpyxl")
        except Exception as e:
            st.error(f"Erreur lecture tbl MOTEURS : {e}")
            return

        if not {"N_TypeMoteur", "code_moteur"}.issubset(mot.columns):
            st.error("tbl MOTEURS doit contenir N_TypeMoteur et code_moteur")
            return

        mot2 = mot[["N_TypeMoteur", "code_moteur"]].copy()
        mot2["N_TypeMoteur"] = pd.to_numeric(mot2["N_TypeMoteur"], errors="coerce")
        mot2["code_moteur"] = (
            mot2["code_moteur"]
            .astype(str)
            .str.replace("\u00A0", " ", regex=False)
            .str.strip()
            .str.upper()
        )
        mot2 = mot2.dropna()
        mot2["N_TypeMoteur"] = mot2["N_TypeMoteur"].astype(int)

        rep = (
            mot2.groupby(["N_TypeMoteur", "code_moteur"])
            .size()
            .reset_index(name="n")
            .sort_values(["N_TypeMoteur", "n"], ascending=[True, False])
            .drop_duplicates("N_TypeMoteur")
        )
        mapper = dict(zip(rep["N_TypeMoteur"].astype(str), rep["code_moteur"]))

        def extract_int(s: str):
            m = re.search(r"\d+", s or "")
            return int(m.group(0)) if m else None

        cat["_num"] = cat["type_moteur_excel"].apply(extract_int)
        cat["code_moteur_join"] = cat["_num"].astype("Int64").astype(str).map(mapper)

        cat["mapping_status"] = np.where(cat["code_moteur_join"].notna(), "✅ Mappé", "❌ Introuvable")
        cat.drop(columns=["_num"], inplace=True)

    besoins = get_besoins_moteurs(2000)
    ventes3m = get_prix_vente_moy_code_3m()

    df = (
        cat.merge(besoins, left_on="code_moteur_join", right_on="code_moteur", how="left")
           .merge(ventes3m, left_on="code_moteur_join", right_on="code_moteur", how="left", suffixes=("", "_v3m"))
    )

    for c in ["nb_vendus_3m", "nb_stock_dispo", "score_urgence", "prix_vente_moy_3m"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["f_urgence"] = (df["score_urgence"] / 8.0).clip(0, 1)
    df["f_surstock"] = (df["nb_stock_dispo"] / (df["nb_vendus_3m"] + 1) / 5.0).clip(0, 1)

    df["marge_effective"] = (marge_cible - bonus_urgence * df["f_urgence"] + malus_surstock * df["f_surstock"]).clip(0.05, 0.9)
    df["prix_achat_propose"] = (df["prix_vente_moy_3m"] * (1 - df["marge_effective"])).round(0)

    def decision(r):
        if str(r["mapping_status"]).startswith("❌"):
            return "❌ Pas de mapping"
        if r["prix_vente_moy_3m"] == 0:
            return "⚠️ Pas de ventes"
        if r["score_urgence"] >= 5:
            return "🔥 Monter prix"
        if r["nb_stock_dispo"] >= 3 and r["nb_vendus_3m"] <= 1:
            return "📦 Baisser prix"
        return "✅ OK"

    df["reco"] = df.apply(decision, axis=1)

    st.dataframe(
        df[[col_type, "type_moteur_excel", "code_moteur_join", "mapping_status",
            "nb_vendus_3m", "nb_stock_dispo", "score_urgence",
            "prix_vente_moy_3m", "marge_effective", "prix_achat_propose", "reco"]],
        use_container_width=True,
        height=520,
    )

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger CSV (propositions)", data=csv, file_name="propositions_prix_achat.csv", mime="text/csv")


# =========================
# INIT DB (PERF) - run once
# =========================
@st.cache_resource(show_spinner=False)
def init_db_once() -> bool:
    # Tout ce qui était relancé à chaque rerun passe ici.
    assert_db_ready()
    ensure_stock_views()
    ensure_breaker_tables()
    return True


# =========================
# MAIN
# =========================
def main():
    st.set_page_config(page_title="Multirex", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")
    inject_custom_css()

    if not check_password():
        st.stop()

    # ✅ perf: init DB une seule fois
    init_db_once()

    if st.session_state.get("mode") == "casse":
        render_casse()
        return

    with st.sidebar:
        md_html("<h2 style='text-align: center; margin-bottom: 2rem;'>🚗 Multirex Auto</h2>")
        st.divider()
        logout_button()

    page = get_page()

    if page != "home":
        if st.sidebar.button("🏠 Accueil", use_container_width=True):
            set_page("home")
            st.rerun()

    md_html(
        """
        <div style='background: white; padding: 2rem; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
            <h1 style='margin: 0; font-size: 2.5rem;'>Multirex Auto DMS</h1>
            <p style='color: #6b7280; margin: 0.5rem 0 0 0; font-size: 1.1rem;'>Système de gestion des moteurs</p>
        </div>
        """
    )

    if page == "home":
        kpis = get_kpis_stock()
        col1, col2, col3 = st.columns(3)

        with col1:
            md_html(
                f"""
                <div class='metric-card'>
                    <p style='color: #6b7280; margin: 0; font-size: 0.9rem; font-weight: 600;'>MOTEURS DISPONIBLES</p>
                    <p style='color: {COLORS['success']}; margin: 0.5rem 0 0 0; font-size: 2.5rem; font-weight: 700;'>{kpis['dispo']:,}</p>
                </div>
                """
            )
        with col2:
            md_html(
                f"""
                <div class='metric-card'>
                    <p style='color: #6b7280; margin: 0; font-size: 0.9rem; font-weight: 600;'>MOTEURS VENDUS</p>
                    <p style='color: {COLORS['primary']}; margin: 0.5rem 0 0 0; font-size: 2.5rem; font-weight: 700;'>{kpis['vendus']:,}</p>
                </div>
                """
            )
        with col3:
            md_html(
                f"""
                <div class='metric-card'>
                    <p style='color: #6b7280; margin: 0; font-size: 0.9rem; font-weight: 600;'>TOTAL MOTEURS</p>
                    <p style='color: {COLORS['secondary']}; margin: 0.5rem 0 0 0; font-size: 2.5rem; font-weight: 700;'>{kpis['total']:,}</p>
                </div>
                """
            )

        md_html("<br>")

        kpis_boites = get_kpis_boites()
        colb1, colb2, colb3 = st.columns(3)

        with colb1:
            md_html(
                f"""
                <div class='metric-card'>
                    <p style='color: #6b7280; margin: 0; font-size: 0.9rem; font-weight: 600;'>BOÎTES DISPONIBLES</p>
                    <p style='color: {COLORS['success']}; margin: 0.5rem 0 0 0; font-size: 2.5rem; font-weight: 700;'>{kpis_boites['dispo']:,}</p>
                </div>
                """
            )
        with colb2:
            md_html(
                f"""
                <div class='metric-card'>
                    <p style='color: #6b7280; margin: 0; font-size: 0.9rem; font-weight: 600;'>BOÎTES VENDUES</p>
                    <p style='color: {COLORS['primary']}; margin: 0.5rem 0 0 0; font-size: 2.5rem; font-weight: 700;'>{kpis_boites['vendus']:,}</p>
                </div>
                """
            )
        with colb3:
            md_html(
                f"""
                <div class='metric-card'>
                    <p style='color: #6b7280; margin: 0; font-size: 0.9rem; font-weight: 600;'>TOTAL BOÎTES</p>
                    <p style='color: {COLORS['secondary']}; margin: 0.5rem 0 0 0; font-size: 2.5rem; font-weight: 700;'>{kpis_boites['total']:,}</p>
                </div>
                """
            )

        md_html("<br>")

    if page == "home":
        render_home()
    elif page == "ventes":
        render_ventes()
    elif page == "besoins":
        render_besoins()
    elif page == "analyse":
        render_analyse()
    elif page == "casse":
        render_casse()
    elif page == "mise_a_jour_prix":
        render_mise_a_jour_prix()
    else:
        set_page("home")
        st.rerun()


if __name__ == "__main__":
    main()
