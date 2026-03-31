from __future__ import annotations

import hmac
import os
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
    "primary": "#C41E3A",
    "secondary": "#8B1A2B",
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

        .main { background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); position: relative; }
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
            background: linear-gradient(135deg, #C41E3A 0%, #991B1E 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(196, 30, 58, 0.3);
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
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(196, 30, 58, 0.4); }
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
            border-color: #C41E3A;
            box-shadow: 0 0 0 4px rgba(196, 30, 58, 0.1);
            transform: translateY(-1px);
        }
        .stTextInput > div > div > input::placeholder { color: #9ca3af; }

        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #C41E3A 0%, #8B1A2B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #C41E3A 0%, #8B1A2B 100%);
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
        .stTabs [data-baseweb="tab"]:hover { background-color: rgba(196, 30, 58, 0.1); }

        ::-webkit-scrollbar { width: 12px; height: 12px; }
        ::-webkit-scrollbar-track { background: rgba(241, 241, 241, 0.5); border-radius: 10px; }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #C41E3A 0%, #8B1A2B 100%);
            border-radius: 10px;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #a01830 0%, #6e1422 100%);
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        /* Style pour la carte de recherche par plaque */
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
        .stApp { background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important; }
        .main .block-container { max-width: 480px !important; padding-top: 3rem !important; }
        div[data-testid="stTextInput"] > div > div > input {
            background-color: #f9fafb !important; border: 2px solid #e5e7eb !important;
            border-radius: 12px !important; padding: 12px 16px !important; font-size: 15px !important;
        }
        div[data-testid="stTextInput"] > div > div > input:focus {
            border-color: #C41E3A !important; box-shadow: 0 0 0 3px rgba(196, 30, 58, 0.1) !important;
        }
        div[data-testid="stTextInput"] label { color: #374151 !important; font-weight: 600 !important; font-size: 14px !important; }
        .stButton button { border-radius: 10px !important; padding: 10px 24px !important; font-weight: 600 !important; font-size: 15px !important; }
        .stButton button[kind="primary"] { background: linear-gradient(135deg, #C41E3A 0%, #991B1E 100%) !important; border: none !important; }
        .stButton button[kind="secondary"] { background: white !important; color: #374151 !important; border: 2px solid #e5e7eb !important; }
        </style>
        """
    )

    inject_custom_css()
    md_html("<div style='height: 20px;'></div>")

    md_html(
        """
        <div style='text-align: center; margin-bottom: 40px;'>
            <div style='font-size: 60px; margin-bottom: 16px;'>🚗</div>
            <h1 style='color: white; font-size: 32px; font-weight: 800; margin: 0 0 12px 0;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);'>Multirex Auto DMS</h1>
            <p style='color: rgba(255, 255, 255, 0.9); font-size: 16px; margin: 0;'>Système de gestion intelligent</p>
        </div>
        """
    )

    md_html(
        """
        <h2 style='color: #111827; font-size: 24px; font-weight: 700; margin: 24px 0 8px 0;'>Connexion</h2>
        <p style='color: #6b7280; font-size: 14px; margin: 0;'>Entrez vos identifiants</p>
        """
    )

    user = st.text_input("Email ou identifiant", key="login_user", placeholder="email@exemple.com")
    pwd = st.text_input("Mot de passe", type="password", key="login_pwd", placeholder="Votre mot de passe")

    md_html("<div style='height: 24px;'></div>")

    col1, col2 = st.columns([1, 1])
    with col1:
        login = st.button("🔐 Se connecter", type="primary", use_container_width=True)
    with col2:
        login_casse = st.button("🔧 Centres VHU", use_container_width=True)

    if login:
        authenticated = False
        user_role = "admin"
        user_email = user
        user_nom = ""

        # Try dms_users table first
        import hashlib
        pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
        try:
            df = sql_df("""
                SELECT id, email, nom, role FROM dms_users
                WHERE email = :email AND password_hash = :pwd AND actif = true
                LIMIT 1
            """, {"email": user.strip(), "pwd": pwd_hash})
            if not df.empty:
                row = df.iloc[0]
                authenticated = True
                user_role = row["role"]
                user_email = row["email"]
                user_nom = row.get("nom", "")
                try:
                    exec_sql("UPDATE dms_users SET last_login = NOW() WHERE id = :uid", {"uid": int(row["id"])})
                except Exception:
                    pass
        except Exception:
            pass

        # Fallback: legacy admin from secrets.toml
        if not authenticated:
            admin_user = st.secrets.get("ADMIN_USER", "")
            admin_pwd = st.secrets.get("ADMIN_PASSWORD", "")
            if admin_user and admin_pwd and hmac.compare_digest(user, admin_user) and hmac.compare_digest(pwd, admin_pwd):
                authenticated = True
                user_role = "super_admin"
                user_email = "admin"
                user_nom = "Administrateur"

        if authenticated:
            st.session_state["authenticated"] = True
            st.session_state["mode"] = "casse" if user_role == "vhu" else "admin"
            st.session_state["page"] = "casse" if user_role == "vhu" else "home"
            st.session_state["user_role"] = user_role
            st.session_state["user_email"] = user_email
            st.session_state["user_nom"] = user_nom
            st.success("Connexion réussie !")
            st.rerun()
        else:
            st.error("Identifiants incorrects")

    if login_casse:
        st.session_state["authenticated"] = True
        st.session_state["mode"] = "casse"
        st.session_state["page"] = "casse"
        st.session_state["user_role"] = "vhu"
        st.rerun()

    md_html(
        """
        <div style='text-align: center; margin-top: 32px;'>
            <div style='display: inline-flex; gap: 12px; background: rgba(255, 255, 255, 0.95);
                padding: 12px 24px; border-radius: 50px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);'>
                <span style='color: #C41E3A; font-weight: 600; font-size: 13px;'>📊 Analytics</span>
                <span style='color: #C41E3A; font-weight: 600; font-size: 13px;'>⚡ Temps réel</span>
                <span style='color: #C41E3A; font-weight: 600; font-size: 13px;'>🔒 Sécurisé</span>
            </div>
            <p style='color: rgba(255, 255, 255, 0.8); margin-top: 24px; font-size: 13px;'>Multirex Auto © 2025</p>
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


def ensure_users_table():
    exec_sql("""
    CREATE TABLE IF NOT EXISTS public.dms_users (
        id BIGSERIAL PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        nom TEXT,
        role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('super_admin', 'admin', 'vhu')),
        actif BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_login TIMESTAMPTZ
    );
    """)
    # Create default super_admin if none exists
    df = sql_df("SELECT COUNT(*) AS n FROM dms_users WHERE role = 'super_admin'")
    if df.iloc[0]["n"] == 0:
        import hashlib
        pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
        try:
            exec_sql("""
            INSERT INTO dms_users (email, password_hash, nom, role)
            VALUES ('admin@multirex.fr', :pwd, 'Administrateur', 'super_admin')
            ON CONFLICT (email) DO NOTHING
            """, {"pwd": pwd_hash})
        except Exception:
            pass


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

    # --- Row 1: Main sections ---
    st.markdown("#### Gestion commerciale")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("📈", key="btn_ventes", use_container_width=True):
            set_page("ventes")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Ventes</h4><p style='color: #6b7280; font-size:0.85rem;'>Analyse des ventes</p></div>")

    with c2:
        if st.button("🎯", key="btn_besoins", use_container_width=True):
            set_page("besoins")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Besoins</h4><p style='color: #6b7280; font-size:0.85rem;'>Besoins centres VHU</p></div>")

    with c3:
        if st.button("📊", key="btn_analyse", use_container_width=True):
            set_page("analyse")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Analyse</h4><p style='color: #6b7280; font-size:0.85rem;'>Statistiques</p></div>")

    with c4:
        if st.button("💶", key="btn_prix", use_container_width=True):
            set_page("mise_a_jour_prix")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Mise à jour prix</h4><p style='color: #6b7280; font-size:0.85rem;'>Propositions achat</p></div>")

    md_html("<br>")

    # --- Row 2: Gestion interne (Access replacement) ---
    st.markdown("#### Gestion interne")
    c5, c6, c7, c8 = st.columns(4)

    with c5:
        if st.button("📥", key="btn_receptions", use_container_width=True):
            set_page("receptions")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Receptions</h4><p style='color: #6b7280; font-size:0.85rem;'>Gestion des arrivages</p></div>")

    with c6:
        if st.button("🔍", key="btn_id_moteurs", use_container_width=True):
            set_page("identification_moteurs")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Moteurs</h4><p style='color: #6b7280; font-size:0.85rem;'>Identification moteurs</p></div>")

    with c7:
        if st.button("⚙️", key="btn_id_boites", use_container_width=True):
            set_page("identification_boites")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Boites</h4><p style='color: #6b7280; font-size:0.85rem;'>Identification BV</p></div>")

    with c8:
        if st.button("📋", key="btn_resa", use_container_width=True):
            set_page("reservations")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Reservations</h4><p style='color: #6b7280; font-size:0.85rem;'>Reservations clients</p></div>")

    md_html("<br>")

    # --- Row 3: Autres ---
    st.markdown("#### Outils")
    c9, c10, c11, c12 = st.columns(4)

    with c9:
        if st.button("📜", key="btn_histo", use_container_width=True):
            set_page("historique")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Historique</h4><p style='color: #6b7280; font-size:0.85rem;'>Receptions & expeditions</p></div>")

    with c10:
        if st.button("🔩", key="btn_pieces", use_container_width=True):
            set_page("pieces_detachees")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Pieces Detachees</h4><p style='color: #6b7280; font-size:0.85rem;'>Stock alternateurs, demarreurs...</p></div>")

    with c11:
        if st.button("🛠️", key="btn_casse", use_container_width=True):
            set_page("casse")
            st.rerun()
        md_html("<div style='text-align: center; margin-top: 0.5rem;'><h4>Centres VHU</h4><p style='color: #6b7280; font-size:0.85rem;'>Interface centres VHU</p></div>")

    with c12:
        md_html("<div style='text-align: center; margin-top: 0.5rem; opacity: 0.3;'><h4>&nbsp;</h4></div>")


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


@st.cache_data(show_spinner=False, ttl=120)
def get_all_dashboard_kpis() -> dict:
    """Fetch all dashboard KPIs in one batch for performance."""
    kpis = {}

    # Moteurs stock
    r = sql_df("""
    SELECT
      SUM(CASE WHEN est_disponible = 1 THEN 1 ELSE 0 END) AS mot_dispo,
      COUNT(*) AS mot_total
    FROM v_moteurs_dispo
    """).iloc[0]
    kpis["mot_dispo"] = int(r["mot_dispo"])
    kpis["mot_total"] = int(r["mot_total"])

    # Boites stock
    r = sql_df("""
    SELECT
      SUM(CASE WHEN est_disponible = 1 THEN 1 ELSE 0 END) AS bv_dispo,
      COUNT(*) AS bv_total
    FROM v_boites_dispo
    """).iloc[0]
    kpis["bv_dispo"] = int(r["bv_dispo"])
    kpis["bv_total"] = int(r["bv_total"])

    # Moteurs reserves
    r = sql_df("""
    SELECT COUNT(*) AS n FROM tbl_moteurs
    WHERE resa_client_moteur IS NOT NULL AND TRIM(resa_client_moteur) <> ''
      AND (n_expedition IS NULL) AND (archiver IS NULL OR archiver = false)
    """).iloc[0]
    kpis["mot_reserves"] = int(r["n"])

    # Boites reservees
    r = sql_df("""
    SELECT COUNT(*) AS n FROM tbl_boites
    WHERE resa_client_bv IS NOT NULL AND TRIM(resa_client_bv) <> ''
      AND (vendu IS NULL OR vendu = false) AND stock = true
    """).iloc[0]
    kpis["bv_reserves"] = int(r["n"])

    # Ventes moteurs ce mois
    r = sql_df("""
    SELECT COUNT(*) AS n, COALESCE(SUM(prix_vente_moteur), 0) AS ca
    FROM tbl_expeditions_moteurs
    WHERE date_validation >= date_trunc('month', NOW())
      AND prix_vente_moteur IS NOT NULL
    """).iloc[0]
    kpis["ventes_mois"] = int(r["n"])
    kpis["ca_mois"] = float(r["ca"])

    # Ventes moteurs mois precedent (pour tendance)
    r = sql_df("""
    SELECT COUNT(*) AS n, COALESCE(SUM(prix_vente_moteur), 0) AS ca
    FROM tbl_expeditions_moteurs
    WHERE date_validation >= date_trunc('month', NOW()) - INTERVAL '1 month'
      AND date_validation < date_trunc('month', NOW())
      AND prix_vente_moteur IS NOT NULL
    """).iloc[0]
    kpis["ventes_mois_prec"] = int(r["n"])
    kpis["ca_mois_prec"] = float(r["ca"])

    # Receptions ce mois
    r = sql_df("""
    SELECT COUNT(*) AS n,
      (SELECT COUNT(*) FROM tbl_moteurs m
       JOIN tbl_receptions r2 ON r2.n_reception = m.num_reception
       WHERE r2.date_achat >= date_trunc('month', NOW())) AS nb_mot
    FROM tbl_receptions
    WHERE date_achat >= date_trunc('month', NOW())
    """).iloc[0]
    kpis["receptions_mois"] = int(r["n"])
    kpis["mot_recus_mois"] = int(r["nb_mot"])

    # Marge estimee ce mois
    r = sql_df("""
    SELECT
      COALESCE(SUM(em.prix_vente_moteur) - SUM(m.prix_achat_moteur), 0) AS marge,
      CASE WHEN SUM(em.prix_vente_moteur) > 0
        THEN ROUND(((SUM(em.prix_vente_moteur) - SUM(m.prix_achat_moteur)) / SUM(em.prix_vente_moteur) * 100)::numeric, 1)
        ELSE 0 END AS pct
    FROM tbl_expeditions_moteurs em
    JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
    WHERE em.date_validation >= date_trunc('month', NOW())
      AND em.prix_vente_moteur IS NOT NULL AND em.prix_vente_moteur > 0
      AND m.prix_achat_moteur IS NOT NULL AND m.prix_achat_moteur > 0
    """).iloc[0]
    kpis["marge_mois"] = float(r["marge"])
    kpis["marge_pct"] = float(r["pct"])

    # Prix moyen achat et vente ce mois
    r = sql_df("""
    SELECT
      COALESCE(AVG(em.prix_vente_moteur), 0) AS prix_vente_moy,
      COALESCE((SELECT AVG(m2.prix_achat_moteur)
       FROM tbl_moteurs m2
       JOIN tbl_receptions r2 ON r2.n_reception = m2.num_reception
       WHERE r2.date_achat >= date_trunc('month', NOW())
         AND m2.prix_achat_moteur > 0), 0) AS prix_achat_moy
    FROM tbl_expeditions_moteurs em
    WHERE em.date_validation >= date_trunc('month', NOW())
      AND em.prix_vente_moteur > 0
    """).iloc[0]
    kpis["prix_vente_moy"] = float(r["prix_vente_moy"])
    kpis["prix_achat_moy"] = float(r["prix_achat_moy"])

    return kpis


# All available KPI definitions for user selection
KPI_CATALOG = {
    "mot_dispo":      {"label": "Moteurs en stock",       "color": "success",  "icon": "📦", "fmt": "int"},
    "bv_dispo":       {"label": "Boites en stock",        "color": "success",  "icon": "⚙️", "fmt": "int"},
    "mot_reserves":   {"label": "Moteurs reserves",       "color": "warning",  "icon": "🔒", "fmt": "int"},
    "bv_reserves":    {"label": "Boites reservees",       "color": "warning",  "icon": "🔒", "fmt": "int"},
    "ventes_mois":    {"label": "Ventes du mois",         "color": "primary",  "icon": "📈", "fmt": "int"},
    "ca_mois":        {"label": "CA du mois (EUR)",       "color": "primary",  "icon": "💰", "fmt": "money"},
    "receptions_mois":{"label": "Receptions du mois",     "color": "info",     "icon": "📥", "fmt": "int"},
    "mot_recus_mois": {"label": "Moteurs recus ce mois",  "color": "info",     "icon": "📥", "fmt": "int"},
    "marge_mois":     {"label": "Marge du mois (EUR)",    "color": "success",  "icon": "💵", "fmt": "money"},
    "marge_pct":      {"label": "Marge du mois (%)",      "color": "success",  "icon": "📊", "fmt": "pct"},
    "prix_vente_moy": {"label": "Prix vente moyen",       "color": "primary",  "icon": "🏷️", "fmt": "money"},
    "prix_achat_moy": {"label": "Prix achat moyen",       "color": "secondary","icon": "🏷️", "fmt": "money"},
    "mot_total":      {"label": "Total moteurs (base)",   "color": "secondary","icon": "🗄️", "fmt": "int"},
    "bv_total":       {"label": "Total boites (base)",    "color": "secondary","icon": "🗄️", "fmt": "int"},
}

DEFAULT_KPIS = ["mot_dispo", "bv_dispo", "mot_reserves", "ventes_mois", "ca_mois", "marge_mois", "receptions_mois", "marge_pct"]


def render_kpi_card(key: str, value, meta: dict):
    color = COLORS.get(meta["color"], COLORS["primary"])
    label = meta["label"]
    fmt = meta["fmt"]
    if fmt == "money":
        display = f"{float(value):,.0f}"
    elif fmt == "pct":
        display = f"{float(value):.1f}%"
    else:
        display = f"{int(value):,}"
    md_html(f"""
    <div class='metric-card'>
        <p style='color:#6b7280;margin:0;font-size:0.8rem;font-weight:600;'>{meta['icon']} {label.upper()}</p>
        <p style='color:{color};margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{display}</p>
    </div>
    """)


@st.cache_data(show_spinner=False, ttl=300)
def get_ventes_recents(n_months: int) -> pd.DataFrame:
    q = """
    SELECT
      em.date_validation::date AS jour,
      to_char(em.date_validation, 'YYYY-MM') AS mois,
      UPPER(m.code_moteur) AS code_moteur,
      vd.marque AS marque,
      vd.energie AS energie,
      LEFT(UPPER(m.code_moteur), 3) AS type_moteur,
      COUNT(*) AS nb_vendus
    FROM tbl_expeditions_moteurs em
    JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
    LEFT JOIN v_moteurs_dispo vd ON vd.n_moteur = m.n_moteur
    WHERE em.date_validation >= NOW() - make_interval(months => :months)
      AND m.code_moteur IS NOT NULL
      AND TRIM(m.code_moteur) <> ''
    GROUP BY jour, mois, UPPER(m.code_moteur), vd.marque, vd.energie
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_ventes_recents_boites(n_months: int) -> pd.DataFrame:
    q = """
    SELECT
      eb.date_validation::date AS jour,
      to_char(eb.date_validation, 'YYYY-MM') AS mois,
      COALESCE(b.ref_bv, eb.n_bv::text) AS code_boite,
      COALESCE(b.ref_bv, eb.n_bv::text) AS type_moteur,
      COUNT(*) AS nb_vendus
    FROM tbl_expeditions_boites eb
    LEFT JOIN tbl_boites b ON b.n_bv = eb.n_bv
    WHERE eb.date_validation >= NOW() - (:months || ' months')::interval
    GROUP BY jour, mois, code_boite, type_moteur
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
# VERSION ULTRA-SÉCURISÉE de get_besoins_moteurs()
# Cette version ne plante pas même si les colonnes n'existent pas
# REMPLACE ta fonction actuelle par celle-ci
# ========================================

@st.cache_data(show_spinner=False, ttl=300)
def get_besoins_moteurs(top_n: int = 50) -> pd.DataFrame:
    """
    Récupère les besoins de moteurs - VERSION SÉCURISÉE
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
            MAX(marque) AS marque,
            MAX(energie) AS energie,
            MAX(type_nom) AS type_nom,
            MAX(type_modele) AS type_modele,
            MAX(type_annee) AS type_annee,
            COUNT(*) AS nb_stock_dispo
        FROM v_moteurs_dispo
        WHERE est_disponible = 1
          AND (archiver IS NULL OR archiver = False)
        GROUP BY UPPER(code_moteur)
    )
    SELECT
        v.code_moteur,
        LEFT(COALESCE(s.type_nom, ''), 3) AS type_moteur,
        COALESCE(s.marque, '') AS marque,          -- ✅ Depuis v_moteurs_dispo
        COALESCE(s.energie, '') AS energie,        -- ✅ Depuis v_moteurs_dispo
        COALESCE(s.type_nom, '') AS type_nom,      -- ✅ Depuis v_moteurs_dispo
        COALESCE(s.type_modele, '') AS type_modele,-- ✅ Depuis v_moteurs_dispo
        COALESCE(s.type_annee, '') AS type_annee,  -- ✅ Depuis v_moteurs_dispo
        v.nb_vendus_3m,
        COALESCE(s.nb_stock_dispo, 0) AS nb_stock_dispo,
        ROUND(a.prix_moy_3m, 2)  AS prix_moy_achat_3m,
        ROUND(a.prix_moy_6m, 2)  AS prix_moy_achat_6m,
        ROUND(a.prix_moy_12m, 2) AS prix_moy_achat_12m
    FROM ventes v
    LEFT JOIN achats a ON a.code_moteur = v.code_moteur
    LEFT JOIN stock_dispo s ON s.code_moteur = v.code_moteur
    ORDER BY v.nb_vendus_3m DESC
    LIMIT :topn
    """
    df = sql_df(q, {"topn": int(top_n)})
    if not df.empty:
        df["score_urgence"] = (df["nb_vendus_3m"] / (df["nb_stock_dispo"] + 1)).round(2)
        df = df.sort_values(["score_urgence", "nb_vendus_3m"], ascending=False)
    return df


@st.cache_data(show_spinner=False, ttl=300)
def get_besoins_boites(top_n: int = 50) -> pd.DataFrame:
    q = """
    WITH ventes AS (
        SELECT
            COALESCE(b.ref_bv, eb.n_bv::text) AS code_boite,
            COUNT(*) AS nb_vendus_3m
        FROM tbl_expeditions_boites eb
        LEFT JOIN tbl_boites b ON b.n_bv = eb.n_bv
        WHERE eb.date_validation >= NOW() - INTERVAL '3 months'
        GROUP BY code_boite
    ),
    stock_dispo AS (
        SELECT
            COALESCE(ref_bv, n_bv::text) AS code_boite,
            COUNT(*) AS nb_stock_dispo
        FROM tbl_boites
        WHERE stock = true AND (vendu IS NULL OR vendu = false)
        GROUP BY code_boite
    )
    SELECT
        v.code_boite,
        v.code_boite AS type_moteur,
        v.nb_vendus_3m,
        COALESCE(s.nb_stock_dispo, 0) AS nb_stock_dispo
    FROM ventes v
    LEFT JOIN stock_dispo s ON s.code_boite = v.code_boite
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
def get_prix_par_mois_filtre(n_months: int, energie: str = "", marque: str = "") -> pd.DataFrame:
    """Prix achat et vente mensuels filtrés par énergie et/ou marque via v_moteurs_dispo."""
    clauses = ["r.date_achat >= NOW() - (:months || ' months')::interval",
               "vd.prix_achat_moteur IS NOT NULL", "vd.prix_achat_moteur > 0"]
    clauses_vente = ["em.date_validation >= NOW() - (:months || ' months')::interval",
                     "em.prix_vente_moteur IS NOT NULL", "em.prix_vente_moteur > 0"]
    params: dict = {"months": int(n_months)}

    if energie and energie.strip():
        clauses.append("UPPER(vd.energie) = UPPER(:energie)")
        clauses_vente.append("UPPER(vd2.energie) = UPPER(:energie)")
        params["energie"] = energie.strip()
    if marque and marque.strip():
        clauses.append("UPPER(vd.marque) = UPPER(:marque)")
        clauses_vente.append("UPPER(vd2.marque) = UPPER(:marque)")
        params["marque"] = marque.strip()

    q_achat = f"""
    SELECT to_char(r.date_achat, 'YYYY-MM') AS mois, AVG(vd.prix_achat_moteur) AS prix_achat_moy
    FROM v_moteurs_dispo vd
    JOIN tbl_receptions r ON r.n_reception = vd.num_reception
    WHERE {' AND '.join(clauses)}
    GROUP BY mois ORDER BY mois
    """
    q_vente = f"""
    SELECT to_char(em.date_validation, 'YYYY-MM') AS mois, AVG(em.prix_vente_moteur) AS prix_vente_moy
    FROM tbl_expeditions_moteurs em
    JOIN v_moteurs_dispo vd2 ON vd2.n_moteur = em.n_moteur
    WHERE {' AND '.join(clauses_vente)}
    GROUP BY mois ORDER BY mois
    """
    achats = sql_df(q_achat, params)
    ventes = sql_df(q_vente, params)
    df = pd.merge(achats, ventes, on="mois", how="outer").sort_values("mois")
    return df


@st.cache_data(show_spinner=False, ttl=300)
def get_stock_evolution(n_months: int = 12) -> pd.DataFrame:
    """Evolution du stock disponible par mois (basé sur les dates d'achat et de sortie)."""
    q = """
    WITH mois_range AS (
        SELECT generate_series(
            date_trunc('month', NOW() - (:months || ' months')::interval),
            date_trunc('month', NOW()),
            '1 month'::interval
        )::date AS mois_date
    ),
    entrees AS (
        SELECT date_trunc('month', r.date_achat)::date AS mois_date, COUNT(*) AS nb_entrees
        FROM tbl_moteurs m
        JOIN tbl_receptions r ON r.n_reception = m.num_reception
        WHERE r.date_achat >= NOW() - (:months || ' months')::interval
        GROUP BY mois_date
    ),
    sorties AS (
        SELECT date_trunc('month', em.date_validation)::date AS mois_date, COUNT(*) AS nb_sorties
        FROM tbl_expeditions_moteurs em
        WHERE em.date_validation >= NOW() - (:months || ' months')::interval
        GROUP BY mois_date
    )
    SELECT
        to_char(mr.mois_date, 'YYYY-MM') AS mois,
        COALESCE(en.nb_entrees, 0) AS entrees,
        COALESCE(so.nb_sorties, 0) AS sorties,
        COALESCE(en.nb_entrees, 0) - COALESCE(so.nb_sorties, 0) AS delta
    FROM mois_range mr
    LEFT JOIN entrees en ON en.mois_date = mr.mois_date
    LEFT JOIN sorties so ON so.mois_date = mr.mois_date
    ORDER BY mr.mois_date
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_distinct_energies() -> list:
    df = sql_df("SELECT DISTINCT energie FROM v_moteurs_dispo WHERE energie IS NOT NULL AND TRIM(energie) <> '' ORDER BY energie")
    return df["energie"].tolist() if not df.empty else []


@st.cache_data(show_spinner=False, ttl=300)
def get_distinct_marques() -> list:
    df = sql_df("SELECT DISTINCT marque FROM v_moteurs_dispo WHERE marque IS NOT NULL AND TRIM(marque) <> '' ORDER BY marque")
    return df["marque"].tolist() if not df.empty else []


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
# Receptions queries
# =========================
@st.cache_data(show_spinner=False, ttl=300)
def get_receptions_list(limit: int = 200, search: str = "") -> pd.DataFrame:
    q = """
    SELECT
      r.n_reception,
      f.nom_fournisseur AS fournisseur,
      r.date_achat,
      r.montant_ht,
      r.facture,
      r.reception_terminee,
      (SELECT COUNT(*) FROM tbl_moteurs m WHERE m.num_reception = r.n_reception) AS nb_moteurs,
      (SELECT COUNT(*) FROM tbl_boites b WHERE b.n_reception = r.n_reception) AS nb_boites,
      (SELECT COUNT(*) FROM tbl_pieces p WHERE p.n_reception = r.n_reception) AS nb_pieces
    FROM tbl_receptions r
    LEFT JOIN tbl_fournisseurs f ON f.n_fournisseur = r.n_fournisseur
    ORDER BY r.n_reception DESC
    LIMIT :lim
    """
    df = sql_df(q, {"lim": int(limit)})
    if search and search.strip():
        s = search.strip().upper()
        df = df[
            df["fournisseur"].astype(str).str.upper().str.contains(s, na=False)
            | df["n_reception"].astype(str).str.contains(s, na=False)
        ]
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def _get_client_map() -> dict:
    """Cache a mapping of client ID -> name for resolving resa_client_moteur."""
    df = sql_df("SELECT n_client, COALESCE(societe, nom_contact, '') AS nom FROM tbl_clients WHERE societe IS NOT NULL OR nom_contact IS NOT NULL")
    if df.empty:
        return {}
    return dict(zip(df["n_client"].astype(str), df["nom"]))


def resolve_client_names(df: pd.DataFrame, col: str = "resa_client_moteur") -> pd.DataFrame:
    """Replace numeric client IDs with actual client names in the given column."""
    if col not in df.columns or df.empty:
        return df
    client_map = _get_client_map()
    if not client_map:
        return df
    df = df.copy()
    df[col] = df[col].apply(
        lambda v: client_map.get(str(int(float(v))), v) if pd.notna(v) and str(v).strip().isdigit() else v
    )
    return df


@st.cache_data(show_spinner=False, ttl=300)
def get_reception_moteurs(n_reception: int) -> pd.DataFrame:
    q = """
    SELECT
      m.n_moteur, m.num_interne_moteur, m.code_moteur, m.num_serie,
      m.modele_saisi, m.prix_achat_moteur, m.etat_moteur,
      m.observations,
      m.resa_client_moteur,
      m.date_resa_moteur,
      CASE WHEN m.n_expedition IS NOT NULL OR m.archiver = true THEN 'Vendu/Archive'
           WHEN m.resa_client_moteur IS NOT NULL AND TRIM(m.resa_client_moteur) <> '' THEN 'Reserve'
           ELSE 'Disponible' END AS statut
    FROM tbl_moteurs m
    WHERE m.num_reception = :nrec
    ORDER BY m.n_moteur
    """
    return resolve_client_names(sql_df(q, {"nrec": int(n_reception)}))


@st.cache_data(show_spinner=False, ttl=300)
def get_reception_boites(n_reception: int) -> pd.DataFrame:
    q = """
    SELECT
      b.n_bv, b.num_interne_bv, b.ref_bv, b.achat_bv,
      b.observations_bv, b.resa_client_bv, b.date_resa_bv,
      CASE WHEN b.vendu = true THEN 'Vendu'
           WHEN b.resa_client_bv IS NOT NULL AND TRIM(b.resa_client_bv) <> '' THEN 'Reserve'
           WHEN b.stock = true THEN 'Disponible'
           ELSE 'Indisponible' END AS statut
    FROM tbl_boites b
    WHERE b.n_reception = :nrec
    ORDER BY b.n_bv
    """
    return sql_df(q, {"nrec": int(n_reception)})


# =========================
# Motor identification queries
# =========================
@st.cache_data(show_spinner=False, ttl=120)
def search_moteurs_db(search: str = "", marque_filter: str = "", energie_filter: str = "", statut_filter: str = "", limit: int = 500) -> pd.DataFrame:
    clauses = []
    params: dict = {"lim": int(limit)}

    if search and search.strip():
        clauses.append("""
            (UPPER(m.code_moteur) LIKE :search
             OR UPPER(m.num_serie) LIKE :search
             OR UPPER(m.num_interne_moteur) LIKE :search
             OR UPPER(m.modele_saisi) LIKE :search)
        """)
        params["search"] = f"%{search.strip().upper()}%"

    if marque_filter and marque_filter.strip():
        clauses.append("UPPER(ma.nom_marque) LIKE :marque")
        params["marque"] = f"%{marque_filter.strip().upper()}%"

    if energie_filter and energie_filter.strip():
        clauses.append("UPPER(e.nom_energie) LIKE :energie")
        params["energie"] = f"%{energie_filter.strip().upper()}%"

    if statut_filter == "Disponible":
        clauses.append("m.n_expedition IS NULL AND (m.archiver IS NULL OR m.archiver = false) AND (m.resa_client_moteur IS NULL OR TRIM(m.resa_client_moteur) = '')")
    elif statut_filter == "Reserve":
        clauses.append("m.resa_client_moteur IS NOT NULL AND TRIM(m.resa_client_moteur) <> '' AND m.n_expedition IS NULL AND (m.archiver IS NULL OR m.archiver = false)")
    elif statut_filter == "Vendu/Archive":
        clauses.append("(m.n_expedition IS NOT NULL OR m.archiver = true)")

    where = " AND ".join(clauses)
    if where:
        where = "WHERE " + where

    q = f"""
    SELECT
      m.n_moteur, m.num_interne_moteur, m.code_moteur, m.num_serie,
      m.modele_saisi, m.prix_achat_moteur,
      m.etat_moteur, m.etat_carter,
      m.observations,
      m.resa_client_moteur,
      m.date_resa_moteur,
      m.date_modif, m.utilisateur,
      m.n_expedition, m.archiver,
      ma.nom_marque AS marque,
      e.nom_energie AS energie,
      r.n_reception, r.date_achat,
      f.nom_fournisseur AS fournisseur,
      CASE WHEN m.n_expedition IS NOT NULL OR m.archiver = true THEN 'Vendu/Archive'
           WHEN m.resa_client_moteur IS NOT NULL AND TRIM(m.resa_client_moteur) <> '' THEN 'Reserve'
           ELSE 'Disponible' END AS statut
    FROM tbl_moteurs m
    LEFT JOIN tbl_receptions r ON r.n_reception = m.num_reception
    LEFT JOIN tbl_fournisseurs f ON f.n_fournisseur = r.n_fournisseur
    LEFT JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
    LEFT JOIN tbl_marques ma ON ma.n_marque = tm.n_marque
    LEFT JOIN tbl_energie e ON e.n_energie = COALESCE(tm.n_energie, m.compo_moteur)
    {where}
    ORDER BY m.n_moteur DESC
    LIMIT :lim
    """
    return resolve_client_names(sql_df(q, params))


# =========================
# Gearbox identification queries
# =========================
@st.cache_data(show_spinner=False, ttl=120)
def search_boites_db(search: str = "", statut_filter: str = "", limit: int = 500) -> pd.DataFrame:
    clauses = []
    params: dict = {"lim": int(limit)}

    if search and search.strip():
        clauses.append("""
            (UPPER(b.ref_bv) LIKE :search
             OR UPPER(b.num_interne_bv) LIKE :search
             OR UPPER(b.num_interne_moteur) LIKE :search)
        """)
        params["search"] = f"%{search.strip().upper()}%"

    if statut_filter == "Disponible":
        clauses.append("b.stock = true AND (b.vendu IS NULL OR b.vendu = false) AND (b.resa_client_bv IS NULL OR TRIM(b.resa_client_bv) = '')")
    elif statut_filter == "Reserve":
        clauses.append("b.resa_client_bv IS NOT NULL AND TRIM(b.resa_client_bv) <> '' AND (b.vendu IS NULL OR b.vendu = false)")
    elif statut_filter == "Vendu":
        clauses.append("b.vendu = true")

    where = " AND ".join(clauses)
    if where:
        where = "WHERE " + where

    q = f"""
    SELECT
      b.n_bv, b.num_interne_bv, b.ref_bv, b.num_interne_moteur,
      b.achat_bv, b.prix_vte_bv,
      b.observations_bv,
      b.resa_client_bv, b.date_resa_bv,
      b.date_modif, b.utilisateur,
      b.stock, b.vendu,
      r.n_reception, r.date_achat,
      f.nom_fournisseur AS fournisseur,
      emp.nom_emplacement AS emplacement,
      CASE WHEN b.vendu = true THEN 'Vendu'
           WHEN b.resa_client_bv IS NOT NULL AND TRIM(b.resa_client_bv) <> '' THEN 'Reserve'
           WHEN b.stock = true THEN 'Disponible'
           ELSE 'Indisponible' END AS statut
    FROM tbl_boites b
    LEFT JOIN tbl_receptions r ON r.n_reception = b.n_reception
    LEFT JOIN tbl_fournisseurs f ON f.n_fournisseur = r.n_fournisseur
    LEFT JOIN tbl_emplacements emp ON emp.id_emplacement = b.id_emplacement
    {where}
    ORDER BY b.n_bv DESC
    LIMIT :lim
    """
    return sql_df(q, params)


# =========================
# Reservations queries
# =========================
@st.cache_data(show_spinner=False, ttl=60)
def get_moteurs_reserves() -> pd.DataFrame:
    q = """
    SELECT
      m.n_moteur, m.num_interne_moteur, m.code_moteur, m.num_serie,
      m.modele_saisi, m.prix_achat_moteur,
      m.resa_client_moteur,
      m.date_resa_moteur,
      m.observations,
      ma.nom_marque AS marque,
      e.nom_energie AS energie
    FROM tbl_moteurs m
    LEFT JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
    LEFT JOIN tbl_marques ma ON ma.n_marque = tm.n_marque
    LEFT JOIN tbl_energie e ON e.n_energie = COALESCE(tm.n_energie, m.compo_moteur)
    WHERE m.resa_client_moteur IS NOT NULL
      AND TRIM(m.resa_client_moteur) <> ''
      AND (m.n_expedition IS NULL)
      AND (m.archiver IS NULL OR m.archiver = false)
    ORDER BY m.date_resa_moteur DESC NULLS LAST
    """
    return resolve_client_names(sql_df(q))


@st.cache_data(show_spinner=False, ttl=60)
def get_boites_reservees() -> pd.DataFrame:
    q = """
    SELECT
      b.n_bv, b.num_interne_bv, b.ref_bv,
      b.achat_bv, b.prix_vte_bv,
      b.resa_client_bv, b.date_resa_bv,
      b.observations_bv,
      emp.nom_emplacement AS emplacement
    FROM tbl_boites b
    LEFT JOIN tbl_emplacements emp ON emp.id_emplacement = b.id_emplacement
    WHERE b.resa_client_bv IS NOT NULL
      AND TRIM(b.resa_client_bv) <> ''
      AND (b.vendu IS NULL OR b.vendu = false)
      AND b.stock = true
    ORDER BY b.date_resa_bv DESC NULLS LAST
    """
    return sql_df(q)


def reserve_moteur(n_moteur: int, client: str):
    exec_sql("""
    UPDATE tbl_moteurs
    SET resa_client_moteur = :client, date_resa_moteur = NOW()
    WHERE n_moteur = :nm
    """, {"nm": int(n_moteur), "client": client.strip()})
    st.cache_data.clear()


def cancel_reservation_moteur(n_moteur: int):
    exec_sql("""
    UPDATE tbl_moteurs
    SET resa_client_moteur = NULL, date_resa_moteur = NULL
    WHERE n_moteur = :nm
    """, {"nm": int(n_moteur)})
    st.cache_data.clear()


def reserve_boite(n_bv: int, client: str):
    exec_sql("""
    UPDATE tbl_boites
    SET resa_client_bv = :client, date_resa_bv = NOW()
    WHERE n_bv = :nb
    """, {"nb": int(n_bv), "client": client.strip()})
    st.cache_data.clear()


def cancel_reservation_boite(n_bv: int):
    exec_sql("""
    UPDATE tbl_boites
    SET resa_client_bv = NULL, date_resa_bv = NULL
    WHERE n_bv = :nb
    """, {"nb": int(n_bv)})
    st.cache_data.clear()


# =========================
# History queries
# =========================
@st.cache_data(show_spinner=False, ttl=300)
def get_historique_receptions(n_months: int = 12) -> pd.DataFrame:
    q = """
    SELECT
      r.n_reception,
      f.nom_fournisseur AS fournisseur,
      r.date_achat,
      r.montant_ht,
      (SELECT COUNT(*) FROM tbl_moteurs m WHERE m.num_reception = r.n_reception) AS nb_moteurs,
      (SELECT COUNT(*) FROM tbl_boites b WHERE b.n_reception = r.n_reception) AS nb_boites
    FROM tbl_receptions r
    LEFT JOIN tbl_fournisseurs f ON f.n_fournisseur = r.n_fournisseur
    WHERE r.date_achat >= NOW() - make_interval(months => :months)
    ORDER BY r.date_achat DESC
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_historique_expeditions(n_months: int = 12) -> pd.DataFrame:
    q = """
    SELECT
      e.n_expedition,
      c.societe AS client,
      e.date_chargement,
      e.montant_ht,
      e.type_container,
      e.ref_container,
      e.expedition_terminee,
      (SELECT COUNT(*) FROM tbl_expeditions_moteurs em WHERE em.n_expedition = e.n_expedition) AS nb_moteurs,
      (SELECT COUNT(*) FROM tbl_expeditions_boites eb WHERE eb.n_expedition = e.n_expedition) AS nb_boites
    FROM tbl_expeditions e
    LEFT JOIN tbl_clients c ON c.n_client = e.n_client
    WHERE e.date_chargement >= NOW() - make_interval(months => :months)
    ORDER BY e.date_chargement DESC
    """
    return sql_df(q, {"months": int(n_months)})


# =========================
# Additional statistics queries
# =========================
@st.cache_data(show_spinner=False, ttl=300)
def get_ca_par_mois(n_months: int = 12) -> pd.DataFrame:
    q = """
    SELECT
      to_char(em.date_validation, 'YYYY-MM') AS mois,
      SUM(em.prix_vente_moteur) AS ca_moteurs,
      COUNT(*) AS nb_moteurs_vendus
    FROM tbl_expeditions_moteurs em
    WHERE em.date_validation >= NOW() - make_interval(months => :months)
      AND em.prix_vente_moteur IS NOT NULL
    GROUP BY mois
    ORDER BY mois
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_top_clients(n_months: int = 12, limit: int = 15) -> pd.DataFrame:
    q = """
    SELECT
      c.societe AS client,
      COUNT(DISTINCT e.n_expedition) AS nb_expeditions,
      SUM(e.montant_ht) AS total_ht,
      COUNT(DISTINCT em.n_moteur) AS nb_moteurs
    FROM tbl_expeditions e
    JOIN tbl_clients c ON c.n_client = e.n_client
    LEFT JOIN tbl_expeditions_moteurs em ON em.n_expedition = e.n_expedition
    WHERE e.date_chargement >= NOW() - make_interval(months => :months)
    GROUP BY c.societe
    ORDER BY total_ht DESC NULLS LAST
    LIMIT :lim
    """
    return sql_df(q, {"months": int(n_months), "lim": int(limit)})


@st.cache_data(show_spinner=False, ttl=300)
def get_top_fournisseurs(n_months: int = 12, limit: int = 15) -> pd.DataFrame:
    q = """
    SELECT
      f.nom_fournisseur AS fournisseur,
      COUNT(DISTINCT r.n_reception) AS nb_receptions,
      SUM(r.montant_ht) AS total_ht,
      COUNT(DISTINCT m.n_moteur) AS nb_moteurs
    FROM tbl_receptions r
    JOIN tbl_fournisseurs f ON f.n_fournisseur = r.n_fournisseur
    LEFT JOIN tbl_moteurs m ON m.num_reception = r.n_reception
    WHERE r.date_achat >= NOW() - make_interval(months => :months)
    GROUP BY f.nom_fournisseur
    ORDER BY total_ht DESC NULLS LAST
    LIMIT :lim
    """
    return sql_df(q, {"months": int(n_months), "lim": int(limit)})


@st.cache_data(show_spinner=False, ttl=300)
def get_marge_estimee(n_months: int = 12) -> pd.DataFrame:
    q = """
    SELECT
      to_char(em.date_validation, 'YYYY-MM') AS mois,
      SUM(em.prix_vente_moteur) AS total_vente,
      SUM(m.prix_achat_moteur) AS total_achat,
      SUM(em.prix_vente_moteur) - SUM(m.prix_achat_moteur) AS marge,
      CASE WHEN SUM(em.prix_vente_moteur) > 0
           THEN ROUND(((SUM(em.prix_vente_moteur) - SUM(m.prix_achat_moteur)) / SUM(em.prix_vente_moteur) * 100)::numeric, 1)
           ELSE 0 END AS pct_marge
    FROM tbl_expeditions_moteurs em
    JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
    WHERE em.date_validation >= NOW() - make_interval(months => :months)
      AND em.prix_vente_moteur IS NOT NULL AND em.prix_vente_moteur > 0
      AND m.prix_achat_moteur IS NOT NULL AND m.prix_achat_moteur > 0
    GROUP BY mois
    ORDER BY mois
    """
    return sql_df(q, {"months": int(n_months)})


@st.cache_data(show_spinner=False, ttl=300)
def get_stock_dispo_breakdown_boites() -> pd.DataFrame:
    return sql_df("""
    SELECT
      COALESCE(tb.ref_bv, 'N/A') AS marque,
      '' AS energie,
      COUNT(*) AS n
    FROM v_boites_dispo tb
    WHERE est_disponible = 1
    GROUP BY tb.ref_bv
    """)


@st.cache_data(show_spinner=False, ttl=300)
def get_rotation_stock(n_months: int = 6) -> pd.DataFrame:
    q = """
    WITH stock AS (
      SELECT UPPER(code_moteur) AS code_moteur,
             MAX(vd.marque) AS marque,
             MAX(vd.type_nom) AS type_nom,
             COUNT(*) AS nb_stock
      FROM v_moteurs_dispo vd
      WHERE est_disponible = 1
        AND code_moteur IS NOT NULL AND TRIM(code_moteur) <> ''
      GROUP BY UPPER(code_moteur)
    ),
    ventes AS (
      SELECT UPPER(m.code_moteur) AS code_moteur, COUNT(*) AS nb_vendus
      FROM tbl_expeditions_moteurs em
      JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
      WHERE em.date_validation >= NOW() - make_interval(months => :months)
        AND m.code_moteur IS NOT NULL AND TRIM(m.code_moteur) <> ''
      GROUP BY UPPER(m.code_moteur)
    )
    SELECT
      s.code_moteur,
      COALESCE(s.marque, '') AS marque,
      COALESCE(s.type_nom, '') AS type_nom,
      s.nb_stock,
      COALESCE(v.nb_vendus, 0) AS nb_vendus,
      CASE WHEN COALESCE(v.nb_vendus, 0) = 0 THEN 999
           ELSE ROUND((s.nb_stock::numeric / v.nb_vendus * :months), 1)
      END AS mois_rotation
    FROM stock s
    LEFT JOIN ventes v ON v.code_moteur = s.code_moteur
    WHERE s.nb_stock > 0
    ORDER BY mois_rotation DESC
    """
    return sql_df(q, {"months": int(n_months)})


# =========================
# Pieces detachees (Supabase)
# =========================

@st.cache_data(show_spinner=False, ttl=120)
def load_all_pieces_stock() -> pd.DataFrame:
    """Load all spare parts stock from Supabase tbl_pieces_detachees."""
    q = """
    SELECT categorie, marque, reference, modele, stock
    FROM tbl_pieces_detachees
    ORDER BY categorie, reference
    """
    df = sql_df(q)
    if df.empty:
        return pd.DataFrame(columns=["categorie", "marque", "reference", "modele", "stock"])
    df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(show_spinner=False, ttl=120)
def load_pieces_mouvements(categorie: str, reference: str) -> pd.DataFrame:
    """Get movement history for a specific part from Supabase tbl_pieces_mouvements."""
    reference = (reference or "").strip()
    if not reference:
        return pd.DataFrame(columns=["date", "quantite", "client"])
    q = """
    SELECT date_mouvement AS date, quantite, client
    FROM tbl_pieces_mouvements
    WHERE UPPER(reference) = UPPER(:ref)
      AND categorie = :cat
    ORDER BY date_mouvement
    """
    df = sql_df(q, {"ref": reference, "cat": categorie})
    if df.empty:
        return pd.DataFrame(columns=["date", "quantite", "client"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df


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

    topn = st.slider("Nombre de references affichees", min_value=10, max_value=500, value=100, step=10,
                      help="Nombre de references a analyser (vendues sur 3 mois)")
    if piece == "moteurs":
        besoins = get_besoins_moteurs(topn)
    else:
        besoins = get_besoins_boites(topn)

    if besoins.empty:
        st.warning("Aucun besoin calcule.")
        return

    st.info("💡 Score urgence = ventes 3 mois / (stock dispo + 1). "
            "Score > 1 = en manque (forte demande, peu de stock). "
            "Score < 0.5 avec stock eleve = surstock potentiel.")

    code_col = "type_moteur" if piece == "moteurs" else "code_boite"

    tab_manque, tab_surstock, tab_all = st.tabs(["🔴 En manque", "🟡 En surstock", "📋 Tout voir"])

    with tab_manque:
        st.markdown("### References recherchees et non disponibles (ou stock insuffisant)")
        manque = besoins[besoins["score_urgence"] >= 1.0].sort_values("score_urgence", ascending=False)
        if manque.empty:
            st.success("Aucune reference en manque critique.")
        else:
            st.warning(f"**{len(manque)} reference(s) en manque** (vendues mais stock insuffisant)")
            fig = px.bar(
                manque.head(50),
                x=code_col,
                y="score_urgence",
                title=f"References en manque (score >= 1)",
                labels={code_col: "Type moteur" if piece == "moteurs" else "Code boite",
                        "score_urgence": "Score d'urgence"},
                color="score_urgence",
                color_continuous_scale=["#f59e0b", "#ef4444"],
            )
            fig.update_layout(template="plotly_white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            base_cols = [code_col, "nb_vendus_3m", "nb_stock_dispo", "score_urgence"]
            optional_cols = ["marque", "energie", "type_nom", "type_modele", "type_annee"]
            cols_to_show = [c for c in base_cols + optional_cols if c in manque.columns]
            st.dataframe(manque[cols_to_show], use_container_width=True)

    with tab_surstock:
        st.markdown("### References en surstock (stock eleve, peu de ventes)")
        surstock = besoins[(besoins["nb_stock_dispo"] > 0) & (besoins["score_urgence"] < 0.5)].sort_values("nb_stock_dispo", ascending=False)
        if surstock.empty:
            st.success("Aucune reference en surstock.")
        else:
            st.info(f"**{len(surstock)} reference(s) en surstock** (stock eleve, faible demande)")
            fig = px.bar(
                surstock.head(50),
                x=code_col,
                y="nb_stock_dispo",
                title="References en surstock",
                labels={code_col: "Type moteur" if piece == "moteurs" else "Code boite",
                        "nb_stock_dispo": "Stock disponible"},
                color="score_urgence",
                color_continuous_scale=["#10b981", "#f59e0b"],
            )
            fig.update_layout(template="plotly_white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            base_cols = [code_col, "nb_vendus_3m", "nb_stock_dispo", "score_urgence"]
            optional_cols = ["marque", "energie", "type_nom", "type_modele", "type_annee"]
            cols_to_show = [c for c in base_cols + optional_cols if c in surstock.columns]
            st.dataframe(surstock[cols_to_show], use_container_width=True)

    with tab_all:
        st.markdown("### Toutes les references analysees")
        topk = min(int(topn), len(besoins))
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
            title=f"Top {topk} besoins par score d'urgence",
            labels={code_col: "Type moteur" if piece == "moteurs" else "Code boite",
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

    # ✅ AJOUTE CE CODE ICI - BOUTON POUR VIDER LE CACHE
    col_debug1, col_debug2 = st.columns([3, 1])
    with col_debug2:
        if st.button("🔄 Vider cache", key="clear_cache_btn"):
            st.cache_data.clear()
            st.success("✅ Cache vidé !")
            st.rerun()

    st.markdown("## 🛠️ Interface Centres VHU - Mode Rapide")

    access_code = st.secrets.get("BREAKER_ACCESS_CODE", "")
    if not access_code:
        st.error("BREAKER_ACCESS_CODE manquant dans .streamlit/secrets.toml")
        st.stop()

    if not st.session_state["breaker_ok"]:
        md_html(
            """
            <div style='text-align: center; margin-bottom: 2rem;'>
                <div style='font-size: 60px; margin-bottom: 1rem;'>🔧</div>
                <h2 style='color: white; margin: 0;'>Interface Rapide Centres VHU</h2>
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
                "🏢 Nom de votre centre VHU",
                key="breaker_name",
                value=saved_name,
                placeholder="Ex: Centre VHU 32",
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
                        st.error("Veuillez entrer le nom de votre centre VHU")
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
        st.warning("Session VHU expirée, merci de vous reconnecter.")
        st.rerun()

    try:
        breaker_id = int(breaker_id_raw)
    except Exception:
        st.session_state["breaker_ok"] = False
        st.warning("Session VHU invalide, merci de vous reconnecter.")
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
            <h2 style='margin: 0 0 0.5rem 0; color: #111827;'>Recherche par Plaque</h2>
            <p style='margin: 0; color: #6b7280; font-size: 0.95rem;'>
                Identifiez instantanément le moteur et son niveau d'urgence
            </p>
            <p style='margin: 0.5rem 0 0 0; color: #C41E3A; font-size: 0.85rem; font-weight: 600;'>
                Integration API 3A prevue prochainement pour identification automatique
            </p>
        </div>
    </div>
    """)

    # Champ de saisie de la plaque - plus visible
    col_plaque_in, col_plaque_btn = st.columns([4, 1])
    with col_plaque_in:
        md_html("""
        <style>
        div[data-testid="stTextInput"][data-st-key="plaque_search"] input {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.15rem !important;
            padding: 1rem 1.2rem !important;
            text-align: center !important;
            border: 3px solid #C41E3A !important;
            border-radius: 12px !important;
        }
        div[data-testid="stTextInput"][data-st-key="plaque_search"] input:focus {
            border-color: #8B1A2B !important;
            box-shadow: 0 0 0 4px rgba(196, 30, 58, 0.15) !important;
        }
        </style>
        """)
        plaque_input = st.text_input(
            "Numero de plaque",
            key="plaque_search",
            placeholder="AB-123-CD",
            label_visibility="collapsed",
        )
    with col_plaque_btn:
        md_html("<div style='height: 0.5rem;'></div>")
        if st.button("Effacer", key="clear_plaque", use_container_width=True):
            st.session_state["plaque_search"] = ""
            st.rerun()

    # Initialiser la variable plaque_data
    plaque_data = None

    # Si une plaque est saisie
    if plaque_input and plaque_input.strip():
        with st.spinner("Recherche en cours..."):
            pass  # Visual searching state
        plaque_df = search_plaque(plaque_input.strip())

        if not plaque_df.empty:
            plaque_data = plaque_df.iloc[0].to_dict()

            # Affichage visuel de la plaque style immatriculation francaise
            plaque_display = plaque_data.get("plaque", "").upper()
            md_html(f"""
            <div style='text-align: center; margin: 2rem 0;'>
                <div style='display:inline-block;background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 100%);
                     border:5px solid #1e3a8a;border-radius:10px;padding:1.2rem 2rem;
                     font-family:Courier New,monospace;font-size:2.5rem;font-weight:900;
                     color:white;letter-spacing:0.4rem;
                     box-shadow:0 6px 12px rgba(0,0,0,0.25),inset 0 2px 4px rgba(255,255,255,0.2);'>
                    {plaque_display}
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

    # ✅ AJOUT MINIMAL : normaliser l'affichage des champs (évite NaN qui rend tout "vide")
    def clean_txt(v):
        if v is None:
            return "—"
        try:
            if pd.isna(v):
                return "—"
        except Exception:
            pass
        s = str(v).strip()
        return s if s else "—"

    for idx, row in besoins.iterrows():
        code = row.get("code_moteur", "")
        score = float(row.get("score_urgence", 0) or 0)
        prix = row.get("prix_moy_achat_3m", None)
        stock = int(row.get("nb_stock_dispo", 0) or 0)
        vendus = int(row.get("nb_vendus_3m", 0) or 0)

        marque = clean_txt(row.get("marque"))
        energie = clean_txt(row.get("energie"))
        type_nom = clean_txt(row.get("type_nom"))
        type_modele = clean_txt(row.get("type_modele"))
        type_annee = clean_txt(row.get("type_annee"))

        desc_casse = suggest_motor_description(row)

        if score > 5:
            border_color, urgence_label, urgence_bg = "#dc2626", "🔥 TRÈS URGENT", "#fee2e2"
        elif score > 2:
            border_color, urgence_label, urgence_bg = "#d97706", "⚠️ URGENT", "#fef3c7"
        else:
            border_color, urgence_label, urgence_bg = "#059669", "✓ Normal", "#d1fae5"

        # ✅ AJOUT DES INFOS MARQUE/ENERGIE ICI
        md_html(f"""
        <div style='background:white;border-left:6px solid {border_color};border-radius:14px;padding:14px;margin-bottom:12px;
                    box-shadow:0 2px 10px rgba(0,0,0,0.08);'>
        <div style='display:flex;justify-content:space-between;align-items:center;gap:12px;'>
            <div style='display:flex;align-items:center;gap:10px;'>
            <span style='font-family:monospace;font-weight:900;font-size:20px;
                        background:linear-gradient(135deg,#C41E3A 0%,#8B1A2B 100%);
                        color:white;padding:8px 12px;border-radius:10px;'>{code}</span>
            <span style='background:{urgence_bg};color:{border_color};padding:6px 10px;border-radius:10px;
                        font-weight:700;font-size:12px;'>{urgence_label}</span>
            </div>
            <div style='text-align:right;'>
            <div style='font-size:11px;color:#6b7280;font-weight:700;'>PRIX MOYEN</div>
            <div style='font-size:18px;color:#111827;font-weight:900;'>{f"{int(prix):d}€" if pd.notna(prix) and float(prix) > 0 else "—"}</div>
            </div>
        </div>

        <!-- ✅ SECTION AJOUTÉE : Affichage marque + energie + modèle -->
        <div style='margin-top:10px;display:flex;gap:12px;flex-wrap:wrap;'>
            <span style='background:#f3f4f6;padding:6px 12px;border-radius:8px;font-size:13px;font-weight:600;color:#374151;'>
            🏭 {marque}
            </span>
            <span style='background:#fef3c7;padding:6px 12px;border-radius:8px;font-size:13px;font-weight:600;color:#92400e;'>
            ⚡ {energie}
            </span>
            <span style='background:#e0e7ff;padding:6px 12px;border-radius:8px;font-size:13px;font-weight:600;color:#3730a3;'>
            🚗 {type_modele}
            </span>
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
            dispo = get_stock_dispo_breakdown_boites()

        col1, col2 = st.columns(2)
        with col1:
            dispo_marque = dispo[dispo["marque"].notna() & (dispo["marque"] != "")]
            if not dispo_marque.empty:
                s = dispo_marque.groupby("marque")["n"].sum().sort_values(ascending=False).head(15).reset_index()
                fig = px.bar(s, x="marque", y="n", title="Top 15 marques en stock", labels={"marque": "Marque", "n": "Quantite"})
                fig.update_traces(marker_color=COLORS["primary"])
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            dispo_energie = dispo[dispo["energie"].notna() & (dispo["energie"] != "")]
            if not dispo_energie.empty:
                s = dispo_energie.groupby("energie")["n"].sum().reset_index()
                fig = px.pie(s, values="n", names="energie", title="Repartition par energie")
                fig.update_traces(textposition="inside", textinfo="percent+label")
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        if piece == "moteurs":
            st.markdown("### Evolution du stock (entrees / sorties)")
            n_months_stock = st.slider("Periode (mois)", 3, 36, 12, 1, key="stock_evol_months")
            stock_evol = get_stock_evolution(n_months_stock)
            if not stock_evol.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=stock_evol["mois"], y=stock_evol["entrees"], name="Entrees (achats)", marker_color=COLORS["success"]))
                fig.add_trace(go.Bar(x=stock_evol["mois"], y=stock_evol["sorties"], name="Sorties (ventes)", marker_color=COLORS["primary"]))
                fig.add_trace(go.Scatter(x=stock_evol["mois"], y=stock_evol["delta"].cumsum(), name="Variation cumulee",
                                         mode="lines+markers", line=dict(color=COLORS["info"], width=3), yaxis="y2"))
                fig.update_layout(
                    title="Flux de stock mensuel", xaxis_title="Mois",
                    yaxis=dict(title="Nombre de moteurs"),
                    yaxis2=dict(title="Variation cumulee", overlaying="y", side="right"),
                    template="plotly_white", barmode="group", hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(stock_evol, use_container_width=True)

    with tabs[1]:
        st.markdown("### Evolution des prix")
        n_months = st.slider("Periode (mois)", 3, 36, 12, 1, key="prix_n_months")

        st.markdown("#### Filtres (optionnel)")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            energies = ["Tous"] + get_distinct_energies()
            sel_energie = st.selectbox("Energie", energies, key="prix_energie_filter")
        with col_f2:
            marques = ["Toutes"] + get_distinct_marques()
            sel_marque = st.selectbox("Marque", marques, key="prix_marque_filter")

        energie_f = "" if sel_energie == "Tous" else sel_energie
        marque_f = "" if sel_marque == "Toutes" else sel_marque

        if energie_f or marque_f:
            df_global = get_prix_par_mois_filtre(n_months, energie=energie_f, marque=marque_f)
            titre_filtre = f" ({sel_energie}" if energie_f else " (Tous"
            titre_filtre += f" / {sel_marque})" if marque_f else " / Toutes)"
        else:
            achats = get_prix_achat_par_mois(n_months)
            ventes = get_prix_vente_par_mois(n_months)
            df_global = pd.merge(achats, ventes, on="mois", how="outer").sort_values("mois")
            titre_filtre = " (global)"

        if not df_global.empty:
            fig = go.Figure()
            if "prix_achat_moy" in df_global.columns:
                fig.add_trace(go.Scatter(x=df_global["mois"], y=df_global["prix_achat_moy"], mode="lines+markers", name="Prix achat",
                                         line=dict(color=COLORS["primary"], width=3), marker=dict(size=8)))
            if "prix_vente_moy" in df_global.columns:
                fig.add_trace(go.Scatter(x=df_global["mois"], y=df_global["prix_vente_moy"], mode="lines+markers", name="Prix vente",
                                         line=dict(color=COLORS["success"], width=3), marker=dict(size=8)))

            fig.update_layout(title=f"Evolution mensuelle des prix moyens{titre_filtre}", xaxis_title="Mois", yaxis_title="Prix (EUR)",
                              template="plotly_white", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            if "prix_achat_moy" in df_global.columns and "prix_vente_moy" in df_global.columns:
                df_global["marge_moy_estimee"] = df_global["prix_vente_moy"] - df_global["prix_achat_moy"]
            st.dataframe(df_global, use_container_width=True)
        else:
            st.info("Aucune donnee de prix pour ces filtres.")

    with tabs[2]:
        st.markdown("### Variations de prix")
        st.info("Compare les prix moyens sur une fenetre recente vs la fenetre precedente. "
                "Les hausses/baisses montrent les types moteurs dont les prix evoluent le plus.")

        col1, col2, col3 = st.columns(3)
        with col1:
            window = st.selectbox("Fenetre (mois)", [1, 2, 3, 4, 6], index=2, key="tendances_window")
        with col2:
            minc = st.selectbox("Min observations", [2, 3, 5, 10, 20], index=1, key="tendances_minc")
        with col3:
            topk = st.selectbox("Top affiche", [10, 20, 30, 50], index=1, key="tendances_topk")

        try:
            movers_achat = get_price_movers("achat", window_months=window, lookback_months=max(12, window * 4), min_count=minc)
            movers_vente = get_price_movers("vente", window_months=window, lookback_months=max(12, window * 4), min_count=minc)
        except Exception as e:
            st.error(f"Erreur lors du calcul des tendances : {e}")
            movers_achat = pd.DataFrame()
            movers_vente = pd.DataFrame()

        try:
            code_info = get_code_info()
        except Exception:
            code_info = pd.DataFrame()

        def enrich(df: pd.DataFrame) -> pd.DataFrame:
            if df is None or df.empty:
                return pd.DataFrame()
            if code_info.empty:
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
            st.markdown("#### Achats - Hausses")
            if not movers_achat_e.empty:
                up = movers_achat_e.sort_values("pct", ascending=False).head(int(topk))
                st.dataframe(up, use_container_width=True, height=300)
            else:
                st.info("Pas assez de donnees d'achat pour cette fenetre.")

            st.markdown("#### Achats - Baisses")
            if not movers_achat_e.empty:
                down = movers_achat_e.sort_values("pct", ascending=True).head(int(topk))
                st.dataframe(down, use_container_width=True, height=300)

        with col5:
            st.markdown("#### Ventes - Hausses")
            if not movers_vente_e.empty:
                up = movers_vente_e.sort_values("pct", ascending=False).head(int(topk))
                st.dataframe(up, use_container_width=True, height=300)
            else:
                st.info("Pas assez de donnees de vente pour cette fenetre.")

            st.markdown("#### Ventes - Baisses")
            if not movers_vente_e.empty:
                down = movers_vente_e.sort_values("pct", ascending=True).head(int(topk))
                st.dataframe(down, use_container_width=True, height=300)

        st.divider()
        st.markdown("### Detail par code moteur")

        candidates = []
        if not movers_achat_e.empty:
            candidates += movers_achat_e.sort_values("pct", ascending=False)["code_moteur"].head(200).tolist()
        if not movers_vente_e.empty:
            candidates += movers_vente_e.sort_values("pct", ascending=False)["code_moteur"].head(200).tolist()
        candidates = sorted(list(dict.fromkeys([c for c in candidates if c])))

        if candidates:
            code = st.selectbox("Choisir un code moteur", candidates, key="tendances_code")
            achats_code = get_prix_achat_par_mois_code(n_months, code)
            ventes_code = get_prix_vente_par_mois_code(n_months, code)
            df_code = pd.merge(achats_code, ventes_code, on="mois", how="outer").sort_values("mois")

            if not df_code.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_code["mois"], y=df_code["prix_achat_moy"], mode="lines+markers", name="Prix achat",
                                         line=dict(color=COLORS["primary"], width=3)))
                fig.add_trace(go.Scatter(x=df_code["mois"], y=df_code["prix_vente_moy"], mode="lines+markers", name="Prix vente",
                                         line=dict(color=COLORS["success"], width=3)))
                fig.update_layout(title=f"Evolution prix pour {code}", xaxis_title="Mois", yaxis_title="Prix (EUR)", template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

                df_code["marge_moy_estimee"] = df_code["prix_vente_moy"] - df_code["prix_achat_moy"]
                st.dataframe(df_code, use_container_width=True)
        else:
            st.info("Aucune donnee de tendance disponible. Essayez de reduire le minimum d'observations.")

    with tabs[3]:
        st.markdown("### 📥 Offres recues des centres VHU")

        st.info("**Offres ciblees** : les centres VHU proposent des moteurs en reponse a vos besoins identifies "
                "(types recherches, urgents). "
                "**Offres libres** : les centres VHU proposent des moteurs ou lots sans lien direct avec vos besoins, "
                "via description texte libre.")

        col6, col7 = st.columns(2)
        with col6:
            st.markdown("#### Offres ciblees")
            df_off = get_recent_click_offers(limit=200)
            if df_off.empty:
                st.info("Aucune offre ciblee recue.")
            else:
                st.dataframe(df_off, use_container_width=True, height=400)

        with col7:
            st.markdown("#### Offres libres")
            df_free = get_recent_free_offers(limit=200)
            if df_free.empty:
                st.info("Aucune offre libre recue.")
            else:
                st.dataframe(df_free, use_container_width=True, height=400)


# =========================
# Render: Receptions
# =========================
def render_receptions():
    if st.button("Retour à l'accueil", use_container_width=False, key="back_receptions"):
        set_page("home")
        st.rerun()

    st.markdown("## 📥 Gestion des Receptions")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        search = st.text_input("Rechercher (N reception, fournisseur)", key="rec_search", placeholder="Ex: 1234 ou DUPONT")
    with col_s2:
        limit = st.selectbox("Nb max de receptions affichees", [50, 100, 200, 500], index=1, key="rec_limit")

    receptions = get_receptions_list(limit=limit, search=search)

    if receptions.empty:
        st.info("Aucune reception trouvee.")
        return

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>RECEPTIONS</p>"
                f"<p style='color:#C41E3A;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{len(receptions)}</p></div>")
    with k2:
        total_moteurs = int(receptions["nb_moteurs"].sum())
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>MOTEURS RECUS</p>"
                f"<p style='color:#10b981;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{total_moteurs:,}</p></div>")
    with k3:
        total_boites = int(receptions["nb_boites"].sum())
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>BOITES RECUES</p>"
                f"<p style='color:#3b82f6;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{total_boites:,}</p></div>")
    with k4:
        total_ht = receptions["montant_ht"].sum()
        total_ht_val = float(total_ht) if pd.notna(total_ht) else 0
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>MONTANT TOTAL HT</p>"
                f"<p style='color:#f59e0b;margin:0.5rem 0 0 0;font-size:1.5rem;font-weight:700;'>{total_ht_val:,.0f} EUR</p></div>")

    md_html("<br>")
    st.dataframe(receptions, use_container_width=True, height=400)

    st.markdown("---")
    st.markdown("### Detail d'une reception")
    rec_ids = sorted(receptions["n_reception"].tolist(), reverse=True)
    sel_rec = st.selectbox("Selectionner une reception", rec_ids, key="rec_detail_id")

    if sel_rec:
        rec_row = receptions[receptions["n_reception"] == sel_rec]
        if not rec_row.empty:
            row = rec_row.iloc[0]
            fournisseur_name = row.get("fournisseur", "N/A") or "N/A"
            date_achat_val = row.get("date_achat", "")
            montant_val = row.get("montant_ht", 0)
            md_html(f"""
            <div class='metric-card' style='margin-bottom:1rem;'>
                <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;'>
                    <div>
                        <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>RECEPTION N°</p>
                        <p style='color:#C41E3A;margin:0.3rem 0 0 0;font-size:1.8rem;font-weight:700;'>{sel_rec}</p>
                    </div>
                    <div>
                        <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>FOURNISSEUR</p>
                        <p style='color:#111827;margin:0.3rem 0 0 0;font-size:1.3rem;font-weight:700;'>{fournisseur_name}</p>
                    </div>
                    <div>
                        <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>DATE</p>
                        <p style='color:#111827;margin:0.3rem 0 0 0;font-size:1.1rem;font-weight:600;'>{date_achat_val}</p>
                    </div>
                    <div>
                        <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>MONTANT HT</p>
                        <p style='color:#f59e0b;margin:0.3rem 0 0 0;font-size:1.1rem;font-weight:700;'>{float(montant_val) if pd.notna(montant_val) else 0:,.0f} EUR</p>
                    </div>
                </div>
            </div>
            """)

        tab_m, tab_b = st.tabs(["Moteurs recus", "Boites recues"])
        with tab_m:
            moteurs = get_reception_moteurs(sel_rec)
            if moteurs.empty:
                st.info("Aucun moteur dans cette reception.")
            else:
                display_cols_m = ["n_moteur", "num_interne_moteur", "code_moteur", "num_serie",
                                  "modele_saisi", "prix_achat_moteur", "etat_moteur",
                                  "statut", "resa_client_moteur", "observations"]
                display_cols_m = [c for c in display_cols_m if c in moteurs.columns]
                st.dataframe(moteurs[display_cols_m], use_container_width=True, height=300)
        with tab_b:
            boites = get_reception_boites(sel_rec)
            if boites.empty:
                st.info("Aucune boite dans cette reception.")
            else:
                st.dataframe(boites, use_container_width=True, height=300)


# =========================
# Render: Motor Identification
# =========================
def render_identification_moteurs():
    if st.button("Retour à l'accueil", use_container_width=False, key="back_id_moteurs"):
        set_page("home")
        st.rerun()

    st.markdown("## ⚙️ Identification Moteurs")

    col_s1, col_s2, col_s3, col_s4 = st.columns([3, 1, 1, 1])
    with col_s1:
        search = st.text_input("Recherche (code, num serie, num interne, modele)", key="mot_search", placeholder="Ex: K9K ou 12345")
    with col_s2:
        statut = st.selectbox("Statut", ["Tous", "Disponible", "Reserve", "Vendu/Archive"], key="mot_statut")
    with col_s3:
        marque_f = st.text_input("Marque", key="mot_marque", placeholder="Ex: RENAULT")
    with col_s4:
        energie_f = st.text_input("Energie", key="mot_energie", placeholder="Ex: DIESEL")

    statut_f = "" if statut == "Tous" else statut
    moteurs = search_moteurs_db(search=search, marque_filter=marque_f, energie_filter=energie_f, statut_filter=statut_f, limit=1000)

    if moteurs.empty:
        st.info("Aucun moteur trouve.")
        return

    k1, k2, k3, k4 = st.columns(4)
    nb_dispo = int((moteurs["statut"] == "Disponible").sum())
    nb_resa = int((moteurs["statut"] == "Reserve").sum())
    nb_vendus = int((moteurs["statut"] == "Vendu/Archive").sum())
    with k1:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>RESULTATS</p>"
                f"<p style='color:#C41E3A;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{len(moteurs)}</p></div>")
    with k2:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>DISPONIBLES</p>"
                f"<p style='color:#10b981;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{nb_dispo}</p></div>")
    with k3:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>RESERVES</p>"
                f"<p style='color:#f59e0b;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{nb_resa}</p></div>")
    with k4:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>VENDUS</p>"
                f"<p style='color:#ef4444;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{nb_vendus}</p></div>")

    md_html("<br>")

    display_cols = ["n_moteur", "num_interne_moteur", "code_moteur", "num_serie", "modele_saisi",
                    "marque", "energie", "prix_achat_moteur", "statut", "resa_client_moteur", "fournisseur", "date_achat"]
    display_cols = [c for c in display_cols if c in moteurs.columns]
    st.dataframe(moteurs[display_cols], use_container_width=True, height=420)

    st.markdown("---")
    st.markdown("### Reserver un moteur")
    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r1:
        dispo_ids = sorted(moteurs[moteurs["statut"] == "Disponible"]["n_moteur"].tolist())
        if dispo_ids:
            sel_mot = st.selectbox("N moteur", dispo_ids, key="resa_mot_id")
        else:
            st.info("Aucun moteur disponible.")
            sel_mot = None
    with col_r2:
        client_resa = st.text_input("Nom du client", key="resa_mot_client", placeholder="Ex: SOCIETE DUPONT")
    with col_r3:
        if sel_mot and client_resa and client_resa.strip():
            if st.button("Reserver", key="btn_resa_mot", use_container_width=True):
                reserve_moteur(sel_mot, client_resa)
                st.success(f"Moteur {sel_mot} reserve pour {client_resa}")
                st.rerun()


# =========================
# Render: Gearbox Identification
# =========================
def render_identification_boites():
    if st.button("Retour à l'accueil", use_container_width=False, key="back_id_boites"):
        set_page("home")
        st.rerun()

    st.markdown("## ⚙️ Identification Boites de vitesses")

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search = st.text_input("Recherche (ref, num interne, num moteur associe)", key="bv_search", placeholder="Ex: JR5 ou BV-123")
    with col_s2:
        statut = st.selectbox("Statut", ["Tous", "Disponible", "Reserve", "Vendu"], key="bv_statut")

    statut_f = "" if statut == "Tous" else statut
    boites = search_boites_db(search=search, statut_filter=statut_f, limit=1000)

    if boites.empty:
        st.info("Aucune boite trouvee.")
        return

    k1, k2, k3, k4 = st.columns(4)
    nb_dispo = int((boites["statut"] == "Disponible").sum())
    nb_resa = int((boites["statut"] == "Reserve").sum())
    nb_vendus = int((boites["statut"] == "Vendu").sum())
    with k1:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>RESULTATS</p>"
                f"<p style='color:#C41E3A;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{len(boites)}</p></div>")
    with k2:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>DISPONIBLES</p>"
                f"<p style='color:#10b981;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{nb_dispo}</p></div>")
    with k3:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>RESERVEES</p>"
                f"<p style='color:#f59e0b;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{nb_resa}</p></div>")
    with k4:
        md_html(f"<div class='metric-card'><p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>VENDUES</p>"
                f"<p style='color:#ef4444;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{nb_vendus}</p></div>")

    md_html("<br>")

    display_cols = ["n_bv", "num_interne_bv", "ref_bv", "num_interne_moteur",
                    "achat_bv", "prix_vte_bv", "statut", "resa_client_bv", "emplacement", "fournisseur", "date_achat"]
    display_cols = [c for c in display_cols if c in boites.columns]
    st.dataframe(boites[display_cols], use_container_width=True, height=420)

    st.markdown("---")
    st.markdown("### Reserver une boite")
    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r1:
        dispo_ids = sorted(boites[boites["statut"] == "Disponible"]["n_bv"].tolist())
        if dispo_ids:
            sel_bv = st.selectbox("N boite", dispo_ids, key="resa_bv_id")
        else:
            st.info("Aucune boite disponible.")
            sel_bv = None
    with col_r2:
        client_resa = st.text_input("Nom du client", key="resa_bv_client", placeholder="Ex: SOCIETE DUPONT")
    with col_r3:
        if sel_bv and client_resa and client_resa.strip():
            if st.button("Reserver", key="btn_resa_bv", use_container_width=True):
                reserve_boite(sel_bv, client_resa)
                st.success(f"Boite {sel_bv} reservee pour {client_resa}")
                st.rerun()


# =========================
# Render: Reservations
# =========================
def render_reservations():
    if st.button("Retour à l'accueil", use_container_width=False, key="back_resa"):
        set_page("home")
        st.rerun()

    st.markdown("## 📋 Reservations clients")

    tab_m, tab_b = st.tabs(["Moteurs", "Boites"])

    with tab_m:
        # --- Nouvelle reservation moteur ---
        st.markdown("### Nouvelle reservation moteur")
        col_r1, col_r2, col_r3 = st.columns([2, 2, 1])
        with col_r1:
            search_mot_resa = st.text_input("Rechercher un moteur disponible (code, num serie...)", key="resa_page_mot_search", placeholder="Ex: K9K ou 12345")
        with col_r2:
            client_resa_mot = st.text_input("Nom du client", key="resa_page_mot_client", placeholder="Ex: SOCIETE DUPONT")

        if search_mot_resa and search_mot_resa.strip():
            dispo_moteurs = search_moteurs_db(search=search_mot_resa, statut_filter="Disponible", limit=50)
            if dispo_moteurs.empty:
                st.info("Aucun moteur disponible correspondant.")
            else:
                display_cols_m = ["n_moteur", "num_interne_moteur", "code_moteur", "num_serie", "modele_saisi", "marque", "energie", "prix_achat_moteur"]
                display_cols_m = [c for c in display_cols_m if c in dispo_moteurs.columns]
                st.dataframe(dispo_moteurs[display_cols_m], use_container_width=True, height=200)
                with col_r3:
                    sel_mot_resa = st.selectbox("N moteur", dispo_moteurs["n_moteur"].tolist(), key="resa_page_sel_mot")
                    if client_resa_mot and client_resa_mot.strip():
                        if st.button("Reserver", key="btn_resa_page_mot", use_container_width=True):
                            reserve_moteur(sel_mot_resa, client_resa_mot)
                            st.success(f"Moteur {sel_mot_resa} reserve pour {client_resa_mot}")
                            st.rerun()

        st.markdown("---")

        # --- Reservations existantes ---
        st.markdown("### Reservations en cours")
        moteurs = get_moteurs_reserves()
        if moteurs.empty:
            st.info("Aucun moteur reserve actuellement.")
        else:
            st.markdown(f"**{len(moteurs)} moteur(s) reserve(s)**")
            st.dataframe(moteurs, use_container_width=True, height=400)

            st.markdown("#### Annuler une reservation")
            sel_cancel = st.selectbox("N moteur a liberer", moteurs["n_moteur"].tolist(), key="cancel_mot_id")
            if st.button("Annuler la reservation", key="btn_cancel_mot"):
                cancel_reservation_moteur(sel_cancel)
                st.success(f"Reservation du moteur {sel_cancel} annulee.")
                st.rerun()

    with tab_b:
        # --- Nouvelle reservation boite ---
        st.markdown("### Nouvelle reservation boite")
        col_r1b, col_r2b, col_r3b = st.columns([2, 2, 1])
        with col_r1b:
            search_bv_resa = st.text_input("Rechercher une boite disponible (ref, num interne...)", key="resa_page_bv_search", placeholder="Ex: JR5")
        with col_r2b:
            client_resa_bv = st.text_input("Nom du client", key="resa_page_bv_client", placeholder="Ex: SOCIETE DUPONT")

        if search_bv_resa and search_bv_resa.strip():
            dispo_boites = search_boites_db(search=search_bv_resa, statut_filter="Disponible", limit=50)
            if dispo_boites.empty:
                st.info("Aucune boite disponible correspondante.")
            else:
                display_cols_b = ["n_bv", "num_interne_bv", "ref_bv", "num_interne_moteur", "achat_bv", "prix_vte_bv", "emplacement"]
                display_cols_b = [c for c in display_cols_b if c in dispo_boites.columns]
                st.dataframe(dispo_boites[display_cols_b], use_container_width=True, height=200)
                with col_r3b:
                    sel_bv_resa = st.selectbox("N boite", dispo_boites["n_bv"].tolist(), key="resa_page_sel_bv")
                    if client_resa_bv and client_resa_bv.strip():
                        if st.button("Reserver", key="btn_resa_page_bv", use_container_width=True):
                            reserve_boite(sel_bv_resa, client_resa_bv)
                            st.success(f"Boite {sel_bv_resa} reservee pour {client_resa_bv}")
                            st.rerun()

        st.markdown("---")

        # --- Reservations existantes ---
        st.markdown("### Reservations en cours")
        boites = get_boites_reservees()
        if boites.empty:
            st.info("Aucune boite reservee actuellement.")
        else:
            st.markdown(f"**{len(boites)} boite(s) reservee(s)**")
            st.dataframe(boites, use_container_width=True, height=400)

            st.markdown("#### Annuler une reservation")
            sel_cancel = st.selectbox("N boite a liberer", boites["n_bv"].tolist(), key="cancel_bv_id")
            if st.button("Annuler la reservation", key="btn_cancel_bv"):
                cancel_reservation_boite(sel_cancel)
                st.success(f"Reservation de la boite {sel_cancel} annulee.")
                st.rerun()


# =========================
# Render: History
# =========================
def render_historique():
    if st.button("Retour à l'accueil", use_container_width=False, key="back_histo"):
        set_page("home")
        st.rerun()

    st.markdown("## 📜 Historique")
    n_months = st.slider("Periode (mois)", 1, 36, 12, key="histo_months")

    tab_r, tab_e, tab_s = st.tabs(["Receptions", "Expeditions", "Statistiques avancees"])

    with tab_r:
        st.markdown("### Historique des receptions")
        receptions = get_historique_receptions(n_months)
        if receptions.empty:
            st.info("Aucune reception sur cette periode.")
        else:
            if "date_achat" in receptions.columns:
                receptions["mois"] = pd.to_datetime(receptions["date_achat"], errors="coerce").dt.to_period("M").astype(str)
                monthly = receptions.groupby("mois").agg(
                    nb_receptions=("n_reception", "count"),
                    total_ht=("montant_ht", "sum"),
                    total_moteurs=("nb_moteurs", "sum")
                ).reset_index()

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    fig = px.bar(monthly, x="mois", y="nb_receptions", title="Receptions par mois",
                                 labels={"mois": "Mois", "nb_receptions": "Nb receptions"})
                    fig.update_traces(marker_color=COLORS["primary"])
                    fig.update_layout(template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
                with col_c2:
                    fig = px.bar(monthly, x="mois", y="total_moteurs", title="Moteurs recus par mois",
                                 labels={"mois": "Mois", "total_moteurs": "Nb moteurs"})
                    fig.update_traces(marker_color=COLORS["success"])
                    fig.update_layout(template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

            st.dataframe(receptions.drop(columns=["mois"], errors="ignore"), use_container_width=True, height=350)

            st.markdown("#### Detail d'une reception")
            rec_ids = sorted(receptions["n_reception"].tolist(), reverse=True)
            sel_rec_h = st.selectbox("Selectionner une reception", rec_ids, key="histo_rec_detail")
            if sel_rec_h:
                rec_row = receptions[receptions["n_reception"] == sel_rec_h]
                if not rec_row.empty:
                    row = rec_row.iloc[0]
                    st.caption(f"Reception **{sel_rec_h}** - {row.get('fournisseur', 'N/A')} - {row.get('date_achat', '')} - {float(row.get('montant_ht', 0) or 0):,.0f} EUR HT")
                tab_hm, tab_hb = st.tabs(["Moteurs", "Boites"])
                with tab_hm:
                    moteurs_h = get_reception_moteurs(sel_rec_h)
                    if moteurs_h.empty:
                        st.info("Aucun moteur.")
                    else:
                        st.dataframe(moteurs_h, use_container_width=True, height=250)
                with tab_hb:
                    boites_h = get_reception_boites(sel_rec_h)
                    if boites_h.empty:
                        st.info("Aucune boite.")
                    else:
                        st.dataframe(boites_h, use_container_width=True, height=250)

    with tab_e:
        st.markdown("### Historique des expeditions")
        expeditions = get_historique_expeditions(n_months)
        if expeditions.empty:
            st.info("Aucune expedition sur cette periode.")
        else:
            if "date_chargement" in expeditions.columns:
                expeditions["mois"] = pd.to_datetime(expeditions["date_chargement"], errors="coerce").dt.to_period("M").astype(str)
                monthly = expeditions.groupby("mois").agg(
                    nb_expeditions=("n_expedition", "count"),
                    total_ht=("montant_ht", "sum"),
                    total_moteurs=("nb_moteurs", "sum")
                ).reset_index()

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    fig = px.bar(monthly, x="mois", y="nb_expeditions", title="Expeditions par mois",
                                 labels={"mois": "Mois", "nb_expeditions": "Nb expeditions"})
                    fig.update_traces(marker_color=COLORS["info"])
                    fig.update_layout(template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
                with col_c2:
                    fig = px.bar(monthly, x="mois", y="total_moteurs", title="Moteurs expedies par mois",
                                 labels={"mois": "Mois", "total_moteurs": "Nb moteurs"})
                    fig.update_traces(marker_color=COLORS["warning"])
                    fig.update_layout(template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

            st.dataframe(expeditions.drop(columns=["mois"], errors="ignore"), use_container_width=True, height=350)

            st.markdown("#### Detail d'une expedition")
            exp_ids = sorted(expeditions["n_expedition"].tolist(), reverse=True)
            sel_exp_h = st.selectbox("Selectionner une expedition", exp_ids, key="histo_exp_detail")
            if sel_exp_h:
                exp_row = expeditions[expeditions["n_expedition"] == sel_exp_h]
                if not exp_row.empty:
                    row = exp_row.iloc[0]
                    st.caption(f"Expedition **{sel_exp_h}** - {row.get('client', 'N/A')} - {row.get('date_chargement', '')} - {float(row.get('montant_ht', 0) or 0):,.0f} EUR HT")
                tab_em, tab_eb = st.tabs(["Moteurs expedies", "Boites expediees"])
                with tab_em:
                    mot_exp = sql_df("""
                        SELECT em.n_moteur, m.code_moteur, m.num_serie, m.modele_saisi,
                               em.prix_vente_moteur, ma.nom_marque AS marque, e.nom_energie AS energie
                        FROM tbl_expeditions_moteurs em
                        JOIN tbl_moteurs m ON m.n_moteur = em.n_moteur
                        LEFT JOIN tbl_types_moteurs tm ON tm.n_type_moteur = m.n_type_moteur
                        LEFT JOIN tbl_marques ma ON ma.n_marque = tm.n_marque
                        LEFT JOIN tbl_energie e ON e.n_energie = COALESCE(tm.n_energie, m.compo_moteur)
                        WHERE em.n_expedition = :nexp
                        ORDER BY em.n_moteur
                    """, {"nexp": int(sel_exp_h)})
                    if mot_exp.empty:
                        st.info("Aucun moteur dans cette expedition.")
                    else:
                        st.markdown(f"**{len(mot_exp)} moteur(s)** - Total: {mot_exp['prix_vente_moteur'].sum():,.0f} EUR")
                        st.dataframe(mot_exp, use_container_width=True, height=250)
                with tab_eb:
                    bv_exp = sql_df("""
                        SELECT eb.n_bv, b.ref_bv, b.num_interne_bv, eb.prix_vente_bv
                        FROM tbl_expeditions_boites eb
                        LEFT JOIN tbl_boites b ON b.n_bv = eb.n_bv
                        WHERE eb.n_expedition = :nexp
                        ORDER BY eb.n_bv
                    """, {"nexp": int(sel_exp_h)})
                    if bv_exp.empty:
                        st.info("Aucune boite dans cette expedition.")
                    else:
                        st.markdown(f"**{len(bv_exp)} boite(s)** - Total: {bv_exp['prix_vente_bv'].sum():,.0f} EUR")
                        st.dataframe(bv_exp, use_container_width=True, height=250)

    with tab_s:
        st.markdown("### Statistiques avancees")
        st.info("**Marge EUR** = Total prix vente - Total prix achat (moteurs avec prix achat et vente renseignes). "
                "**% Marge** = Marge / Total prix vente x 100. "
                "Seuls les moteurs ayant un prix d'achat ET un prix de vente > 0 sont pris en compte.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Chiffre d'affaires moteurs")
            ca = get_ca_par_mois(n_months)
            if not ca.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=ca["mois"], y=ca["ca_moteurs"], name="CA moteurs",
                                     marker_color=COLORS["primary"]))
                fig.add_trace(go.Scatter(x=ca["mois"], y=ca["nb_moteurs_vendus"], name="Nb vendus",
                                         yaxis="y2", mode="lines+markers",
                                         line=dict(color=COLORS["success"], width=2)))
                fig.update_layout(
                    title="CA et volume par mois",
                    yaxis=dict(title="CA (EUR)"),
                    yaxis2=dict(title="Nb vendus", overlaying="y", side="right"),
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Top clients")
            clients = get_top_clients(n_months)
            if not clients.empty:
                fig = px.bar(clients.head(10), x="client", y="total_ht", title="Top 10 clients par CA",
                             labels={"client": "Client", "total_ht": "CA HT (EUR)"})
                fig.update_traces(marker_color=COLORS["primary"])
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(clients, use_container_width=True, height=250)

        with col2:
            st.markdown("#### Marge estimee")
            marge = get_marge_estimee(n_months)
            if not marge.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=marge["mois"], y=marge["marge"], name="Marge EUR",
                                     marker_color=COLORS["success"]))
                fig.add_trace(go.Scatter(x=marge["mois"], y=marge["pct_marge"], name="% Marge",
                                         yaxis="y2", mode="lines+markers",
                                         line=dict(color=COLORS["warning"], width=2)))
                fig.update_layout(
                    title="Marge estimee par mois",
                    yaxis=dict(title="Marge (EUR)"),
                    yaxis2=dict(title="% Marge", overlaying="y", side="right"),
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Top fournisseurs")
            fournisseurs = get_top_fournisseurs(n_months)
            if not fournisseurs.empty:
                fig = px.bar(fournisseurs.head(10), x="fournisseur", y="total_ht", title="Top 10 fournisseurs",
                             labels={"fournisseur": "Fournisseur", "total_ht": "Montant HT (EUR)"})
                fig.update_traces(marker_color=COLORS["info"])
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(fournisseurs, use_container_width=True, height=250)

        st.markdown("---")
        st.markdown("#### Rotation de stock")
        st.info("**Rotation** = nb mois pour ecouler le stock au rythme de vente actuel. "
                "999 = aucune vente sur la periode. Rotation < 3 = forte demande. Rotation > 12 = surstock.")
        rotation = get_rotation_stock(n_months)
        if not rotation.empty:
            # Build display label
            rotation["label"] = rotation.apply(
                lambda r: f"{r['code_moteur']} ({r['marque']})" if r.get("marque") else r["code_moteur"], axis=1)

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("##### Rotation lente (surstock)")
                slow = rotation[(rotation["mois_rotation"] >= 6) & (rotation["mois_rotation"] < 999)].sort_values("mois_rotation", ascending=False).head(30)
                if not slow.empty:
                    fig = px.bar(slow, x="label", y="mois_rotation", title="Codes a rotation lente (> 6 mois)",
                                 labels={"label": "Code moteur", "mois_rotation": "Mois pour ecouler"}, color="nb_stock",
                                 hover_data=["type_nom", "nb_vendus"])
                    fig.update_layout(template="plotly_white", xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucun code en surstock.")

                st.markdown("##### Sans vente (stock mort)")
                dead = rotation[rotation["mois_rotation"] >= 999].sort_values("nb_stock", ascending=False).head(30)
                if not dead.empty:
                    fig = px.bar(dead, x="label", y="nb_stock", title=f"Codes sans vente depuis {n_months} mois",
                                 labels={"label": "Code moteur", "nb_stock": "Quantite en stock"},
                                 hover_data=["type_nom"])
                    fig.update_layout(template="plotly_white", xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

            with col_r2:
                st.markdown("##### Rotation rapide (forte demande)")
                fast = rotation[(rotation["mois_rotation"] < 6) & (rotation["mois_rotation"] > 0)].sort_values("mois_rotation").head(30)
                if not fast.empty:
                    fig = px.bar(fast, x="label", y="mois_rotation", title="Codes a rotation rapide (< 6 mois)",
                                 labels={"label": "Code moteur", "mois_rotation": "Mois pour ecouler"}, color="nb_vendus",
                                 hover_data=["type_nom", "nb_stock"])
                    fig.update_layout(template="plotly_white", xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Aucun code a rotation rapide.")

            st.markdown("##### Tableau complet")
            display_cols_rot = ["code_moteur", "marque", "type_nom", "nb_stock", "nb_vendus", "mois_rotation"]
            display_cols_rot = [c for c in display_cols_rot if c in rotation.columns]
            st.dataframe(rotation[display_cols_rot].sort_values("mois_rotation"), use_container_width=True, height=400)


# =========================
# Render: Pieces Detachees
# =========================
def render_pieces_detachees():
    if st.button("Retour à l'accueil", use_container_width=False, key="back_pieces"):
        set_page("home")
        st.rerun()

    st.markdown("## Pieces Detachees - Stock")

    pieces = load_all_pieces_stock()

    if pieces.empty:
        st.warning("Aucune donnee de pieces detachees trouvee dans Supabase.")
        st.info("Lancez le script **Transfert_supabase.py** pour importer les fichiers Excel de stock dans la base de donnees.")
        return

    # --- KPIs ---
    total_refs = len(pieces)
    total_stock = int(pieces["stock"].sum())
    n_categories = pieces["categorie"].nunique()
    zero_stock = int((pieces["stock"] == 0).sum())

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        md_html(f"""
        <div class='metric-card'>
            <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>REFERENCES</p>
            <p style='color:#C41E3A;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{total_refs:,}</p>
        </div>
        """)
    with k2:
        md_html(f"""
        <div class='metric-card'>
            <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>STOCK TOTAL</p>
            <p style='color:#10b981;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{total_stock:,}</p>
        </div>
        """)
    with k3:
        md_html(f"""
        <div class='metric-card'>
            <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>CATEGORIES</p>
            <p style='color:#3b82f6;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{n_categories}</p>
        </div>
        """)
    with k4:
        md_html(f"""
        <div class='metric-card'>
            <p style='color:#6b7280;margin:0;font-size:0.85rem;font-weight:600;'>STOCK = 0</p>
            <p style='color:#ef4444;margin:0.5rem 0 0 0;font-size:2rem;font-weight:700;'>{zero_stock:,}</p>
        </div>
        """)

    md_html("<br>")

    # --- Filters ---
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        cats = sorted(pieces["categorie"].dropna().unique().tolist())
        sel_cats = st.multiselect("Filtrer par categorie", cats, default=cats, key="pieces_cats")
    with col_f2:
        search_txt = st.text_input("Recherche reference / marque", key="pieces_search", placeholder="Ex: 1234 ou RENAULT")

    filtered = pieces.copy()
    if sel_cats:
        filtered = filtered[filtered["categorie"].isin(sel_cats)]
    if search_txt and search_txt.strip():
        s = search_txt.strip().upper()
        filtered = filtered[
            filtered["reference"].str.upper().str.contains(s, na=False)
            | filtered["marque"].str.upper().str.contains(s, na=False)
        ]

    # --- Stock table ---
    st.markdown("### Tableau de stock")

    def color_stock(val):
        try:
            v = int(val)
        except Exception:
            return ""
        if v == 0:
            return "background-color: #fee2e2; color: #991b1b;"
        elif v <= 2:
            return "background-color: #fef3c7; color: #92400e;"
        else:
            return "background-color: #d1fae5; color: #065f46;"

    st.dataframe(
        filtered.style.applymap(color_stock, subset=["stock"]) if not filtered.empty else filtered,
        use_container_width=True,
        height=420,
    )

    # --- Charts ---
    if not filtered.empty:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            stock_by_cat = filtered.groupby("categorie")["stock"].sum().sort_values(ascending=False).reset_index()
            fig_bar = px.bar(
                stock_by_cat, x="categorie", y="stock",
                title="Stock par categorie",
                labels={"categorie": "Categorie", "stock": "Quantite"},
            )
            fig_bar.update_traces(marker_color=COLORS["primary"])
            fig_bar.update_layout(template="plotly_white", showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_c2:
            refs_by_cat = filtered.groupby("categorie").size().reset_index(name="n")
            fig_pie = px.pie(refs_by_cat, values="n", names="categorie", title="Repartition par categorie")
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(template="plotly_white")
            st.plotly_chart(fig_pie, use_container_width=True)

        # Top 20 highest stock
        top20 = filtered.nlargest(20, "stock")
        if not top20.empty:
            fig_top = px.bar(
                top20, x="reference", y="stock", color="categorie",
                title="Top 20 references par stock",
                labels={"reference": "Reference", "stock": "Quantite"},
            )
            fig_top.update_layout(template="plotly_white")
            st.plotly_chart(fig_top, use_container_width=True)

    # --- Movement history ---
    st.markdown("---")
    st.markdown("### Historique des mouvements")

    all_refs = sorted(filtered["reference"].dropna().unique().tolist()) if not filtered.empty else []
    if all_refs:
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            sel_ref = st.selectbox("Selectionner une reference", all_refs, key="pieces_mvt_ref")
        with col_m2:
            sel_cat_row = filtered[filtered["reference"] == sel_ref]
            sel_cat = sel_cat_row.iloc[0]["categorie"] if not sel_cat_row.empty else ""
            st.text_input("Categorie", value=sel_cat, disabled=True, key="pieces_mvt_cat")

        if sel_ref:
            mvts = load_pieces_mouvements(sel_cat, sel_ref)
            if mvts.empty:
                st.info("Pas de donnees de mouvement disponibles pour cette reference.")
            else:
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    fig_mvt = px.bar(
                        mvts, x="date", y="quantite", color="client",
                        title=f"Mouvements: {sel_ref}",
                        labels={"date": "Date", "quantite": "Quantite"},
                    )
                    fig_mvt.update_layout(template="plotly_white")
                    st.plotly_chart(fig_mvt, use_container_width=True)
                with col_h2:
                    mvts_sorted = mvts.sort_values("date").copy()
                    mvts_sorted["cumul"] = mvts_sorted["quantite"].cumsum()
                    fig_cum = px.line(
                        mvts_sorted, x="date", y="cumul",
                        title=f"Stock cumule: {sel_ref}",
                        labels={"date": "Date", "cumul": "Stock cumule"},
                    )
                    fig_cum.update_traces(line_color=COLORS["primary"], line_width=3)
                    fig_cum.update_layout(template="plotly_white")
                    st.plotly_chart(fig_cum, use_container_width=True)

                st.dataframe(mvts, use_container_width=True)
    else:
        st.info("Aucune reference disponible avec les filtres actuels.")

    # --- Mouvement de stock (entree/sortie) ---
    st.markdown("---")
    st.markdown("### Entree / Sortie de stock")

    col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns([2, 2, 1, 1, 1])
    with col_e1:
        mvt_ref = st.selectbox("Reference", all_refs if all_refs else [""], key="pieces_mvt_add_ref")
    with col_e2:
        mvt_client = st.text_input("Client (pour sortie)", key="pieces_mvt_client", placeholder="Ex: DUPONT")
    with col_e3:
        mvt_qte = st.number_input("Quantite", min_value=-100, max_value=100, value=1, step=1, key="pieces_mvt_qte",
                                   help="Positif = entree, Negatif = sortie")
    with col_e4:
        mvt_cat_row = filtered[filtered["reference"] == mvt_ref] if not filtered.empty and mvt_ref else pd.DataFrame()
        mvt_cat = mvt_cat_row.iloc[0]["categorie"] if not mvt_cat_row.empty else ""
        st.text_input("Categorie", value=mvt_cat, disabled=True, key="pieces_mvt_add_cat")
    with col_e5:
        md_html("<div style='height:28px;'></div>")
        if mvt_ref and mvt_qte != 0:
            if st.button("Valider mouvement", key="btn_mvt_pieces", use_container_width=True):
                try:
                    exec_sql("""
                        INSERT INTO tbl_pieces_mouvements (reference, categorie, quantite, client, date_mouvement)
                        VALUES (:ref, :cat, :qte, :cli, NOW())
                    """, {"ref": mvt_ref, "cat": mvt_cat, "qte": int(mvt_qte), "cli": mvt_client.strip() or None})
                    # Update stock
                    exec_sql("""
                        UPDATE tbl_pieces_detachees SET stock = stock + :qte
                        WHERE reference = :ref AND categorie = :cat
                    """, {"ref": mvt_ref, "cat": mvt_cat, "qte": int(mvt_qte)})
                    st.cache_data.clear()
                    st.success(f"Mouvement enregistre : {'+' if mvt_qte > 0 else ''}{mvt_qte} x {mvt_ref}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

    # --- Pieces sans vente depuis X mois ---
    st.markdown("---")
    st.markdown("### Pieces sans mouvement recent")
    mois_inactif = st.slider("Inactif depuis (mois)", 3, 24, 12, key="pieces_inactif_mois")
    if not filtered.empty:
        try:
            last_mvt = sql_df("""
                SELECT reference, categorie, MAX(date_mouvement) AS dernier_mouvement
                FROM tbl_pieces_mouvements
                GROUP BY reference, categorie
            """)
            if not last_mvt.empty:
                merged = filtered.merge(last_mvt, on=["reference", "categorie"], how="left")
                merged["dernier_mouvement"] = pd.to_datetime(merged["dernier_mouvement"], errors="coerce")
                cutoff = pd.Timestamp.now() - pd.DateOffset(months=mois_inactif)
                inactives = merged[(merged["dernier_mouvement"].isna()) | (merged["dernier_mouvement"] < cutoff)]
                inactives = inactives[inactives["stock"] > 0].sort_values("stock", ascending=False)
                if inactives.empty:
                    st.success(f"Toutes les pieces en stock ont eu un mouvement dans les {mois_inactif} derniers mois.")
                else:
                    st.warning(f"**{len(inactives)} reference(s)** en stock sans mouvement depuis {mois_inactif} mois")
                    display_cols_p = ["categorie", "reference", "marque", "modele", "stock", "dernier_mouvement"]
                    display_cols_p = [c for c in display_cols_p if c in inactives.columns]
                    st.dataframe(inactives[display_cols_p], use_container_width=True, height=300)
            else:
                st.info("Aucun historique de mouvement disponible.")
        except Exception:
            st.info("Table de mouvements non disponible.")


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
            <h3 style='margin:0 0 0.5rem 0;'>📎 Mode d'emploi</h3>
            <ol style='margin:0.5rem 0 0 1.5rem; color:#374151; line-height:1.8;'>
                <li><strong>Etape 1</strong> : Importer votre catalogue prix Excel (doit contenir une colonne "Type moteur")</li>
                <li><strong>Etape 2</strong> : Importer le fichier tbl_MOTEURS.xlsx pour faire le lien entre vos types moteurs et les codes moteurs en base</li>
                <li><strong>Etape 3</strong> : Ajuster les curseurs de marge ci-dessus selon votre strategie</li>
                <li><strong>Etape 4</strong> : Consulter les prix d'achat proposes et telecharger le CSV</li>
            </ol>
            <p style='margin:0.5rem 0 0 0; color:#6b7280; font-size:0.9rem;'>
                Le systeme calcule automatiquement un prix d'achat propose en fonction du prix de vente moyen sur 3 mois,
                de l'urgence (forte demande = on peut payer plus) et du surstock (trop de stock = on baisse le prix).
            </p>
        </div>
        """
    )

    file_cat = st.file_uploader("Etape 1 - Catalogue prix (fichier Excel avec colonne 'Type moteur')", type=["xlsx"], key="maj_prix_cat")
    file_mot = st.file_uploader("Etape 2 - tbl MOTEURS.xlsx (pour le mapping type moteur -> code moteur)", type=["xlsx"], key="maj_prix_mot")

    if file_cat is None:
        st.info("Importez votre catalogue prix Excel pour commencer. Ce fichier doit contenir au minimum une colonne 'Type moteur'.")
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


def render_admin_users():
    if st.session_state.get("user_role") != "super_admin":
        st.error("Accès réservé aux super administrateurs.")
        return

    if st.button("⬅ Retour à l'accueil", use_container_width=False):
        set_page("home")
        st.rerun()

    st.markdown("## 👥 Gestion des utilisateurs")

    users = sql_df("SELECT id, email, nom, role, actif, created_at, last_login FROM dms_users ORDER BY id")

    if not users.empty:
        st.dataframe(users, use_container_width=True, height=300)

    st.markdown("---")
    st.markdown("### Ajouter un utilisateur")

    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        new_email = st.text_input("Email", key="new_user_email", placeholder="email@exemple.com")
    with col2:
        new_nom = st.text_input("Nom", key="new_user_nom", placeholder="Jean Dupont")
    with col3:
        new_role = st.selectbox("Rôle", ["admin", "vhu", "super_admin"], key="new_user_role")
    with col4:
        new_pwd = st.text_input("Mot de passe", type="password", key="new_user_pwd")

    if st.button("Créer l'utilisateur", key="btn_create_user"):
        if not new_email or not new_pwd:
            st.error("Email et mot de passe requis.")
        else:
            import hashlib
            pwd_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
            try:
                exec_sql("""
                    INSERT INTO dms_users (email, password_hash, nom, role)
                    VALUES (:email, :pwd, :nom, :role)
                """, {"email": new_email.strip(), "pwd": pwd_hash, "nom": new_nom.strip(), "role": new_role})
                st.cache_data.clear()
                st.success(f"Utilisateur {new_email} créé avec le rôle {new_role}.")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

    if not users.empty:
        st.markdown("---")
        st.markdown("### Modifier / Désactiver un utilisateur")
        sel_user = st.selectbox("Utilisateur", users["email"].tolist(), key="edit_user_sel")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Désactiver", key="btn_deactivate_user"):
                exec_sql("UPDATE dms_users SET actif = false WHERE email = :email", {"email": sel_user})
                st.cache_data.clear()
                st.success(f"{sel_user} désactivé.")
                st.rerun()
        with col_b:
            if st.button("Réactiver", key="btn_reactivate_user"):
                exec_sql("UPDATE dms_users SET actif = true WHERE email = :email", {"email": sel_user})
                st.cache_data.clear()
                st.success(f"{sel_user} réactivé.")
                st.rerun()

        st.markdown("#### Changer le mot de passe")
        new_pwd_change = st.text_input("Nouveau mot de passe", type="password", key="change_user_pwd")
        if st.button("Changer le mot de passe", key="btn_change_pwd"):
            if new_pwd_change:
                import hashlib
                pwd_hash = hashlib.sha256(new_pwd_change.encode()).hexdigest()
                exec_sql("UPDATE dms_users SET password_hash = :pwd WHERE email = :email", {"email": sel_user, "pwd": pwd_hash})
                st.success(f"Mot de passe de {sel_user} mis à jour.")


# =========================
# INIT DB (PERF) - run once
# =========================
@st.cache_resource(show_spinner=False)
def init_db_once() -> bool:
    # Tout ce qui était relancé à chaque rerun passe ici.
    assert_db_ready()
    ensure_stock_views()
    ensure_breaker_tables()
    ensure_users_table()
    return True


# =========================
# MAIN
# =========================
def main():
    st.set_page_config(page_title="Multirex Auto DMS", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")
    inject_custom_css()

    if not check_password():
        st.stop()

    # ✅ perf: init DB une seule fois
    init_db_once()

    if st.session_state.get("mode") == "casse":
        render_casse()
        return

    with st.sidebar:
        md_html("<h2 style='text-align: center; margin-bottom: 2rem;'>MULTIREX AUTO</h2>")
        user_nom = st.session_state.get("user_nom", "")
        user_role = st.session_state.get("user_role", "admin")
        role_label = {"super_admin": "Super Admin", "admin": "Admin", "vhu": "VHU"}.get(user_role, user_role)
        md_html(f"<p style='text-align:center;font-size:0.85rem;opacity:0.9;margin:0;'>{user_nom or ''} ({role_label})</p>")
        st.divider()
        logout_button()

    page = get_page()

    if page != "home":
        if st.sidebar.button("🏠 Accueil", use_container_width=True):
            set_page("home")
            st.rerun()

    st.sidebar.markdown("**Commercial**")
    sidebar_pages_1 = {
        "📈 Ventes": "ventes",
        "🎯 Besoins": "besoins",
        "📊 Analyse": "analyse",
        "💶 Mise à jour prix": "mise_a_jour_prix",
    }
    for label, pg in sidebar_pages_1.items():
        if st.sidebar.button(label, use_container_width=True, key=f"sb_{pg}"):
            set_page(pg)
            st.rerun()

    st.sidebar.markdown("**Gestion interne**")
    sidebar_pages_2 = {
        "📥 Receptions": "receptions",
        "🔍 Moteurs": "identification_moteurs",
        "⚙️ Boites": "identification_boites",
        "📋 Reservations": "reservations",
        "📜 Historique": "historique",
    }
    for label, pg in sidebar_pages_2.items():
        if st.sidebar.button(label, use_container_width=True, key=f"sb_{pg}"):
            set_page(pg)
            st.rerun()

    st.sidebar.markdown("**Outils**")
    sidebar_pages_3 = {
        "🔩 Pieces Detachees": "pieces_detachees",
        "🛠️ Centres VHU": "casse",
    }
    for label, pg in sidebar_pages_3.items():
        if st.sidebar.button(label, use_container_width=True, key=f"sb_{pg}"):
            set_page(pg)
            st.rerun()

    if st.session_state.get("user_role") == "super_admin":
        st.sidebar.markdown("**Administration**")
        if st.sidebar.button("👥 Utilisateurs", use_container_width=True, key="sb_admin_users"):
            set_page("admin_users")
            st.rerun()

    md_html(
        """
        <div style='background: white; padding: 2rem; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
            <h1 style='margin: 0; font-size: 2.5rem;'>Multirex Auto DMS</h1>
            <p style='color: #6b7280; margin: 0.5rem 0 0 0; font-size: 1.1rem;'>Système de gestion intelligent</p>
        </div>
        """
    )

    if page == "home":
        # --- Configurable KPIs ---
        with st.expander("Configurer les indicateurs", expanded=False):
            available = list(KPI_CATALOG.keys())
            labels = [f"{KPI_CATALOG[k]['icon']} {KPI_CATALOG[k]['label']}" for k in available]
            default_idx = [available.index(k) for k in DEFAULT_KPIS if k in available]
            selected_labels = st.multiselect(
                "Choisissez les indicateurs a afficher",
                labels,
                default=[labels[i] for i in default_idx],
                key="kpi_selector",
            )
            selected_keys = [available[labels.index(l)] for l in selected_labels if l in labels]

        if not selected_keys:
            selected_keys = DEFAULT_KPIS

        kpis_data = get_all_dashboard_kpis()

        # Tendance ventes
        delta_ventes = kpis_data["ventes_mois"] - kpis_data["ventes_mois_prec"]
        delta_ca = kpis_data["ca_mois"] - kpis_data["ca_mois_prec"]

        # Display KPIs in rows of 4
        for row_start in range(0, len(selected_keys), 4):
            row_keys = selected_keys[row_start:row_start + 4]
            cols = st.columns(len(row_keys))
            for col, key in zip(cols, row_keys):
                with col:
                    meta = KPI_CATALOG[key]
                    render_kpi_card(key, kpis_data.get(key, 0), meta)

        # Show trend indicators
        if "ventes_mois" in selected_keys or "ca_mois" in selected_keys:
            trend_sign_v = "+" if delta_ventes >= 0 else ""
            trend_sign_c = "+" if delta_ca >= 0 else ""
            trend_color_v = "#10b981" if delta_ventes >= 0 else "#ef4444"
            trend_color_c = "#10b981" if delta_ca >= 0 else "#ef4444"
            md_html(f"""
            <div style='background: rgba(255,255,255,0.9); border-radius:12px; padding:0.8rem 1.5rem; margin-top:0.5rem; display:flex; gap:2rem; flex-wrap:wrap;'>
                <span style='color:#6b7280; font-size:0.85rem;'>Tendance vs mois precedent :</span>
                <span style='color:{trend_color_v}; font-weight:600; font-size:0.85rem;'>{trend_sign_v}{delta_ventes} ventes</span>
                <span style='color:{trend_color_c}; font-weight:600; font-size:0.85rem;'>{trend_sign_c}{delta_ca:,.0f} EUR CA</span>
            </div>
            """)

        md_html("<br>")

    page_map = {
        "home": render_home,
        "ventes": render_ventes,
        "besoins": render_besoins,
        "analyse": render_analyse,
        "casse": render_casse,
        "mise_a_jour_prix": render_mise_a_jour_prix,
        "pieces_detachees": render_pieces_detachees,
        "receptions": render_receptions,
        "identification_moteurs": render_identification_moteurs,
        "identification_boites": render_identification_boites,
        "reservations": render_reservations,
        "historique": render_historique,
        "admin_users": render_admin_users,
    }

    renderer = page_map.get(page)
    if renderer:
        renderer()
    else:
        set_page("home")
        st.rerun()


if __name__ == "__main__":
    main()
