# ChatbotCore

## Overview
ChatbotCore is the Python backend that powers the T3V chatbot. It classifies user intent, routes requests through a LangGraph workflow, retrieves knowledge-base content with RAG, queries the movie catalog API, and synthesizes final answers for the client apps.

## Key responsibilities
- **Intent classification** for SERVICE vs MOVIE vs OTHER queries.
- **LangGraph orchestration** to route queries through specialized nodes.
- **Service RAG** with self-refinement against T3V documents and embeddings.
- **Movie search** via the internal movie API endpoint.
- **Web search fallback** and response synthesis when needed.
- **ReAct reasoning** for low-confidence queries.

## Architecture flow (high level)
1. **Classifier** (`classifier.py`) assigns the query category and confidence.
2. **Router** (`graph.py`) selects the best node (service, movie, web, or ReAct).
3. **Tools** (`service_tools.py`, `movie_tools.py`, `search_tools.py`) collect data.
4. **Synthesizer** (`response_tools.py`) composes the final answer.

## Entry points
- **CLI demo:** `main.py`
- **HTTP API:** `chat_graphapi.py` (FastAPI)
- **Graph builder:** `graph.py`

## Configuration
Configuration lives in `config.py` and `.env`. It wires up the LLM provider, memory, and API endpoints used by the chatbot. Provide the required API keys and service URLs before running.

## Data & embeddings
Training assets and vector stores live under `data/` and `embeddings/`. The `EmbeddingManager` builds a Chroma collection from the T3V training PDF for retrieval-augmented answers.

## Directory highlights
- `classifier.py` – intent detection and routing hints.
- `document_tools.py` – RAG helpers and document retrieval.
- `movie_tools.py` – movie API lookups and formatting.
- `react_agent.py` – ReAct-style reasoning for ambiguous queries.
- `response_tools.py` – answer synthesis and formatting.
