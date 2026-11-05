# ME - look and feel for the web app
# Navy and white with an orange dot, Lora headings, and the animated "ME." logo.

import streamlit as st

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,700;1,400&family=Inter:wght@400;600&display=swap');

html, body, .stApp, p, label, input, textarea, button { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 2.5rem; }
h1, h2, h3 { font-family: 'Lora', serif !important; color: #14213D !important; }

.me-hero {
    background: #14213D;
    border-radius: 16px;
    padding: 28px 24px 24px;
    text-align: center;
    margin-bottom: 20px;
}
.me-logo {
    font-family: 'Lora', serif;
    font-weight: 700;
    font-size: 76px;
    line-height: 1;
    color: #FFFFFF;
    display: inline-block;
    animation: me-flip 1.3s cubic-bezier(.2, .8, .2, 1) both;
}
.me-dot {
    color: #E07A3F;
    display: inline-block;
    animation: me-pop .5s 1.2s both;
}
.me-tag {
    font-family: 'Lora', serif;
    color: #FFFFFF;
    font-size: 20px;
    margin-top: 12px;
}
.me-tag em { color: #AEC2EA; }
.me-hero.small { padding: 14px; }
.me-hero.small .me-logo { font-size: 40px; }

@keyframes me-flip {
    0%   { transform: perspective(700px) rotateY(-180deg); opacity: 0; }
    50%  { opacity: 1; }
    100% { transform: perspective(700px) rotateY(0deg); opacity: 1; }
}
@keyframes me-pop {
    0%   { transform: scale(0); }
    70%  { transform: scale(1.5); }
    100% { transform: scale(1); }
}
@media (prefers-reduced-motion: reduce) {
    .me-logo, .me-dot { animation: none; }
}

div.stButton > button {
    border: 1.5px solid #14213D;
    border-radius: 10px;
    color: #14213D;
}
div.stButton > button:hover { border-color: #E07A3F; color: #E07A3F; }
</style>
"""

HERO = """
<div class="me-hero">
  <div class="me-logo">ME<span class="me-dot">.</span></div>
  <div class="me-tag">Your mind, understood. <em>And it belongs to you.</em></div>
</div>
"""

HERO_SMALL = """
<div class="me-hero small">
  <div class="me-logo">ME<span class="me-dot">.</span></div>
</div>
"""


def apply_style(big_logo):
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown(HERO if big_logo else HERO_SMALL, unsafe_allow_html=True)
