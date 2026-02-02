import streamlit as st
import os
from openai import OpenAI
import json

# --- 1. הגדרות עמוד ועיצוב ---
st.set_page_config(page_title="Macro Alpha Generator", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .big-font { font-size:18px !important; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; height: 50px; }
    .metric-box { border: 1px solid #e0e0e0; padding: 15px; border-radius: 8px; margin-bottom: 10px; background-color: #f9f9f9; }
    .term-box { background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-right: 5px solid #2196f3; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    h1 { color: #0f172a; }
    h2, h3 { color: #334155; }
</style>
""", unsafe_allow_html=True)

# --- 2. ניהול Session State ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'client' not in st.session_state: st.session_state.client = None
if 'model_name' not in st.session_state: st.session_state.model_name = "anthropic/claude-3.5-sonnet"

# --- 3. סרגל צד (Sidebar) - הגרסה החכמה ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/bullish.png", width=60)
    st.header("הגדרות מערכת")
    
    # --- בדיקה האם יש מפתח שמור ב-Secrets ---
    if "OPENROUTER_API_KEY" in st.secrets:
        # המערכת מצאה מפתח סודי בשרת
        secret_key = st.secrets["OPENROUTER_API_KEY"]
        
        # חיבור אוטומטי (רק אם עדיין לא מחובר)
        if not st.session_state.client:
            try:
                if secret_key.startswith("sk-or-"):
                    st.session_state.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=secret_key)
                    st.session_state.model_name = "anthropic/claude-3.5-sonnet"
                else:
                    st.session_state.client = OpenAI(api_key=secret_key)
                    st.session_state.model_name = "gpt-4o"
            except Exception as e:
                st.error("תקלה בחיבור למפתח השמור")
        
        st.success("🔑 מחובר באמצעות רישיון משותף")
    
    else:
        # --- אם אין מפתח שמור, בקש מהמשתמש ---
        raw_api_key = st.text_input("API Key (OpenAI / OpenRouter)", type="password", help="הכנס מפתח ולחץ Enter")
        
        if raw_api_key:
            api_key = raw_api_key.strip()
            # זיהוי סוג המפתח
            if api_key.startswith("sk-or-"):
                st.session_state.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
                st.session_state.model_name = "anthropic/claude-3.5-sonnet"
                st.success("זוהה: OpenRouter ✅")
            else:
                st.session_state.client = OpenAI(api_key=api_key)
                st.session_state.model_name = "gpt-4o"
                st.success("זוהה: OpenAI ✅")
    
    st.markdown("---")
    if st.button("🏠 התחל ניתוח חדש"):
        keys_to_reset = ['step', 'analysis', 'strategies', 'deep_analysis', 'selected_strat', 'view', 'cap']
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# --- 4. פונקציות הליבה (AI Logic) ---
def clean_json_response(content):
    """מנקה את התשובה של ה-AI כדי לחלץ רק את ה-JSON"""
    try:
        content = content.strip()
        if "```" in content:
            if "json" in content:
                return json.loads(content.split("```json")[1].split("```")[0])
            else:
                return json.loads(content.split("```")[1])
        return json.loads(content)
    except Exception as e:
        st.error(f"שגיאה בפענוח תשובת המודל: {str(e)}")
        return None

def get_analyst_challenge(view):
    """שלב 1: אתגר את התזה"""
    if not st.session_state.client: return None
    
    prompt = f"""
    You are a Mentor & Risk Manager. User View: "{view}".
    Analyze critically.
    Output JSON ONLY in this format:
    {{
        "consensus_view": "What market thinks (Hebrew)",
        "risk_factors": "Risks to user view (Hebrew)",
        "calibration_questions": ["Q1 (Hebrew)", "Q2 (Hebrew)", "Q3 (Hebrew)"]
    }}
    """
    try:
        response = st.session_state.client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_json_response(response.choices[0].message.content)
    except Exception as e:
        st.error(f"שגיאה בתקשורת: {str(e)}")
        return None

def get_strategies(view, answers, capital):
    """שלב 2: בניית אסטרטגיות"""
    if not st.session_state.client: return None
    
    ans_str = ", ".join(answers)
    prompt = f"""
    User View: {view} | User Answers: {ans_str} | Capital: ${capital}
    
    Create 3 distinct trading strategies. BE SPECIFIC with Tickers.
    Output JSON ONLY:
    {{
        "strategies": [
            {{
                "id": 0,
                "name": "Name of Strategy (Hebrew)",
                "instrument": "Type (e.g. Stocks, Options)",
                "specific_tickers": "Specific Tickers (e.g. TEVA, SPY)",
                "brief_explanation": "Short explanation in Hebrew",
                "max_profit": "Estimated Profit",
                "max_loss": "Max Risk"
            }},
            {{ "id": 1, "name": "...", "instrument": "...", "specific_tickers": "...", "brief_explanation": "...", "max_profit": "...", "max_loss": "..." }},
            {{ "id": 2, "name": "...", "instrument": "...", "specific_tickers": "...", "brief_explanation": "...", "max_profit": "...", "max_loss": "..." }}
        ]
    }}
    """
    try:
        response = st.session_state.client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_json_response(response.choices[0].message.content)
    except Exception as e:
        st.error(f"שגיאה ביצירת אסטרטגיות: {str(e)}")
        return None

def get_deep_dive(strategy, view):
    """שלב 3: ניתוח עומק"""
    if not st.session_state.client: return None

    prompt = f"""
    Analyze this specific strategy: {strategy} based on user view: {view}.
    Output JSON ONLY:
    {{
        "educational_terms": [
            {{ "term": "Term Name", "definition": "Simple definition in Hebrew" }},
            {{ "term": "Term Name", "definition": "Simple definition in Hebrew" }}
        ],
        "asset_analysis": "Deep analysis of the asset in Hebrew",
        "market_context": "Current market context in Hebrew",
        "scenarios": [
            {{ "move": "Bear Case (-5%)", "outcome": "What happens", "pnl": "-$..." }},
            {{ "move": "Base Case (0%)", "outcome": "What happens", "pnl": "+$..." }},
            {{ "move": "Bull Case (+5%)", "outcome": "What happens", "pnl": "+$..." }}
        ]
    }}
    """
    try:
        response = st.session_state.client.chat.completions.create(
            model=st.session_state.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_json_response(response.choices[0].message.content)
    except Exception as e:
        st.error(f"שגיאה בניתוח עומק: {str(e)}")
        return None

# --- 5. ממשק המשתמש (Main UI) ---
st.title("🧠 Macro Alpha Generator")
st.markdown("### מערכת תומכת החלטה למשקיעי מקרו")

# --- Step 1: Input ---
if st.session_state.step == 1:
    st.info("👋 שלום! הכנס את תזת ההשקעה שלך כדי להתחיל.")
    view = st.text_area("מה התזה שלך?", placeholder="לדוגמה: מחירי הנפט יעלו בחורף הקרוב בגלל משבר אנרגיה...", height=120)
    
    if st.button("🚀 התחל ניתוח"):
        # בדיקה כפולה: או שיש קליינט מחובר (מה-Secrets) או שאין כלום
        if not st.session_state.client:
            st.error("⚠️ המערכת לא מחוברת. אם אין לך מפתח ב-Secrets, נא להזין אחד בצד ימין.")
        elif not view:
            st.warning("⚠️ לא כתבת כלום...")
        else:
            with st.spinner('המנתח הוירטואלי בודק את התזה שלך...'):
                data = get_analyst_challenge(view)
                if data:
                    st.session_state.analysis = data
                    st.session_state.view = view
                    st.session_state.step = 2
                    st.rerun()

# --- Step 2: Calibration ---
elif st.session_state.step == 2:
    data = st.session_state.analysis
    
    st.success("✅ הניתוח הראשוני הושלם")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"### 🤔 קונצנזוס השוק\n{data.get('consensus_view', 'N/A')}")
    with col2:
        st.markdown(f"### ⚠️ גורמי סיכון\n{data.get('risk_factors', 'N/A')}")
    
    st.markdown("---")
    
    with st.form("calib_form"):
        st.subheader("כיול מדויק לבניית אסטרטגיה")
        
        answers = []
        questions = data.get('calibration_questions', [])
        for i, q in enumerate(questions):
            answers.append(st.text_input(f"{i+1}. {q}"))
            
        cap = st.number_input("כמה הון אתה מקצה לסיכון הזה? ($)", value=1000, step=100)
        
        if st.form_submit_button("הצג אסטרטגיות השקעה 💼"):
            with st.spinner('בונה תיק השקעות אופטימלי...'):
                strategies_data = get_strategies(st.session_state.view, answers, cap)
                if strategies_data:
                    st.session_state.strategies = strategies_data
                    st.session_state.cap = cap
                    st.session_state.step = 3
                    st.rerun()

# --- Step 3: Selection ---
elif st.session_state.step == 3:
    st.subheader("📊 בחר את האסטרטגיה המתאימה לך")
    
    strats = st.session_state.strategies.get('strategies', [])
    cols = st.columns(3)
    
    for i, strat in enumerate(strats):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"### {strat.get('name')}")
                st.markdown(f"**{strat.get('instrument')}")
                st.code(strat.get('specific_tickers'))
                
                c1, c2 = st.columns(2)
                c1.metric("רווח", strat.get('max_profit'))
                c2.metric("סיכון", strat.get('max_loss'))
                
                st.write(strat.get('brief_explanation'))
                
                if st.button(f"🔍 נתח לעומק", key=f"s_{i}"):
                    st.session_state.selected_strat = strat
                    st.session_state.step = 4
                    st.rerun()

# --- Step 4: Deep Dive ---
elif st.session_state.step == 4:
    strat = st.session_state.selected_strat
    st.button("⬅️ חזרה לאסטרטגיות", on_click=lambda: st.session_state.update(step=3))
    
    st.title(f"ניתוח עומק: {strat.get('name')}")
    
    # Run Deep Dive if not cached
    if 'deep_analysis' not in st.session_state or st.session_state.get('last_strat_id') != strat.get('id'):
        with st.spinner(f"מבצע בדיקת נאותות על {strat.get('specific_tickers')}..."):
            deep_data = get_deep_dive(strat, st.session_state.view)
            if deep_data:
                st.session_state.deep_analysis = deep_data
                st.session_state.last_strat_id = strat.get('id')
            else:
                st.error("לא הצלחנו לבצע את הניתוח. נסה שוב.")

    if 'deep_analysis' in st.session_state:
        deep = st.session_state.deep_analysis
        st.balloons()
        
        # Terms Section
        st.subheader("📚 מושגים שחובה להכיר")
        terms = deep.get('educational_terms', [])
        t_cols = st.columns(2)
        for idx, t in enumerate(terms):
            with t_cols[idx % 2]:
                st.markdown(f"""
                <div class="term-box">
                    <strong>{t.get('term')}</strong><br>
                    <span style="color:#555">{t.get('definition')}</span>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Asset Analysis
        st.subheader(f"📈 ניתוח הנכס: {strat.get('specific_tickers')}")
        st.write(deep.get('asset_analysis'))
        st.info(f"**הקשר שוק:** {deep.get('market_context')}")
        
        # Scenarios
        st.subheader("🔮 תרחישי קיצון (P&L)")
        st.table(deep.get('scenarios'))
