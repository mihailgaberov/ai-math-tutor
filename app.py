import streamlit as st

from tutor.chat import MODEL, chat, is_ollama_running, model_is_available

st.set_page_config(page_title="Maximo — Math Tutor", page_icon="🧮", layout="centered")

st.title("🧮 Maximo — Your Math Tutor")
st.caption("Type a math problem and I'll help you figure it out — step by step!")

# ── Health checks ────────────────────────────────────────────────────────────
if not is_ollama_running():
    st.error(
        "Ollama is not running. Please start it with `ollama serve` in your terminal.",
        icon="🚨",
    )
    st.stop()

if not model_is_available():
    st.warning(
        f"Model **{MODEL}** is not pulled yet. Run `ollama pull {MODEL}` in your terminal.",
        icon="⚠️",
    )
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎒 Session")
    st.caption(f"Model: `{MODEL}`")
    if st.button("🔄 New problem"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.markdown(
        "**How it works:**\n"
        "- Type a math problem below\n"
        "- Maximo will guide you with hints\n"
        "- Try to find the answer yourself!\n"
        "- Ask for another nudge if you're stuck"
    )

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = "🧮" if msg["role"] == "assistant" else "🧒"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Type your math problem here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧒"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧮"):
        with st.spinner("Maximo is thinking..."):
            reply = chat(st.session_state.messages)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
