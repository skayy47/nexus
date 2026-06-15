import json
import uuid
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import get_settings
from core.retrieval import hybrid_retrieve
from core.llm import stream_answer
from core.contradiction import detect_contradiction
from core.transparency import build_confidence

router = APIRouter(tags=["chat"])
settings = get_settings()

# In-memory session query counter (resets on restart — acceptable for V1)
_session_counts: dict[str, int] = defaultdict(int)


class ChatRequest(BaseModel):
    question: str
    session_id: str = ""


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    session_id = request.session_id or str(uuid.uuid4())

    if _session_counts[session_id] >= settings.max_queries_per_session:
        raise HTTPException(
            status_code=429,
            detail="Session query limit reached. Please refresh to start a new session."
        )
    _session_counts[session_id] += 1

    try:
        return StreamingResponse(
            _generate(request.question, session_id),
            media_type="text/event-stream",
            headers={"X-Session-ID": session_id},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _generate(question: str, session_id: str):
    # 1. Retrieve relevant chunks
    chunks = await hybrid_retrieve(question, k=settings.retrieval_k)
    if not chunks:
        yield _sse("error", {"message": "No relevant documents found."})
        return

    # 2. Stream the answer token by token
    answer_tokens = []
    async for token in stream_answer(question, chunks):
        answer_tokens.append(token)
        yield _sse("token", {"text": token})

    full_answer = "".join(answer_tokens)

    # 3. Build confidence + source attribution
    confidence = build_confidence(chunks)
    yield _sse("confidence", confidence.model_dump())

    # 4. Check for contradictions (second LLM call)
    contradiction = await detect_contradiction(chunks)
    if contradiction:
        yield _sse("contradiction", contradiction.model_dump())

    yield _sse("done", {"answer": full_answer, "session_id": session_id})


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
