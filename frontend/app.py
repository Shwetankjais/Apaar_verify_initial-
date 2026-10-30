import os
import sys
import io
import datetime
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Ensure frontend can import api_client and translations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import ApiClient
from translations import t

st.set_page_config(
    page_title="APAAR Verify — Sutrāyukti",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None
if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = None
if "current_nav" not in st.session_state:
    st.session_state["current_nav"] = "nav_home"

lang = st.session_state["lang"]
client = ApiClient(token=st.session_state["auth_token"])

# Robust Backend Health Check (Scoped to client.base_url: 127.0.0.1:8001)
def check_engine_health():
    try:
        h = client.get_health()
        return h.get("status") == "healthy"
    except Exception:
        return False

api_online = check_engine_health()

# ---------------------------------------------------------------------------
# CUSTOM GOVERNMENT PALETTE: SAGE GREEN, CONCRETE GREY & BURNT AMBER
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');
    
    html {
        font-size: 15px;
    }
    
    .stApp {
        font-family: 'Plus Jakarta Sans', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #202622;
        background-color: #F6F8F6;
    }
    
    /* Ensure icon fonts, SVG symbols and Streamlit expanders are NOT mangled by font inheritance */
    [data-testid="stIcon"], [data-testid="stExpander"] svg, [data-testid="stExpanderToggleIcon"], [class*="material-icons"] {
        font-family: inherit !important;
    }
    
    [data-testid="stExpander"] {
        border: 1px solid #CBD5CE !important;
        border-radius: 8px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 2px rgba(32, 38, 34, 0.03) !important;
    }
    
    [data-testid="stExpander"] summary {
        font-size: 0.86rem !important;
        font-weight: 600 !important;
        color: #202622 !important;
        padding: 8px 12px !important;
    }

    /* Top Utility Accessibility Bar */
    .gov-utility-bar {
        background: #202622;
        border-bottom: 2px solid #BF531D;
        border-radius: 8px;
        padding: 6px 14px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #E2E8E4;
        font-size: 0.78rem;
    }
    
    /* Heritage Tricolour Stripe (Burnt Amber, Concrete White, Sage Green) */
    .tricolour-stripe {
        height: 4px;
        background: linear-gradient(90deg, #BF531D 0%, #BF531D 33%, #E5EAE7 33%, #E5EAE7 66%, #4E705B 66%, #4E705B 100%);
        border-radius: 2px;
        margin-bottom: 16px;
    }
    
    /* Brand Header Box */
    .brand-header-box {
        background: linear-gradient(135deg, #1C231F 0%, #2A362E 100%);
        border: 1px solid #3A473E;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 22px;
        color: #F4F7F5;
        box-shadow: 0 2px 6px rgba(28, 35, 31, 0.08);
    }
    .brand-logo-icon {
        background: #151A17;
        color: #DC6B32;
        border: 2px solid #BF531D;
        border-radius: 10px;
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.6rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    
    /* Badges in Theme Colors */
    .badge-sage {
        background-color: #E6EFE9;
        color: #2D4C38;
        border: 1px solid #B4CEBC;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-amber {
        background-color: #FDF1EA;
        color: #9E4314;
        border: 1px solid #F0C4AC;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-concrete {
        background-color: #ECEFEA;
        color: #38423C;
        border: 1px solid #CBD4CD;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Citizen Hero Card */
    .hero-banner {
        background: linear-gradient(135deg, #202723 0%, #2B3830 100%);
        border-left: 4px solid #BF531D;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 20px;
        color: #FFFFFF;
        box-shadow: 0 2px 8px rgba(32, 39, 35, 0.06);
    }
    .hero-title {
        color: #FFFFFF !important;
        font-size: 1.42rem !important;
        font-weight: 700 !important;
        margin: 4px 0 !important;
        line-height: 1.25;
    }
    .hero-subtitle {
        color: #D3DFD7 !important;
        font-size: 0.88rem !important;
        line-height: 1.45;
        margin: 0;
    }
    
    /* Equal Spacing Card Elements */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 10px !important;
        border: 1px solid #D6E0D8 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(32, 38, 34, 0.04) !important;
    }
    .card-icon {
        width: 38px;
        height: 38px;
        border-radius: 8px;
        background: #E6EFE9;
        color: #2D4C38;
        border: 1px solid #B4CEBC;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 8px;
    }
    .card-title {
        font-size: 0.96rem;
        font-weight: 700;
        color: #1F2622;
        margin: 0 0 4px 0;
    }
    .card-desc {
        font-size: 0.82rem;
        color: #525E56;
        line-height: 1.4;
        min-height: 42px;
        margin-bottom: 8px;
    }
    
    /* Metrics Row */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #D5DDD7;
        border-top: 3px solid #4E705B;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(32, 42, 35, 0.05);
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1F2522;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.76rem;
        font-weight: 600;
        color: #556259;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    
    /* Timeline */
    .timeline-item {
        border-left: 3px solid #4E705B;
        padding-left: 18px;
        margin-bottom: 22px;
        position: relative;
    }
    .timeline-bullet {
        position: absolute;
        left: -8px;
        top: 2px;
        width: 13px;
        height: 13px;
        border-radius: 50%;
        background-color: #BF531D;
        border: 2px solid #FFFFFF;
    }
    
    /* Global Primary Button: Burnt Amber */
    .stButton > button[kind="primary"] {
        background-color: #BF531D !important;
        border-color: #9E4314 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #DC6B32 !important;
        border-color: #BF531D !important;
    }
    
    /* Global Secondary Button: Sage Concrete */
    .stButton > button:not([kind="primary"]) {
        background-color: #E8EDE9 !important;
        border-color: #CBD5CE !important;
        color: #26332B !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background-color: #D9E2DC !important;
        border-color: #4E705B !important;
        color: #18231C !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOP UTILITY BAR (Bilingual & Government Identity)
# ---------------------------------------------------------------------------
col_util_left, col_util_right = st.columns([7, 3])
with col_util_left:
    st.markdown(f"""
    <div style="font-size:0.8rem; color:#4E5A52; display:flex; align-items:center; gap:12px; padding:6px 0;">
        <span>🇮🇳 <strong>भारत सरकार</strong> | Government of India</span>
        <span>•</span>
        <span><strong>{t('gov_portal_header', lang)}</strong></span>
    </div>
    """, unsafe_allow_html=True)

with col_util_right:
    c_skip, c_lang = st.columns([1.2, 1.8])
    with c_skip:
        st.markdown(f"<span style='font-size:0.75rem; color:#6B7870; line-height:32px;'>{t('skip_to_content', lang)}</span>", unsafe_allow_html=True)
    with c_lang:
        lang_choice = st.radio(
            "Lang",
            ["English", "हिन्दी"],
            index=0 if lang == "en" else 1,
            horizontal=True,
            label_visibility="collapsed"
        )
        new_lang = "hi" if lang_choice == "हिन्दी" else "en"
        if new_lang != st.session_state["lang"]:
            st.session_state["lang"] = new_lang
            st.rerun()

# ---------------------------------------------------------------------------
# TRICOLOUR ACCENT STRIPE
# ---------------------------------------------------------------------------
st.markdown('<div class="tricolour-stripe"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# MAIN BRAND BANNER & IDENTITY
# ---------------------------------------------------------------------------
col_brand_l, col_brand_r = st.columns([7, 3])
with col_brand_l:
    st.markdown(f"""
    <div class="brand-header-box">
        <div style="display:flex; align-items:center; gap:16px;">
            <div class="brand-logo-icon">अ</div>
            <div>
                <div style="font-size:1.45rem; font-weight:700; color:#F4F7F5; line-height:1.2;">
                    {t('app_title', lang)} <span style="font-size:0.95rem; font-weight:400; color:#B4C2B9;">{t('brand_org', lang)}</span>
                </div>
                <div style="font-size:0.9rem; font-weight:600; color:#DC6B32; margin-top:3px;">
                    “{t('tagline_primary', lang)}” • <span style="font-size:0.8rem; font-weight:400; color:#CBD5CE;">{t('tagline_secondary', lang)}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_brand_r:
    user = st.session_state["auth_user"]
    if user:
        st.markdown(f"""
        <div style="text-align:right; border-left:2px solid #CBD5CE; padding-left:16px; margin-top:8px;">
            <div style="font-size:0.75rem; color:#5E6B63;">{t('signed_in_as', lang)}:</div>
            <div style="font-size:0.95rem; font-weight:700; color:#202622;">{user.get('full_name')}</div>
            <div style="margin-top:4px;">
                <span class="badge-sage">{user.get('role').replace('_', ' ').title()}</span>
                {f'<span class="badge-amber" style="margin-left:4px;">{user.get("institution_id")}</span>' if user.get("institution_id") else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t("sign_out", lang), type="secondary", use_container_width=False):
            st.session_state["auth_user"] = None
            st.session_state["auth_token"] = None
            st.session_state["current_nav"] = "nav_home"
            client.set_token(None)
            st.rerun()
    else:
        st.markdown(f"""
        <div style="text-align:right; margin-top:12px;">
            <span class="badge-amber">DEMO / SYNTHETIC DATA ENVIRONMENT</span>
            <div style="font-size:0.75rem; color:#5A665E; margin-top:4px;">Aligned with AICTE PS-26263 • Public Access</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION & ROLE PERMISSIONS
# ---------------------------------------------------------------------------
st.sidebar.markdown(f"### 🇮🇳 {t('app_title', lang)}")
st.sidebar.caption("SIH 2026 • Problem Statement PS-26263")

academic_year = st.sidebar.selectbox("Academic Session", ["2025-2026", "2024-2025"])

user = st.session_state["auth_user"]
current_role = user.get("role") if user else "public"
current_institution_id = user.get("institution_id") if user else None

nav_options = [
    ("nav_home", f"🏠 {t('nav_home', lang)}"),
    ("nav_doc_submit", f"📤 {t('nav_doc_submit', lang)}"),
    ("nav_doc_track", f"🔍 {t('nav_doc_track', lang)}"),
    ("nav_verification", f"🛡️ {t('nav_verification', lang)}"),
    ("nav_student_journey", f"🧭 {t('nav_student_journey', lang)}"),
    ("nav_edupath", f"🎓 {t('nav_edupath', lang)}"),
    ("nav_regulatory", f"📖 {t('nav_regulatory', lang)}")
]

if current_role == "aicte_admin":
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🏛️ AICTE Regulator Console**")
    nav_options.append(("nav_dashboard", f"📊 {t('nav_dashboard', lang)}"))
    nav_options.append(("nav_exceptions", f"⚠️ {t('nav_exceptions', lang)}"))
    nav_options.append(("nav_doc_review", f"📋 {t('nav_doc_review', lang)}"))
    nav_options.append(("nav_audit", f"📜 {t('nav_audit', lang)}"))

elif current_role in ["institution_admin", "institution_approver", "institution_officer"]:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**🏫 Institution Portal ({current_institution_id})**")
    nav_options.append(("nav_institution", f"📥 {t('nav_institution', lang)}"))
    nav_options.append(("nav_doc_review", f"📋 {t('nav_doc_review', lang)}"))
    nav_options.append(("nav_exceptions", f"⚠️ {t('nav_exceptions', lang)}"))
    nav_options.append(("nav_students", f"👥 {t('nav_students', lang)}"))

elif current_role == "auditor":
    st.sidebar.markdown("---")
    st.sidebar.markdown("**⚖️ CAG / Statutory Audit Desk**")
    nav_options.append(("nav_audit", f"📜 {t('nav_audit', lang)}"))
    nav_options.append(("nav_dashboard", f"📊 {t('nav_dashboard', lang)}"))

nav_keys = [k for k, _ in nav_options]
nav_labels = [label for _, label in nav_options]

curr_idx = 0
if st.session_state["current_nav"] in nav_keys:
    curr_idx = nav_keys.index(st.session_state["current_nav"])

chosen_nav_label = st.sidebar.radio(
    "Navigation",
    nav_labels,
    index=curr_idx,
    label_visibility="collapsed"
)
st.session_state["current_nav"] = nav_keys[nav_labels.index(chosen_nav_label)]
selected_section = st.session_state["current_nav"]

# Core Infrastructure Status Pill in Sage Green / Burnt Amber
st.sidebar.markdown("---")
st.sidebar.markdown("**Core Infrastructure Status:**")
clean_base = client.base_url.replace('http://', '').replace('https://', '')
if api_online:
    st.sidebar.markdown(f"""
    <div style="background:#E6EFE9; border:1px solid #AECBB7; border-radius:8px; padding:8px 12px;">
        <span style="color:#2B4D36; font-weight:700; font-size:0.82rem;">● FastAPI REST Engine: Online</span>
        <div style="font-size:0.72rem; color:#4E6054; margin-top:2px;">{clean_base} • Database Connected</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"""
    <div style="background:#FDF1EA; border:1px solid #ECC1AC; border-radius:8px; padding:8px 12px;">
        <span style="color:#9E4314; font-weight:700; font-size:0.82rem;">○ FastAPI Offline ({clean_base})</span>
        <div style="font-size:0.72rem; color:#854019; margin-top:2px;">Check uvicorn service on port 8001</div>
    </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("🔄 Check Engine Status", key="btn_check_engine", use_container_width=True):
        st.rerun()

st.sidebar.markdown(f"""
<div style="font-size:0.75rem; color:#5D6B63; margin-top:16px; line-height:1.4;">
    <strong>{t('app_title', lang)} {t('brand_org', lang)}</strong><br/>
    AICTE-Approved Technical Institutions Platform<br/>
    <em>Non-Official Prototype · Synthetic Data</em>
</div>
""", unsafe_allow_html=True)

# Sidebar Login Drawer
if not user:
    with st.sidebar.expander("Institutional / Staff Sign In", expanded=False):
        login_email = st.text_input("Official Email", placeholder="officer@mit-demo.ac.in")
        login_password = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button(t("sign_in", lang), type="primary", use_container_width=True):
            res = client.login(login_email, login_password)
            if res["status_code"] == 200:
                token = res["data"]["access_token"]
                st.session_state["auth_token"] = token
                client.set_token(token)
                me = client.get_me(token)
                if me["status_code"] == 200:
                    st.session_state["auth_user"] = me["data"]
                    st.success(f"Welcome, {me['data']['full_name']}!")
                    st.rerun()
            else:
                st.error("Invalid credentials. Try demo presets below.")

        st.markdown("<div style='font-size:0.75rem; font-weight:600; color:#4E5A52; margin:8px 0;'>Quick Evaluator Demo Logins:</div>", unsafe_allow_html=True)
        q1, q2 = st.columns(2)
        if q1.button("🏛️ AICTE Admin", use_container_width=True):
            res = client.login("admin@aicte.gov.in", "DemoPass123!")
            if res["status_code"] == 200:
                st.session_state["auth_token"] = res["data"]["access_token"]
                st.session_state["auth_user"] = client.get_me(res["data"]["access_token"])["data"]
                st.rerun()
        if q2.button("🏫 MIT Officer", use_container_width=True):
            res = client.login("officer@mit-demo.ac.in", "DemoPass123!")
            if res["status_code"] == 200:
                st.session_state["auth_token"] = res["data"]["access_token"]
                st.session_state["auth_user"] = client.get_me(res["data"]["access_token"])["data"]
                st.rerun()
        q3, q4 = st.columns(2)
        if q3.button("📋 MIT Approver", use_container_width=True):
            res = client.login("approver@mit-demo.ac.in", "DemoPass123!")
            if res["status_code"] == 200:
                st.session_state["auth_token"] = res["data"]["access_token"]
                st.session_state["auth_user"] = client.get_me(res["data"]["access_token"])["data"]
                st.rerun()
        if q4.button("🎓 Student 010", use_container_width=True):
            res = client.login("student@demo.ac.in", "DemoPass123!")
            if res["status_code"] == 200:
                st.session_state["auth_token"] = res["data"]["access_token"]
                st.session_state["auth_user"] = client.get_me(res["data"]["access_token"])["data"]
                st.rerun()

# Global Service Offline Warning Notice
if not api_online:
    st.markdown(f"""
    <div style="background:#FDF1EA; border-left:4px solid #BF531D; border-radius:8px; padding:12px 18px; margin-bottom:18px;">
        <strong style="color:#9E4314; font-size:0.92rem;">⚠️ FastAPI Backend Engine Initializing or Offline ({client.base_url})</strong>
        <p style="color:#525E56; font-size:0.82rem; margin:3px 0 0 0;">
            The frontend is attempting to connect to the backend on <strong>{client.base_url}</strong>. Ensure uvicorn is running: <code>python -m uvicorn backend.app.main:app --port 8001</code>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ===========================================================================
# VIEW 1: CITIZEN SERVICES HOME (Equal Spacing & Sizing)
# ===========================================================================
if selected_section == "nav_home":
    st.markdown(f"""
    <div class="hero-banner">
        <span class="badge-amber" style="margin-bottom:10px;">{t('synthetic_banner', lang)[:52]}...</span>
        <h1 class="hero-title">{t('tagline_primary', lang)}</h1>
        <p class="hero-subtitle">
            {t('tagline_secondary', lang)}
            A unified digital governance ecosystem empowering students, technical institutions, and regulators under the National Education Policy (NEP 2020).
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 6 Interactive Citizen Service Cards (Equal Sizing & Spacing)
    st.markdown(f"### 📌 {t('nav_home', lang)} — Quick Portals")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown(f"""
            <div class="card-icon">📤</div>
            <div class="card-title">{t('card_submit_doc_title', lang)}</div>
            <div class="card-desc">{t('card_submit_doc_desc', lang)}</div>
            """, unsafe_allow_html=True)
            if st.button(f"Go to {t('card_submit_doc_title', lang)} →", key="btn_h_sub", use_container_width=True):
                st.session_state["current_nav"] = "nav_doc_submit"
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown(f"""
            <div class="card-icon">🔍</div>
            <div class="card-title">{t('card_track_status_title', lang)}</div>
            <div class="card-desc">{t('card_track_status_desc', lang)}</div>
            """, unsafe_allow_html=True)
            if st.button(f"Go to {t('card_track_status_title', lang)} →", key="btn_h_track", use_container_width=True):
                st.session_state["current_nav"] = "nav_doc_track"
                st.rerun()

    with col3:
        with st.container(border=True):
            st.markdown(f"""
            <div class="card-icon">🛡️</div>
            <div class="card-title">{t('card_verify_qr_title', lang)}</div>
            <div class="card-desc">{t('card_verify_qr_desc', lang)}</div>
            """, unsafe_allow_html=True)
            if st.button(f"Go to {t('card_verify_qr_title', lang)} →", key="btn_h_qr", use_container_width=True):
                st.session_state["current_nav"] = "nav_verification"
                st.rerun()

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    col4, col5, col6 = st.columns(3)

    with col4:
        with st.container(border=True):
            st.markdown(f"""
            <div class="card-icon">🧭</div>
            <div class="card-title">{t('nav_student_journey', lang)}</div>
            <div class="card-desc">Inspect verified academic progression, NCrF credit milestones, and institutional transfers.</div>
            """, unsafe_allow_html=True)
            if st.button(f"View Academic Journey →", key="btn_h_journey", use_container_width=True):
                st.session_state["current_nav"] = "nav_student_journey"
                st.rerun()

    with col5:
        with st.container(border=True):
            st.markdown(f"""
            <div class="card-icon">🎓</div>
            <div class="card-title">{t('card_edupath_title', lang)}</div>
            <div class="card-desc">{t('card_edupath_desc', lang)}</div>
            """, unsafe_allow_html=True)
            if st.button(f"Open EduPath Advisory →", key="btn_h_edupath", use_container_width=True):
                st.session_state["current_nav"] = "nav_edupath"
                st.rerun()

    with col6:
        with st.container(border=True):
            st.markdown(f"""
            <div class="card-icon">📖</div>
            <div class="card-title">{t('card_regulatory_title', lang)}</div>
            <div class="card-desc">{t('card_regulatory_desc', lang)}</div>
            """, unsafe_allow_html=True)
            if st.button(f"Consult AICTE Assistant →", key="btn_h_reg", use_container_width=True):
                st.session_state["current_nav"] = "nav_regulatory"
                st.rerun()

    # Public FAQ Accordion
    st.markdown("---")
    st.markdown("#### 💬 Frequently Asked Questions (FAQ)")
    with st.expander("What is APAAR ID and how does it safeguard student privacy?"):
        st.write("""
        APAAR (Automated Permanent Academic Account Registry) is a unique lifetime academic identifier created under the National Education Policy (NEP 2020).
        In APAAR Verify by Sutrāyukti, raw identifiers are never exposed or indexed directly. The system generates a cryptographically keyed HMAC lookup token and displays only masked tokens (`DEMO-APAAR-***1`). No Aadhaar numbers or biometrics are collected.
        """)
    with st.expander("How does the document submission and verification workflow operate?"):
        st.write("""
        Students upload authentic academic credentials (PDF, JPEG, PNG). Each upload is defensively verified via binary magic-byte signatures and stored in private filesystem storage. The institution's nodal officer and verification approver inspect the document, raising deficiencies if necessary or approving the record into the permanent ledger.
        """)
    with st.expander("How are AICTE approved intake quotas strictly enforced?"):
        st.write("""
        Rule engine checks (V005) match incoming enrolments against approved regular and supernumerary caps per course in the AICTE Approval database. Any attempt to over-admit regular students triggers a hard validation stop prior to database commit.
        """)


# ===========================================================================
# VIEW 2: DIRECT ACADEMIC DOCUMENT SUBMISSION WORKFLOW
# ===========================================================================
elif selected_section == "nav_doc_submit":
    st.markdown(f"### 📤 {t('doc_upload_title', lang)}")
    st.caption(t('doc_upload_subtitle', lang))

    # Pre-fill for demonstration ease
    default_name = user.get("full_name") if user and user.get("role") == "student" else "Student Demo 010"
    default_apaar = "DEMO-APAAR-0010"

    sub_c1, sub_c2 = st.columns(2)
    with sub_c1:
        s_name = st.text_input(t("student_name_label", lang), value=default_name)
        s_apaar = st.text_input(t("apaar_id_label", lang), value=default_apaar)
        s_inst = st.selectbox(
            t("institution_select_label", lang),
            ["DEMO001", "DEMO002", "DEMO003"],
            format_func=lambda x: f"{x} — " + (
                "Mysuru Institute of Tech" if x == "DEMO001" else (
                    "Deccan Engineering College" if x == "DEMO002" else "Coastal Technical Inst"
                )
            )
        )
    with sub_c2:
        s_course = st.selectbox(t("course_code_label", lang), ["CSE", "ECE", "MECH"])
        s_year = st.selectbox(t("academic_year_label", lang), ["2025-2026", "2024-2025"])
        s_doc_type = st.selectbox(
            t("document_type_label", lang),
            [
                "CLASS_12_MARKSHEET",
                "TRANSFER_CERTIFICATE",
                "DEGREE_DIPLOMA",
                "IDENTITY_PROOF",
                "CATEGORY_CERTIFICATE"
            ],
            format_func=lambda x: {
                "CLASS_12_MARKSHEET": t("type_class_12", lang),
                "TRANSFER_CERTIFICATE": t("type_tc", lang),
                "DEGREE_DIPLOMA": t("type_degree", lang),
                "IDENTITY_PROOF": t("type_identity", lang),
                "CATEGORY_CERTIFICATE": t("type_caste", lang)
            }.get(x, x)
        )

    st.markdown("---")
    st.markdown("#### 📎 Attach Digital Credential")
    
    # Preset quick-load buttons for testing
    st.markdown("💡 **Evaluator Test Presets:**")
    tp1, tp2 = st.columns([2, 4])
    if tp1.button("📄 Generate Sample Valid PDF Document", use_container_width=True):
        st.session_state["doc_test_bytes"] = b"%PDF-1.4\n1 0 obj\n<< /Title (Student Transcript) >>\nendobj\ntrailer\n<<>>\n%%EOF"
        st.session_state["doc_test_name"] = "academic_transcript_official.pdf"
        st.toast("Created valid in-memory PDF with '%PDF' magic header!")

    uploaded_doc = st.file_uploader(t("file_upload_label", lang), type=["pdf", "jpeg", "jpg", "png"])
    
    active_bytes = None
    active_filename = None
    if uploaded_doc is not None:
        active_bytes = uploaded_doc.read()
        active_filename = uploaded_doc.name
    elif "doc_test_bytes" in st.session_state:
        active_bytes = st.session_state["doc_test_bytes"]
        active_filename = st.session_state["doc_test_name"]

    if active_bytes and active_filename:
        st.info(f"📁 Selected: `{active_filename}` ({len(active_bytes)} bytes)")

        if st.button(t("btn_submit_document", lang), type="primary"):
            with st.spinner("Inspecting binary magic bytes, generating SHA-256 hash, and lodging in private storage..."):
                res = client.submit_document(
                    student_name=s_name,
                    student_apaar=s_apaar,
                    institution_id=s_inst,
                    course_code=s_course,
                    academic_year=s_year,
                    document_type=s_doc_type,
                    file_bytes=active_bytes,
                    filename=active_filename,
                    role=current_role,
                    token=st.session_state["auth_token"]
                )

                if res["status_code"] in [200, 201]:
                    doc_data = res["data"]
                    st.success(f"✓ {t('operation_success', lang)}")
                    st.markdown(f"""
                    <div style="background:#EBF2EE; border:1px solid #B8CFC1; border-radius:10px; padding:16px 20px; margin:16px 0;">
                        <h4 style="color:#264835; margin:0 0 6px 0;">Application Lodged Successfully</h4>
                        <div><strong>Application No:</strong> <code>{doc_data.get('application_no')}</code></div>
                        <div><strong>Status:</strong> <span class="badge-sage">{doc_data.get('status')}</span></div>
                        <div><strong>Cryptographic SHA-256 Hash:</strong> <code>{doc_data.get('file_hash_sha256')}</code></div>
                        <div style="font-size:0.8rem; color:#4A6252; margin-top:6px;">Please note your application reference to track verification status.</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"Upload rejected: {res.get('data', {}).get('detail', 'Unknown error')}")


# ===========================================================================
# VIEW 3: APPLICATION STATUS TRACKER
# ===========================================================================
elif selected_section == "nav_doc_track":
    st.markdown(f"### 🔍 {t('nav_doc_track', lang)}")
    st.caption("Track review milestones, deficiency requisitions, and approval certificates.")

    t_col1, t_col2 = st.columns([3, 1])
    search_apaar = t_col1.text_input("Enter Synthetic APAAR ID to Query Submissions", value="DEMO-APAAR-0010")

    if search_apaar.strip():
        docs = client.get_documents(
            role=current_role,
            student_apaar=search_apaar.strip(),
            token=st.session_state["auth_token"]
        )
        if docs:
            st.write(f"Found **{len(docs)}** submitted applications for `{search_apaar}`:")
            for d in docs:
                status_color = {
                    "SUBMITTED": "badge-concrete",
                    "UNDER_REVIEW": "badge-amber",
                    "DEFICIENCY_RAISED": "badge-amber",
                    "RESUBMITTED": "badge-amber",
                    "APPROVED": "badge-sage",
                    "REJECTED": "badge-amber"
                }.get(d["status"], "badge-concrete")

                with st.expander(f"📄 {d['application_no']} — {d['document_type']} | Status: {d['status']}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Student Name:** {d['student_name']}")
                        st.markdown(f"**Institution:** `{d['institution_id']}` | Course: `{d['course_code']}` ({d['academic_year']})")
                        st.markdown(f"**Filename:** `{d['original_filename']}` ({d['file_size_bytes']} bytes)")
                        st.markdown(f"**SHA-256 Digest:** <code>{d['file_hash_sha256']}</code>", unsafe_allow_html=True)
                        st.markdown(f"**Submitted At:** {d['created_at']}")
                        if d.get("deficiency_notes"):
                            st.error(f"⚠️ **Deficiency Requisition:** {d['deficiency_notes']}")
                        if d.get("reviewer_comments"):
                            st.info(f"📋 **Reviewer Feedback:** {d['reviewer_comments']} (Reviewed by `{d.get('reviewer_id')}`)")
                    with c2:
                        st.markdown(f"<span class='gov-badge {status_color}'>{d['status']}</span>", unsafe_allow_html=True)
                        if d["status"] == "DEFICIENCY_RAISED":
                            st.warning("Action Required: Please re-upload corrected document.")
        else:
            st.info("No applications found matching this APAAR ID.")


# ===========================================================================
# VIEW 4: INSTITUTIONAL DOCUMENT VERIFICATION DESK
# ===========================================================================
elif selected_section == "nav_doc_review":
    st.markdown(f"### 📋 {t('nav_doc_review', lang)}")
    st.caption("Scrutiny and verification desk for institutional approvers and AICTE administrative officers.")

    target_inst = current_institution_id or "DEMO001"
    docs = client.get_documents(
        role=current_role,
        institution_id=target_inst if current_role != "aicte_admin" else None,
        token=st.session_state["auth_token"]
    )

    if docs:
        st.write(f"Displaying **{len(docs)}** document submissions in queue:")
        for d in docs:
            with st.expander(f"📁 {d['application_no']} — {d['student_name']} ({d['student_apaar']}) | Status: {d['status']}"):
                col_d1, col_d2 = st.columns([2, 1])
                with col_d1:
                    st.markdown(f"**Document Type:** `{d['document_type']}`")
                    st.markdown(f"**Institution / Course:** `{d['institution_id']}` / `{d['course_code']}`")
                    st.markdown(f"**File:** `{d['original_filename']}` | SHA-256: `...{d['file_hash_sha256'][-16:]}`")
                    if d.get("deficiency_notes"):
                        st.error(f"Current Deficiency: {d['deficiency_notes']}")
                    if d.get("reviewer_comments"):
                        st.info(f"Notes: {d['reviewer_comments']}")

                with col_d2:
                    st.markdown(f"**Workflow Action:** Current: `<span class='badge-sage'>{d['status']}</span>`", unsafe_allow_html=True)
                    
                    # Available transitions
                    action_note = st.text_input("Reviewer Comments", key=f"notes_{d['id']}", placeholder="e.g. Scrutinized and verified against state quota.")
                    
                    if d["status"] in ["SUBMITTED", "RESUBMITTED"]:
                        if st.button("🔍 Begin Scrutiny (Under Review)", key=f"ur_{d['id']}", type="primary"):
                            res = client.transition_document(d["id"], "UNDER_REVIEW", action_note, role=current_role, token=st.session_state["auth_token"])
                            if res["status_code"] == 200:
                                st.success("Updated to UNDER_REVIEW")
                                st.rerun()

                    elif d["status"] == "UNDER_REVIEW":
                        b_app, b_def, b_rej = st.columns(3)
                        with b_app:
                            if st.button("✅ Approve", key=f"app_{d['id']}", type="primary"):
                                res = client.transition_document(d["id"], "APPROVED", action_note or "Verified authentic", role=current_role, token=st.session_state["auth_token"])
                                if res["status_code"] == 200:
                                    st.success("Document Approved!")
                                    st.rerun()
                        with b_def:
                            if st.button("⚠️ Deficiency", key=f"def_{d['id']}"):
                                if not action_note:
                                    st.error("Please explain deficiency in notes.")
                                else:
                                    res = client.transition_document(d["id"], "DEFICIENCY_RAISED", action_note, role=current_role, token=st.session_state["auth_token"])
                                    if res["status_code"] == 200:
                                        st.warning("Deficiency Raised")
                                        st.rerun()
                        with b_rej:
                            if st.button("❌ Reject", key=f"rej_{d['id']}"):
                                res = client.transition_document(d["id"], "REJECTED", action_note or "Rejected during scrutiny", role=current_role, token=st.session_state["auth_token"])
                                if res["status_code"] == 200:
                                    st.error("Document Rejected")
                                    st.rerun()
                    else:
                        st.info(f"Status is terminal or completed: {d['status']}")
    else:
        st.info("No documents pending in current queue.")


# ===========================================================================
# VIEW 5: SECURE VERIFICATION & QR CODE
# ===========================================================================
elif selected_section == "nav_verification":
    st.markdown(f"### 🛡️ {t('nav_verification', lang)}")
    st.caption("Cryptographic third-party verification of academic credentials with minimal PII disclosure.")

    v_col1, v_col2 = st.columns([1, 1])

    with v_col1:
        st.markdown("#### 1. Generate Verification Reference (Student / Officer)")
        students = client.get_students(role=current_role, institution_id=current_institution_id, token=st.session_state["auth_token"])
        if students:
            std_options = {f"{s['student_name']} ({s['display_apaar_id']})": s["id"] for s in students}
            chosen_std = st.selectbox("Student Master Record", list(std_options.keys()), key="v_std")
            purpose = st.selectbox("Authorized Purpose", [
                "EMPLOYMENT_BACKGROUND_CHECK",
                "HIGHER_EDUCATION_ADMISSION",
                "SCHOLARSHIP_VALIDATION",
                "REGULATORY_AUDIT"
            ])
            exp_hours = st.slider("Reference Expiry (Hours)", 1, 168, 72)

            if st.button("🔑 Generate Secure QR & Token", type="primary"):
                v_res = client.create_verification_ref(
                    student_id=std_options[chosen_std],
                    role=current_role,
                    purpose=purpose,
                    hours=exp_hours,
                    token=st.session_state["auth_token"]
                )
                st.session_state["active_vref"] = v_res
                st.success("Verification Reference Created Successfully!")

        if "active_vref" in st.session_state:
            vref = st.session_state["active_vref"]
            st.markdown(f"**Reference Code:** `{vref['reference_code']}`")
            st.markdown(f"**Expires At:** `{vref['expires_at']}`")
            if vref.get("qr_data_url"):
                st.image(vref["qr_data_url"], width=180, caption="Scan to Verify at Sutrāyukti Endpoint")

    with v_col2:
        st.markdown("#### 2. Verify Academic Reference (Public Verifier)")
        
        # Quick test scenario buttons
        st.markdown("💡 **Evaluator Test Scenarios:**")
        tc1, tc2, tc3 = st.columns(3)
        test_val = st.session_state.get("active_vref", {}).get("reference_code", "vref_demo_test")
        
        if tc1.button("Valid Token"):
            if "active_vref" in st.session_state:
                test_val = st.session_state["active_vref"]["reference_code"]
        if tc2.button("Forged Token"):
            test_val = "vref_tampered_forged_code_xyz"
        if tc3.button("Non-Existent"):
            test_val = "vref_000000000000"

        test_ref = st.text_input("Enter Verification Reference Code", value=test_val)
        
        if st.button("🔍 Check Credential Reference", type="primary"):
            with st.spinner("Validating HMAC signature, expiry, and revocation state..."):
                v_result = client.verify_reference(test_ref, role=current_role, token=st.session_state["auth_token"])
                st.session_state["verify_check_result"] = v_result

        if "verify_check_result" in st.session_state:
            res = st.session_state["verify_check_result"]
            if res.get("is_valid"):
                st.success(f"✓ Credential Verified! Status: {res.get('status')} (HMAC Signature Match)")
                st.markdown("##### Permitted Disclosure Fields (Minimal PII):")
                fields = res.get("permitted_fields", {})
                st.json(fields)
                st.caption(f"Cryptographic Signature: `{res.get('signature')[:24]}...`")

                if st.button("⛔ Revoke This Reference Code", key="btn_rev"):
                    client.revoke_reference(test_ref, "Revoked by institutional officer for demo", role=current_role, token=st.session_state["auth_token"])
                    st.warning("Reference revoked!")
                    st.rerun()
            else:
                st.error(f"❌ Verification Failed! Status: {res.get('status')}")
                st.write(f"**Reason:** {res.get('rejection_reason')}")


# ===========================================================================
# VIEW 6: VERIFIED ACADEMIC JOURNEY
# ===========================================================================
elif selected_section == "nav_student_journey":
    st.markdown(f"### 🧭 {t('nav_student_journey', lang)}")
    st.caption("Chronological, issuer-authenticated milestones tracking student academic progression from admission to qualification.")

    students = client.get_students(role=current_role, institution_id=current_institution_id, token=st.session_state["auth_token"])
    if students:
        std_options = {f"{s['student_name']} ({s['display_apaar_id']})": s["id"] for s in students}
        default_idx = 0
        for i, k in enumerate(std_options.keys()):
            if "010" in k:
                default_idx = i
                break

        selected_label = st.selectbox("Select Student to View Academic Timeline", list(std_options.keys()), index=default_idx)
        selected_student_id = std_options[selected_label]

        events = client.get_student_journey(selected_student_id, role=current_role, token=st.session_state["auth_token"])
        
        st.info("""
        **Regulatory Distinction on Academic Credits:**
        Under UGC/AICTE & National Credit Framework guidelines, credits are recorded under separate distinct lifecycle states:
        1. **Reported**: Submitted by institutional exam cell.
        2. **Validated**: Checked against course curriculum regulations.
        3. **Earned**: Formally awarded upon passing term assessments.
        4. **Accepted**: Recognized by a receiving institution upon migration/transfer.
        """)

        if events:
            st.markdown(f"#### Academic Journey Timeline for `{selected_label}`")
            for ev in events:
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-bullet"></div>
                    <div style="display:flex; justify-content:space-between;">
                        <h4 style="margin:0; color:#202622;">{ev['event_title']}</h4>
                        <span style="font-size:0.8rem; color:#5D6B63;">{ev['timestamp'][:10]}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#4E5A52; margin-top:4px;">
                        <strong>Issuer:</strong> {ev['issuer_name']} | <strong>Reference:</strong> <code>{ev['source_reference']}</code>
                    </div>
                    <div style="font-size:0.85rem; margin-top:6px;">
                        <span class="badge-sage">Status: {ev['credit_status']}</span>
                        <span style="margin-left:12px;"><strong>Credits Validated:</strong> {ev['credits_validated']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No academic events recorded yet for this student.")

        # Interactive form to submit new milestone
        st.markdown("---")
        with st.expander("➕ Append Milestone Event (Institutional Exam Branch)"):
            m_c1, m_c2 = st.columns(2)
            ev_title = m_c1.text_input("Milestone Title", value="Semester 2 Credits Validated")
            ev_term = m_c2.text_input("Academic Term", value="Semester 2 (Spring 2026)")
            credits_num = m_c1.number_input("Credits Validated", min_value=0.0, max_value=40.0, value=20.0, step=1.0)
            issuer = m_c2.text_input("Issuer Authority", value="Institution Examination Branch")

            if st.button("Submit Milestone Event", type="primary"):
                milestone_payload = {
                    "student_id": selected_student_id,
                    "institution_id": current_institution_id or "DEMO001",
                    "event_type": "SEMESTER_CREDITS",
                    "event_title": ev_title,
                    "term": ev_term,
                    "credits_reported": credits_num,
                    "credits_validated": credits_num,
                    "credit_status": "VALIDATED",
                    "issuer_name": issuer,
                    "source_reference": f"EXAM-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M')}"
                }
                client.add_academic_milestone(milestone_payload, role=current_role, token=st.session_state["auth_token"])
                st.success("New milestone event appended to student academic journey!")
                st.rerun()


# ===========================================================================
# VIEW 7: AICTE NATIONAL ANALYTICS & INTAKE GOVERNANCE
# ===========================================================================
elif selected_section == "nav_dashboard":
    st.markdown(f"### 📊 {t('nav_dashboard', lang)}")
    st.caption("Live database-backed aggregates across registered AICTE technical institutions.")

    try:
        summary = client.get_dashboard_summary(role=current_role, academic_year=academic_year, token=st.session_state["auth_token"])
        institutions_data = client.get_dashboard_institutions(role=current_role, academic_year=academic_year, token=st.session_state["auth_token"])
        
        # Metric Cards Row
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Active Enrolments</div>
                <div class="metric-val">{summary.get('total_active_enrolments', 0)}</div>
                <div style="font-size:0.75rem; color:#10B981; margin-top:4px;">Verified Active Records</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Approved Intake</div>
                <div class="metric-val">{summary.get('total_approved_intake', 0)}</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Reg: {summary.get('regular_capacity')} | Sup: {summary.get('supernumerary_capacity')}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            util = summary.get('intake_utilization_pct', 0.0)
            u_color = "#10B981" if util <= 100.0 else "#EF4444"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Intake Utilization</div>
                <div class="metric-val" style="color:{u_color};">{util}%</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Admissions ÷ Approved</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Open Exceptions</div>
                <div class="metric-val" style="color:#F59E0B;">{summary.get('open_exceptions', 0)}</div>
                <div style="font-size:0.75rem; color:#F59E0B; margin-top:4px;">Pending Human Review</div>
            </div>
            """, unsafe_allow_html=True)
        with c5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Batches Processed</div>
                <div class="metric-val">{summary.get('total_submissions', 0)}</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:4px;">Idempotent Commits</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

        # Filters and Charts
        f_c1, f_c2 = st.columns([1, 3])
        state_filter = f_c1.selectbox("Filter State", ["All", "Karnataka", "Maharashtra"])

        df_inst = pd.DataFrame(institutions_data)
        if state_filter != "All" and not df_inst.empty:
            df_inst = df_inst[df_inst["state"].str.lower() == state_filter.lower()]

        ch1, ch2 = st.columns([3, 2])
        with ch1:
            if not df_inst.empty:
                fig_bar = px.bar(
                    df_inst,
                    x="institution_code",
                    y=["active_enrolment", "approved_intake"],
                    barmode="group",
                    title="Intake Capacity vs. Actual Active Enrolment by Institution",
                    labels={"value": "Student Count", "institution_code": "Institution"},
                    color_discrete_map={"active_enrolment": "#4E705B", "approved_intake": "#A8B4AC"}
                )
                fig_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=320)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with ch2:
            if not df_inst.empty:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=summary.get("intake_utilization_pct", 0.0),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "National Seat Utilization (%)"},
                    gauge={
                        'axis': {'range': [0, 120]},
                        'bar': {'color': "#BF531D"},
                        'steps': [
                            {'range': [0, 80], 'color': "#ECEFEA"},
                            {'range': [80, 100], 'color': "#E6EFE9"},
                            {'range': [100, 120], 'color': "#FDF1EA"}
                        ],
                        'threshold': {
                            'line': {'color': "#BF531D", 'width': 3},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                fig_gauge.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=320)
                st.plotly_chart(fig_gauge, use_container_width=True)

        # Detailed Institution Roster & Export
        st.markdown("#### Registered Technical Institutions & Compliance Status")
        if not df_inst.empty:
            display_df = df_inst[[
                "institution_code", "institution_name", "state", "approved_intake",
                "active_enrolment", "utilization_pct", "open_exceptions", "compliance_status"
            ]].copy()
            display_df.columns = [
                "Institution Code", "Institution Name", "State", "Approved Intake",
                "Active Enrolment", "Utilization %", "Open Exceptions", "Compliance Status"
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export National Compliance Matrix (CSV)",
                data=csv_data,
                file_name=f"aicte_compliance_report_{academic_year}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")


# ===========================================================================
# VIEW 8: INSTITUTION INGESTION & INTAKE PORTAL
# ===========================================================================
elif selected_section == "nav_institution":
    target_inst = current_institution_id or "DEMO001"
    st.markdown(f"### 📥 Student Record Ingestion & Validation Portal: `{target_inst}`")
    st.caption("Upload student admission spreadsheets. Validation runs deterministically in preview mode prior to database commit.")

    try:
        intake_info = client.get_institution_intake(target_inst, role=current_role, academic_year=academic_year, token=st.session_state["auth_token"])
        intakes_list = intake_info.get("intakes", [])
        
        cols = st.columns(len(intakes_list) if intakes_list else 1)
        for i, c in enumerate(intakes_list):
            with cols[i]:
                st.info(f"**{c['course_code']}** | Regular: {c['regular_intake']} | Supernumerary: {c['supernumerary_intake']}\n\nEnrolled: {c['enrolled_regular']} Regular + {c['enrolled_supernumerary']} Sup ({c['utilization_pct']}% utilized)")
    except Exception as e:
        st.warning(f"Could not load intake context: {e}")

    st.markdown("---")
    st.markdown("#### Upload Student Admission Roster (CSV / Excel)")
    
    st.markdown("💡 **Evaluator Test Datasets:**")
    qc1, qc2, qc3 = st.columns([1.5, 1.5, 3])

    faulty_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "faulty_upload_demo.csv"))
    valid_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "valid_upload_sample.csv"))

    with qc1:
        if st.button("🚨 Load Intentionally Flawed CSV", use_container_width=True):
            if os.path.exists(faulty_path):
                with open(faulty_path, "rb") as f:
                    st.session_state["active_upload_bytes"] = f.read()
                    st.session_state["active_upload_name"] = "faulty_upload_demo.csv"
                st.toast("Loaded faulty_upload_demo.csv into upload buffer!")
    with qc2:
        if st.button("✅ Load Clean Valid CSV", use_container_width=True):
            if os.path.exists(valid_path):
                with open(valid_path, "rb") as f:
                    st.session_state["active_upload_bytes"] = f.read()
                    st.session_state["active_upload_name"] = "valid_upload_sample.csv"
                st.toast("Loaded valid_upload_sample.csv into upload buffer!")

    uploaded_file = st.file_uploader("Or choose a file from disk", type=["csv", "xlsx"])
    if uploaded_file is not None:
        st.session_state["active_upload_bytes"] = uploaded_file.read()
        st.session_state["active_upload_name"] = uploaded_file.name

    if "active_upload_bytes" in st.session_state and st.session_state["active_upload_bytes"]:
        file_bytes = st.session_state["active_upload_bytes"]
        file_name = st.session_state["active_upload_name"]
        
        st.write(f"📁 **Selected File:** `{file_name}` ({len(file_bytes)} bytes)")
        
        if st.button("🔍 Run Deterministic Validation Preview", type="primary"):
            with st.spinner("Executing rule engine V001–V010 against database state..."):
                preview_result = client.validate_file(
                    file_bytes=file_bytes,
                    filename=file_name,
                    institution_id=target_inst,
                    role=current_role,
                    academic_year=academic_year,
                    token=st.session_state["auth_token"]
                )
                st.session_state["last_preview"] = preview_result

    if "last_preview" in st.session_state:
        preview = st.session_state["last_preview"]
        st.markdown("### 📋 Upload Validation Report")
        
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Total Rows", preview.get("total_rows", 0))
        r2.metric("Eligible Rows (Passed)", preview.get("eligible_count", 0))
        r3.metric("Review Required (Flags)", preview.get("review_required_count", 0))
        r4.metric("Rejected (Hard Errors)", preview.get("rejected_count", 0))

        issues = preview.get("issues", [])
        if issues:
            st.markdown("#### Detected Validation Exceptions & Warnings")
            issues_df = pd.DataFrame(issues)[[
                "row_number", "rule_code", "severity", "student_apaar", "field_name", "message", "suggested_correction"
            ]].copy()
            issues_df.columns = ["Row #", "Rule Code", "Severity", "Student APAAR", "Field", "Explanation", "Suggested Correction"]
            st.dataframe(issues_df, use_container_width=True, hide_index=True)

            rejected_csv = issues_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Rejected Rows & Error Correction Report (CSV)",
                data=rejected_csv,
                file_name=f"rejected_rows_report_{preview['batch_key']}.csv",
                mime="text/csv"
            )

        preview_rows = preview.get("rows", [])
        if preview_rows:
            flat_rows = []
            for r in preview_rows:
                d = r["data"].copy()
                d["row_num"] = r["row_number"]
                d["outcome"] = r["outcome"]
                flat_rows.append(d)
            st.dataframe(pd.DataFrame(flat_rows), use_container_width=True, hide_index=True)

        st.markdown("---")
        eligible_cnt = preview.get("eligible_count", 0)
        review_cnt = preview.get("review_required_count", 0)

        if eligible_cnt > 0 or review_cnt > 0:
            st.success(f"✓ {eligible_cnt} records are eligible for transactional commit; {review_cnt} review records will be queued for administrative review.")
            if st.button("🚀 Commit Eligible Records (Atomic Transaction)", type="primary"):
                with st.spinner("Committing transaction with V008 idempotency lock..."):
                    raw_rows = [r["data"] for r in preview_rows]
                    sub_res = client.submit_batch(
                        batch_key=preview["batch_key"],
                        institution_id=target_inst,
                        academic_year=academic_year,
                        filename=preview["file_name"],
                        rows=raw_rows,
                        role=current_role,
                        token=st.session_state["auth_token"]
                    )
                    st.success(f"Batch successfully committed! Status: {sub_res.get('status')} | Batch ID: `{sub_res.get('id')}`")
                    st.rerun()

    # Submission History
    st.markdown("---")
    st.markdown("#### Institutional Submission History")
    submissions = client.get_submissions(role=current_role, institution_id=current_institution_id, token=st.session_state["auth_token"])
    if submissions:
        sub_df = pd.DataFrame(submissions)[[
            "id", "batch_key", "institution_id", "academic_year", "file_name", "total_rows", "eligible_rows", "status", "created_at"
        ]].copy()
        sub_df.columns = ["Batch ID", "Batch Key", "Institution", "Academic Year", "File", "Total", "Eligible", "Status", "Timestamp"]
        st.dataframe(sub_df, use_container_width=True, hide_index=True)


# ===========================================================================
# VIEW 9: CENTRALIZED EXCEPTION MANAGEMENT QUEUE
# ===========================================================================
elif selected_section == "nav_exceptions":
    st.markdown(f"### ⚠️ {t('nav_exceptions', lang)}")
    st.caption("Review conflicts, duplicate identifiers, excess intake, and cross-institution overlap. Sutrāyukti records every human adjudication in the audit trail.")

    exceptions = client.get_exceptions(role=current_role, institution_id=current_institution_id, token=st.session_state["auth_token"])
    
    if exceptions:
        f1, f2 = st.columns([1, 2])
        status_filter = f1.selectbox("Filter Status", ["ALL", "OPEN", "RESOLVED", "DISMISSED"])
        
        filtered_exceptions = exceptions
        if status_filter != "ALL":
            filtered_exceptions = [e for e in exceptions if e.get("status") == status_filter]

        st.write(f"Showing **{len(filtered_exceptions)}** exceptions:")

        for exc in filtered_exceptions:
            with st.expander(f"Rule {exc['rule_code']} ({exc['severity']}) — Student: {exc.get('student_apaar') or 'Batch'} | Row {exc['row_number']} | Status: {exc['status']}"):
                ec1, ec2 = st.columns([2, 1])
                with ec1:
                    st.markdown(f"**Explanation:** {exc['message']}")
                    st.markdown(f"**Suggested Action:** {exc.get('suggested_correction') or 'Review institutional documentation'}")
                    if exc.get("reviewer_comment"):
                        st.info(f"**Reviewer Note:** {exc['reviewer_comment']} (Resolved by: {exc.get('resolved_by')})")
                with ec2:
                    if exc["status"] == "OPEN":
                        st.markdown("**Adjudicate Exception:**")
                        comment = st.text_input(f"Reviewer Comment", key=f"c_{exc['id']}", placeholder="e.g. Verified valid Transfer Certificate.")
                        b_res, b_dis = st.columns(2)
                        with b_res:
                            if st.button("Resolve", key=f"res_{exc['id']}", type="primary"):
                                client.resolve_exception(exc["id"], "RESOLVED", comment or "Approved by officer", role=current_role, token=st.session_state["auth_token"])
                                st.success("Marked as RESOLVED!")
                                st.rerun()
                        with b_dis:
                            if st.button("Dismiss", key=f"dis_{exc['id']}"):
                                client.resolve_exception(exc["id"], "DISMISSED", comment or "Dismissed by officer", role=current_role, token=st.session_state["auth_token"])
                                st.warning("Dismissed.")
                                st.rerun()
                    else:
                        st.success(f"Status: {exc['status']}")
    else:
        st.info("No active exceptions detected. All records are compliant.")


# ===========================================================================
# VIEW 10: STUDENT RECORDS DIRECTORY
# ===========================================================================
elif selected_section == "nav_students":
    st.markdown(f"### 👥 {t('nav_students', lang)}")
    st.caption("Authorized access to student records with masked synthetic APAAR identifiers. Access scoped by role and institution tenant.")

    s_c1, s_c2 = st.columns([3, 1])
    search_query = s_c1.text_input("Search Students (Name, Masked APAAR, Roll No)", placeholder="e.g. Student Demo 010, DEMO001-CSE")
    
    students_list = client.get_students(role=current_role, institution_id=current_institution_id, search=search_query, token=st.session_state["auth_token"])
    
    if students_list:
        st.write(f"Displaying **{len(students_list)}** matching student records:")
        
        df_students = pd.DataFrame(students_list)[[
            "id", "display_apaar_id", "student_name", "current_institution", "current_course", "current_status"
        ]].copy()
        df_students.columns = ["Student UUID", "Masked APAAR ID", "Student Name", "Institution", "Course", "Status"]
        st.dataframe(df_students, use_container_width=True, hide_index=True)

        st.markdown("---")
        with st.expander("🔍 Inspect Student Academic Profile & Enrolment History"):
            std_options = {f"{s['student_name']} ({s['display_apaar_id']})": s["id"] for s in students_list}
            inspect_label = st.selectbox("Select Student Record", list(std_options.keys()))
            inspect_id = std_options[inspect_label]
            
            detail = client.get_student_detail(inspect_id, role=current_role, token=st.session_state["auth_token"])
            st.markdown(f"**Name:** {detail.get('student_name')} | **Masked Identifier:** `{detail.get('display_apaar_id')}` | **Email:** {detail.get('email')}")
            
            enrolments = detail.get("enrolments", [])
            if enrolments:
                st.markdown("##### Enrolment History:")
                enr_df = pd.DataFrame(enrolments)[[
                    "institution_id", "course_code", "academic_year", "admission_date", "category", "seat_type", "status"
                ]]
                enr_df.columns = ["Institution", "Course", "Academic Year", "Admission Date", "Category", "Seat Type", "Status"]
                st.dataframe(enr_df, use_container_width=True, hide_index=True)
    else:
        st.info("No student records found matching the query.")


# ===========================================================================
# VIEW 11: TAMPER-EVIDENT REGULATORY AUDIT TRAIL
# ===========================================================================
elif selected_section == "nav_audit":
    st.markdown(f"### 📜 {t('nav_audit', lang)}")
    st.caption("Cryptographically sequenced log of all sensitive operations, submissions, exception resolutions, and verification inspections.")

    audit_records = client.get_audit_trail(role=current_role, institution_id=current_institution_id, token=st.session_state["auth_token"])
    if audit_records:
        df_audit = pd.DataFrame(audit_records)[[
            "id", "timestamp", "actor_role", "actor_id", "action", "entity_type", "entity_id", "event_hash", "previous_hash"
        ]].copy()
        df_audit.columns = [
            "Event ID", "Timestamp", "Role", "Actor", "Action", "Entity", "Target ID", "Cryptographic Hash", "Parent Hash"
        ]
        st.dataframe(df_audit, use_container_width=True, hide_index=True)

        audit_csv = df_audit.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Tamper-Evident Audit Log (CSV)",
            data=audit_csv,
            file_name=f"audit_trail_{datetime.datetime.utcnow().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No audit events recorded yet.")


# ===========================================================================
# VIEW 12: EDUPATH NEP ADVISORY EXTENSION
# ===========================================================================
elif selected_section == "nav_edupath":
    st.markdown(f"### 🎓 {t('card_edupath_title', lang)}")
    st.caption("Adapted from EduSetu domain models. Provides student-controlled college search and scholarship eligibility guidance.")

    ep_tab1, ep_tab2 = st.tabs(["🏛️ College & Programme Explorer", "💰 Scholarship Eligibility Matcher"])

    with ep_tab1:
        st.markdown("#### Discover AICTE-Approved Engineering & Technical Colleges")
        q = st.text_input("Search by College Name or Branch", placeholder="e.g. Computer Science, Pune, Mysuru")
        st_filter = st.selectbox("Filter State", ["All", "Karnataka", "Maharashtra", "Jammu & Kashmir"], key="edupath_state")
        
        colleges = client.search_edupath(query=q, state=st_filter)
        for col in colleges:
            with st.container():
                st.markdown(f"**{col['name']}** — `{col['type']}` ({col['state']})")
                st.markdown(f"• **Offered Programmes:** {', '.join(col['programmes'])}")
                st.markdown(f"• **Eligibility:** {col['eligibility_criteria']}")
                st.caption(f"Accepted Schemes: {', '.join(col['scholarships_accepted'])} | Source: {col['data_freshness']}")
                st.markdown("---")

    with ep_tab2:
        st.markdown("#### AICTE & National Scholarship Eligibility Engine")
        sc1, sc2, sc3 = st.columns(3)
        income = sc1.number_input("Annual Family Income (₹)", min_value=0, max_value=5000000, value=400000, step=50000)
        is_fem = sc2.checkbox("Female Candidate")
        has_dis = sc3.checkbox("Specially-Abled (Disability >= 40%)")

        matched = client.match_scholarships(family_income=income, is_female=is_fem, has_disability=has_dis)
        for s in matched:
            status_badge = "✅ Eligible" if s["is_eligible"] else "❌ Not Eligible"
            with st.expander(f"{s['name']} — {status_badge}"):
                st.markdown(f"**Benefit:** {s['benefit']}")
                st.markdown(f"**Eligibility Details:** {s['eligibility_summary']}")
                st.markdown(f"**Required Documents:** {', '.join(s['documents'])}")
                st.markdown(f"[Official Portal Application Link]({s['portal_url']})")


# ===========================================================================
# VIEW 13: AICTE REGULATORY HANDBOOK ASSISTANT (RAG)
# ===========================================================================
elif selected_section == "nav_regulatory":
    st.markdown(f"### 📖 {t('card_regulatory_title', lang)}")
    st.caption("Advisory question-answering grounded in the official AICTE Approval Process Handbook (APH 2024–2027), APAAR guidelines, and DPDP rules.")

    st.markdown("💡 **Sample Queries:**")
    sq1, sq2, sq3 = st.columns(3)
    preset_q = None
    if sq1.button("How are supernumerary TFW seats counted?"):
        preset_q = "How are supernumerary TFW seats counted?"
    if sq2.button("What is APAAR ID format and purpose?"):
        preset_q = "What is APAAR ID format and purpose?"
    if sq3.button("Can a student have simultaneous active enrolments?"):
        preset_q = "Can a student have simultaneous active enrolments?"

    user_q = st.text_input("Ask a question regarding AICTE intake, APAAR, or admission rules:", value=preset_q or "")
    if st.button("Consult Regulatory Handbook", type="primary") or user_q:
        if user_q.strip():
            with st.spinner("Retrieving official clauses from regulatory handbook corpus..."):
                ans = client.ask_policy(user_q)
                st.markdown("#### Assistant Advisory Response:")
                st.markdown(ans["answer"])
                st.markdown("---")
                st.markdown(f"**Source Document:** `{ans['source_document']}`")
                st.markdown(f"**Statutory Clause:** `{ans['clause']}` ({ans['version_date']})")
                st.markdown(f"**Official Reference:** [Open Document]({ans['source_url']})")
                st.warning(f"⚠️ {ans['advisory_disclaimer']}")
