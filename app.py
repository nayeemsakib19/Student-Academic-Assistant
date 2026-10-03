import streamlit as st
import time
from io import BytesIO
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import dotenv_values, set_key

# ═══════════════════════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════════════════════
ENV_PATH = Path(__file__).with_name(".env")

FALLBACK_MODELS = {
    "Google Gemini": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
    "OpenAI":        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
}

PRESET_PROMPTS = {
    "None": "",
    "🤖 General Assistant":          "You are a helpful, friendly AI assistant. Answer clearly and concisely.",
    "🎓 Student Academic Assistant":  (
        "You are a knowledgeable and patient academic assistant for university students. "
        "Help students understand concepts step by step, assist with assignments, "
        "and recommend study strategies. Always encourage learning and critical thinking."
    ),
    "🏥 Health Awareness":            (
        "You are a health awareness assistant. Provide general health education, wellness tips, "
        "and lifestyle advice. NEVER diagnose diseases or prescribe medications. "
        "Always remind users to consult a licensed healthcare professional for medical concerns."
    ),
    "✍️ Writing Coach":               (
        "You are a writing coach. Help users improve their essays, emails, and creative writing. "
        "Give constructive feedback on structure, grammar, and clarity."
    ),
    "🧮 Math Tutor":                  (
        "You are a patient math tutor. Solve problems step by step, explain each step clearly, "
        "and encourage understanding of concepts rather than just memorising answers."
    ),
    "🌍 Language Partner":            (
        "You are a friendly language learning partner. Help the user practice a new language, "
        "correct mistakes gently, and explain grammar rules in simple terms."
    ),
    "💼 Career Advisor":              (
        "You are a career advisor for students. Help with resume writing, interview preparation, "
        "career path guidance, and professional development tips."
    ),
    "✏️ Custom":                      "__custom__",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  .env helpers  –  every change is immediately persisted
# ═══════════════════════════════════════════════════════════════════════════════
def _env() -> dict:
    return dotenv_values(str(ENV_PATH)) if ENV_PATH.exists() else {}

def _save(key: str, value: str):
    ENV_PATH.touch(exist_ok=True)
    last_err = None
    for _ in range(3):
        try:
            set_key(str(ENV_PATH), key, str(value))
            return
        except OSError as e:
            last_err = e
            time.sleep(0.08)

    env_data = _env()
    env_data[key] = str(value)
    _write_env_direct(env_data)

    if last_err:
        raise RuntimeError(f"Failed to save {key} to .env: {last_err}")


def _write_env_direct(values: dict):
    lines = [f'{k}="{str(v).replace("\\", "\\\\").replace("\"", "\\\"")}"' for k, v in values.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _save_many(values: dict):
    for key, value in values.items():
        _save(key, value)

# ═══════════════════════════════════════════════════════════════════════════════
#  LLM helpers
# ═══════════════════════════════════════════════════════════════════════════════
def normalize(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    return str(content)


def validate_api_key(provider: str, api_key: str):
    try:
        if provider == "Google Gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            list(genai.list_models())
        else:
            from openai import OpenAI
            OpenAI(api_key=api_key).models.list()
        return True, "Valid"
    except Exception as e:
        return False, str(e)


def fetch_models(provider: str, api_key: str) -> list:
    try:
        if provider == "Google Gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models = sorted([
                m.name.replace("models/", "")
                for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods and "gemini" in m.name
            ])
            return models or FALLBACK_MODELS[provider]
        else:
            from openai import OpenAI
            models = sorted([
                m.id for m in OpenAI(api_key=api_key).models.list()
                if m.id.startswith("gpt")
            ])
            return models or FALLBACK_MODELS[provider]
    except Exception:
        return FALLBACK_MODELS[provider]


def get_llm(provider: str, api_key: str, model: str, temperature: float):
    if provider == "Google Gemini":
        return ChatGoogleGenerativeAI(
            model=model, google_api_key=api_key, temperature=temperature
        )
    return ChatOpenAI(model=model, openai_api_key=api_key, temperature=temperature)


def stream_chat(llm, system_prompt: str, history: list, user_text: str):
    msgs = []
    if system_prompt.strip():
        msgs.append(SystemMessage(content=system_prompt.strip()))
    for m in history:
        if m["role"] == "user":
            msgs.append(HumanMessage(content=m["content"]))
        else:
            msgs.append(AIMessage(content=m["content"]))
    msgs.append(HumanMessage(content=user_text))
    for chunk in llm.stream(msgs):
        t = normalize(chunk.content)
        if t:
            yield t


def extract_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = (uploaded_file.name or "").lower()
    data = uploaded_file.getvalue()
    if not data:
        return ""
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(data)).pages).strip()
        except Exception:
            return ""
    if name.endswith(".docx"):
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(BytesIO(data)).paragraphs if p.text.strip()).strip()
        except Exception:
            return ""
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return ""

