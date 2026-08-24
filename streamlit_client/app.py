import streamlit as st

from styles import CSS
from api import check_health, BackendUnavailableError, stream_query
from chat import get_messages, add_message, clear_messages, render_history, render_sources

st.set_page_config(page_title="DevDocs AI", page_icon=">_", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="app-header">
        <div class="icon">&gt;_</div>
        <h1>DevDocs AI</h1>
    </div>
    <p class="app-subtitle">Ask questions about FastAPI, Python, LlamaIndex — grounded in the actual docs.</p>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("**Connection**")

    if "backend_status" not in st.session_state:
        st.session_state.backend_status = "unknown"

    if st.button("Check backend", use_container_width=True):
        st.session_state.backend_status = "online" if check_health() else "offline"

    dot_class = st.session_state.backend_status
    labels = {"online": "Backend connected", "offline": "Backend unreachable", "unknown": "Not checked yet"}
    st.markdown(
        f'<span class="status-pill"><span class="status-dot {dot_class}"></span>{labels[dot_class]}</span>',
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("Clear conversation", use_container_width=True):
        clear_messages()
        st.rerun()

messages = get_messages()

if not messages:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">&gt;_</div>
            <p>Ask something to get started.</p>
            <p class="sub">Try “How do I create a FastAPI app?” or “How does LlamaIndex chunk documents?”</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    render_history(messages)

query = st.chat_input("Ask a question...")

if query:
    add_message("user", query)
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        answer_text = ""
        sources = []

        try:
            for event in stream_query(query):
                event_type = event.get("type")

                if event_type == "token":
                    answer_text += event.get("content", "")
                    placeholder.markdown(answer_text + " ▌")
                elif event_type == "sources":
                    sources = event.get("sources", [])
                elif event_type == "error":
                    answer_text = event.get("message", "Something went wrong.")
                    break

            placeholder.markdown(answer_text)
            render_sources(sources)
            st.session_state.backend_status = "online"

        except BackendUnavailableError:
            answer_text = '<span class="error-text">Couldn\'t reach the backend. Is the FastAPI server running?</span>'
            placeholder.markdown(answer_text, unsafe_allow_html=True)
            st.session_state.backend_status = "offline"

    add_message("assistant", answer_text, sources)

