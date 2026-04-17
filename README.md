# Mahd (مهد) — Deployment Guide

## File Structure
```
mahd_app/
├── app.py                   ← Main Streamlit application
├── requirements.txt         ← Python dependencies
├── body_best.pt             ← YOLOv8 body model  (add manually)
├── face_best.pt             ← YOLOv8 face model  (add manually)
├── supabase_schema.sql      ← Run once in Supabase SQL Editor
└── .streamlit/
    └── secrets.toml         ← Supabase credentials (DO NOT commit)
```

## Step-by-Step Setup

### 1. Supabase
1. Create a free project at https://supabase.com
2. Go to **SQL Editor** and run the contents of `supabase_schema.sql`
3. Go to **Authentication → Providers → Phone** and enable it (uses Twilio)
4. Copy your **Project URL** and **anon/public API key** from Project Settings → API

### 2. Secrets
Edit `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJhbGci..."
```

### 3. Model Weights
Place your two model files in the project root:
- `body_best.pt` — detects `back` / `stomach`
- `face_best.pt` — detects `head` / `nose`

These are the models trained in `Computer_vision2.ipynb`.
Download them from your Colab session or Google Drive before deploying.

### 4. Local Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

### 5. Streamlit Cloud Deployment
1. Push to a GitHub repo (add `*.pt`, `secrets.toml` to `.gitignore`)
2. Go to https://share.streamlit.io → New App
3. Select your repo and set `app.py` as the main file
4. Under **Advanced → Secrets**, paste your `secrets.toml` contents
5. Upload model weights via `st.file_uploader` workaround or store in cloud storage

## Safety Logic Summary
| Detected           | Status                     | Action                            |
|--------------------|----------------------------|-----------------------------------|
| stomach (< 10 s)   | ⚠️ WARNING + countdown    | Orange bar, timer visible         |
| stomach (≥ 10 s)   | 🚨 DANGER                  | Red bar + emergency call buttons  |
| back + nose        | ✅ SAFE                    | Green bar                         |
| back, no nose      | ⚠️ Face May Be Covered     | Orange bar                        |
| nothing detected   | 🔍 SCANNING                | Grey bar                          |

## Notes
- On Streamlit Cloud, `tel:` links only work when opened on a mobile browser.
- `opencv-python-headless` is used (not `opencv-python`) to avoid GUI library issues on cloud.
- The danger alert is logged once per video session to avoid duplicate rows.