# ═══════════════════════════════════════════════════════════════════════════════
#  Page config  (must be first Streamlit call)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Smart AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
#  Session state  –  hydrated from .env on first load
# ═══════════════════════════════════════════════════════════════════════════════
if "messages" not in st.session_state:
    env = _env()
    saved_provider = env.get("PROVIDER", "Google Gemini")
    key_name = "GOOGLE_API_KEY" if saved_provider == "Google Gemini" else "OPENAI_API_KEY"
    st.session_state.update({
        "messages":       [],
        "provider":       saved_provider,
        "api_key":        env.get(key_name, ""),
        "model":          env.get("MODEL", ""),
        "temperature":    float(env.get("TEMPERATURE", "0.7")),
        "system_prompt":  env.get("SYSTEM_PROMPT", ""),
        "fetched_models": [],
        "settings_open":  False,
        "notif":          None,
    })

# Migrate old tuple history
if st.session_state.messages and isinstance(st.session_state.messages[0], (tuple, list)):
    st.session_state.messages = [
        {"role": r, "content": c, "file": ""} for r, c in st.session_state.messages
    ]

S = st.session_state   # shorthand


def _infer_preset(prompt: str) -> str:
    if not prompt.strip():
        return "None"
    for name, value in PRESET_PROMPTS.items():
        if value not in ("", "__custom__") and prompt == value:
            return name
    return "✏️ Custom"


def _on_preset_change():
    selected = st.session_state.get("settings_preset", "None")
    preset_text = PRESET_PROMPTS.get(selected, "")
    if preset_text == "__custom__":
        return
    st.session_state["settings_prompt"] = "" if selected == "None" else preset_text

# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════════
title_col, action_col = st.columns([6, 2])
with title_col:
    st.title("Smart AI Assistant")
    st.caption("LangChain with Gemini and OpenAI")

with action_col:
    btn_a, btn_b = st.columns(2)
    with btn_a:
        if st.button("⚙️", key="btn_settings", use_container_width=True, help="Open settings to configure API keys, model, and system prompt."):
            S.settings_open = not S.settings_open
            if S.settings_open:
                S.settings_provider = S.provider
                S.settings_api_key = S.api_key
                S.settings_model = S.model
                S.settings_temperature = float(S.temperature)
                S.settings_prompt = S.system_prompt
                S.settings_preset = _infer_preset(S.system_prompt)
                S.settings_models = S.fetched_models[:] if S.fetched_models else []
            st.rerun()
    with btn_b:
        if st.button("🗑️", key="btn_clear", use_container_width=True, help="Clear the chat history."):
            S.messages = []
            st.rerun()

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
#  SETTINGS PANEL
# ═══════════════════════════════════════════════════════════════════════════════
if S.settings_open:
    st.subheader("Settings")

    st.selectbox("Provider", ["Google Gemini", "OpenAI"], key="settings_provider")

    st.text_input(
        "API Key",
        type="password",
        key="settings_api_key",
        placeholder="Paste your key here",
    )
    if S.settings_provider == "Google Gemini":
        st.caption("Get a Gemini API key: https://aistudio.google.com/app/apikey")
    else:
        st.caption("Get an OpenAI API key: https://platform.openai.com/api-keys")

    ka_col, km_col = st.columns(2)
    with ka_col:
        if st.button("Validate API Key", key="btn_validate", use_container_width=True):
            if S.settings_api_key.strip():
                with st.spinner("Checking API key..."):
                    ok, msg = validate_api_key(S.settings_provider, S.settings_api_key.strip())
                if ok:
                    S.notif = ("success", "API key looks valid.")
                else:
                    S.notif = ("error", f"Invalid key - {msg[:120]}")
            else:
                S.notif = ("warning", "Enter a key first.")
            st.rerun()
    with km_col:
        if st.button("Load Models", key="btn_models", use_container_width=True):
            key_to_use = S.settings_api_key.strip()
            if key_to_use:
                with st.spinner("Fetching models..."):
                    models = fetch_models(S.settings_provider, key_to_use)
                S.settings_models = models
                if models and S.settings_model not in models:
                    S.settings_model = models[0]
                if models:
                    S.notif = ("success", f"Loaded {len(models)} models.")
                else:
                    S.notif = ("error", "No models found. Check your API key.")
            else:
                S.notif = ("warning", "Set your API key first.")
            st.rerun()

    model_options = S.settings_models if S.get("settings_models") else []
    if model_options:
        if S.settings_model not in model_options:
            S.settings_model = model_options[0]
        st.selectbox("Model", model_options, key="settings_model")
    else:
        st.caption("No models loaded yet. Click Load Models.")

    st.slider(
        "Temperature",
        0.0,
        1.0,
        step=0.05,
        key="settings_temperature",
        help="0 = focused and factual, 1 = creative and varied",
    )

    st.selectbox(
        "System Prompt Preset",
        list(PRESET_PROMPTS.keys()),
        key="settings_preset",
        on_change=_on_preset_change,
    )
    st.text_area(
        "System Prompt",
        key="settings_prompt",
        height=120,
        placeholder="How should the AI behave? (optional)",
    )

    save_col, close_col = st.columns(2)
    with save_col:
        if st.button("Save Settings", key="btn_save_settings", type="primary", use_container_width=True):
            S.provider = S.settings_provider
            S.api_key = S.settings_api_key.strip()
            S.model = S.settings_model
            S.temperature = float(S.settings_temperature)
            S.system_prompt = S.settings_prompt
            S.fetched_models = S.settings_models[:] if S.get("settings_models") else []

            env_k = "GOOGLE_API_KEY" if S.provider == "Google Gemini" else "OPENAI_API_KEY"
            values_to_save = {
                "PROVIDER": S.provider,
                "TEMPERATURE": str(S.temperature),
                "SYSTEM_PROMPT": S.system_prompt,
            }
            if S.api_key:
                values_to_save[env_k] = S.api_key
            if S.model:
                values_to_save["MODEL"] = S.model

            try:
                _save_many(values_to_save)
                S.notif = ("success", "Settings saved.")
                S.settings_open = False
            except Exception as e:
                S.notif = ("error", f"Could not save settings to .env: {e}")
            st.rerun()
    with close_col:
        if st.button("Close without saving", key="btn_close", use_container_width=True):
            S.settings_open = False
            S.notif = ("warning", "Settings closed without saving.")
            st.rerun()

    st.divider()

