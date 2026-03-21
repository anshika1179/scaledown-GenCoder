# app.py
import streamlit as st
from tutor_backend import get_relevant_context, generate_answer, chapters

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="NCERT History Tutor | Class 10",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ── Premium Dark Theme ─────────────────────────
st.markdown("""
<style>
/* ── Import Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary: #f5f3ff;
    --bg-secondary: #ede9ff;
    --bg-card: #ffffff;
    --bg-hover: #e2deff;
    --accent: #4c1d95;
    --accent-glow: rgba(76, 29, 149, 0.25);
    --accent-light: #5b21b6;
    --text-primary: #0a081a;
    --text-secondary: #1e1b3a;
    --border: #d5cfff;
    --success: #10b981;
    --warning: #f59e0b;
}

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"], .main, [data-testid="stApp"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ede9ff 0%, #e2deff 100%) !important;
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary) !important;
}

/* ── Hero Header ── */
.hero-container {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    margin-bottom: 1rem;
}

.hero-icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7c5cfc, #a78bfa, #c4b5fd);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
    letter-spacing: -0.5px;
}

.hero-subtitle {
    font-size: 1rem;
    color: var(--text-secondary);
    font-weight: 300;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1.2rem !important;
    margin-bottom: 1rem !important;
    transition: border-color 0.3s ease;
}

[data-testid="stChatMessage"]:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
}

[data-testid="stChatMessage"] p {
    color: var(--text-primary) !important;
    line-height: 1.7 !important;
}

/* ── Chat Input ── */
[data-testid="stChatInput"] {
    border-color: var(--border) !important;
}

[data-testid="stChatInput"] textarea {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    transition: border-color 0.3s, box-shadow 0.3s;
}

[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

.stSpinner > div > span {
    color: var(--text-secondary) !important;
}

/* ── Sidebar Info Box ── */
[data-testid="stAlert"] {
    background: rgba(124, 92, 252, 0.08) !important;
    border: 1px solid rgba(124, 92, 252, 0.25) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar Stat Cards ── */
.stat-card {
    background: linear-gradient(135deg, rgba(124, 92, 252, 0.12), rgba(167, 139, 250, 0.06));
    border: 1px solid rgba(124, 92, 252, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.7rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px var(--accent-glow);
}

.stat-number {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent-light);
}

.stat-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.2rem;
}

/* ── Chapter Pills ── */
.chapter-pill {
    display: inline-block;
    background: rgba(124, 92, 252, 0.1);
    border: 1px solid rgba(124, 92, 252, 0.25);
    border-radius: 8px;
    padding: 0.5rem 0.9rem;
    margin: 0.3rem 0;
    font-size: 0.85rem;
    color: var(--text-primary);
    width: 100%;
    transition: background 0.2s, transform 0.1s;
}

.chapter-pill:hover {
    background: rgba(124, 92, 252, 0.2);
    transform: translateX(4px);
}

.chapter-number {
    color: var(--accent-light);
    font-weight: 600;
    margin-right: 0.4rem;
}

/* ── Divider ── */
.custom-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.2rem 0;
}

/* ── Welcome Cards ── */
.welcome-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.welcome-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.3rem;
    transition: border-color 0.3s, transform 0.2s, box-shadow 0.3s;
    cursor: default;
}

.welcome-card:hover {
    border-color: var(--accent);
    transform: translateY(-3px);
    box-shadow: 0 8px 25px var(--accent-glow);
}

.welcome-card-icon {
    font-size: 1.5rem;
    margin-bottom: 0.6rem;
}

.welcome-card-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
    margin-bottom: 0.3rem;
}

.welcome-card-desc {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 1.5rem 0;
    color: var(--text-secondary);
    font-size: 0.78rem;
    margin-top: 2rem;
    border-top: 1px solid var(--border);
}

/* ── Scrollbar ── */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: var(--bg-primary);
}
::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--accent);
}

/* ── Bold/Strong text in answers ── */
strong, b {
    color: var(--accent-light) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Hero Header ──────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-icon">📖</div>
    <div class="hero-title">NCERT History AI Tutor</div>
    <div class="hero-subtitle">
        Your intelligent study companion for CBSE Class 10 History — 
        <em>India and the Contemporary World – II</em> (Chapters 1–5)
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Study Dashboard")

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Stats
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">5</div>
            <div class="stat-label">Chapters</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        msg_count = len(st.session_state.get("messages", []))
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{msg_count // 2}</div>
            <div class="stat-label">Questions</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### Chapters Covered")
    for idx, ch in enumerate(chapters, 1):
        st.markdown(f"""
        <div class="chapter-pill">
            <span class="chapter-number">Ch. {idx}</span> {ch['title']}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### How It Works")
    st.info(
        "This tutor uses AI-powered context pruning to find the most relevant "
        "textbook excerpts for your question, then generates a focused answer — "
        "reducing LLM costs by 70–80% while keeping answers accurate."
    )

    st.markdown("#### Tips")
    st.markdown("""
    - Ask **specific** questions for better answers
    - Mention chapter topics to improve accuracy
    - Try asking follow-up questions!
    """)


# ── Chat History ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show welcome cards when chat is empty
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-grid">
        <div class="welcome-card">
            <div class="welcome-card-icon">🌍</div>
            <div class="welcome-card-title">Nationalism in Europe</div>
            <div class="welcome-card-desc">Ask about the rise of nation-states, revolutions, and unification movements</div>
        </div>
        <div class="welcome-card">
            <div class="welcome-card-icon">🇮🇳</div>
            <div class="welcome-card-title">Indian National Movement</div>
            <div class="welcome-card-desc">Explore the freedom struggle, key leaders, and milestone events</div>
        </div>
        <div class="welcome-card">
            <div class="welcome-card-icon">🏭</div>
            <div class="welcome-card-title">Industrialisation</div>
            <div class="welcome-card-desc">Learn about the Age of Industry, factories, and the changing world of labour</div>
        </div>
        <div class="welcome-card">
            <div class="welcome-card-icon">🖨️</div>
            <div class="welcome-card-title">Print Culture</div>
            <div class="welcome-card-desc">Discover how printing transformed knowledge, culture, and society</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ── Chat Input ───────────────────────────────────────────────
if prompt := st.chat_input("Ask any question from Class 10 History..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Finding relevant passages and generating answer..."):
            chunks = get_relevant_context(prompt)
            if not chunks:
                answer = "I couldn't find relevant content for this question in the textbook."
            else:
                sources = list(set(c['chapter_title'] for c in chunks))
                answer = generate_answer(prompt, chunks)
                answer += f"\n\n---\n**Sources:** {' - '.join(sources)}"

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


# ── Footer ───────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Built with Streamlit · Powered by HuggingFace Free Inference & FAISS · NCERT History (Class 10)
</div>
""", unsafe_allow_html=True)