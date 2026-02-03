import streamlit as st
import os
import json
from openai import OpenAI

# --- 1. הגדרות עמוד ועיצוב משודרג ---
st.set_page_config(page_title="Pro Macro Alpha", page_icon="🦁", layout="wide")

st.markdown("""
<style>
    /* תמיכה טובה יותר בעברית */
    body { direction: rtl; }
    .stMarkdown, .stText, .stTitle, h1, h2, h3, h4, h5, h6 { text-align: right; direction: rtl; }
    
    /* עיצוב כרטיסיות */
    .card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-right: 5px solid #4CAF50;
        margin-bottom: 20px;
    }
    .logic-chain {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        font-size: 0.9em;
        border-right: 3px solid #ff9800;
        margin-top: 10px;
    }
    .rationale {
        font-size: 0.85em;
        color: #666;
        background-color: #e8f5e9;
        padding: 8px;
        border-radius: 5px;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. ניהול Session State ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'client' not in st.session_state: st.session_state.client = None
if 'model_name' not in st.session_state: st.session_state.model_name = "gpt-4o"

# --- 3. סרגל צד (Sidebar) ---
with st.sidebar:
    st.header("⚙️ חדר בקרה")
    
    # חיבור אוטומטי מ-Secrets או ידני
    if "OPENROUTER_API_KEY" in st.secrets:
        secret_key = st.secrets["OPENROUTER_API_KEY"]
        if not st.session_state.client:
            try:
                if secret_key.startswith("sk-or-"):
                    st.session_state.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=secret_key)
                    st.session_state.model_name = "anthropic/claude-3.5-sonnet" # מודל חכם יותר
                else:
                    st.session_state.client = OpenAI(api_key=secret_key)
            except Exception as e:
                st.error("תקלה בחיבור למפתח")
        st.success("מחובר למערכת 🟢")
    else:
        api_key = st.text_input("מפתח API", type="password")
        if api_key:
            st.session_state.client = OpenAI(api_key=api_key)
            st.success("מחובר ידנית 🟢")

    if st.button("🔄 איפוס מערכת"):
        st.session_state.clear()
        st.rerun()

# --- 4. המוח (AI Logic) ---

def safe_json_parse(content):
    """מנסה לחלץ JSON מתוך הטקסט של ה-AI גם אם הוא מוסיף שטויות מסביב"""
    try:
        content = content.replace("```json", "").replace("```", "").strip()
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        return json.loads(content)
    except:
        return None

def get_analyst_challenge(view):
    """שלב 1: אתגר את התזה - עם הסברים למה שואלים"""
    prompt = f"""
    You are a Senior Macro Strategist at a Hedge Fund. 
    User View: "{view}".
    
    Your Goal: Challenge this view to find weak spots.
    
    Output JSON format:
    {{
        "consensus_view": "What the boring majority thinks (Hebrew)",
        "contrarian_angle": "A surprising counter-view (Hebrew)",
        "calibration_questions": [
            {{
                "question": "The actual question (Hebrew)",
                "rationale": "EXPLAIN WHY you are asking this. How does it change the trade? (Hebrew)"
            }},
            {{ "question": "...", "rationale": "..." }}
        ]
    }}
    """
    response = st.session_state.client.chat.completions.create(
        model=st.session_state.model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return safe_json_parse(response.choices[0].message.content)

def get_strategies(view, answers, capital):
    """שלב 2: אסטרטגיות - עם חשיבה עקיפה (Lateral Thinking)"""
    ans_str = "\n".join([f"Q: {a['q']} | A: {a['a']}" for a in answers])
    
    prompt = f"""
    You are a Legendary Macro Investor (like Soros/Druckenmiller).
    
    User View: {view}
    User Context: {ans_str}
    Capital: ${capital}
    
    TASK: Generate 3 distinct trading strategies.
    CRITICAL: Use "Second-Level Thinking". Do not just go for the obvious.
    Example of Lateral Thinking:
    - Obvious: "It's hot" -> Buy Air Conditioning stocks.
    - Lateral: "It's hot" -> Crops will fail -> Food prices up -> Political instability in Emerging Markets -> Short EM Currencies.
    
    Output JSON format:
    {{
        "strategies": [
            {{
                "name": "Creative Name (Hebrew)",
                "ticker": "TICKER (e.g. SPY, GLD)",
                "direction": "Long/Short",
                "logic_chain": "Event -> Effect A -> Effect B -> Profit (Hebrew)",
                "risk_reward": "High/Med/Low",
                "youtube_query": "Search term to learn this strategy (e.g. 'How to trade VIX futures')"
            }}
        ]
    }}
    """
    response = st.session_state.client.chat.completions.create(
        model=st.session_state.model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return safe_json_parse(response.choices[0].message.content)

def get_deep_dive(strategy, view):
    """שלב 3: ניתוח עומק"""
    prompt = f"""
    Deep Analysis for strategy: {strategy['name']} ({strategy['ticker']}).
    User View: {view}
    
    Output JSON format:
    {{
        "bull_case": "Best case scenario (Hebrew)",
        "bear_case": "Worst case scenario (Hebrew)",
        "key_metric": "What is the #1 data point to watch? (Hebrew)",
        "institutional_positioning": "How are the big banks positioned? (Hebrew)",
        "video_tutorial_query": "Exact YouTube search query for a tutorial on this instrument"
    }}
    """
    response = st.session_state.client.chat.completions.create(
        model=st.session_state.model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    return safe_json_parse(response.choices[0].message.content)

# --- 5. הממשק (UI) ---
st.title("🦁 Macro Alpha Pro")
st.caption("מערכת מסחר מוסדית מבוססת AI")

# שלב 1: קלט
if st.session_state.step == 1:
    view = st.text_area("מה התזה שלך?", height=150, placeholder="למשל: האינפלציה בארה״ב תרד מהר מהצפוי, אבל הכלכלה תיכנס למיתון...")
    if st.button("נתח שוק 🧠"):
        if not st.session_state.client:
            st.error("נא להתחבר עם מפתח API בצד ימין")
        elif not view:
            st.warning("נא להזין תזה")
        else:
            with st.spinner('המערכת מבצעת ניתוח סיכונים...'):
                st.session_state.analysis = get_analyst_challenge(view)
                st.session_state.view = view
                st.session_state.step = 2
                st.rerun()

# שלב 2: כיול והסברים
elif st.session_state.step == 2:
    data = st.session_state.analysis
    
    # הצגת הקונצנזוס מול דעת המיעוט
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**מה כולם חושבים:**\n{data.get('consensus_view')}")
    with c2:
        st.warning(f"**זווית מפתיעה:**\n{data.get('contrarian_angle')}")

    with st.form("calib"):
        st.subheader("דיוק התזה (Calibration)")
        
        user_answers = []
        questions = data.get('calibration_questions', [])
        
        for i, q in enumerate(questions):
            # כאן הקסם: הצגת השאלה עם הסבר "למה"
            st.markdown(f"**{i+1}. {q['question']}**")
            st.markdown(f"<div class='rationale'>💡 למה אנחנו שואלים? {q['rationale']}</div>", unsafe_allow_html=True)
            ans = st.text_input(f"התשובה שלך לשאלה {i+1}", key=f"q{i}")
            user_answers.append({"q": q['question'], "a": ans})
            st.markdown("---")
            
        cap = st.number_input("הון להשקעה ($)", value=10000)
        
        if st.form_submit_button("בנה אסטרטגיות חכמות 🚀"):
            with st.spinner('מפעיל חשיבה רוחבית (Lateral Thinking)...'):
                st.session_state.strategies = get_strategies(st.session_state.view, user_answers, cap)
                st.session_state.step = 3
                st.rerun()

# שלב 3: הצגת אסטרטגיות
elif st.session_state.step == 3:
    st.subheader("🎯 האסטרטגיות שנבחרו")
    strats = st.session_state.strategies.get('strategies', [])
    
    for i, s in enumerate(strats):
        with st.container():
            st.markdown(f"""
            <div class="card">
                <h3>{s['name']} ({s['ticker']}) - {s['direction']}</h3>
                <div class="logic-chain">⛓️ <b>שרשרת הלוגיקה:</b> {s['logic_chain']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1,1,2])
            with c1:
                # כפתור יוטיוב חכם
                yt_query = s.get('youtube_query', f"How to trade {s['ticker']}")
                st.link_button("📺 צפה במדריך וידאו", f"https://www.youtube.com/results?search_query={yt_query}")
            with c2:
                if st.button("חפור לעומק 🔬", key=f"btn_{i}"):
                    st.session_state.selected_strat = s
                    st.session_state.step = 4
                    st.rerun()
            
            st.write("") # מרווח

    if st.button("התחל מחדש"):
        st.session_state.step = 1
        st.rerun()

# שלב 4: מחקר עומק
elif st.session_state.step == 4:
    strat = st.session_state.selected_strat
    st.button("חזרה", on_click=lambda: st.session_state.update(step=3))
    
    st.title(f"תיק ניתוח: {strat['ticker']}")
    
    if 'deep_data' not in st.session_state or st.session_state.last_ticker != strat['ticker']:
        with st.spinner('קורא דוחות מוסדיים...'):
            st.session_state.deep_data = get_deep_dive(strat, st.session_state.view)
            st.session_state.last_ticker = strat['ticker']
            
    deep = st.session_state.deep_data
    
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"📈 תרחיש חיובי\n{deep.get('bull_case')}")
    with c2:
        st.error(f"📉 תרחיש שלילי\n{deep.get('bear_case')}")
        
    st.info(f"**נתון המפתח שיש לעקוב אחריו:** {deep.get('key_metric')}")
    
    # חיפוש וידאו נוסף
    st.markdown("### 🎓 למידה נוספת")
    vid_q = deep.get('video_tutorial_query', 'trading tutorial')
    st.markdown(f"[לחץ כאן לחיפוש סרטוני הדרכה ספציפיים למוצר זה ביוטיוב](https://www.youtube.com/results?search_query={vid_q})")
