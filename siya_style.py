# Siya - the look: a calm, dark, premium chat
# Only this app uses it; the public study app keeps its own light ME look.

import streamlit as st
import streamlit.components.v1 as components

COLORS = {
    "night": "#0B0C10",      # page
    "surface": "#15161C",    # Siya's messages, inputs
    "raised": "#1C1D25",     # hover, borders
    "line": "#2A2B35",
    "text": "#EDE8E1",       # warm off-white
    "muted": "#9C98A3",
    "gold": "#D9A75A",       # accent, like a diya's flame
    "you": "#2A2218",        # your messages: a warm, dark gold
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Inter:wght@400;500&display=swap');

:root {{
  --night: {night}; --surface: {surface}; --raised: {raised}; --line: {line};
  --text: {text}; --muted: {muted}; --gold: {gold}; --you: {you};
}}

/* Page (html and body too: the phone shows them behind its status bar) */
:root {{ color-scheme: dark; }}
html, body, [data-testid="stHeader"], .stApp, [data-testid="stAppViewContainer"], [data-testid="stBottom"], [data-testid="stBottom"] > div {{
  background: var(--night) !important;
}}
.stApp {{
  background-image: radial-gradient(1200px 500px at 50% -180px, rgba(217,167,90,0.13), transparent 70%) !important;
  background-attachment: fixed !important;
}}
html, body, .stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button {{
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--text);
}}
.block-container {{ max-width: 720px; padding: 1.2rem 1rem 6rem; }}

/* Hide Streamlit's own chrome so it feels like an app */
[data-testid="stHeader"] {{ display: none !important; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"],
#MainMenu, footer {{ display: none !important; }}

/* Header */
.siya-header {{ text-align: center; padding: 18px 0 22px; }}
.siya-mark {{ font-size: 26px; line-height: 1; opacity: .95; filter: drop-shadow(0 0 12px rgba(217,167,90,.45)); }}
.siya-name {{
  font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 46px; letter-spacing: .02em;
  color: var(--text); line-height: 1.05; margin-top: 6px;
}}
.siya-tag {{
  color: var(--muted); font-size: 11px; letter-spacing: .28em; text-transform: uppercase; margin-top: 6px;
}}
.siya-rule {{ width: 44px; height: 1px; margin: 14px auto 0; background: linear-gradient(90deg, transparent, var(--gold), transparent); }}

/* Messages: every paragraph is its own bubble, like a real chat */
[data-testid="stChatMessage"] {{
  background: transparent !important; padding: 3px 0; gap: 10px; align-items: flex-end;
}}
[data-testid="stChatMessageContent"] {{
  background: none; border: 0; padding: 0; max-width: 84%; display: flex; flex-direction: column;
}}
[data-testid="stChatMessageContent"] > [data-testid="stVerticalBlock"] {{ gap: 5px; }}
[data-testid="stChatMessageContent"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{ height: auto !important; }}
[data-testid="stChatMessageContent"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] > [data-testid="stMarkdown"] {{
  margin-bottom: 0 !important;
}}
[data-testid="stChatMessageContent"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] > [data-testid="stMarkdown"] [data-testid="stMarkdownContainer"] {{
  display: inline-block; width: fit-content !important; max-width: 100%; margin-bottom: 0 !important; background: var(--surface); border: 1px solid var(--line);
  border-radius: 20px 20px 20px 6px; padding: 9px 14px; box-shadow: 0 1px 0 rgba(255,255,255,.02) inset;
}}
[data-testid="stChatMessageContent"] p {{ font-size: 15.5px; line-height: 1.5; margin: 0 !important; }}

/* "The verses Siya used": a small, quiet pill under the bubble */
[data-testid="stChatMessageContent"] [data-testid="stExpander"] {{ margin-top: 2px; width: fit-content !important; min-width: 220px; }}
[data-testid="stChatMessageContent"] [data-testid="stExpander"] details {{
  border-color: rgba(217,167,90,.22) !important; border-radius: 12px; background: rgba(217,167,90,.04);
}}
[data-testid="stChatMessageContent"] [data-testid="stExpander"] summary {{ padding: 6px 12px; min-height: 0; }}

/* Siya's lotus */
[data-testid="stChatMessage"] > div:first-child {{
  width: 32px; height: 32px; min-width: 32px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 16px; background: var(--raised) !important;
  border: 1px solid rgba(217,167,90,.35); box-shadow: 0 0 14px rgba(217,167,90,.12);
}}

/* Your messages: right side, warm gold, no avatar */
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {{ flex-direction: row-reverse; }}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) > div:first-child {{ display: none; }}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stChatMessageContent"] {{
  margin-left: auto; align-items: flex-end;
}}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stMarkdownContainer"] {{
  background: var(--you) !important; border-color: rgba(217,167,90,.28) !important;
  border-radius: 20px 20px 6px 20px !important; text-align: left;
}}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stElementContainer"] {{
  display: flex; justify-content: flex-end; width: 100% !important;
}}

