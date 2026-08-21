# rag/generator.py

from llama_index.llms.ollama import Ollama
from llama_index.core import PromptTemplate

from app.rag.retriever import retrieve

from app.config import settings
from app.utils.logger import logger

from opentelemetry import trace

tracer = trace.get_tracer("devdocs")


llm = Ollama(
    model = settings.OLLAMA_MODEL_NAME,
    base_url = settings.OLLAMA_BASE_URL,
    request_timeout = settings.OLLAMA_REQUEST_TIMEOUT,
    context_window = settings.OLLAMA_CONTEXT_WINDOW,
)


prompt_QA = PromptTemplate(
    """
You are a software documentation assistant.

Answer the user's question using ONLY the documentation provided below.

STRICT RULES:
- Do NOT use your own knowledge.
- Do NOT infer information that is not explicitly supported by the documentation.
- If the documentation does not contain enough information to answer,
  say: "The provided documentation does not contain enough information to answer this question."
- Keep the answer concise and technically accurate.
- When making a factual claim, cite the relevant source using:
  [Source: <file_path>]
- Do not cite sources that do not support the claim.

Documentation:
{context}

Question:
{query}

Answer:
"""
)


def generate_answer_stream(query: str):
    with tracer.start_as_current_span("rag.query") as span:
        # telemetry
        span.set_attribute("rag.query", query)

        results = retrieve(
            query,
            top_k=settings.FINAL_TOP_K,
            candidate_k=settings.CANDIDATE_TOP_K,
        )

        # telemetry
        span.set_attribute("rag.retrieved_count", len(results))
        if results:
            span.set_attribute(
                "rag.top_score",
                results[0].score if results[0].score is not None else 0.0
            )

        context = "\n\n---\n\n".join(
            f"[Source: {result.node.metadata.get('file_path', 'unknown')}]\n"
            f"{result.node.get_content()}"
            for result in results
        )

        prompt = prompt_QA.format(
            context=context,
            query=query,
        )

        response = llm.stream_complete(prompt)

        response_text = ""

        for chunk in response:
            response_text += chunk.delta
            yield {
                "type": "token",
                "content": chunk.delta,
            }

        # telemetry
        span.set_attribute(
            "rag.response_length",
            len(response_text)
        )

        sources = [
            result.node.metadata.get("file_path", "unknown")
            for result in results
        ]

        yield {
            "type": "sources",
            "sources": sources,
        }


def generate_answer(query: str):
    with tracer.start_as_current_span("rag.query") as span:
        #telemetry
        span.set_attribute("rag.query", query)

        results = retrieve(query, top_k=settings.FINAL_TOP_K, candidate_k=settings.CANDIDATE_TOP_K)

        #telemetry
        span.set_attribute("rag.retrieved_count", len(results))
        if results:
            span.set_attribute(
                "rag.top_score",
                results[0].score if results[0].score is not None else 0.0
            )

        # --- intermediate logging ---
        # for i, result in enumerate(results, 1):
        #     logger.info(
        #         f"Result {i} | "
        #         f"Score: {result.score:.4f} | "
        #         f"Source: {result.node.metadata.get('file_path')}"
        #     )

        context = "\n\n---\n\n".join(
            f"[Source: {result.node.metadata.get('file_path', 'unknown')}]\n"
            f"{result.node.get_content()}"
            for result in results
        )

        """ # So the LLM receives:
            [Source: data/fastapi/docs/en/docs/tutorial/first-steps.md]
            First Steps...
            ...
        
        """

        prompt = prompt_QA.format(
            context = context,
            query = query,
        )

        response = llm.complete(prompt)

        # telemtry
        span.set_attribute("rag.response_length", len(response.text))

    # return doc source list 
    sources = [
        result.node.metadata.get("file_path", "unknown")
        for result in results
    ]

    return response.text, sources


if __name__ == "__main__":
    query = "How do I create a FastAPI application?"
    queries = [
        # 1. Direct answer — should work
        "How do I create a FastAPI application?",

        # 2. Specific technical question — tests retrieval precision
        "How do I create a VectorStoreIndex in LlamaIndex?",

        # 3. Conceptual — tests whether the chunks contain enough context
        "How does LlamaIndex handle document chunking?",

        # 4. Another specific implementation question
        "How can I use Qdrant with LlamaIndex?",

        # 5. Out-of-scope — should refuse instead of hallucinating
        "How do I deploy a FastAPI application to AWS?",
    ]

    for query in queries:
        answer, sources = generate_answer(query)

        logger.info("\nAnswer:\n")
        logger.info(answer)

        # logger.info("\nSources:\n")
        # for source in sources:
        #     logger.info(source)