# ── Notification toast ────────────────────────────────────────────────────────
if S.notif:
    kind, msg = S.notif
    if kind == "success":
        st.success(msg)
    elif kind == "error":
        st.error(msg)
    else:
        st.warning(msg)
    S.notif = None

# ── Sync locals ───────────────────────────────────────────────────────────────
provider      = S.provider
api_key       = S.api_key
model         = S.model
temperature   = float(S.temperature)
system_prompt = S.system_prompt

# ═══════════════════════════════════════════════════════════════════════════════
#  STATUS
# ═══════════════════════════════════════════════════════════════════════════════
ready = bool(api_key and model)
status_text = "Ready" if ready else "Setup required"
st.caption(
    f"Provider: {provider} | Model: {model or 'No model selected'} | Temperature: {temperature:.2f} | Status: {status_text}"
)

# ═══════════════════════════════════════════════════════════════════════════════
#  CHAT AREA
# ═══════════════════════════════════════════════════════════════════════════════
if not S.messages:
    st.caption(
        "Open Settings to add your API key and select a model, select a system prompt then start chatting. You can also attach a PDF, DOCX, or text file from the chat input."
    )

for msg in S.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("file"):
            st.caption(f"📎 {msg['file']}")

# ── Chat input  (📎 paperclip built-in via accept_file) ───────────────────────
prompt = st.chat_input(
    "Message AI Assistant…",
    accept_file=True,
    file_type=["pdf", "docx", "txt", "md", "csv", "json", "py", "log"],
)

# ═══════════════════════════════════════════════════════════════════════════════
#  PROCESS INPUT
# ═══════════════════════════════════════════════════════════════════════════════
if prompt:
    user_text = (prompt.text or "").strip()
    files     = prompt.files if hasattr(prompt, "files") else []

    file_name    = ""
    file_context = ""
    if files:
        extracted = extract_text(files[0])
        if extracted.strip():
            file_name    = files[0].name
            file_context = extracted[:12000]

    if not user_text and not file_context:
        st.stop()

    if not api_key.strip():
        st.warning("⚠️ Tap ⚙️ in the toolbar and add your API key first.")
        st.stop()
    if not model:
        st.warning("⚠️ Tap ⚙️, click 'Load Models', and select a model.")
        st.stop()

    llm = get_llm(provider, api_key.strip(), model, temperature)

    if file_context and user_text:
        final_input = f"{user_text}\n\n[File: {file_name}]\n---\n{file_context}"
    elif file_context:
        final_input = (
            f"[File: {file_name}]\n---\n{file_context}"
            "\n\nPlease summarise or analyse this file."
        )
    else:
        final_input = user_text

    with st.chat_message("user"):
        if user_text:
            st.markdown(user_text)
        if file_name:
            st.caption(f"📎 {file_name}")

    try:
        with st.chat_message("assistant"):
            reply = st.write_stream(
                stream_chat(llm, system_prompt, S.messages, final_input)
            )
        stored = user_text or f"[File: {file_name}]"
        S.messages.append({"role": "user",      "content": stored, "file": file_name})
        S.messages.append({"role": "assistant", "content": reply,  "file": ""})
    except Exception as e:
        err = str(e)
        if any(k in err.lower() for k in ("api_key", "api key", "authentication",
                                           "permission", "access", "invalid", "unauthorized")):
            st.error("❌ API key invalid or unauthorised — tap ⚙️ to update it.")
        elif any(k in err.lower() for k in ("quota", "rate", "resource_exhausted", "limit")):
            st.error("❌ Quota or rate limit hit — wait a moment or switch API keys.")
        else:
            st.error(f"❌ {err}")