/* Chat input */
[data-testid="stChatInput"] {{
  background: var(--surface) !important; border: 1px solid var(--line) !important; border-radius: 24px !important;
}}
[data-testid="stChatInput"]:focus-within {{ border-color: rgba(217,167,90,.6) !important; box-shadow: 0 0 0 3px rgba(217,167,90,.12); }}
[data-testid="stChatInput"] div {{ background: transparent !important; }}
[data-testid="stChatInput"] textarea {{ color: var(--text) !important; caret-color: var(--gold); background: transparent !important; }}
[data-testid="stChatInput"] textarea::placeholder {{ color: var(--muted) !important; }}
[data-testid="stChatInputSubmitButton"] {{ background: var(--gold) !important; border-radius: 50% !important; }}
[data-testid="stChatInputSubmitButton"] svg {{ fill: var(--night) !important; color: var(--night) !important; }}

/* Password box */
[data-testid="stTextInput"] div {{ background: transparent !important; }}
[data-testid="stTextInput"] div[data-baseweb="input"] {{
  background: var(--surface) !important; border: 1px solid var(--line) !important; border-radius: 14px !important;
}}
[data-testid="stTextInput"] input {{ color: var(--text) !important; background: transparent !important; caret-color: var(--gold); }}
[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {{ border-color: rgba(217,167,90,.6) !important; }}
[data-testid="stTextInput"] button svg {{ color: var(--muted) !important; }}

/* Expanders (verses, notes) */
[data-testid="stExpander"] details {{
  background: transparent; border: 1px solid var(--line) !important; border-radius: 14px;
}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {{ color: var(--muted) !important; font-size: 13px; }}
[data-testid="stExpander"] summary:hover p {{ color: var(--gold) !important; }}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{ font-size: 14px; }}
[data-testid="stExpander"] em {{ color: var(--muted); }}
[data-testid="stExpander"] strong {{ color: var(--gold); font-weight: 500; }}
[data-testid="stExpander"] svg {{ color: var(--muted) !important; }}

/* Small text, spinner, alerts */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: var(--muted) !important; }}
[data-testid="stSpinner"], [data-testid="stSpinner"] p {{ color: var(--muted) !important; font-size: 13px; }}
[data-testid="stAlert"] {{ background: var(--surface) !important; border: 1px solid var(--line); border-radius: 14px; }}
</style>
""".format(**COLORS)


# Tells the phone's browser to colour its status bar and home-screen app dark, and names the app "Siya".
THEME_SCRIPT = """
<script>
const head = window.parent.document.head;
function setMeta(name, content) {{
  let tag = head.querySelector(`meta[name="${{name}}"]`);
  if (!tag) {{ tag = window.parent.document.createElement("meta"); tag.name = name; head.appendChild(tag); }}
  tag.content = content;
}}
setMeta("theme-color", "{night}");
setMeta("apple-mobile-web-app-capable", "yes");
setMeta("mobile-web-app-capable", "yes");
setMeta("apple-mobile-web-app-status-bar-style", "black-translucent");
setMeta("apple-mobile-web-app-title", "Siya");
window.parent.document.documentElement.style.background = "{night}";
window.parent.document.body.style.background = "{night}";
</script>
""".format(**COLORS)


def siya_style():
    st.markdown(CSS, unsafe_allow_html=True)
    components.html(THEME_SCRIPT, height=0)


def header(tagline):
    st.markdown(
        f"""<div class="siya-header">
  <div class="siya-mark">🪷</div>
  <div class="siya-name">Siya</div>
  <div class="siya-tag">{tagline}</div>
  <div class="siya-rule"></div>
</div>""",
        unsafe_allow_html=True,
    )
