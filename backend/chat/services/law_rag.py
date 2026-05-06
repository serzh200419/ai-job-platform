import logging
import math

from django.conf import settings
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

_LEGAL_KEYWORDS = [
    # English
    "labor law", "labour law", "employment law", "work contract", "employment contract",
    "termination", "dismissal", "fired", "layoff", "redundancy",
    "overtime", "working hours", "rest period", "vacation", "annual leave",
    "sick leave", "maternity leave", "paternity leave", "parental leave",
    "minimum wage", "salary", "wage", "compensation", "severance",
    "probation", "trial period", "notice period",
    "discrimination", "harassment", "workplace rights",
    "union", "collective agreement", "strike",
    "pension", "social insurance", "benefits",
    "occupational safety", "workplace safety", "injury",
    # Armenian (transliterated common terms)
    "ashkhatanqayin", "ashkhatavardz", "ardzakutyun",
    "amsorya", "vcharel", "depqum", "paymanagir",
]


def is_legal_query(message: str) -> bool:
    lower = message.lower()
    return any(kw in lower for kw in _LEGAL_KEYWORDS)


def embed_text(text: str) -> list[float]:
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
    )
    return resp.data[0].embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_similar(query: str, top_k: int = 3) -> list[str]:
    from chat.models import LawDocument

    docs = list(LawDocument.objects.exclude(embedding=[]).only("content", "embedding"))
    if not docs:
        return []

    try:
        query_vec = embed_text(query)
    except OpenAIError as exc:
        logger.warning("Embedding failed for RAG query: %s", exc)
        return []

    scored = [
        (doc, _cosine_similarity(query_vec, doc.embedding))
        for doc in docs
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc.content for doc, _ in scored[:top_k]]


def build_law_context(message: str) -> str:
    if not is_legal_query(message):
        print("[RAG] No legal keywords detected — skipping embedding search.")
        return ""

    print("[RAG] Legal query detected — searching embeddings...")
    chunks = search_similar(message, top_k=3)
    if not chunks:
        print("[RAG] No matching chunks found in LawDocument table.")
        return ""

    print(f"[RAG] Retrieved {len(chunks)} chunk(s). Preview: {chunks[0][:120]!r}")
    return "\n\n---\n\n".join(chunks)
