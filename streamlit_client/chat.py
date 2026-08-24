import streamlit as st


def get_messages() -> list[dict]:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    return st.session_state.messages


def add_message(role: str, content: str, sources: list[str] | None = None) -> None:
    st.session_state.messages.append(
        {"role": role, "content": content, "sources": sources or []}
    )


def clear_messages() -> None:
    st.session_state.messages = []


def render_sources(sources: list[str]) -> None:
    if not sources:
        return
    chips = "".join(f'<span class="source-chip">{s}</span>' for s in sources)
    st.markdown(
        f'<div class="sources-wrap"><span class="sources-label">Sources</span>{chips}</div>',
        unsafe_allow_html=True,
    )


def render_history(messages: list[dict]) -> None:
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)
            render_sources(message.get("sources", []))