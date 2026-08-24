import json
from typing import Iterator

import requests
import streamlit as st

API_BASE_URL = st.secrets["API_BASE_URL"]
STREAM_ENDPOINT = st.secrets["STREAM_ENDPOINT"]
QUERY_ENDPOINT = st.secrets["QUERY_ENDPOINT"]
HEALTH_ENDPOINT = st.secrets["HEALTH_ENDPOINT"]
REQUEST_TIMEOUT = st.secrets["REQUEST_TIMEOUT"]


class BackendUnavailableError(Exception):
    """Raised when the FastAPI backend can't be reached at all."""


def check_health() -> bool:
    try:
        requests.get(HEALTH_ENDPOINT, timeout=3)
        return True
    except requests.exceptions.RequestException:
        return False


def stream_query(query: str) -> Iterator[dict]:
    """POST a query to the streaming endpoint and yield each parsed SSE event."""
    try:
        response = requests.post(
            STREAM_ENDPOINT,
            json={"query": query},
            stream=True,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise BackendUnavailableError(str(exc)) from exc

    buffer = ""
    with response:
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if not chunk:
                continue

            buffer += chunk
            while "\n\n" in buffer:
                raw_event, buffer = buffer.split("\n\n", 1)

                if not raw_event.startswith("data:"):
                    continue

                data = raw_event[len("data:"):].strip()
                if not data:
                    continue

                try:
                    yield json.loads(data)
                except json.JSONDecodeError:
                    continue


def query_once(query: str) -> dict:
    """POST to the non-streaming endpoint. Returns the parsed JSON body."""
    try:
        response = requests.post(
            QUERY_ENDPOINT,
            json={"query": query},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise BackendUnavailableError(str(exc)) from exc