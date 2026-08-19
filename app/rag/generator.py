# rag/generator.py

from llama_index.llms.ollama import Ollama
from llama_index.core import PromptTemplate

from app.rag.retriever import retrieve

from app.config import settings
from app.utils.logger import logger


llm = Ollama(
    model = settings.OLLAMA_MODEL_NAME,
    base_url = settings.OLLAMA_BASE_URL,
    request_timeout = settings.OLLAMA_REQUEST_TIMEOUT,
    context_window = settings.OLLAMA_CONTEXT_WINDOW,
)


prompt_QA = PromptTemplate(
    """
    You are a helpful software documentation assistant.

    Answer the question using ONLY the provided documentation.

    Documentation:
    {context}

    Question:
    {query}

    Answer:
    """
)


def generate_answer(query: str):
    nodes = retrieve(query)

    prompt = prompt_QA.format(
        context = "\n\n---\n\n".join([node.get_content() for node in nodes]),
        query = query,
    )

    response = llm.complete(prompt)

    return response.text


if __name__ == "__main__":
    query = "How do I create a FastAPI application?"

    answer = generate_answer(query)

    logger.info("\nAnswer:\n")
    logger.info(answer)

