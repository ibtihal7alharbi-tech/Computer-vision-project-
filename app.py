"""
Mahd (مهد) — AI-Powered Baby Sleep Safety Monitor
Complete Streamlit application with Supabase auth, YOLOv8 inference, and emergency alerts.
"""

import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import time
from datetime import datetime
from pathlib import Path

# ─── Page Config (must be FIRST Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Mahd — مهد",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Lazy Imports (cached) ─────────────────────────────────────────────────────
@st.cache_resource
def load_supabase():
    from supabase import create_client, Client
    url  = st.secrets["SUPABASE_URL"]
    key  = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_resource
def load_models():
    from ultralytics import YOLO
    body_model = YOLO("body_best.pt")
    face_model = YOLO("face_best.pt")
    return body_model, face_model

# ─── Global CSS ────────────────────────────────────────────────────────────────
THEME_CSS = """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Colour Variables ── */
:root {
    --bg:          #FDFBF7;
    --sidebar-bg:  #F5EFE6;
    --accent:      #8DB580;
    --accent-dark: #6A9660;
    --danger:      #E07070;
    --warning:     #E8A96A;
    --text:        #4A4A4A;
    --text-light:  #8A8A8A;
    --border:      #E8E0D5;
    --card-bg:     #FFFFFF;
    --safe-bg:     #EEF5EC;
    --warn-bg:     #FDF3E8;
    --danger-bg:   #FDEAEA;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
    background-color: var(--bg);
}

/* ── Remove default Streamlit padding ── */
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Buttons ── */
.stButton > button {
    background-color: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 24px !important;
    padding: 0.55rem 1.4rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
    transition: background 0.2s ease, transform 0.1s ease !important;
}
.stButton > button:hover {
    background-color: var(--accent-dark) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Danger button override ── */
button[data-danger="true"] {
    background-color: var(--danger) !important;
}

/* ── Inputs ── */
input, textarea, select {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    background-color: var(--card-bg) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Card ── */
.mahd-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

/* ── Status Badge ── */
.status-badge {
    display: inline-block;
    border-radius: 50px;
    padding: 0.45rem 1.2rem;
    font-weight: 600;
    font-size: 1.05rem;
    letter-spacing: 0.02em;
}
.status-safe    { background: var(--safe-bg);   color: var(--accent-dark); }
.status-warning { background: var(--warn-bg);   color: #B86F0A; }
.status-danger  { background: var(--danger-bg); color: #C0392B; }
.status-scan    { background: #F2F2F2;           color: var(--text-light); }

/* ── Brand Logo Block ── */
.brand-block { text-align: center; padding: 1.2rem 0 1rem; }
.brand-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: var(--accent-dark);
    margin: 0;
}
.brand-sub { font-size: 0.8rem; color: var(--text-light); margin-top: 2px; }

/* ── Auth page ── */
.auth-wrapper {
    max-width: 440px;
    margin: 4vh auto;
    background: var(--card-bg);
    border-radius: 28px;
    padding: 2.5rem 2.8rem;
    border: 1px solid var(--border);
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}
.auth-logo-emoji { font-size: 3rem; text-align: center; display: block; margin-bottom: 0.4rem; }
.auth-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.9rem;
    text-align: center;
    color: var(--accent-dark);
    margin-bottom: 0.2rem;
}
.auth-subtitle { text-align: center; color: var(--text-light); font-size: 0.88rem; margin-bottom: 1.6rem; }

/* ── Section Heading ── */
.section-heading {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: var(--text);
    margin-bottom: 0.6rem;
}

/* ── Emergency CTA buttons ── */
.emergency-btn-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; }
.emergency-btn {
    flex: 1;
    min-width: 180px;
    display: inline-block;
    text-align: center;
    padding: 0.75rem 1.2rem;
    border-radius: 50px;
    font-weight: 600;
    font-size: 0.96rem;
    text-decoration: none !important;
    transition: opacity 0.2s;
}
.emergency-btn:hover { opacity: 0.85; }
.emergency-btn-911   { background: var(--danger); color: white; }
.emergency-btn-mom   { background: var(--accent); color: white; }

/* ── Progress bar override ── */
.stProgress > div > div { background-color: var(--accent) !important; border-radius: 10px; }

/* ── Timer ring ── */
.timer-block {
    text-align: center;
    padding: 0.8rem;
    border-radius: 16px;
    background: var(--warn-bg);
    border: 1px solid #F0C98A;
}
.timer-number { font-size: 3rem; font-weight: 700; color: #B86F0A; line-height: 1; }
.timer-label  { font-size: 0.78rem; color: #B86F0A; margin-top: 4px; }

/* ── Info pill ── */
.info-pill {
    display: inline-block;
    background: var(--safe-bg);
    color: var(--accent-dark);
    border-radius: 50px;
    padding: 0.25rem 0.8rem;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 2px;
}

/* ── Divider ── */
hr.mahd-hr { border: none; border-top: 1px solid var(--border); margin: 1.2rem 0; }

/* ── Selectbox, file uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: 16px !important;
    background: var(--card-bg) !important;
    padding: 1rem !important;
}
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)

# ─── Session State Initialisation ─────────────────────────────────────────────
for key, val in {
    "user": None,
    "profile": None,
    "auth_mode": "login",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─── Helpers ──────────────────────────────────────────────────────────────────

def normalise_phone(phone: str) -> str:
    """Strip spaces/dashes; ensure leading +"""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone

def log_alert(supabase, user_id: str, baby_name: str, status: str):
    try:
        supabase.table("alerts").insert({
            "user_id":   user_id,
            "baby_name": baby_name,
            "status":    status,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        st.warning(f"Could not log alert: {e}")

def draw_boxes(frame, results, color, model):
    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        lbl  = model.names[int(box.cls[0])]
        conf = float(box.conf[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{lbl} {conf:.2f}", (x1, max(y1 - 8, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return frame

def status_html(status_key: str, text: str) -> str:
    cls_map = {
        "safe":    "status-safe",
        "warning": "status-warning",
        "danger":  "status-danger",
        "scan":    "status-scan",
    }
    return f'<span class="status-badge {cls_map.get(status_key, "status-scan")}">{text}</span>'

# ─── Auth Page ─────────────────────────────────────────────────────────────────

def auth_page():
    supabase = load_supabase()

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown('<div class="auth-wrapper">', unsafe_allow_html=True)
        st.markdown('<span class="auth-logo-emoji">🌙</span>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Mahd · مهد</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">AI-powered baby sleep safety</div>', unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔑 Sign In", "✨ Sign Up"])

        # ── LOGIN ──
        with tab_login:
            with st.form("login_form"):
                phone    = st.text_input("Phone Number", placeholder="+966 50 000 0000")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In →", use_container_width=True)

            if submitted:
                if not phone or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        phone = normalise_phone(phone)
                        res   = supabase.auth.sign_in_with_password({"phone": phone, "password": password})
                        st.session_state.user = res.user

                        # Fetch profile
                        prof = supabase.table("profiles").select("*").eq("user_id", res.user.id).single().execute()
                        st.session_state.profile = prof.data
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")

        # ── SIGNUP ──
        with tab_signup:
            with st.form("signup_form"):
                mother_name = st.text_input("Mother's Name / اسم الأم")
                baby_name   = st.text_input("Baby's Name / اسم الطفل")
                phone_s     = st.text_input("Phone Number (login ID)", placeholder="+966 50 000 0000")
                emergency_p = st.text_input("Emergency Number", placeholder="+966 99 911")
                password_s  = st.text_input("Password", type="password")
                submitted_s = st.form_submit_button("Create Account →", use_container_width=True)

            if submitted_s:
                if not all([mother_name, baby_name, phone_s, emergency_p, password_s]):
                    st.error("Please fill in all fields.")
                else:
                    try:
                        phone_s = normalise_phone(phone_s)
                        res     = supabase.auth.sign_up({
                            "phone":    phone_s,
                            "password": password_s,
                        })
                        uid = res.user.id

                        # Insert profile
                        supabase.table("profiles").insert({
                            "user_id":       uid,
                            "mother_name":   mother_name,
                            "baby_name":     baby_name,
                            "phone":         phone_s,
                            "emergency_phone": normalise_phone(emergency_p),
                        }).execute()

                        st.success("Account created! Please sign in.")
                    except Exception as e:
                        st.error(f"Sign-up failed: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    profile = st.session_state.profile or {}
    supabase = load_supabase()

    with st.sidebar:
        # Brand
        st.markdown("""
        <div class="brand-block">
            <div style="font-size:2.4rem; margin-bottom:4px;">🌙</div>
            <div class="brand-title">Mahd · مهد</div>
            <div class="brand-sub">Cradle Protection</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="mahd-hr">', unsafe_allow_html=True)

        mother = profile.get("mother_name", "Parent")
        baby   = profile.get("baby_name",   "Baby")

        st.markdown(f"""
        <div style="padding: 0.4rem 0 0.8rem;">
            <div style="font-size:0.78rem; color: var(--text-light); margin-bottom:2px;">SIGNED IN AS</div>
            <div style="font-weight:600; font-size:1rem;">👩 {mother}</div>
            <div style="margin-top:6px; font-size:0.78rem; color: var(--text-light);">MONITORING</div>
            <div style="font-weight:600; font-size:1rem;">👶 {baby}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="mahd-hr">', unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.user    = None
            st.session_state.profile = None
            st.rerun()

# ─── Dashboard ─────────────────────────────────────────────────────────────────

def dashboard_page():
    supabase = load_supabase()
    profile  = st.session_state.profile or {}
    user     = st.session_state.user
    baby     = profile.get("baby_name",       "Baby")
    emergency_phone = profile.get("emergency_phone", "911")
    mother_phone    = profile.get("phone",           "")

    # ── Header ──
    st.markdown(f"""
    <div style="margin-bottom:1.6rem;">
        <h1 style="font-family:'DM Serif Display',serif; font-size:2.1rem; margin:0; color:var(--text);">
            Mahd — طفلك في أمان
        </h1>
        <p style="color:var(--text-light); font-size:0.92rem; margin-top:6px;">
            AI-powered sleep safety for <strong>{baby}</strong> · Real-time monitoring
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Upload Section ──
    st.markdown('<div class="mahd-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">📹 Upload Baby Monitor Footage</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.88rem; color:var(--text-light); margin-bottom:1rem;">Upload an MP4 or MOV recording from your baby monitor. Mahd will analyse every frame.</p>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Choose a video file",
        type=["mp4", "mov", "avi"],
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if not uploaded:
        # Placeholder info cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="mahd-card" style="text-align:center; padding:1.4rem 1rem;">
                <div style="font-size:2rem;">🟢</div>
                <div style="font-weight:600; margin-top:8px;">SAFE</div>
                <div style="font-size:0.8rem; color:var(--text-light); margin-top:4px;">Back sleeping + nose visible</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="mahd-card" style="text-align:center; padding:1.4rem 1rem;">
                <div style="font-size:2rem;">🟠</div>
                <div style="font-weight:600; margin-top:8px;">WARNING</div>
                <div style="font-size:0.8rem; color:var(--text-light); margin-top:4px;">Back sleeping, face may be covered</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class="mahd-card" style="text-align:center; padding:1.4rem 1rem;">
                <div style="font-size:2rem;">🔴</div>
                <div style="font-weight:600; margin-top:8px;">DANGER</div>
                <div style="font-size:0.8rem; color:var(--text-light); margin-top:4px;">Stomach sleeping for 10 s</div>
            </div>""", unsafe_allow_html=True)
        return

    # ── Load Models ──
    with st.spinner("Loading AI models…"):
        try:
            body_model, face_model = load_models()
        except Exception as e:
            st.error(f"Could not load YOLO models: {e}. Make sure `body_best.pt` and `face_best.pt` are present.")
            return

    # ── Save uploaded file to temp ──
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix)
    tfile.write(uploaded.read())
    tfile.close()

    cap = cv2.VideoCapture(tfile.name)
    if not cap.isOpened():
        st.error("Could not open the video file. Please try a different format.")
        os.unlink(tfile.name)
        return

    fps        = max(int(cap.get(cv2.CAP_PROP_FPS)), 1)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    WAIT_SECONDS   = 10
    frames_threshold = fps * WAIT_SECONDS

    # ── UI Layout ──
    col_video, col_status = st.columns([3, 2])

    with col_video:
        st.markdown('<div class="section-heading">🎥 Live Feed</div>', unsafe_allow_html=True)
        frame_placeholder = st.empty()

    with col_status:
        st.markdown('<div class="section-heading">📊 Safety Status</div>', unsafe_allow_html=True)
        status_placeholder   = st.empty()
        timer_placeholder    = st.empty()
        emergency_placeholder = st.empty()
        progress_placeholder  = st.empty()
        log_placeholder       = st.empty()

    # ── Processing Loop ──
    danger_counter = 0
    frame_idx      = 0
    alert_logged   = False
    status_log     = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Run inference
        body_res = body_model(frame, verbose=False, conf=0.25)[0]
        face_res = face_model(frame, verbose=False, conf=0.25)[0]

        # Collect labels
        all_labels = []
        nose_found = False
        for res in [body_res, face_res]:
            for box in res.boxes:
                lbl = res.names[int(box.cls[0])].lower()
                all_labels.append(lbl)
                if "nose" in lbl:
                    nose_found = True

        combined = " ".join(all_labels)

        # Safety logic
        if "stomach" in combined:
            danger_counter += 1
            remaining = max(0, WAIT_SECONDS - (danger_counter // fps))
            if danger_counter < frames_threshold:
                status_key  = "warning"
                status_text = f"⚠️ STOMACH DETECTED — {remaining}s to DANGER"
            else:
                status_key  = "danger"
                status_text = "🚨 DANGER: STOMACH SLEEPING"
        elif "back" in combined:
            danger_counter = 0
            if nose_found:
                status_key  = "safe"
                status_text = "✅ SAFE — Back + Nose Visible"
            else:
                status_key  = "warning"
                status_text = "⚠️ WARNING: Face May Be Covered"
        else:
            danger_counter = 0
            status_key  = "scan"
            status_text = "🔍 SCANNING…"

        # Draw boxes
        annotated = frame.copy()
        annotated = draw_boxes(annotated, body_res, (0, 200, 80),  body_model)
        annotated = draw_boxes(annotated, face_res, (80, 100, 220), face_model)

        # Status bar on frame
        bar_color = {
            "safe":    (100, 190, 90),
            "warning": (50, 150, 220),
            "danger":  (60, 60, 210),
            "scan":    (180, 180, 180),
        }[status_key]

        cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 52), (20, 20, 20), -1)
        cv2.putText(annotated, status_text, (14, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, bar_color, 2)

        # Render frame (RGB)
        frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_rgb, use_container_width=True)

        # Status card
        status_placeholder.markdown(
            f'<div class="mahd-card" style="padding:1rem 1.4rem;">'
            f'{status_html(status_key, status_text)}'
            f'<div style="margin-top:10px; font-size:0.8rem; color:var(--text-light);">'
            f'Frame {frame_idx} / {total_frames}</div></div>',
            unsafe_allow_html=True,
        )

        # Progress
        progress_placeholder.progress(min(frame_idx / max(total_frames, 1), 1.0))

        # Timer card
        if "stomach" in combined and danger_counter < frames_threshold:
            remaining = max(0, WAIT_SECONDS - (danger_counter // fps))
            timer_placeholder.markdown(f"""
            <div class="timer-block">
                <div class="timer-number">{remaining}</div>
                <div class="timer-label">seconds until DANGER alert</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            timer_placeholder.empty()

        # DANGER — log + show emergency buttons
        if status_key == "danger":
            if not alert_logged and user:
                log_alert(supabase, user.id, baby, status_text)
                alert_logged = True

            tel_emergency = f"tel:{emergency_phone.replace('+','').replace(' ','')}"
            tel_mother    = f"tel:{mother_phone.replace('+','').replace(' ','')}"

            emergency_placeholder.markdown(f"""
            <div class="mahd-card" style="background:var(--danger-bg); border-color:#E07070; padding:1.2rem 1.4rem;">
                <div style="font-weight:700; color:#C0392B; font-size:1rem; margin-bottom:0.8rem;">
                    🚨 Emergency Response
                </div>
                <div class="emergency-btn-row">
                    <a href="{tel_emergency}" class="emergency-btn emergency-btn-911">
                        📞 Call {emergency_phone}
                    </a>
                    <a href="{tel_mother}" class="emergency-btn emergency-btn-mom">
                        📞 Call Mother
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.toast("🚨 DANGER: Stomach sleeping detected!", icon="🚨")
        else:
            emergency_placeholder.empty()

        # Append to rolling log
        status_log.append(status_text)
        if len(status_log) > 6:
            status_log.pop(0)

        log_html = "".join(
            f'<div style="font-size:0.78rem; color:var(--text-light); padding:2px 0;">'
            f'· {s}</div>'
            for s in reversed(status_log)
        )
        log_placeholder.markdown(
            f'<div class="mahd-card" style="padding:0.8rem 1.2rem;">'
            f'<div style="font-size:0.78rem; font-weight:600; color:var(--text); margin-bottom:6px;">Recent Events</div>'
            f'{log_html}</div>',
            unsafe_allow_html=True,
        )

        # Throttle: process every N frames to keep UI responsive
        # Skip 2 frames for performance (process 1 in 3)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx + 1)

    cap.release()
    os.unlink(tfile.name)

    # Final summary
    st.markdown('<hr class="mahd-hr">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="mahd-card" style="background:var(--safe-bg); border-color:var(--accent);">
        <div style="font-weight:600; color:var(--accent-dark);">✅ Analysis Complete</div>
        <div style="font-size:0.88rem; color:var(--text-light); margin-top:6px;">
            Processed <strong>{frame_idx}</strong> frames for <strong>{baby}</strong>.
            {"An emergency alert was logged." if alert_logged else "No danger events detected."}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Router ────────────────────────────────────────────────────────────────────

def main():
    if st.session_state.user is None:
        auth_page()
    else:
        render_sidebar()
        dashboard_page()

if __name__ == "__main__":
    main()
